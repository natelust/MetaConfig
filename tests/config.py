#!/usr/bin/env python

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
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
import lsst.utils.tests as utilsTests
import unittest
from lsst.pex.policy import *
import os



class InnerConfig(Config):
    f = Field(float, "Inner.f", default=0.0, check = lambda x: x >= 0, optional=False)


class OuterConfig(InnerConfig, Config):
    i = ConfigField(InnerConfig, "Outer.i", optional=False)   
    def __init__(self):
        Config.__init__(self)
        self.i.f = 5

    def validate(self):
        Config.validate(self)
        if self.i.f < 5:
            raise ValueError("validation failed, outer.i.f must be greater than 5")

class PluginConfig(Config):
    algA = ConfigField(InnerConfig, "alg A policy", optional=True)
    algB = ConfigField(OuterConfig, "alg B policy", optional=True)
    algChoice = ChoiceField(str, "choice between algs A, B", default="A", allowed={"A":"choose algA", "B":"choose algB"})

    def validate(self):
        Config.validate(self);
        if (self.algChoice == "A" and self.algA is None) or (self.algChoice == "B" and self.algB is None):
            raise ValueError("no policy provided for chosen algorithm " + self.algChoice)

class ListConfig(Config):
    li = ListField(int, "list of ints", default = [1,2,3], optional=False, length=3, itemCheck=lambda x: x > 0)
    
class ConfigTest(unittest.TestCase):
    def setUp(self):    
        pass

    def tearDown(self):
        pass

    def testInit(self):
        i = InnerConfig()
        self.assertEqual(i.f, 0.0)

        o = OuterConfig()
        self.assertEqual(o.i.f, 5.0)
        self.assertEqual(o.f, 0.0)

        p = PluginConfig()
        self.assertEqual(p.algChoice, "A")
        self.assertEqual(p.algA, None)
        self.assertEqual(p.algB, None)
   
    def testValidate(self):
        o = OuterConfig()
        o.i.f=-5
        self.assertRaises(ValueError, o.validate)
        o.i.f=10
        o.validate()

        o.i = InnerConfig()
        self.assertRaises(ValueError, o.validate)

        p = PluginConfig()
        self.assertRaises(ValueError, p.validate)

        p.algA = InnerConfig()
        p.validate()

        p = PluginConfig()
        p.algB = OuterConfig()
        p.algChoice = "B"
        p.validate()

        listConfig = ListConfig()
        listConfig.validate()

        listConfig.li[1]=5
        self.assertEqual(listConfig.li[1], 5)


    def testSave(self):
        p = PluginConfig()
        p.algB = OuterConfig()
        p.algChoice = "B"
        p.save("roundtrip.test")

        roundTrip = Config.load("roundtrip.test")
        #os.remove("roundtrip.test")

        self.assertEqual(p.algB.i.f, roundTrip.algB.i.f)
        self.assertEqual(p.algA, roundTrip.algA)
        self.assertEqual(p.algChoice, roundTrip.algChoice)


def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ConfigTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(sexit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run()
