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
import os
import unittest
import lsst.utils.tests as utilsTests
import lsst.pex.config as pexConfig
import sys

GLOBAL_REGISTRY = {}

class Simple(pexConfig.Config):
    i = pexConfig.Field("integer test", int, optional=True)
    f = pexConfig.Field("float test", float, default=3.0)
    b = pexConfig.Field("boolean test", bool, default=False, optional=False)
    c = pexConfig.ChoiceField("choice test", str, default="Hello",
            allowed={"Hello":"First choice", "World":"second choice"})
    r = pexConfig.RangeField("Range test", float, default = 3.0, optional=False,
            min=3.0, inclusiveMin=True)
    l = pexConfig.ListField("list test", int, default=[1,2,3], maxLength=5,
        itemCheck=lambda x: x is not None and x>0)
    d = pexConfig.DictField("dict test", str, str, default={"key":"value"}, 
            itemCheck=lambda x: x.startswith('v'))

GLOBAL_REGISTRY["AAA"] = Simple

class InnerConfig(pexConfig.Config):
    f = pexConfig.Field("Inner.f", float, default=0.0, check = lambda x: x >= 0, optional=False)
GLOBAL_REGISTRY["BBB"] = InnerConfig

class OuterConfig(InnerConfig, pexConfig.Config):
    i = pexConfig.ConfigField("Outer.i", InnerConfig)   
    def __init__(self):
        pexConfig.Config.__init__(self)
        self.i.f = 5.0

    def validate(self):
        pexConfig.Config.validate(self)
        if self.i.f < 5:
            raise ValueError("validation failed, outer.i.f must be greater than 5")


class Complex(pexConfig.Config):
    c = pexConfig.ConfigField("an inner config", InnerConfig)
    r = pexConfig.ConfigChoiceField("a registry field", typemap=GLOBAL_REGISTRY,
                                    default="AAA", optional=False)
    p = pexConfig.ConfigChoiceField("another registry", typemap=GLOBAL_REGISTRY,
                                    default="BBB", optional=True)


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
        self.assertEqual(self.simple.c, "Hello")
        self.assertEqual(list(self.simple.l), [1,2,3])
        self.assertEqual(self.simple.d["key"], "value")
        self.assertEqual(self.inner.f, 0.0)

        self.assertEqual(self.outer.i.f, 5.0)
        self.assertEqual(self.outer.f, 0.0)

        self.assertEqual(self.comp.c.f, 0.0)
        self.assertEqual(self.comp.r.name, "AAA")
        self.assertEqual(self.comp.r.active.f, 3.0)
        self.assertEqual(self.comp.r["BBB"].f, 0.0)


    def testValidate(self):
        self.simple.validate()

        self.inner.validate()
        self.assertRaises(ValueError, setattr, self.outer.i, "f",-5)
        self.outer.i.f=10.
        self.outer.validate()

        self.simple.d["failKey"]= "failValue"
        self.assertRaises(pexConfig.FieldValidationError, self.simple.validate)
        del self.simple.d["failKey"]
        self.simple.validate()

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
        self.comp.r="BBB"
        self.comp.p="AAA"
        self.comp.c.f=5.
        self.comp.save("roundtrip.test")
        roundTrip = Complex()

        roundTrip.load("roundtrip.test")
        #os.remove("roundtrip.test")

        self.assertEqual(self.comp.c.f, roundTrip.c.f)
        self.assertEqual(self.comp.r.name, roundTrip.r.name)

    def testDuplicateRegistryNames(self):
        self.comp.r["AAA"].f = 5.0
        self.assertEqual(self.comp.p["AAA"].f, 3.0)

    def testInheritance(self):
        class AAA(pexConfig.Config):
            a = pexConfig.Field("AAA.a", int, default=4)
        class BBB(AAA):
            b = pexConfig.Field("BBB.b", int, default=3)
        class CCC(BBB):
            c = pexConfig.Field("CCC.c", int, default=2)
        
        #test multi-level inheritance
        c= CCC()
        self.assertEqual(c.toDict().has_key("a"), True)
        self.assertEqual(c._fields["a"].dtype, int)
        self.assertEqual(c.a, 4)

        #test conflicting multiple inheritance
        class DDD(pexConfig.Config):
            a = pexConfig.Field("DDD.a", float, default=0.0)

        class EEE(DDD, AAA):
            pass

        e = EEE()
        self.assertEqual(e._fields["a"].dtype, float)
        self.assertEqual(e.toDict().has_key("a"), True)
        self.assertEqual(e.a, 0.0)

        class FFF(AAA, DDD):
            pass
        f = FFF()
        self.assertEqual(f._fields["a"].dtype, int)
        self.assertEqual(f.toDict().has_key("a"), True)
        self.assertEqual(f.a, 4)

        #test inheritance from non Config objects
        class GGG(object):
            a = pexConfig.Field("AAA.a", float, default=10.)
        class HHH(GGG, AAA):
            pass
        h = HHH()
        self.assertEqual(h._fields["a"].dtype, float)
        self.assertEqual(h.toDict().has_key("a"), True)
        self.assertEqual(h.a, 10.0)

        #test partial Field redefinition

        class III(AAA):
            pass
        III.a.default=5

        self.assertEqual(III.a.default, 5)
        self.assertEqual(AAA.a.default, 4)
    
    def testConvert(self):
        pol = pexConfig.makePolicy(self.simple)
        self.assertEqual(pol.exists("i"), False)
        self.assertEqual(pol.get("f"), self.simple.f)
        self.assertEqual(pol.get("b"), self.simple.b)
        self.assertEqual(pol.get("c"), self.simple.c)
        self.assertEqual(pol.getArray("l"), list(self.simple.l))
        
        ps = pexConfig.makePropertySet(self.simple)
        self.assertEqual(ps.exists("i"), False)
        self.assertEqual(ps.get("f"), self.simple.f)
        self.assertEqual(ps.get("b"), self.simple.b)
        self.assertEqual(ps.get("c"), self.simple.c)
        self.assertEqual(list(ps.get("l")), list(self.simple.l))

        pol = pexConfig.makePolicy(self.comp)
        self.assertEqual(pol.get("c.f"), self.comp.c.f)

        ps = pexConfig.makePropertySet(self.comp)
        self.assertEqual(ps.get("c.f"), self.comp.c.f)
def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ConfigTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
