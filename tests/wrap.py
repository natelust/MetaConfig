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
import re
import os
import unittest
import lsst.utils.tests as utilsTests
import lsst.pex.config as pexConfig
import sys
import pickle

import testLib

class WrapTest(unittest.TestCase):

    def testMakeControl(self):
        config = testLib.ConfigObject()
        config.foo = 2
        config.bar.append("baz")
        control = config.makeControl()
        self.assert_(testLib.checkControl(control, config.foo, config.bar))

    def testReadControl(self):
        vec = testLib.StringVec()
        vec.push_back("zot")
        vec.push_back("yox")
        control = testLib.ControlObject()
        control.foo = 3
        control.bar = vec
        config = testLib.ConfigObject()
        config.readControl(control)
        self.assert_(testLib.checkControl(control, config.foo, config.bar))

    def testDefaults(self):
        config = testLib.ConfigObject()
        control = testLib.ControlObject()
        self.assert_(testLib.checkControl(control, config.foo, config.bar))

def suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(WrapTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
