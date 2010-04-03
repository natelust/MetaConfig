#!/usr/bin/env python
"""
Comprehensive tests reading and retrieving data of all types
"""
import pdb                              # we may want to say pdb.set_trace()
import os
import sys
import unittest
import time

from lsst.pex.policy import Policy, PolicyString

class PolicyStringTestCase(unittest.TestCase):

    def setUp(self):
        self.data = """#<?cfg paf policy ?>
int: 7
dbl: -1.0
"""

    def tearDown(self):
        pass

    def testRead(self):
        ps = PolicyString(self.data)
        p = Policy.createPolicy(ps)
        self.assertEquals(p.get("int"), 7)
        self.assertEquals(p.get("dbl"), -1.0)




__all__ = "PolicyStringTestCase".split()        

if __name__ == "__main__":
    unittest.main()

