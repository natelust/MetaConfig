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
from __future__ import print_function
import os
import sys
sys.path = [os.path.join(os.path.abspath(os.path.dirname(__file__)), "ticket2818")] + sys.path

import io
import unittest
import lsst.utils.tests as utilsTests

from ticket2818.define import BaseConfig

class ImportTest(unittest.TestCase):
    def test(self):
        from ticket2818.another import AnotherConfigurable # Leave this uncommented to demonstrate bug
        config = BaseConfig()
        config.loadFromStream("""from ticket2818.another import AnotherConfigurable
config.test.retarget(AnotherConfigurable)
""")
        stream = io.BytesIO()
        config.saveToStream(stream)
        print(stream.getvalue())
        self.assertTrue("import ticket2818.another" in stream.getvalue())

def suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(ImportTest)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    utilsTests.run(suite(), exit)

if __name__=='__main__':
    run(True)
