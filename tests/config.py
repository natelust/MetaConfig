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


class Simple(Config):
    i = Field(int, "integer test", optional=True)
    f = Field(float, "float test", default=3.0)
    b = Field(bool, "boolean test", default=False, optional=False)
    t = Field(tuple, "tuple test", default=("A", 1), optional=False, 
            check=lambda x: len(x)==2 and type(x[0])==str and type(x[1])==int)
    c = ChoiceField(str, "choice test", default="Hello",
            allowed={"Hello":"First choice", "World":"second choice"})
    r = RangeField(float, "Range test", default = 3.0, optional=False,
            min=3.0, inclusiveMin=True)
    l = ListField(int, "list test", default=[1,2,3], maxLength=5, itemCheck=lambda x: x is not None and x>0)


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

class Complex(Config):
    c = ConfigField(InnerConfig, "an inner config", default=OuterConfig, optional=False)
    r = RegistryField("restricted registry", typemap={"AAA":Simple, "BBB":InnerConfig}, restricted=True, default="AAA", optional=False)    
    p = RegistryField("open, plugin-style registry", optional=True)
    l = ConfigListField("list of configs", default=[Simple, InnerConfig, OuterConfig], optional=False, length=3)

class ConfigTest(unittest.TestCase):
    def setUp(self): 
        self.simple = Simple()
        self.inner = InnerConfig()
        self.outer = OuterConfig()
        self.comp = Complex()

    def tearDown(self):
        del self.simple
        del self.inner
        del self.outer
        del self.comp

    def testInit(self):
        self.assertEqual(self.simple.i, None)
        self.assertEqual(self.simple.f, 3.0)
        self.assertEqual(self.simple.b, False)
        self.assertEqual(self.simple.t, ("A", 1))
        self.assertEqual(self.simple.c, "Hello")
        self.assertEqual(list(self.simple.l), [1,2,3])

        self.assertEqual(self.inner.f, 0.0)

        self.assertEqual(self.outer.i.f, 5.0)
        self.assertEqual(self.outer.f, 0.0)

        self.assertEqual(self.comp.c.f, 0.0)
        self.assertEqual(self.comp.r.active, "AAA")
        self.assertEqual(self.comp.r[self.comp.r.active].f, 3.0)
        self.assertEqual(self.comp.r["BBB"].f, 0.0)
        self.assertEqual(self.comp.p.active, None)


    def testValidate(self):
        self.simple.validate()

        self.inner.validate()
        self.outer.i.f=-5
        self.assertRaises(ValueError, self.outer.validate)
        self.outer.i.f=10
        self.outer.validate()

        self.outer.i = InnerConfig
        self.assertRaises(ValueError, self.outer.validate)
        self.outer.i = InnerConfig()
        self.assertRaises(ValueError, self.outer.validate)
        
        self.comp.validate()
        self.comp.r= None
        self.assertRaises(ValueError, self.comp.validate)
        self.comp.r="BBB"
        self.comp.validate()

    def testSave(self):
        self.comp.p["test"]=InnerConfig
        self.comp.p["foo"]=Simple
        self.comp.p = "test"

        self.comp.save("roundtrip.test")

        roundTrip = Config.load("roundtrip.test")
        #os.remove("roundtrip.test")

        self.assertEqual(self.comp.c.f, roundTrip.c.f)
        self.assertEqual(self.comp.r.active, roundTrip.r.active)
        self.assertEqual(self.comp.p.active, roundTrip.p.active)
        self.assertEqual(self.comp.p["foo"].i, roundTrip.p["foo"].i)
        self.assertEqual(len(self.comp.l), len(roundTrip.l))
        self.assertEqual(self.comp.l[0].f, roundTrip.l[0].f)
        self.assertEqual(self.comp.l[1].f, roundTrip.l[1].f)
        self.assertEqual(self.comp.l[2].f, roundTrip.l[2].f)

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
