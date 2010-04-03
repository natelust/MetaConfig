#!/usr/bin/env python
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


        
