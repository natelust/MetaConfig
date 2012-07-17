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

def isSorted(l):
    if len(l)<=1:
        return True

    p = l[0]
    for x in l[1:]:
        if x < p:
            return False
        p=x
    return True

def isPositive(x):
    return x>0

class Config1(pexConfig.Config):
    l1 = pexConfig.ListField("l1", int, minLength=2, maxLength=5, default=[1,2,3], itemCheck=isPositive)
    l2 = pexConfig.ListField("l2", int, length = 3, default=[1,2,3], listCheck=isSorted, itemCheck=isPositive)
    l3 = pexConfig.ListField("l3", int, length = 3, default=None, optional=True, itemCheck=isPositive)
    l4 = pexConfig.ListField("l4", int, length = 3, default=None, itemCheck=isPositive)

class Config2(pexConfig.Config):
    lf= pexConfig.ListField("lf", float, default=[1,2,3])
    ls = pexConfig.ListField("ls", str, default=["hi"])

class ListFieldTest(unittest.TestCase):
    def testConstructor(self):
        try:
            class BadDtype(pexConfig.Config):
                l = pexConfig.ListField("...", list)
        except:
            pass
        else:
            raise SyntaxError("Unsupported dtype ListFields should not be allowed")

        try:
            class BadLengths(pexConfig.Config):
                l = pexConfig.ListField("...", int, minLength=4, maxLength=2)
        except ValueError, e:
            pass
        else:
            raise SyntaxError("minLnegth <= maxLength should not be allowed")
        
        try:
            class BadLength(pexConfig.Config):
                l = pexConfig.ListField("...", int, length=-1)
        except:
            pass
        else:
            raise SyntaxError("negative length should not be allowed")
        
        try:
            class BadLength(pexConfig.Config):
                l = pexConfig.ListField("...", int, maxLength=-1)
        except:
            pass
        else:
            raise SyntaxError("negative max length should not be allowed")

    def testAssignment(self):
        c = Config1()
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l1", [1.2, 3, 4])
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l1", [-1, -2, -3])
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l1", [1, 2, 0])
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l1", [1, 2, None])
        c.l1 = None; c.l1 = [1, 1]; c.l1 = [1,1,1]; c.l1 = [1,1,1,1]; c.l1= [1,1,1,1,1]
        

        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l2", [1, 2, None])
        c.l2 = None; c.l2 = [1,2,3];
        
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l3", [0,3,2])
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l3", [1, 2, None])
        c.l3 = None; c.l3 = [1,1,1]

        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l4", [0,3,2])
        self.assertRaises(pexConfig.FieldValidationError, setattr, c, "l4", [1, 2, None])
        c.l4 = None; c.l4 = [1,1,1]
       
    def testValidate(self):
        c = Config1()
        self.assertRaises(pexConfig.FieldValidationError, Config1.validate, c)

        c.l4 = [1,2,3]
        c.validate()

    def testInPlaceModification(self):
        c= Config1()
        self.assertRaises(pexConfig.FieldValidationError, c.l1.__setitem__, 2, 0)
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

    def testNoArbitraryAttributes(self):
        c= Config1()        
        self.assertRaises(pexConfig.FieldValidationError, setattr, c.l1, "should", "fail")

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
