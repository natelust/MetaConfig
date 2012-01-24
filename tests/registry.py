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

class ConfigTest(unittest.TestCase):
    def setUp(self):
        """Note: the classes are defined here in order to test the register decorator
        """
        class ParentConfig(pexConfig.Config):
            pass
        
        self.configRegistry = pexConfig.makeConfigRegistry(doc="unit test configs", baseType=ParentConfig)
        self.algorithmRegistry = pexConfig.makeAlgorithmRegistry(doc="unit test algorithms", requiredAttributes=("foo",))
        
        @pexConfig.register("foo1", self.configRegistry) # one way to register
        class FooConfig1(ParentConfig):
            pass
        self.fooConfig1Class = FooConfig1
        
        class FooConfig2(ParentConfig):
            pass
        self.fooConfig2Class = FooConfig2
        self.configRegistry.add("foo2", FooConfig2)  # the other way to register
        
        class Config1(pexConfig.Config):
            pass
        self.config1Class = Config1
        
        class Config2(pexConfig.Config):
            pass
        self.config2Class = Config2
        
        @pexConfig.register("foo1", self.algorithmRegistry)
        class FooAlg1(object):
            ConfigClass = FooConfig1
            def foo(self):
                pass
        self.fooAlg1Class = FooAlg1
        
        class FooAlg2(object):
            ConfigClass = FooConfig2
            def foo(self):
                pass
        self.algorithmRegistry.add("foo2", FooAlg2)
        self.fooAlg2Class = FooAlg2
    
    def tearDown(self):
        del self.configRegistry
        del self.algorithmRegistry
        del self.fooConfig1Class
        del self.fooConfig2Class
        del self.fooAlg1Class
        del self.fooAlg2Class
        
    def testBasics(self):
        self.assertEqual(self.configRegistry.get("foo1"), self.fooConfig1Class)
        self.assertEqual(self.configRegistry.get("foo2"), self.fooConfig2Class)
        self.assertEqual(set(self.configRegistry.keys()), set(("foo1", "foo2")))
        self.assertEqual(self.algorithmRegistry.get("foo1"), self.fooAlg1Class)
        self.assertEqual(self.algorithmRegistry.get("foo2"), self.fooAlg2Class)
        self.assertEqual(set(self.algorithmRegistry.keys()), set(("foo1", "foo2")))

    def testConfigReplace(self):
        """Test replacement in config registry
        """
        self.assertRaises(Exception, self.configRegistry.add, "foo1", self.fooConfig1Class)
        self.assertRaises(Exception, self.configRegistry.add, "foo3", self.fooConfig1Class, isNew=False)
        self.assertEqual(self.configRegistry.get("foo1"), self.fooConfig1Class)
        self.configRegistry.add("foo1", self.fooConfig2Class, isNew=False)
        self.assertEqual(self.configRegistry.get("foo1"), self.fooConfig2Class)
        self.configRegistry.add("foo1", self.fooConfig1Class, isNew=False)
        self.assertEqual(self.configRegistry.get("foo1"), self.fooConfig1Class)
    
    def testAlgorithmReplace(self):
        """Test replacement in algorithm registry
        """
        self.assertRaises(Exception, self.algorithmRegistry.add, "foo1", self.fooAlg1Class)
        self.assertRaises(Exception, self.algorithmRegistry.add, "foo3", self.fooAlg1Class, isNew=False)
        self.assertEqual(self.algorithmRegistry.get("foo1"), self.fooAlg1Class)
        self.algorithmRegistry.add("foo1", self.fooAlg2Class, isNew=False)
        self.assertEqual(self.algorithmRegistry.get("foo1"), self.fooAlg2Class)
        self.algorithmRegistry.add("foo1", self.fooAlg1Class, isNew=False)
        self.assertEqual(self.algorithmRegistry.get("foo1"), self.fooAlg1Class)
    
    def testClass(self):
        """Test subclass test of ConfigRegistry
        """
        class BarConfig(pexConfig.Config):
            pass
        self.assertRaises(Exception, self.configRegistry.add, "bar", BarConfig)
    
    def testAttr(self):
        """Test attribute test of AlgorithmRegistry
        """
        class FooAlgNoConfig(object):
            def foo(self):
                pass
        self.assertRaises(Exception, self.algorithmRegistry.add, "fooNoConfig", FooAlgNoConfig)

        class BarConfig(pexConfig.Config):
            pass
        class BarAlg(object):
            ConfigClass = BarConfig
            def bar(self):
                pass

        self.assertRaises(Exception, self.algorithmRegistry.add, "bar", BarAlg)

def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ConfigTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run()
