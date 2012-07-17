#! /usr/bin/env python

# 
# LSST Data Management System
# Copyright 2012 LSST Corporation.
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
import math
import tempfile
import unittest
import lsst.utils.tests as utilsTests
import lsst.pex.config as pexConfig

class Config1(pexConfig.Config):
    pass

class Config2(pexConfig.Config):
    c = pexConfig.ConfigChoiceField(
            doc="c", 
            typemap={"AAA":Config1, "BBB":Config1, "CCC":Config1},
            default=["AAA"],
            multi=True)

class MutableSelectionSetTest(unittest.TestCase):    
    def testModify(self):
        config = Config2()
        config.c.names.add("BBB")
        self.assertEqual(set(config.c.names), set(["AAA", "BBB"]))
        config.c.names.remove("AAA")
        self.assertEqual(set(config.c.names), set(["BBB"]))
        self.assertRaises(KeyError, config.c.names.remove, "AAA")

    def testBadAssignment(self):
        config = Config2()
        self.assertRaises(
                pexConfig.FieldValidationError, 
                setattr, config.c, "names", "AAA")
        config.c.names=["AAA"]
        print config.history["c"]


def suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(MutableSelectionSetTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
