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
import unittest
import lsst.utils.tests as utilsTests
import lsst.pex.config as pexConf

class Config1(pexConf.Config):
    f = pexConf.Field("Config1.f", float, default=4)

class Config2(pexConf.Config):
    c = pexConf.ConfigField("Config2.c", Config1)

class Config3(pexConf.Config):
    r = pexConf.ConfigChoiceField("Config3.r", {"c1":Config1, "c2":Config2}, default="c1")

class HistoryMergeTest(unittest.TestCase):
    def test(self):
        a = Config2()
        b = Config2()
        b.c.f = 3
        b.c.f = 5
        a.c=b.c

        self.assertEqual([h[0] for h in a.c.history["f"]], [4, 5])

        c = Config3()
        c.r["c1"]=b.c
        c.r["c2"]=a

        self.assertEqual([h[0] for h in c.r["c1"].history["f"]], [4, 5])
        self.assertEqual([h[0] for h in c.r["c2"].c.history["f"]], [4, 5])


def  suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(HistoryMergeTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
