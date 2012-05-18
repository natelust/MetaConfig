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
import lsst.pex.config as pexConf

class TestConfig(pexConf.Config):
    list1 = pexConf.ListField(dtype=int, default=[1, 2], doc="list1")
    f1 = pexConf.Field(dtype=float, doc="f1")
    f2 = pexConf.Field(dtype=float, doc="f2")

class EqualityTest(unittest.TestCase):
    def test(self):
        c1 = TestConfig()
        c2 = TestConfig()
        self.assertEqual(c1, c2)
        c1.list1 = [1,2,3,4,5]
        self.assertNotEqual(c1, c2)
        c2.list1 = c1.list1
        self.assertEqual(c1, c2)

class LoadSpecialTest(unittest.TestCase):
    def test(self):
        c1 = TestConfig()
        c2 = TestConfig()
        c1.list1 = None
        c1.f1 = float('nan')
        c2.f2 = float('inf')
        with tempfile.NamedTemporaryFile() as f:
            c1.saveToStream(f.file)
            f.file.close()
            c2.load(f.name)
        self.assertEqual(c1.list1, c2.list1)
        self.assertEqual(c1.f2, c2.f2)
        self.assertTrue(math.isnan(c2.f1))
        
def suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(EqualityTest)
    suites += unittest.makeSuite(LoadSpecialTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
