import os
import unittest
import eups
#import inspect

import lsst.utils.tests as tests

from lsst.pex.policy import Policy, UrnPolicyFile
from lsst.pex.exceptions import LsstCppException

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# TODO: test cross-package loading more thoroughly -- mix up the packages and
# repositories in a deeply nested and linked policy file.

class UrnPolicyFileTestCase(unittest.TestCase):
    def assertRaiseLCE(self, excClass, excMsg, callableObj, failMsg, *args, **kwargs):
        """
        Expect callableObj(args, kwargs) to raise an LsstCppException that wraps
        the class specified by excClass, and carrying a message that contains
        excMsg.

        excClass: the subclass of LsstCppException we expect to see
        excMsg: a substring of the message it should carry
        callableObj: the thing that, when called, should raise an exception
        failMsg: the assertion message if this fails
        args, kwargs (optional): arguments to pass to callableObj
        """
        try:
            callableObj(*args, **kwargs)
        except LsstCppException, e:
            self.assert_(isinstance(e, LsstCppException))
            lce = "lsst.pex.exceptions.exceptionsLib.LsstCppException"
            self.assert_(str(e.__class__).find(lce) > 0,
                         failMsg + ": expected an " + lce + ", found a " 
                         + str(e.__class__))
            self.assert_(len(e.args) == 1)
            nested = e.args[0] # the real exception that was thrown
            self.assert_(str(nested.__class__).find(excClass) > 0,
                         failMsg + ": expected a " + excClass + "; found a " 
                         + str(nested.__class__))
            self.assert_(str(e).find(excMsg) > 0, 
                         failMsg + ": expected to see the message \"" + excMsg 
                         + "\"; actual message was \"" + str(e) + "\".")
        else:
            self.fail(failMsg + ": did not raise " + excClass)

    examplesDir = None
    def getExamples(self, filename=None):
        if not self.examplesDir:
            self.examplesDir = os.path.join(eups.productDir("pex_policy"),
                                            "examples")
        if filename:
            return os.path.join(self.examplesDir, filename)
        else:
            return self.examplesDir

    def testReference(self):
        addr = "pex_policy:examples:EventTransmitter_policy.paf"
        p = Policy()

        p.set("transmitter.logVerbosity", "not")
        UrnPolicyFile(addr).load(p)
        self.assert_(p.get("transmitter.logVerbosity") == "debug")

        p.set("transmitter.logVerbosity", "not")
        UrnPolicyFile("urn:eupspkg:" + addr).load(p)
        self.assert_(p.get("transmitter.logVerbosity") == "debug")

        p.set("transmitter.logVerbosity", "not")
        UrnPolicyFile("@@" + addr).load(p)
        self.assert_(p.get("transmitter.logVerbosity") == "debug")

    def testIndirect(self):
        urn = "@urn:eupspkg:pex_policy:tests/urn:indirect_parent_good.paf"
        p = Policy()
        UrnPolicyFile(urn).load(p)
        self.assert_(p.get("urn_full.name") == "Simple Policy")
        self.assert_(p.get("urn_brief.name") == "Simple Policy")
        self.assert_(p.get("urn_mixed_case.name") == "Simple Policy")
        self.assert_(p.get("local.foo") == "bar")

        p = Policy()
        UrnPolicyFile("pex_policy:tests/urn:level_1.paf").load(p)
        self.assert_(p.get("foo.bar.baz.qux.quux") == "schmazzle")

    def testTypos(self):
        base = "pex_policy:tests/urn:indirect_parent_typo_"
        self.assertRaiseLCE("IoErrorException", "failure opening Policy file",
                            UrnPolicyFile(base + "1.paf").load, "Typo in URN",
                            Policy())
        self.assertRaiseLCE("IoErrorException", "failure opening Policy file",
                            UrnPolicyFile(base + "2.paf").load, "Typo in URN",
                            Policy())

    def testRepos(self):
        # when the repository is mis-specified, local files cannot be loaded
        upf = UrnPolicyFile("pex_policy:tests:urn/indirect_parent_good.paf")
        # we expect it to look in <package>/tests/simple.paf
        expectedFile = os.environ["PEX_POLICY_DIR"] + "/tests/simple.paf"
        self.assertRaiseLCE("IoErrorException",
                            "failure opening Policy file: " + expectedFile,
                            upf.load, "Wrong repository dir.", Policy())

        # a PAF file designed to have "tests" as it repository
        p = Policy()
        UrnPolicyFile("pex_policy:tests:urn/local_tests_repos.paf").load(p)
        self.assert_(p.get("local.polish") == "fancy")

def suite():
    """a suite containing all the test cases in this module"""
    tests.init()

    suites = []
    suites += unittest.makeSuite(UrnPolicyFileTestCase)
    suites += unittest.makeSuite(tests.MemoryTestCase)

    return unittest.TestSuite(suites)

def run(exit=False):
    """Run the tests"""
    tests.run(suite(), exit)

if __name__ == "__main__":
    run(True)
