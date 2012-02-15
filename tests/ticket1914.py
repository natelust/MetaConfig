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
import eups

class Config1(pexConf.Config):
    f = pexConf.Field("Config1.f", float, default=4)

class Config2(pexConf.Config):
    r = pexConf.ConfigChoiceField("Config2.r", {"c1":Config1}, default="c1")

class Config3(pexConf.Config):
    c = pexConf.ConfigField("Config3.c", Config2)

class FieldNameReportingTest(unittest.TestCase):
    def test(self):
        c3 = Config3()
        pex_product_dir = eups.productDir("pex_config")
        c3.load(pex_product_dir+ "/tests/config/ticket1914.py")

def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(FieldNameReportingTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run()
