import os
import unittest
import eups
#import inspect

import lsst.utils.tests as tests

from lsst.pex.policy import Policy, Dictionary, PolicyFile, DefaultPolicyFile
from lsst.pex.policy import ValidationError #, DictionaryError
from lsst.pex.exceptions import LsstCppException

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class DictionaryTestCase(unittest.TestCase):
    def assertRaiseLCE(self, excClass, excMsg, callableObj, failMsg, *args, **kwargs):
        """
        Expect callableObj(args, kwargs) to raise an LsstCppException that wraps
        the class specified by excClass, and carrying a message that contains
        excMsg.

        excClass: the subclass of LsstCppException we expect to see
        excMsg: a substring of the message it should carry
        callableObj: the thing that, when called, should raise an exception
        failMsg: the assertion message if this fails
        args, kwargs (optional): arguments to pass to callableObj
        """
        try:
            callableObj(*args, **kwargs)
        except LsstCppException, e:
            self.assert_(isinstance(e, LsstCppException))
            lce = "lsst.pex.exceptions.exceptionsLib.LsstCppException"
            self.assert_(str(e.__class__).find(lce) > 0,
                         failMsg + ": expected an " + lce + ", found a " 
                         + str(e.__class__))
            self.assert_(len(e.args) == 1)
            nested = e.args[0] # the real exception that was thrown
#            print "%%% wrapped exception is ", nested
#            print "  % class is ", nested.__class__
            self.assert_(str(nested.__class__).find(excClass) > 0,
                         failMsg + ": expected a " + excClass + "; found a " 
                         + str(nested.__class__))
            self.assert_(str(e).find(excMsg) > 0, 
                         failMsg + ": expected to see the message \"" + excMsg 
                         + "\"; actual message was \"" + str(e) + "\".")
