#!/usr/bin/env python

#
# LSST Data Management System
# Copyright 2008-2015 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#

import unittest
import lsst.utils.tests
import lsst.pex.config as pexConfig
import lsst.pex.config.history as pexConfigHistory


class PexTestConfig(pexConfig.Config):
    a = pexConfig.Field('Parameter A', float, default=1.0)


class HistoryTest(unittest.TestCase):
    def testHistory(self):
        b = PexTestConfig()
        b.update(a=4.0)
        pexConfigHistory.Color.colorize(False)
        output = b.formatHistory("a", writeSourceLine=False)

        # The history differs depending on how the tests are executed and might
        # depend on pytest internals. We therefore test the output for the presence
        # of strings that we know should be there.

        # For reference, this is the output from running with unittest.main()
        """a
1.0 unittest.main()
    self.runTests()
    self.result = testRunner.run(self.test)
    test(result)
    return self.run(*args, **kwds)
    test(result)
    return self.run(*args, **kwds)
    testMethod()
    b = PexTestConfig()
    a = pexConfig.Field('Parameter A', float, default=1.0)
4.0 unittest.main()
    self.runTests()
    self.result = testRunner.run(self.test)
    test(result)
    return self.run(*args, **kwds)
    test(result)
    return self.run(*args, **kwds)
    testMethod()
    b.update(a=4.0)"""

        self.assertTrue(output.startswith("a\n1.0"))
        self.assertIn("""return self.run(*args, **kwds)
    testMethod()
    b = PexTestConfig()
    a = pexConfig.Field('Parameter A', float, default=1.0)
4.0""", output)

        self.assertIn("""    return self.run(*args, **kwds)
    testMethod()
    b.update(a=4.0)""", output)


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()

if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
