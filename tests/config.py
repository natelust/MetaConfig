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
import io
import itertools
import re
import os
import unittest
import lsst.utils.tests as utilsTests
import lsst.pex.config as pexConfig
import pickle

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
    n = pexConfig.Field("nan test", float, default=float("NAN"))

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
       
        try:
            self.simple.d["failKey"]="failValue"
        except pexConfig.FieldValidationError:
            pass
        except:
            raise "Validation error Expected"
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

    def testRangeFieldConstructor(self):
        """Test RangeField constructor's checking of min, max
        """
        val = 3
        self.assertRaises(ValueError, pexConfig.RangeField, "", int, default=val, min=val, max=val-1)
        self.assertRaises(ValueError, pexConfig.RangeField, "", float, default=val, min=val, max=val-1e-15)
        for inclusiveMin, inclusiveMax in itertools.product((False, True), (False, True)):
            if inclusiveMin and inclusiveMax:
                # should not raise
                class Cfg1(pexConfig.Config):
                    r1 = pexConfig.RangeField(doc="", dtype=int,
                        default=val, min=val, max=val, inclusiveMin=inclusiveMin, inclusiveMax=inclusiveMax)
                    r2 = pexConfig.RangeField(doc="", dtype=float,
                        default=val, min=val, max=val, inclusiveMin=inclusiveMin, inclusiveMax=inclusiveMax)
                Cfg1()
            else:
                # raise while constructing the RangeField (hence cannot make it part of a Config)
                self.assertRaises(ValueError, pexConfig.RangeField, doc="", dtype=int,
                    default=val, min=val, max=val, inclusiveMin=inclusiveMin, inclusiveMax=inclusiveMax)
                self.assertRaises(ValueError, pexConfig.RangeField, doc="", dtype=float,
                    default=val, min=val, max=val, inclusiveMin=inclusiveMin, inclusiveMax=inclusiveMax)

    def testRangeFieldDefault(self):
        """Test RangeField's checking of the default value
        """
        minVal = 3
        maxVal = 4
        for val, inclusiveMin, inclusiveMax, shouldRaise in (
            (minVal, False, True, True),
            (minVal, True, True, False),
            (maxVal, True, False, True),
            (maxVal, True, True, False),
        ):
            class Cfg1(pexConfig.Config):
                r = pexConfig.RangeField(doc="", dtype=int,
                    default=val, min=minVal, max=maxVal,
                    inclusiveMin=inclusiveMin, inclusiveMax=inclusiveMax)
            class Cfg2(pexConfig.Config):
                r2 = pexConfig.RangeField(doc="", dtype=float,
                    default=val, min=minVal, max=maxVal,
                    inclusiveMin=inclusiveMin, inclusiveMax=inclusiveMax)
        if shouldRaise:
            self.assertRaises(pexConfig.FieldValidationError, Cfg1)
            self.assertRaises(pexConfig.FieldValidationError, Cfg2)
        else:
            Cfg1()
            Cfg2()

    def testSave(self):
        self.comp.r="BBB"
        self.comp.p="AAA"
        self.comp.c.f=5.
        self.comp.save("roundtrip.test")
        
        roundTrip = Complex()
        roundTrip.load("roundtrip.test")
        os.remove("roundtrip.test")

        self.assertEqual(self.comp.c.f, roundTrip.c.f)
        self.assertEqual(self.comp.r.name, roundTrip.r.name)

        del roundTrip
        #test saving to an open file
        outfile = open("roundtrip.test", "w")
        self.comp.saveToStream(outfile)
        outfile.close()

        roundTrip = Complex()
        roundTrip.load("roundtrip.test")
        os.remove("roundtrip.test")

        self.assertEqual(self.comp.c.f, roundTrip.c.f)
        self.assertEqual(self.comp.r.name, roundTrip.r.name)

        # test backwards compatibility feature of allowing "root" instead of "config"
        outfile = open("roundtrip.test", "w")
        self.comp.saveToStream(outfile, root="root")
        outfile.close()

        roundTrip = Complex()
        roundTrip.load("roundtrip.test")
        os.remove("roundtrip.test")

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
        self.assertEqual("a" in c.toDict(), True)
        self.assertEqual(c._fields["a"].dtype, int)
        self.assertEqual(c.a, 4)

        #test conflicting multiple inheritance
        class DDD(pexConfig.Config):
            a = pexConfig.Field("DDD.a", float, default=0.0)

        class EEE(DDD, AAA):
            pass

        e = EEE()
        self.assertEqual(e._fields["a"].dtype, float)
        self.assertEqual("a" in e.toDict(), True)
        self.assertEqual(e.a, 0.0)

        class FFF(AAA, DDD):
            pass
        f = FFF()
        self.assertEqual(f._fields["a"].dtype, int)
        self.assertEqual("a" in f.toDict(), True)
        self.assertEqual(f.a, 4)

        #test inheritance from non Config objects
        class GGG(object):
            a = pexConfig.Field("AAA.a", float, default=10.)
        class HHH(GGG, AAA):
            pass
        h = HHH()
        self.assertEqual(h._fields["a"].dtype, float)
        self.assertEqual("a" in h.toDict(), True)
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
    def testFreeze(self):
        self.comp.freeze()

        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp.c, "f", 10.0)
        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp, "r", "AAA")
        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp, "p", "AAA")
        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp.p["AAA"], "f", 5.0) 

    def checkImportRoundTrip(self, importStatement, searchString, shouldBeThere):
        self.comp.c.f=5.

        # Generate a Config through loading
        stream = io.BytesIO()
        stream.write(importStatement)
        self.comp.saveToStream(stream)
        roundtrip = Complex()
        roundtrip.loadFromStream(stream.getvalue())
        self.assertEqual(self.comp.c.f, roundtrip.c.f)
        
        # Check the save stream
        stream = io.BytesIO()
        roundtrip.saveToStream(stream)
        self.assertEqual(self.comp.c.f, roundtrip.c.f)
        if shouldBeThere:
            self.assertTrue(re.search(searchString, stream.getvalue()))
        else:
            self.assertFalse(re.search(searchString, stream.getvalue()))


    def testImports(self):
        importing = "import lsst.daf.base.citizen\n" # A module not used by anything else, but which exists
        self.checkImportRoundTrip(importing, importing, True)

    def testBadImports(self):
        dummy = "somethingThatDoesntExist"
        importing = """
try:
    import %s
except ImportError:
    pass
""" % dummy
        self.checkImportRoundTrip(importing, dummy, False)

    def testPickle(self):
        self.simple.f = 5
        simple = pickle.loads(pickle.dumps(self.simple))
        self.assertTrue(isinstance(simple, Simple))
        self.assertEqual(self.simple.f, simple.f)

        self.comp.c.f = 5
        comp = pickle.loads(pickle.dumps(self.comp))
        self.assertTrue(isinstance(comp, Complex))
        self.assertEqual(self.comp.c.f, comp.c.f)

    def testCompare(self):
        comp2 = Complex()
        inner2 = InnerConfig()
        simple2 = Simple()
        self.assert_(self.comp.compare(comp2))
        self.assert_(comp2.compare(self.comp))
        self.assert_(self.comp.c.compare(inner2))
        self.assert_(self.simple.compare(simple2))
        self.assert_(simple2.compare(self.simple))
        self.assert_(self.simple == simple2)
        self.assert_(simple2 == self.simple)
        outList = []
        outFunc = lambda msg: outList.append(msg)
        simple2.b = True
        simple2.l.append(4)
        simple2.d["foo"] = "var"
        self.assertFalse(self.simple.compare(simple2, shortcut=True, output=outFunc))
        self.assertEqual(len(outList), 1)
        del outList[:]
        self.assertFalse(self.simple.compare(simple2, shortcut=False, output=outFunc))
        output = "\n".join(outList)
        self.assert_("Inequality in b" in output)
        self.assert_("Inequality in size for l" in output)
        self.assert_("Inequality in keys for d" in output)
        del outList[:]
        self.simple.d["foo"] = "vast"
        self.simple.l.append(5)
        self.simple.b = True
        self.simple.f += 1E8
        self.assertFalse(self.simple.compare(simple2, shortcut=False, output=outFunc))
        output = "\n".join(outList)
        self.assert_("Inequality in f" in output)
        self.assert_("Inequality in l[3]" in output)
        self.assert_("Inequality in d['foo']" in output)
        del outList[:]
        comp2.r["BBB"].f = 1.0  # changing the non-selected item shouldn't break equality
        self.assert_(self.comp.compare(comp2))
        comp2.r["AAA"].i = 56   # changing the selected item should break equality
        comp2.c.f = 1.0
        self.assertFalse(self.comp.compare(comp2, shortcut=False, output=outFunc))
        output = "\n".join(outList)
        self.assert_("Inequality in c.f" in output)
        self.assert_("Inequality in r['AAA']" in output)
        self.assert_("Inequality in r['BBB']" not in output)

    def testLoadError(self):
        """Check that loading allows errors in the file being loaded to propagate
        """
        self.assertRaises(SyntaxError, self.simple.loadFromStream, "bork bork bork")
        self.assertRaises(NameError, self.simple.loadFromStream, "config.f = bork")

def suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ConfigTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
