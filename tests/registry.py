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

class ParentConfig(pexConfig.Config):
    pass

configRegistry = pexConfig.makeConfigRegistry(doc="unit test configs", baseType=ParentConfig)
algorithmRegistry = pexConfig.makeAlgorithmRegistry(doc="unit test algorithms", requiredAttributes=("foo",))

@pexConfig.register("foo1", configRegistry) # one way to register
class FooConfig1(ParentConfig):
    pass

class FooConfig2(ParentConfig):
    pass
configRegistry.add("foo2", FooConfig2)  # the other way to register

class BarConfig(pexConfig.Config):
    pass

class Config1(pexConfig.Config):
    pass

class Config2(pexConfig.Config):
    pass

@pexConfig.register("foo1", algorithmRegistry)
class FooAlg1(object):
    ConfigClass = FooConfig1
    def foo(self):
        pass

class FooAlg2(object):
    ConfigClass = FooConfig2
    def foo(self):
        pass
algorithmRegistry.add("foo2", FooAlg2)

class BarAlg(object):
    ConfigClass = BarConfig
    def bar(self):
        pass

class ConfigTest(unittest.TestCase):
    def testBasics(self):
        self.assertEqual(configRegistry.get("foo1"), FooConfig1)
        self.assertEqual(configRegistry.get("foo2"), FooConfig2)
        self.assertEqual(set(configRegistry.keys()), set(("foo1", "foo2")))
        self.assertEqual(algorithmRegistry.get("foo1"), FooAlg1)
        self.assertEqual(algorithmRegistry.get("foo2"), FooAlg2)
        self.assertEqual(set(algorithmRegistry.keys()), set(("foo1", "foo2")))

    def testConfigReplace(self):
        """Test replacement in config registry
        """
        self.assertRaises(Exception, configRegistry.add, "foo1", FooConfig1)
        self.assertRaises(Exception, configRegistry.add, "foo3", FooConfig1, isNew=False)
        self.assertEqual(configRegistry.get("foo1"), FooConfig1)
        configRegistry.add("foo1", FooConfig2, isNew=False)
        self.assertEqual(configRegistry.get("foo1"), FooConfig2)
        configRegistry.add("foo1", FooConfig1, isNew=False)
        self.assertEqual(configRegistry.get("foo1"), FooConfig1)
    
    def testAlgorithmReplace(self):
        """Test replacement in algorithm registry
        """
        self.assertRaises(Exception, algorithmRegistry.add, "foo1", FooAlg1)
        self.assertRaises(Exception, algorithmRegistry.add, "foo3", FooAlg1, isNew=False)
        self.assertEqual(algorithmRegistry.get("foo1"), FooAlg1)
        algorithmRegistry.add("foo1", FooAlg2, isNew=False)
        self.assertEqual(algorithmRegistry.get("foo1"), FooAlg2)
        algorithmRegistry.add("foo1", FooAlg1, isNew=False)
        self.assertEqual(algorithmRegistry.get("foo1"), FooAlg1)
    
    def testClass(self):
        """Test subclass test of ConfigRegistry
        """
        self.assertRaises(Exception, configRegistry.add, "bar", BarConfig)
    
    def testAttr(self):
        """Test attribute test of AlgorithmRegistry
        """
        self.assertRaises(Exception, algorithmRegistry.add, "bar", BarAlg)

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
