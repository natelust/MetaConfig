#! /usr/bin/env python
#
# LSST Data Management System
# Copyright 2013 LSST Corporation.
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
import sys
import io
import unittest
import lsst.utils.tests

# Extend path to find the helper code for this test relative to the test file
sys.path = [os.path.join(os.path.abspath(os.path.dirname(__file__)), "ticket2818helper")] + sys.path

from ticket2818helper.define import BaseConfig  # noqa E402 module level import not at top of file


class ImportTest(unittest.TestCase):
    def test(self):
        from ticket2818helper.another import AnotherConfigurable  # noqa F401 imported but unused
        config = BaseConfig()
        config.loadFromStream("""from ticket2818helper.another import AnotherConfigurable
config.test.retarget(AnotherConfigurable)
""")
        stream = io.StringIO()
        config.saveToStream(stream)
        values = stream.getvalue()
        print(values)
        self.assertIn("import ticket2818helper.another", values)


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
