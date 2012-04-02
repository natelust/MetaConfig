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


    
class Config1(pexConf.Config):
    f = pexConf.Field("f", dtype=float, default=5, check=lambda x: x > 0)

class Target1(object):
    ConfigClass = Config1

    def __init__(self, config):
        self.f = config.f

def Target2(config):
    return config.f

class Config2(pexConf.Config):
    c1=  pexConf.ConfigurableField("c1", target=Target1)
    c2 = pexConf.ConfigurableField("c2", target=Target2, ConfigClass=Config1, default=Config1(f=3))

class ConfigurableFieldTest(unittest.TestCase):
    def testConstructor(self):
        try:
            class BadTarget(pexConf.Config):
                d = pexConf.ConfigurableField("...", target=None)
        except:
            pass
        else:
            raise SyntaxError("Uncallable targets should not be allowed")

        try:
            class NoConfigClass(pexConf.Config):
                d = pexConf.ConfigurableField("...", target=Target2)
        except:
            pass
        else:
            raise SyntaxError("Missing ConfigClass should not be allowed")
       
        try:
            class BadConfigClass(pexConf.Config):
                d = pexConf.DictField("...", target=Target2, ConfigClass=Target2)
        except:
            pass
        else:
            raise SyntaxError("ConfigClass that are not subclasses of Config should not be allowed")
        
    def testBasics(self):
        c = Config2()
        self.assertEqual(c.c1.f, 5)
        self.assertEqual(c.c2.f, 3)
        
        self.assertEqual(type(c.c1.apply()), Target1)
        self.assertEqual(c.c1.apply().f, 5)
        self.assertEqual(c.c2.apply(), 3)

        c.c2.retarget(Target1)
        self.assertEqual(c.c2.f, 3)
        self.assertEqual(type(c.c2.apply()), Target1)
        self.assertEqual(c.c2.apply().f, 3)
        
        c.c1.f=2
        self.assertEqual(c.c1.f, 2)
        self.assertRaises(pexConf.FieldValidationError, setattr, c.c1, "f", 0)
        
        c.c1 = Config1(f=10)
        self.assertEqual(c.c1.f, 10)
    
        c.c1 = Config1
        self.assertEqual(c.c1.f, 5)
    def testValidate(self):
        c = Config2()
        self.assertRaises(pexConf.FieldValidationError, setattr, c.c1, "f", 0)

        c.validate()

def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ConfigurableFieldTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