#            print " -%%% e = ", e
#            print "    % members of e: ", dir(e)
#            print "    % members of len(e.args): ", len(e.args)
#            print "    % members of e.args.args[0]: ", inspect.getmembers(e.args[0])
#            print "    % inspect(e): ", inspect.getmembers(e)
        else:
            self.fail(failMsg + ": did not raise " + excClass)

    def assertValidationError(self, errorCode, callableObj, field, value):
        try:
            callableObj(field, value)
        except LsstCppException, e:
            ve = e.args[0]
            self.assert_(ve.getErrors(field) == errorCode)

    testDictDir = None
    def getTestDictionary(self, filename=None):
        if not self.testDictDir:
            self.testDictDir = os.path.join(eups.productDir("pex_policy"),
                                                  "tests", "dictionary")
        return os.path.join(self.testDictDir, filename) if filename else self.testDictDir

    def testDictionaryLoad(self):
        d = Dictionary()
        df = PolicyFile(self.getTestDictionary("simple_dictionary.paf"))
        self.assert_(not d.isDictionary(), "false positive dictionary")
        df.load(d)
        self.assert_(d.isDictionary(), "failed to recognize a dictionary")

    def testBadDictionary(self):
        d = Dictionary(self.getTestDictionary("dictionary_bad_policyfile.paf"))
        self.assertRaiseLCE("DictionaryError", "Illegal type: \"PolicyFile\"",
                            d.makeDef("file_type").getType,
                            "Dictionary specified PolicyFile type")

        d = Dictionary(self.getTestDictionary("dictionary_bad_unknown_type.paf"))
        self.assertRaiseLCE("DictionaryError", "Unknown type: \"NotAType\"",
                            d.makeDef("something").getType,
                            "Dictionary specifies unknown types")

        d = Dictionary(self.getTestDictionary("dictionary_bad_type_type.paf"))
        self.assertRaiseLCE("DictionaryError", "Expected string",
                            d.makeDef("something").getType,
                            "Expected string \"type\" type")

        self.assertRaiseLCE("DictionaryError", "property found at bad: min_occurs",
                            Dictionary,
                            "Dictionary has mispelled keyword \"min_occurs\".",
                            self.getTestDictionary("dictionary_bad_keyword.paf"))

        dbmd = self.getTestDictionary("dictionary_bad_multiple_definitions.paf")
        self.assertRaiseLCE("DictionaryError", "expected a single",
                            Dictionary,
                            "Dictionary has two 'definitions' sections",
                            dbmd)

        p = Policy(self.getTestDictionary("values_policy_good_1.paf"))
        d = Dictionary(self.getTestDictionary("dictionary_bad_multiple_min.paf"))
        self.assertRaiseLCE("DictionaryError", "Min value for int_ra", d.validate,
                            "Two mins specified.", p)
        d = Dictionary(self.getTestDictionary("dictionary_bad_multiple_max.paf"))
        self.assertRaiseLCE("DictionaryError", "Max value for int_ra", d.validate,
                            "Two maxes specified.", p)
        d = Dictionary(self.getTestDictionary("dictionary_bad_min_wrong_type.paf"))
        self.assertRaiseLCE("DictionaryError",
                            "Wrong type for int_range_count_type min",
                            d.validate, "Wrong min type.", p)
        d = Dictionary(self.getTestDictionary("dictionary_bad_max_wrong_type.paf"))
        self.assertRaiseLCE("DictionaryError",
                            "Wrong type for int_range_count_type max",
                            d.validate, "Wrong max type.", p)

        # conflict between minOccurs and maxOccurs
        d = Dictionary(self.getTestDictionary("conflict_occurs_dictionary.paf"))
        p = Policy(self.getTestDictionary("conflict_occurs_policy_1.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testBadDictionary")
        d.validate(p, ve)
        self.assert_(ve.getErrors("1to0") == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getErrors("2to1") == ValidationError.NOT_AN_ARRAY)
        self.assert_(ve.getParamCount() == 2)
        p = Policy(self.getTestDictionary("conflict_occurs_policy_2.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testBadDictionary")
        d.validate(p, ve)
        self.assert_(ve.getErrors("1to0") == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getErrors("2to1") == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getParamCount() == 2)

    def testSimpleValidate(self):
        d = Dictionary(self.getTestDictionary("simple_dictionary.paf"))
        p = Policy(self.getTestDictionary("simple_policy.paf"))
        ve = ValidationError("Dictionary_1.py", 0, "testSimpleValidate")
        d.validate(p, ve)
        self.assert_(ve.getErrors("name") == 0, "no errors in name")
        self.assert_(ve.getErrors("height") == 0, "no errors in height")
        self.assert_(ve.getErrors() == 0, "no errors overall")

    def testTypeValidation(self):
        d = Dictionary(self.getTestDictionary("types_dictionary.paf"))
        self.assert_(d.makeDef("undef_type") .getType() == Policy.UNDEF,
                     "UNDEF definition type")
        self.assert_(d.makeDef("bool_type")  .getType() == Policy.BOOL,
                     "BOOL definition type")
        self.assert_(d.makeDef("int_type")   .getType() == Policy.INT,
                     "INT definition type")
        self.assert_(d.makeDef("double_type").getType() == Policy.DOUBLE,
                     "DOUBLE definition type")
        self.assert_(d.makeDef("string_type").getType() == Policy.STRING,
                     "STRING definition type")
        self.assert_(d.makeDef("policy_type").getType() == Policy.POLICY,
                     "POLICY definition type")
        self.assert_(d.makeDef("file_type").getType() == Policy.POLICY,
                     "POLICY definition type (substituted for PolicyFile)")

        p = Policy(self.getTestDictionary("types_policy_good.paf"))

        ve = ValidationError("Dictionary_1.py", 0, "testTypeValidation")
        d.validate(p, ve)
        self.assert_(ve.getErrors("file_type") == ValidationError.NOT_LOADED,
                     "require loadPolicyFiles before validating")
        self.assert_(ve.getErrors("undef_file") == ValidationError.NOT_LOADED,
                     "require loadPolicyFiles before validating")
        self.assert_(ve.getErrors() == ValidationError.NOT_LOADED, "no other errors")
        self.assert_(ve.getParamCount() == 2, "no other errors")

        p.loadPolicyFiles(self.getTestDictionary(), True)
        ve = ValidationError("Dictionary_1.py", 0, "testTypeValidation")
        d.validate(p, ve)

        self.assert_(ve.getErrors("undef_type")  == 0, "no errors with undef")
        self.assert_(ve.getErrors("int_type")    == 0, "no errors with int")
        self.assert_(ve.getErrors("double_type") == 0, "no errors with double")
        self.assert_(ve.getErrors("bool_type")   == 0, "no errors with bool")
        self.assert_(ve.getErrors("string_type") == 0, "no errors with string")
        self.assert_(ve.getErrors("policy_type") == 0, "no errors with policy")
        self.assert_(ve.getErrors("file_type")   == 0, "no errors with file")
        self.assert_(ve.getErrors() == 0, "no errors overall")

    def testWrongType(self):
        d = Dictionary(self.getTestDictionary("types_dictionary.paf"))

        p = Policy(self.getTestDictionary("types_policy_bad_bool.paf"))
        ve = ValidationError("Dictionary_1.py", 0, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.WRONG_TYPE, "wrong type")
        self.assert_(ve.getParamCount() == 5, "number of errors")
        self.assert_(ve.getErrors("bool_type") == 0, "correct type")
        
        p = Policy(self.getTestDictionary("types_policy_bad_int.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.WRONG_TYPE, "wrong type")
        self.assert_(ve.getParamCount() == 5, "number of errors")
        self.assert_(ve.getErrors("int_type") == 0, "correct type")
        self.assert_(ve.getErrors("double_type") == ValidationError.WRONG_TYPE,
                     "int can't pass as double")
        
        p = Policy(self.getTestDictionary("types_policy_bad_double.paf"))
        ve = ValidationError("Dictionary_1.py", 2, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.WRONG_TYPE, "wrong type")
        self.assert_(ve.getParamCount() == 5, "number of errors")
        self.assert_(ve.getErrors("double_type") == 0, "correct type")

        p = Policy(self.getTestDictionary("types_policy_bad_string.paf"))
        ve = ValidationError("Dictionary_1.py", 3, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.WRONG_TYPE, "wrong type")
        self.assert_(ve.getParamCount() == 5, "number of errors")
        self.assert_(ve.getErrors("string_type") == 0, "correct type")

        p = Policy(self.getTestDictionary("types_policy_bad_policy.paf"))
        ve = ValidationError("Dictionary_1.py", 4, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.WRONG_TYPE, "wrong type")
        self.assert_(ve.getParamCount() == 4, "number of errors")
        self.assert_(ve.getErrors("policy_type") == 0, "correct type")
        self.assert_(ve.getErrors("file_type") == 0, "correct type")

        p = Policy(self.getTestDictionary("types_policy_bad_file.paf"))
        ve = ValidationError("Dictionary_1.py", 5, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.NOT_LOADED, "not loaded")
        self.assert_(ve.getParamCount() == 6, "number of errors")
        self.assert_(ve.getErrors("bool_type") == ValidationError.NOT_LOADED,
                     "not loaded")
        self.assert_(ve.getErrors("file_type") == ValidationError.NOT_LOADED,
                     "not loaded")
        self.assert_(ve.getErrors("policy_type") == ValidationError.NOT_LOADED,
                     "not loaded")
        p.loadPolicyFiles(self.getTestDictionary(), True)
        ve = ValidationError("Dictionary_1.py", 6, "testWrongType")
        d.validate(p, ve)
        self.assert_(ve.getErrors() == ValidationError.WRONG_TYPE, "wrong type")
        self.assert_(ve.getErrors("file_type") == 0, "correct type")
        self.assert_(ve.getErrors("policy_type") == 0, "correct type")
        self.assert_(ve.getParamCount() == 4, "wrong type")

    def testValues(self):
        d = Dictionary(self.getTestDictionary("values_dictionary.paf"))
        d.check()
        p = Policy(self.getTestDictionary("values_policy_good_1.paf"))
        ve = ValidationError("Dictionary_1.py", 0, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getParamCount() == 0)

        # policy: disallow allowed, min, max
        p = Policy(self.getTestDictionary("values_policy_bad_policy_set.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getErrors("policy_set_type") 
                     == ValidationError.VALUE_DISALLOWED)
        p = Policy(self.getTestDictionary("values_policy_bad_policy_max.paf"))
        ve = ValidationError("Dictionary_1.py", 2, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getErrors("policy_max_type") 
                     == ValidationError.VALUE_OUT_OF_RANGE)
        p = Policy(self.getTestDictionary("values_policy_bad_policy_min.paf"))
        ve = ValidationError("Dictionary_1.py", 3, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getErrors("policy_min_type") 
                     == ValidationError.VALUE_OUT_OF_RANGE)

        # minOccurs/maxOccurs
        p = Policy(self.getTestDictionary("values_policy_bad_occurs.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getParamCount() == 6)
        self.assert_(ve.getErrors("bool_set_count_type")
                    == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getErrors("int_range_count_type")
                    == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getErrors("double_range_count_type")
                    == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getErrors("string_count_type")
                    == ValidationError.ARRAY_TOO_SHORT)
        self.assert_(ve.getErrors("disallowed")
                    == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getErrors("policy_count_type")
                    == ValidationError.TOO_MANY_VALUES)

        # min
        p = Policy(self.getTestDictionary("values_policy_bad_min.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getParamCount() == 4)
        self.assert_(ve.getErrors() == ValidationError.VALUE_OUT_OF_RANGE)
        self.assert_(ve.getErrors("string_count_type") == ValidationError.OK)
        self.assert_(ve.getErrors("policy_count_type") == ValidationError.OK)
        # max
        p = Policy(self.getTestDictionary("values_policy_bad_max.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getParamCount() == 4)
        self.assert_(ve.getErrors() == ValidationError.VALUE_OUT_OF_RANGE)
        self.assert_(ve.getErrors("string_count_type") == ValidationError.OK)
        self.assert_(ve.getErrors("policy_count_type") == ValidationError.OK)

        # allowed
        p = Policy(self.getTestDictionary("values_policy_bad_allowed.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getParamCount() == 4)
        self.assert_(ve.getErrors() == ValidationError.VALUE_DISALLOWED)
        self.assert_(ve.getErrors("int_range_count_type") == ValidationError.OK)
        self.assert_(ve.getErrors("string_count_type") == ValidationError.OK)
        self.assert_(ve.getErrors("policy_count_type") == ValidationError.OK)

        # allowed & min/max
        p = Policy(self.getTestDictionary("values_policy_bad_allowedminmax.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)
        self.assert_(ve.getParamCount() == 2)
        self.assert_(ve.getErrors("int_range_set_type") 
                     == ValidationError.VALUE_DISALLOWED 
                     + ValidationError.VALUE_OUT_OF_RANGE)
        self.assert_(ve.getErrors("double_range_count_type") 
                     == ValidationError.TOO_MANY_VALUES 
                     + ValidationError.VALUE_OUT_OF_RANGE)
        ve = ValidationError("Dictionary_1.py", 1, "testValues")
        d.validate(p, ve)

    def testNested(self):
        self.assertRaiseLCE("DictionaryError",
                            "policy_bad_subdef.dictionary is a string",
                            Dictionary, "Malformed subdictionary",
                            self.getTestDictionary("nested_dictionary_bad_1.paf"))

        p = Policy(self.getTestDictionary("nested_policy_good.paf"))
        self.assertRaiseLCE("DictionaryError", "Unknown Dictionary property",
                            Dictionary, "Malformed subdictionary",
                            self.getTestDictionary("nested_dictionary_bad_2.paf"))

        d = Dictionary(self.getTestDictionary("nested_dictionary_good.paf"))
        d.check()
        self.assertRaiseLCE("LogicErrorException", "dictionaryFile needs to be loaded",
                            d.validate, "dictionaryFile not loaded", p)
        self.assert_(not d.hasSubDictionary("policy_1"))
        self.assert_(d.hasSubDictionary("policy_2"))
        self.assert_(not d.hasSubDictionary("policy_load"))
        n = d.loadPolicyFiles(self.getTestDictionary(), True)
        self.assert_(d.hasSubDictionary("policy_load"))
        self.assert_(n == 1) # number of files loaded
        d.validate(p)

        ve = ValidationError("Dictionary_1.py", 1, "testNested")
        p = Policy(self.getTestDictionary("nested_policy_bad.paf"))
        d.validate(p, ve)
        self.assert_(ve.getErrors("policy_1") == ValidationError.WRONG_TYPE)
        self.assert_(ve.getErrors("policy_2.foo")
                     == ValidationError.VALUE_DISALLOWED)
        self.assert_(ve.getErrors("policy_2.bar")
                     == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getErrors("policy_3.baz.qux")
                     == ValidationError.WRONG_TYPE)
        self.assert_(ve.getErrors("policy_3.baz.paisley")
                     == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getErrors("policy_3.baz.paisley")
                     == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getErrors("policy_load.height")
                     == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getParamCount() == 6)

        # multiple nesting
        p = Policy(self.getTestDictionary("nested_policy_1.paf"))
        n = p.loadPolicyFiles(self.getTestDictionary())
        self.assert_(n == 3)
        self.assert_(p.getString("1.2b.foo") == "bar")

        d = Dictionary(self.getTestDictionary("nested_dictionary_1.paf"))
        n = d.loadPolicyFiles(self.getTestDictionary())
        self.assert_(n == 3)
        p = Policy(True, d) # load from defaults
        self.assert_(p.getString("1.2a.foo") == "bar")
        self.assert_(p.getString("1.2b.foo") == "bar")

        # error in child
        d = Dictionary(self.getTestDictionary("nested_dictionary_bad_child.paf"))
        d.loadPolicyFiles(self.getTestDictionary())
        # this should really be caught during loadPolicyFiles(), above
        self.assertRaiseLCE("DictionaryError", "Unknown type: \"NotAType\"",
                            d.makeDef("sub.something").getType,
                            "Loaded sub-dictionary specified a bogus type")

    def testChildDef(self):
        # simple
        d = Dictionary(self.getTestDictionary("childdef_simple_dictionary.paf"))
        p = Policy(self.getTestDictionary("childdef_simple_policy_good.paf"))
        d.validate(p)
        p = Policy(self.getTestDictionary("childdef_simple_policy_bad.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testChildDef")
        d.validate(p, ve)
        self.assert_(ve.getErrors("baz") == ValidationError.WRONG_TYPE)

        # multiple childDefs (DictionaryError)
        d = Dictionary(self.getTestDictionary("childdef_dictionary_bad_multiple.paf"))
        self.assertRaiseLCE("DictionaryError", "Multiple childDef",
                            d.validate, "Dictionary specifies unknown types", p)

        # complex
        d = Dictionary(self.getTestDictionary("childdef_complex_dictionary.paf"))
        p = Policy(self.getTestDictionary("childdef_complex_policy_good_1.paf"))
        d.validate(p)
        p = Policy(self.getTestDictionary("childdef_complex_policy_good_2.paf"))
        d.validate(p)
        p = Policy(self.getTestDictionary("childdef_complex_policy_bad_1.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testChildDef")
        d.validate(p, ve)
        self.assert_(ve.getErrors("joe") == ValidationError.NOT_AN_ARRAY)
        self.assert_(ve.getErrors("deb") == ValidationError.NOT_AN_ARRAY)
        self.assert_(ve.getErrors("bob") == ValidationError.NOT_AN_ARRAY)
        self.assert_(ve.getErrors("bob.bar") == ValidationError.NOT_AN_ARRAY)
        self.assert_(ve.getErrors("nested.helen.qux") 
                     == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getErrors("nested.marvin.rafael") 
                     == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getErrors("disallowed.foo") 
                     == ValidationError.TOO_MANY_VALUES)
        self.assert_(ve.getParamCount() == 7)
        
    def testDefaults(self):
        p = Policy.createPolicy(self.getTestDictionary("defaults_dictionary_good.paf"),
                                "", True)
        self.assert_(p.valueCount("bool_set_count") == 1)
        self.assert_(p.getBool("bool_set_count") == True)
        self.assert_(p.valueCount("int_range_count") == 3)
        self.assert_(p.getDouble("deep.sub_double") == 1.)
        self.assert_(p.get("indirect4.string_type") == "foo")

        try:
            p = Policy.createPolicy(self.getTestDictionary("defaults_dictionary_bad_1.paf"),
                                    "", True)
        except LsstCppException, e:
            ve = e.args[0] # the real exception that was thrown
            self.assert_(ve.getErrors("double")
                         == ValidationError.WRONG_TYPE)
            self.assert_(ve.getErrors("int_range_count")
                         == ValidationError.NOT_AN_ARRAY)
            self.assert_(ve.getErrors("bool_set_count")
                         == ValidationError.TOO_MANY_VALUES)
            self.assert_(ve.getErrors("deep.sub_double")
                         == ValidationError.WRONG_TYPE)
            self.assert_(ve.getParamCount() == 4)

    # test setting and adding when created with a dictionary
    def testSetAdd(self):
        p = Policy.createPolicy(self.getTestDictionary("defaults_dictionary_good.paf"),
                                "", True)
        self.assert_(p.canValidate())
        self.assertValidationError(
            ValidationError.TOO_MANY_VALUES, 
            p.add, "bool_set_count", True)
        self.assert_(p.valueCount("bool_set_count") == 1)
        self.assertValidationError(
            ValidationError.VALUE_DISALLOWED, 
            p.set, "bool_set_count", False)
        self.assert_(p.getBool("bool_set_count") == True)
        p.set("int_range_count", -7)
        self.assertValidationError(
            ValidationError.VALUE_OUT_OF_RANGE, 
            p.add, "int_range_count", 10)
        # add & set don't check against minOccurs, but validate() does
        try:
            p.validate()
        except LsstCppException, e:
            self.assert_(e.args[0].getErrors("int_range_count")
                         == ValidationError.NOT_AN_ARRAY)
            self.assert_(e.args[0].getErrors("required")
                         == ValidationError.MISSING_REQUIRED)
        p.add("int_range_count", -8)
        p.set("required", "foo")
        p.validate()

    def testSelfValidation(self):
        # assign a dictionary after creation
        p = Policy(self.getTestDictionary("types_policy_good.paf"))
        p.loadPolicyFiles(self.getTestDictionary(), True)
        typesDict = Dictionary(self.getTestDictionary("types_dictionary.paf"))
        valuesDict = Dictionary(self.getTestDictionary("values_dictionary.paf"))
        self.assert_(not p.canValidate())
        p.setDictionary(typesDict)
        self.assert_(p.canValidate())
        p.validate()
        p.set("bool_type", True)
        self.assertValidationError(
            ValidationError.WRONG_TYPE, p.set, "bool_type", "foo")

        # create with dictionary
        p = Policy.createPolicy(self.getTestDictionary("types_dictionary.paf"), "", True)
        self.assert_(p.canValidate())
        p.set("bool_type", True)
        self.assertValidationError(
            ValidationError.WRONG_TYPE, p.set, "bool_type", "foo")

        # assign a dictionary after invalid modifications
        p = Policy()
        p.set("bool_type", "foo")
        p.setDictionary(typesDict)
        ve = ValidationError("Dictionary_1.py", 1, "testSelfValidation")
        p.validate(ve)
        self.assert_(ve.getErrors("bool_type") == ValidationError.WRONG_TYPE)
        try:
            p.validate()
        except LsstCppException, e:
            ve = e.args[0]
            self.assert_(ve.getErrors("bool_type") == ValidationError.WRONG_TYPE)
            self.assert_(ve.getParamCount() == 1)
        p.set("bool_type", True)
        p.set("int_type", 1)
        p.validate()

        # switch dictionaries
        oldD = p.getDictionary()
        p.setDictionary(valuesDict)
        try:
            p.validate()
        except LsstCppException, e:
            self.assert_(e.args[0].getErrors("bool_type")
                         == ValidationError.UNKNOWN_NAME)
        p.set("string_range_type", "moo")
        try:
            p.set("string_range_type", "victor")
        except LsstCppException, e:
            self.assert_(e.args[0].getErrors("string_range_type")
                         == ValidationError.VALUE_OUT_OF_RANGE)
        p.setDictionary(oldD)
        p.remove("string_range_type")
        p.validate()

    def testMergeDefaults(self):
        # from a non-trivial dictionary
        p = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        p.set("required", "foo")
        d = Dictionary(self.getTestDictionary("defaults_dictionary_good.paf"))
        d.loadPolicyFiles(self.getTestDictionary(), True)
        self.assert_(p.nameCount() == 2)
        p.mergeDefaults(d)
        self.assert_(p.valueCount("int_range_count") == 3)
        self.assert_(p.nameCount() == 7)

        # from a policy that's really a dictionary
        p = Policy()
        pd = Policy(self.getTestDictionary("defaults_dictionary_indirect.paf"))
        p.mergeDefaults(pd)
        self.assert_(p.getString("string_type") == "foo")
        self.assert_(p.getDictionary().isDictionary())
        
        # from a policy that's really a non-trivial dictionary
        p = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        p.set("required", "foo")
        pd = Policy(self.getTestDictionary("defaults_dictionary_policy.paf"))
        pd.loadPolicyFiles(self.getTestDictionary(), True)
        self.assert_(p.nameCount() == 2)
        p.mergeDefaults(pd)
        self.assert_(p.valueCount("int_range_count") == 3)
        self.assert_(p.nameCount() == 5)

        # ensure post-load validation
        p.set("int_range_count", -5)
        self.assertValidationError(ValidationError.UNKNOWN_NAME,
                                   p.add, "unknown", 0)

        # test throwing validation
        p = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        try:
            p.mergeDefaults(pd)
        except LsstCppException, e:
            self.assert_(e.args[0].getErrors("required")
                         == ValidationError.MISSING_REQUIRED)

        # non-throwing validation
        p = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        ve = ValidationError("Dictionary_1.py", 1, "testMergeDefaults")
        p.mergeDefaults(pd, False, ve)
        self.assert_(ve.getErrors("required") == ValidationError.MISSING_REQUIRED)
        self.assert_(ve.getParamCount() == 1)

        # non-retention
        p = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        p.set("required", "foo")
        p.mergeDefaults(pd, False)
        # make sure validate() fails gracefully when no dictionary present
        self.assertRaiseLCE("DictionaryError", "No dictionary",
                            p.validate, "No dictionary assigned")
        p.add("unknown", 0) # would be rejected if dictionary was kept

        # deep merge from a Policy that's not a Dictionary
        p = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        p.mergeDefaults(Policy(self.getTestDictionary("defaults_policy_most.paf")))
        self.assert_(p.nameCount() == 3)
        self.assert_(p.getBool("bool_set_count") == True)
        self.assert_(p.getString("indirect.string_type") == "bar")

        # propagation of a Dictionary from one Policy to another via mergeDefaults
        d = Dictionary(self.getTestDictionary("defaults_dictionary_complete.paf"))
        d.loadPolicyFiles(self.getTestDictionary())
        pEmpty = Policy()
        pEmpty.mergeDefaults(d)
        self.assert_(pEmpty.canValidate())
        pPartial = Policy(self.getTestDictionary("defaults_policy_partial.paf"))
        pPartial.mergeDefaults(pEmpty)
        self.assert_(pPartial.canValidate(), "Dictionary handed off via mergeDefaults.")

    # test the sample code at http://dev.lsstcorp.org/trac/wiki/PolicyHowto
    def testSampleCode(self):
        policyFile = DefaultPolicyFile("pex_policy", "defaults_dictionary_complete.paf",
                                       "tests/dictionary")
        defaults = Policy.createPolicy(policyFile, policyFile.getRepositoryPath(), True)
        policy = Policy()
        policy.mergeDefaults(defaults)
        self.assert_(policy.canValidate())

        policy = Policy()
        policy.mergeDefaults(defaults, False)
        self.assert_(not policy.canValidate())

        # even if not keeping it around for future validation, validate the merge now
        policy = Policy()
        policy.set("bad", "worse")
        self.assertValidationError(ValidationError.UNKNOWN_NAME,
                                   policy.mergeDefaults, defaults, False)
        self.assert_(not policy.canValidate())

    # test operations on an empty sub-dictionary (ticket 1210)
    def testEmptySubdict(self):
        d = Dictionary(self.getTestDictionary("empty_subdictionary.paf"))
        p = Policy()
        p.set("empty_required", Policy(self.getTestDictionary("simple_policy.paf")))
        p.mergeDefaults(d)
        self.assert_(p.get("empty_sub_with_default.foo") == "bar")
        p.setDictionary(d)
        # this works because there is a definition for "empty_sub_with_default.foo"
        p.set("empty_sub_with_default.foo", "baz")

        p2 = Policy()
        p2.set("foo", "baz")
        p.set("empty_sub_no_default", p2)
        # this fails because Policy tries to makeDef("empty_sub_no_default.foo")
        # which fails because there's only a definition for "empty_sub_no_default",
        # but it doesn't contain any sub-definitions
        # p.set("empty_sub_no_default.foo", "baz")
        self.assertRaiseLCE("DictionaryError",
                            "empty_sub_no_default.dictionary not found",
                            p.set, "Empty policy definition -- if this fails, "
                            "it means a known bug has been fixed.  That's good.",
                            "empty_sub_no_default.foo", "baz")

def suite():
    """a suite containing all the test cases in this module"""
    tests.init()

    suites = []
    suites += unittest.makeSuite(DictionaryTestCase)
    suites += unittest.makeSuite(tests.MemoryTestCase)

    return unittest.TestSuite(suites)

def run(exit=False):
    """Run the tests"""
    tests.run(suite(), exit)

if __name__ == "__main__":
    run(True)
