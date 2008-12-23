import pdb                          # we may want to say pdb.set_trace()
import unittest

import lsst.utils.tests as tests
from lsst.pex.policy import Policy
from lsst.pex.exceptions import LsstCppException

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class PolicyTestCase(unittest.TestCase):
    def testPolicySetget(self):
        p = Policy()
        self.assert_(not p.exists("foo"), "empty existence test failed")
        self.assertEqual(p.valueCount("foo.bar"), 0,
                         "empty valueCount test failed")

        self.assertEqual(p.getInt("foo", 5), 5, "providing default failed")
        self.assertRaises(LsstCppException, p.getTypeInfo, "foo")

        p.set("doall", "true")

        # non-existence tests on a non-empty policy
        self.failUnless(not p.exists("foo"),
                        "non-empty non-existence test failed")
        self.assertEqual(p.valueCount("foo.bar"), 0,
                         "empty valueCount test failed");
        self.failUnless(not p.isInt("foo"),
                        "non-empty non-existence type test failed");
        self.assertRaises(LsstCppException, p.getTypeInfo, "foo")

        # existance tests
        self.assert_(p.exists("doall"), "non-empty existance test failed")
        self.assertEquals(p.valueCount("doall"), 1,
                          "single valueCount test failed");

        self.assertRaises(LsstCppException, p.getInt, "doall")
        self.assertRaises(LsstCppException, p.getDoubleArray, "doall")

        self.assertEquals(p.get("doall"), "true",
                          "top-level getString failed")
        p.set("doall", "duh")
        self.assertEquals(p.get("doall"), "duh",
                          "top-level getString failed")
        
        # test array access
        ary = p.getArray("doall")
        self.assertEquals(len(ary), 1,
                          "scalar property has more than one value")


        self.assertEquals(ary[0], "duh", "scalar access via array failed")

        p.add("doall", "never");
        self.assertEquals(p.valueCount("doall"), 2,
                          "2-elem. valueCount test failed")
        self.assertEquals(p.get("doall"), "never", "top-level add failed");
        ary = p.getArray("doall")
        self.assertEquals(len(ary), 2,
                          "scalar property has wrong number of values")
        self.assertEquals(ary[0], "duh",
                          "scalar access via (2-el) array failed")
        self.assertEquals(ary[-1], "never",
                          "scalar access via (2-el) array failed")

        # test hierarchical access


        # list names

        # show types

        # test shallow & deep copies

    def testSimpleLoad(self):
#        n = mwid.Citizen_census(0)
        p = Policy.createPolicy("examples/EventTranmitter_policy.paf")
        self.assertEquals(p.get("transmitter.serializationFormat"), "deluxe")
        p = None
#        self.assertEquals(mwid.Citizen_census(0), n, "Policy apparently leaked")

    def testEmptyPolicy(self):
        p = Policy()

    def testPolicyCopy(self):
        p = Policy.createPolicy("examples/EventTranmitter_policy.paf")
        pp = Policy(p, True)
        self.assertEquals(p.get("transmitter.serializationFormat"), "deluxe")
        self.assertEquals(pp.getString("transmitter.serializationFormat"), "deluxe")
        p = None
        self.assertEquals(pp.getString("transmitter.serializationFormat"), "deluxe")


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def suite():
    """Returns a suite containing all the test cases in this module."""
    tests.init()

    suites = []
    suites += unittest.makeSuite(PolicyTestCase)
    suites += unittest.makeSuite(tests.MemoryTestCase)

    return unittest.TestSuite(suites)

if __name__ == "__main__":
    tests.run(suite())




