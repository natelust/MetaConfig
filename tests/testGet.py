#!/usr/bin/env python
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

class GetTestCase(unittest.TestCase):

    def setUp(self):
        self.policyfile = os.path.join(proddir,"examples","types.paf")
        self.policy = Policy.createPolicy(self.policyfile, False)

    def tearDown(self):
        pass

    def testGet(self):
        p = self.policy
        self.assertEquals(p.get("int"), 0)
        self.assertEquals(p.get("true"), True)
        self.assertEquals(p.get("false"), False)
        self.assertAlmostEquals(p.get("dbl"), -0.05, 8)
        self.assertEquals(p.get("str"), "birthday")
        self.assert_(p.isFile("file"),
                     "Unexpected: 'file' is not a PolicyFile")
        self.assert_(p.get("file") is not None, "file value returned as None")
        self.assertEquals(p.get("file").getPath(), "CacheManager_dict.paf")
        self.assert_(p.isPolicy("pol"), "Unexpected: 'pol' is not a Policy")
        sp = p.get("pol")
        self.assertEquals(sp.get("int"), 2)

    def testGetIntArray(self):
        self.assert_(self.policy.isInt("int"))
        v = self.policy.getArray("int")
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        truth = [-11, 0, 3, 42, -11, 0 , 3, 42, 0, 0]
        self.assertEquals(len(v), len(truth),"wrong number of values in array")
        for i in xrange(len(truth)):
            self.assertEquals(v[i], truth[i],
                              "wrong array element at index %d: %d != %d" %
                              (i, v[i], truth[i]))

    def testGetBoolArray(self):
        self.assert_(self.policy.isBool("true"))
        v = self.policy.getArray("true")
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        truth = [ True ]
        self.assertEquals(len(v), len(truth),"wrong number of values in array")
        for i in xrange(len(truth)):
            self.assertEquals(v[i], truth[i],
                              "wrong array element at index %i: %s != %s" %
                              (i, v[i], truth[i]))

        self.assert_(self.policy.isBool("false"))
        v = self.policy.getArray("false")
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        truth = [ False ]
        self.assertEquals(len(v), len(truth),"wrong number of values in array")
        for i in xrange(len(truth)):
            self.assertEquals(v[i], truth[i],
                              "wrong array element at index %i: %s != %s" %
                              (i, v[i], truth[i]))

    def testGetDoublArray(self):
        self.assert_(self.policy.isDouble("dbl"))
        v = self.policy.getArray("dbl")
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        truth = [-1.0, -65.78, -14.0, -0.12, -0.12, 1.0, 65.78, 14.0, 0.12, 
                 0.12, 1.0, 65.78, 14.0, 0.12, 0.12, -1.0e10, -65780000.0, 
                 -0.014, -0.12e14, 0.12e-11, 14.0, 0.12, 0.12, 1.0, 65.78, 
                 14.0, 50000, -0.05 ]
        self.assertEquals(len(v), len(truth),
                          "wrong number of values in array: %i != %i" %
                          (len(v), len(truth)))
        for i in xrange(len(truth)):
            self.assertAlmostEquals(v[i], truth[i], 8,
                              "wrong array element at index %d: %g != %g" %
                              (i, v[i], truth[i]))

    def testGetStringArray(self):
        #pdb.set_trace()
        self.assert_(self.policy.isString("str"))
        v = self.policy.getArray("str")
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        truth = ["word", "two words", "quoted ' words", 'quoted " words',
                 "a very long, multi-line description", "happy", "birthday" ]
        self.assertEquals(len(v), len(truth),"wrong number of values in array")
        for i in xrange(len(truth)):
            self.assertEquals(v[i], truth[i],
                              "wrong array element at index %d: %s != %s" %
                              (i, v[i], truth[i]))

    def testGetEmptyString(self):
        p = self.policy
        self.assertEquals(p.get("empty"), '')
        s = p.getArray("empty")
        self.assertEquals(len(s), 5)
        self.assertEquals(s[0], ' description ')
        self.assertEquals(s[1], '  ')
        self.assertEquals(s[2], '  ')
        self.assertEquals(s[3], ' ')
        self.assertEquals(s[4], '')
        
    def testGetFileArray(self):
        self.assert_(self.policy.isFile("file"))
        v = self.policy.getArray("file")
        self.assert_(v is not None, "file array returned as None")

        # this is be fixed in another ticket
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        truth = ["EventTransmitter_policy.paf", "CacheManager_dict.paf"]
        self.assertEquals(len(v), len(truth),"wrong number of values in array")
        for i in xrange(len(truth)):
            self.assertEquals(v[i].getPath(), truth[i],
                          "wrong array element at index %d: %s != %s" %
                          (i, v[i], truth[i]))

    def testGetPolicyArray(self):
        self.assert_(self.policy.isPolicy("pol"))
        v = self.policy.getArray("pol")
        # this is be fixed in another ticket
        self.assert_(isinstance(v, list), "array value not returned as a list")
        
        self.assertEquals(len(v), 2,"wrong number of values in array")
        self.assertEquals(v[0].get("int"), 1)
        self.assertEquals(v[1].get("int"), 2)
        self.assertAlmostEquals(v[0].get("dbl"), 0.0003, 8)
        self.assertAlmostEquals(v[1].get("dbl"), -5.2, 8)
    


__all__ = "GetTestCase".split()        

if __name__ == "__main__":
    unittest.main()

