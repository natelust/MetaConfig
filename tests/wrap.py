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

import testLib


class WrapTest(unittest.TestCase):

    def testMakeControl(self):
        """Test making a C++ Control object from a Config object."""
        config = testLib.ConfigObject()
        config.foo = 2
        config.bar.append("baz")
        control = config.makeControl()
        self.assertTrue(testLib.checkControl(control, config.foo, config.bar.list()))

    def testReadControl(self):
        """Test reading the values from a C++ Control object into a Config object."""
        control = testLib.ControlObject()
        control.foo = 3
        control.bar = ["zot", "yox"]
        config = testLib.ConfigObject()
        config.readControl(control)
        self.assertTrue(testLib.checkControl(control, config.foo, config.bar.list()))

    def testDefaults(self):
        """Test that C++ Control object defaults are correctly used as defaults for Config objects."""
        config = testLib.ConfigObject()
        control = testLib.ControlObject()
        self.assertTrue(testLib.checkControl(control, config.foo, config.bar.list()))


class NestedWrapTest(unittest.TestCase):

    def testMakeControl(self):
        """Test making a C++ Control object from a Config object."""
        config = testLib.OuterConfigObject()
        self.assertIsInstance(config.a, testLib.InnerConfigObject)
        config.a.p = 5.0
        config.a.q = 7
        config.b = 2
        control = config.makeControl()
        self.assertTrue(testLib.checkNestedControl(control, config.a.p, config.a.q, config.b))

    def testReadControl(self):
        """Test reading the values from a C++ Control object into a Config object."""
        control = testLib.OuterControlObject()
        control.a.p = 6.0
        control.a.q = 4
        control.b = 3
        config = testLib.OuterConfigObject()
        config.readControl(control)
        self.assertTrue(testLib.checkNestedControl(control, config.a.p, config.a.q, config.b))

    def testDefaults(self):
        """Test that C++ Control object defaults are correctly used as defaults for Config objects."""
        config = testLib.OuterConfigObject()
        control = testLib.OuterControlObject()
        self.assertTrue(testLib.checkNestedControl(control, config.a.p, config.a.q, config.b))

    def testInt64(self):
        """Test that we can wrap C++ Control objects with int64 members."""
        config = testLib.OuterConfigObject()
        control = testLib.OuterControlObject()
        self.assertTrue(testLib.checkNestedControl(control, config.a.p, config.a.q, config.b))
        self.assertGreater(config.a.q, 1 << 30)
        self.assertGreater(control.a.q, 1 << 30)


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()

if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
