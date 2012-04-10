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
import lsst.pex.config as pexConf

def isSorted(l):
    if len(l)<=1:
        return True

    p = l[0]
    for x in l[1:]:
        if x < p:
            return False
        p=x
    return True

class Config1(pexConf.Config):
    l1 = pexConf.ListField("l1", int, minLength=2, maxLength=5, default=[1,2,3], itemCheck=lambda x: x > 0)
    l2 = pexConf.ListField("l2", int, length = 3, default=[1,2,3], listCheck=isSorted)
    l3 = pexConf.ListField("l3", int, length = 3, default=None, optional=True, itemCheck=lambda x: x > 0)
    l4 = pexConf.ListField("l4", int, length = 3, default=None, itemCheck=lambda x: x > 0)

class Config2(pexConf.Config):
    lf= pexConf.ListField("lf", float, default=[1,2,3])
    ls = pexConf.ListField("ls", str, default=["hi"])

class ListFieldTest(unittest.TestCase):
    def testConstructor(self):
        try:
            class BadDtype(pexConf.Config):
                l = pexConf.ListField("...", list)
        except:
            pass
        else:
            raise SyntaxError("Unsupported dtype ListFields should not be allowed")

        try:
            class BadLengths(pexConf.Config):
                l = pexConf.ListField("...", int, minLength=4, maxLength=2)
        except ValueError, e:
            pass
        else:
            raise SyntaxError("minLnegth <= maxLength should not be allowed")
        
        try:
            class BadLength(pexConf.Config):
                l = pexConf.ListField("...", int, length=-1)
        except:
            pass
        else:
            raise SyntaxError("negative length should not be allowed")
        
        try:
            class BadLength(pexConf.Config):
                l = pexConf.ListField("...", int, maxLength=-1)
        except:
            pass
        else:
            raise SyntaxError("negative max length should not be allowed")

    def testAssignment(self):
        c = Config1()
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l1", [1.2, 3, 4])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l1", [])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l1", [1,2,3,4,5,6])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l1", [-1, -2, -3])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l1", [1, 2, 0])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l1", [1, 2, None])
        c.l1 = None; c.l1 = [1, 1]; c.l1 = [1,1,1]; c.l1 = [1,1,1,1]; c.l1= [1,1,1,1,1]
        

        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l2", [])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l2", range(10))
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l2", [1,3,2])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l2", [1, 2, None])
        c.l2 = None; c.l2 = [0,0,0]; c.l2 = [-1,1,2]
        
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l3", [])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l3", range(10))
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l3", [0,3,2])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l3", [1, 2, None])
        c.l3 = None; c.l3 = [1,1,1]

        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l4", [])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l4", range(10))
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l4", [0,3,2])
        self.assertRaises(pexConf.FieldValidationError, setattr, c, "l4", [1, 2, None])
        c.l4 = None; c.l4 = [1,1,1]
       
    def testValidate(self):
        c = Config1()
        self.assertRaises(pexConf.FieldValidationError, Config1.validate, c)

        c.l4 = [1,2,3]
        c.validate()

    def testInPlaceModification(self):
        c= Config1()
        self.assertRaises(pexConf.FieldValidationError, c.l1.__setitem__, 2, 0)
        c.l1[2]=10
        self.assertEqual(c.l1, [1,2,10])
        self.assertEqual((1,2, 10), c.l1)

        c.l1.insert(2, 20)
        self.assertEqual(c.l1, [1,2, 20, 10])
        c.l1.append(30)
        self.assertEqual(c.l1, [1,2, 20, 10, 30])
        c.l1.extend([4,5,6])
        self.assertEqual(c.l1, [1,2, 20, 10, 30, 4,5,6])

    def testCastAndTypes(self):
        c = Config2()
        self.assertEqual(c.lf, [1., 2., 3.])

        c.lf[2]=10
        self.assertEqual(c.lf, [1.,2.,10.])


        c.ls.append("foo")
        self.assertEqual(c.ls, ["hi", "foo"])

def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ListFieldTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
