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

"""
Comprehensive tests reading and retrieving data of all types
"""
import pdb                              # we may want to say pdb.set_trace()
import os
import sys
import unittest
import time

from lsst.pex.policy import Policy

proddir = os.environ["PEX_POLICY_DIR"]

class BigBoolTestCase(unittest.TestCase):

    def setUp(self):
        self.policy = Policy()

    def tearDown(self):
        del self.policy
        
    def testBigBoolArray(self):
        biglen = 1000
        self.policy.isBool("true")
        for i in xrange(biglen):
            self.policy.add("true", True)

        v = self.policy.getArray("true")
        self.assertEquals(len(v), biglen,"wrong big number of values in array")
        for i in xrange(biglen):
            self.assert_(v[i], "big array with bad value")

        del v
        self.assert_(True, "Blew up True")

        fd = open("/dev/null", "w")
        print >> fd, "look: %s" % True
        fd.close()

        

__all__ = "BigBoolTestCase".split()        

if __name__ == "__main__":
    unittest.main()
