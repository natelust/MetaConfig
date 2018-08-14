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
import lsst.utils.tests
import lsst.pex.config as pexConf


class SubConfigDefaultsTest(unittest.TestCase):

    def setUp(self):
        class Configurable(object):
            class ConfigClass(pexConf.Config):
                v = pexConf.Field(dtype=int, doc="dummy int field for registry configurable", default=0)

            def __init__(self, cfg):
                self.value = cfg.v
        self.registry = pexConf.makeRegistry("registry for Configurable", Configurable.ConfigClass)
        self.registry.register("C1", Configurable)
        self.registry.register("C2", Configurable)

    def testCustomDefaults(self):
        class Config1(pexConf.Config):
            r1 = self.registry.makeField("single-item registry field")
            r2 = self.registry.makeField("single-item registry field", multi=True)

            def setDefaults(self):
                self.r1.name = "C1"
                self.r2.names = ["C2"]
        typemap = {"B": Config1}

        class Config2(pexConf.Config):
            c = pexConf.ConfigField(dtype=Config1, doc="holder for Config1")
            b = pexConf.ConfigChoiceField(typemap=typemap, doc="choice holder for Config1")
        c1 = Config1()
        self.assertEqual(c1.r1.name, "C1")
        self.assertEqual(list(c1.r2.names), ["C2"])
        print(c1.r1.target)
        print(c1.r2.targets)
        c1.validate()
        c2 = Config2()
        self.assertEqual(Config2.c.default, Config1)
        self.assertEqual(c2.c.r1.name, "C1")
        self.assertEqual(list(c2.c.r2.names), ["C2"])
        self.assertEqual(type(c2.b["B"]), Config1)
        c2.b.name = "B"
        self.assertEqual(c2.b.active.r1.name, "C1")
        self.assertEqual(list(c2.b.active.r2.names), ["C2"])
        c2.c = Config1


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
