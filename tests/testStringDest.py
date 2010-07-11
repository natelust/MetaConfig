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

from lsst.pex.policy import Policy, PolicyStringDestination, PAFWriter

class PolicyOutStringTestCase(unittest.TestCase):

    def setUp(self):
        self.policy = Policy()
        self.policy.set("answer", 42)
        self.policy.set("name", "ray")

    def tearDown(self):
        pass

    def testDest(self):
        dest = PolicyStringDestination("#<?cfg paf policy ?>")
        self.assertEquals(dest.getData(), "#<?cfg paf policy ?>")

    def testWrite(self):
        writer = PAFWriter()
        writer.write(self.policy, True)
        out = writer.toString();
        self.assert_(out.startswith("#<?cfg paf policy ?>"))

__all__ = "PolicyOutStringTestCase".split()        

if __name__ == "__main__":
    unittest.main()


        
