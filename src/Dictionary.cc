/*
 * Dictionary
 */
#include "lsst/pex/policy/Dictionary.h"
#include "lsst/pex/policy/PolicyFile.h"
// #include "lsst/pex/utils/Trace.h"

#include <boost/scoped_ptr.hpp>
#include <boost/make_shared.hpp>
#include <boost/lexical_cast.hpp>

#include <stdexcept>
#include <memory>
#include <string>
#include <set>

namespace lsst {
namespace pex {
namespace policy {

//@cond

using boost::regex;
using boost::sregex_token_iterator;
using boost::scoped_ptr;
using namespace std;
using namespace boost;

const string ValidationError::EMPTY;

ValidationError::MsgLookup ValidationError::_errmsgs;

POL_EXCEPT_VIRTFUNCS(lsst::pex::policy::ValidationError)

void ValidationError::_loadMessages() {
    _errmsgs[OK] = EMPTY;
    _errmsgs[WRONG_TYPE] = "value has the incorrect type";
    _errmsgs[MISSING_REQUIRED] = "no value available for required parameter";
    _errmsgs[NOT_AN_ARRAY] = "value is not an array as required";
    _errmsgs[ARRAY_TOO_SHORT] = "insufficient number of array values";
    _errmsgs[TOO_FEW_VALUES] = "not enough values for parameter";
    _errmsgs[TOO_MANY_VALUES] = "too many values provided for parameter";
    _errmsgs[WRONG_OCCURRENCE_COUNT]="incorrect number of values for parameter";
    _errmsgs[VALUE_DISALLOWED] = "value is not among defined set";
    _errmsgs[VALUE_OUT_OF_RANGE] = "value is out of range";
    _errmsgs[BAD_VALUE] = "illegal value";
    _errmsgs[UNKNOWN_NAME] = "parameter name is unknown";
    _errmsgs[BAD_DEFINITION] = "malformed definition";
    _errmsgs[NOT_LOADED] = "file not loaded"
        " -- call Policy.loadPolicyFiles() before validating";
    _errmsgs[UNKNOWN_ERROR] = "unknown error";
}

vector<string> ValidationError::getParamNames() const {
    std::vector<std::string> result;
    ParamLookup::const_iterator i;
    for (i = _errors.begin(); i != _errors.end(); ++i)
        result.push_back(i->first);
    return result;
}

string ValidationError::describe(string prefix) const {
    ostringstream os;
    std::list<std::string> names;
    paramNames(names);
    for (std::list<string>::const_iterator i = names.begin(); i != names.end(); ++i)
        os << prefix << *i << ": " 
           << getErrorMessageFor((ErrorType)getErrors(*i)) << endl;
    return os.str();
}

char const* ValidationError::what(void) const throw() {
    // static to avoid memory issue -- but a concurrency problem?
    // copied from pex/exceptions/src/Exception.cc
    static std::string buffer;
    ostringstream os;
    int n = getParamCount();
    os << "Validation error";
    if (n == 1) os << " (1 error)";
    else if (n > 1) os << " (" << getParamCount() << " errors)";
    if (getParamCount() == 0)
        os << ": no errors" << "\n";
    else {
        os << ": \n" << describe("  * ");
    }
    buffer = os.str();
    return buffer.c_str();
}

ValidationError::~ValidationError() throw() { }

///////////////////////////////////////////////////////////
//  Definition
///////////////////////////////////////////////////////////

Definition::~Definition() { }

Policy::ValueType Definition::_determineType() const {
    if (_policy->isString(Dictionary::KW_TYPE)) {
        const string& type = _policy->getString(Dictionary::KW_TYPE);
        Policy::ValueType result;
        try {
            result = Policy::getTypeByName(type);
        } catch(BadNameError&) {
            throw LSST_EXCEPT
                (DictionaryError, string("Unknown type: \"") + type + "\".");
        }
        if (result == Policy::FILE)
            throw LSST_EXCEPT(DictionaryError, string("Illegal type: \"") + type
                              + "\"; use \"" + Policy::typeName[Policy::POLICY]
                              + "\" instead.");
        else return result;
    }
    else if (_policy->exists(Dictionary::KW_TYPE)) {
        throw LSST_EXCEPT
            (DictionaryError, string("Expected string for \"type\"; found ") 
             + _policy->getTypeName(Dictionary::KW_TYPE) + " instead.");
    }

    else return Policy::UNDEF;
}
    
/**
 * Return the semantic definition for the parameter, empty string if none is
 * specified, or throw a TypeError if it is the wrong type.
 */
const string Definition::getDescription() const {
    if (_policy->exists(Dictionary::KW_DESCRIPTION)) 
        return _policy->getString(Dictionary::KW_DESCRIPTION);
    else return "";
}

/**
 * return the maximum number of occurrences allowed for this parameter, 
 * or -1 if there is no limit.
 */
const int Definition::getMaxOccurs() const {
    try {  return _policy->getInt(Dictionary::KW_MAX_OCCUR);  }
    catch (NameNotFound& ex) {  return -1;  }
}

/**
 * return the minimum number of occurrences allowed for this parameter.
 * Zero is returned if a minimum is not specified.
 */
const int Definition::getMinOccurs() const {
    try {  return _policy->getInt(Dictionary::KW_MIN_OCCUR);  }
    catch (NameNotFound& ex) {  return 0;  }
}


/*
 * the default value into the given policy
 * @param policy   the policy object update
 * @param withName the name to look for the value under.  This must be 
 *                    a non-hierarchical name.
 * @exception ValidationError if the value does not conform to this definition.
 */
void Definition::setDefaultIn(Policy& policy, const string& withName,
                              ValidationError* errs) const 
{
    if (! _policy->exists("default")) return;
/*
    Policy::ValueType type = getType();
    if (type == Policy::UNDEF) 
        type = _policy->getValueType("default");
*/
    Policy::ValueType type = _policy->getValueType("default");

    if (type == Policy::BOOL) 
        setDefaultIn<bool>(policy, withName, errs);
    else if (type == Policy::INT)
        setDefaultIn<int>(policy, withName, errs);
    else if (type == Policy::DOUBLE)
        setDefaultIn<double>(policy, withName, errs);
    else if (type == Policy::STRING)
        setDefaultIn<string>(policy, withName, errs);
    else if (type == Policy::POLICY)
        setDefaultIn<Policy::Ptr>(policy, withName, errs);
    else throw LSST_EXCEPT(pexExcept::LogicErrorException,
                           string("Programmer Error: Unknown type for \"")
                           + getPrefix() + withName + "\": "
                           + Policy::typeName[getType()]);
}

/*
 * confirm that a Policy parameter conforms to this definition
 * @param policy   the policy object to inspect
 * @param name     the name to look for the value under.  If not given
 *                  the name set in this definition will be used.
 * @exception ValidationError   if the value does not conform.  The message
 *                 should explain why.
 */
void Definition::validate(const Policy& policy, const string& name,
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    if (! policy.exists(name)) {
        try {
            if (_policy->getInt(Dictionary::KW_MIN_OCCUR) > 0)
                use->addError(getPrefix() + name, ValidationError::MISSING_REQUIRED);
        }
        catch (NameNotFound&) { }
        return;
    }

    // What type is actually present in the policy?
    Policy::ValueType type = policy.getValueType(name);

    switch (type) {
    case Policy::BOOL: 
        validateBasic<bool>(name, policy, use);
        break;

    case Policy::INT:
        validateBasic<int>(name, policy, use);
        break;

    case Policy::DOUBLE:
        validateBasic<double>(name, policy, use);
        break;

    case Policy::STRING:
        validateBasic<string>(name, policy, use);
        break;

    case Policy::POLICY:
        validateBasic<Policy::ConstPtr>(name, policy, use);
        validateRecurse(name, policy.getConstPolicyArray(name), use);
        break;

    case Policy::FILE:
        use->addError(getPrefix() + name, ValidationError::NOT_LOADED);
        break;

    default:
        throw LSST_EXCEPT(pexExcept::LogicErrorException,
                          string("Unknown type for \"") + getPrefix() + name 
                          + "\": \"" + policy.getTypeName(name) + "\"");
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

/**
 * Validate the number of values for a field. Used internally by the
 * validate() functions. 
 * @param name   the name of the parameter being checked
 * @param count  the number of values this name actually has
 * @param errs   report validation errors here
 */
void Definition::validateCount(const string& name, int count,
                               ValidationError *errs) const {
    int max = getMaxOccurs(); // -1 means no limit / undefined
    if (max >= 0 && count > max) 
        errs->addError(getPrefix() + name, ValidationError::TOO_MANY_VALUES);
    if (count < getMinOccurs()) {
        if (count == 0) 
            errs->addError(getPrefix() + name, ValidationError::MISSING_REQUIRED);
        else if (count == 1) 
            errs->addError(getPrefix() + name, ValidationError::NOT_AN_ARRAY);
        else 
            errs->addError(getPrefix() + name, ValidationError::ARRAY_TOO_SHORT);
    }
}

/**
 * Stubs for validation template functions.  Always return true, which always
 * failes validation tests.  In other words, any values of min or max for these
 * types will cause a failure.
 */
bool operator<(const Policy& a, const Policy& b) { return true; }
bool operator<(const Policy::ConstPtr& a, const Policy::ConstPtr& b) { return true; }
bool operator<(const Policy::FilePtr& a, const Policy::FilePtr& b) { return true; }

void Definition::validateRecurse(const string& name,
                                 Policy::ConstPolicyPtrArray value,
                                 ValidationError *errs) const
{
    for (Policy::ConstPolicyPtrArray::const_iterator i = value.begin();
         i != value.end(); ++i) {
        Policy::ConstPtr p = *i;
        validateRecurse(name, *p, errs);
    }
}

/* Validate a sub-policy using a sub-dictionary. */
void Definition::validateRecurse(const string& name, const Policy& value,
                                 ValidationError *errs) const
{
    if (!getType() == Policy::POLICY) // should have checked this at a higher level
        throw LSST_EXCEPT
            (pexExcept::LogicErrorException, string("Wrong type: expected ") 
             + Policy::typeName[Policy::POLICY] + " for " + getPrefix() + name 
             + " but found " + getTypeName() + ". // recurse if we have a sub-definition");
    // recurse if we have a sub-definition
    else if (_policy->exists(Dictionary::KW_DICT)) {
        if (!_policy->isPolicy(Dictionary::KW_DICT))
            throw LSST_EXCEPT
                (DictionaryError, string("Wrong type for ") + getPrefix() + name 
                 + " \"" + Dictionary::KW_DICT + "\": expected Policy, but found " 
                 + _policy->getTypeName(Dictionary::KW_DICT) + ".");
        else {
            Dictionary subdict(*(_policy->getPolicy(Dictionary::KW_DICT)));
            subdict.setPrefix(_prefix + name + ".");
            subdict.validate(value, errs);
        }
    }
    else if (_policy->exists(Dictionary::KW_DICT_FILE)) {
        throw LSST_EXCEPT
            (pexExcept::LogicErrorException, _prefix + name
             + "." + Dictionary::KW_DICT_FILE + " needs to be loaded with "
             "Dictionary.loadPolicyFiles() before validating.");
    }
    // Otherwise, make sure no unknown fields are there -- did somebody try to
    // specify some constraints and get it wrong?
    else {
        static set<string> okayNames;
        if (okayNames.size() == 0) {
            okayNames.insert(Dictionary::KW_TYPE);
            okayNames.insert(Dictionary::KW_DICT);
            okayNames.insert(Dictionary::KW_DICT_FILE);
            okayNames.insert(Dictionary::KW_MIN_OCCUR);
            okayNames.insert(Dictionary::KW_MAX_OCCUR);
            okayNames.insert(Dictionary::KW_ALLOWED);
        }
        Policy::StringArray names = _policy->names(true);
        for (Policy::StringArray::const_iterator i = names.begin();
             i != names.end(); ++i) 
        {
            if (okayNames.count(*i) == 1) continue;
            else throw LSST_EXCEPT
                (DictionaryError, string("Unknown Dictionary property found at ")
                 + _prefix + name + ": " + *i);
        }
    }
}

template <class T>
void Definition::validateBasic(const string& name, const T& value,
                               int curcount, ValidationError *errs) const
{
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check if we're going to get too many
    if (curcount >= 0) {
        int maxOccurs = getMaxOccurs();
        if (maxOccurs >= 0 && curcount + 1 > maxOccurs) 
            use->addError(getPrefix() + name, ValidationError::TOO_MANY_VALUES);
    }

    if (getType() != Policy::UNDEF && getType() != Policy::getValueType<T>()) {
        use->addError(getPrefix() + name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy(Dictionary::KW_ALLOWED)) {
        Policy::PolicyPtrArray allowed
            = _policy->getPolicyArray(Dictionary::KW_ALLOWED);

        T min, max;
        bool minFound = false, maxFound = false;
        set<T> allvals;
        for (Policy::PolicyPtrArray::const_iterator it = allowed.begin();
             it != allowed.end(); ++it)
        {
            Policy::Ptr a = *it;
            if (a->exists(Dictionary::KW_MIN)) {
                if (minFound) {
                    // Would like to catch this in Dictionary::check(), but that
                    // would require some fancy type-based logic.
                    throw LSST_EXCEPT
                        (DictionaryError, 
                         string("Min value for ") + getPrefix() + name
                         + " (" + lexical_cast<string>(min) 
                         + ") already specified; additional value not allowed.");
                }
                try {
                    min = a->getValue<T>(Dictionary::KW_MIN);
                } catch(TypeError& e) {
                    throw LSST_EXCEPT
                        (DictionaryError, 
                         string("Wrong type for ") + getPrefix() + name 
                         + " min value: expected " + getTypeName() + ", found \"" 
                         + lexical_cast<string>(max) + "\".");
                } catch(...) {
                    throw;
                }
                minFound = true; // after min assign, in case of exceptions
            }
            if (a->exists(Dictionary::KW_MAX)) {
                if (maxFound)
                    throw LSST_EXCEPT
                        (DictionaryError,
                         string("Max value for ") + getPrefix() + name
                         + " (" + lexical_cast<string>(max) 
                         + ") already specified; additional value not allowed.");
                try {
                    max = a->getValue<T>(Dictionary::KW_MAX);
                } catch(TypeError& e) {
                    throw LSST_EXCEPT
                        (DictionaryError, 
                         string("Wrong type for ") + getPrefix() + name 
                         + " max value: expected " + getTypeName() + ", found \"" 
                         + lexical_cast<string>(max) + "\".");
                }
                maxFound = true; // after max assign, in case of exceptions
            }
            if (a->exists(Dictionary::KW_VALUE))
                allvals.insert(a->getValue<T>(Dictionary::KW_VALUE));
        }

        if ((minFound && value < min) || (maxFound && max < value))
            use->addError(getPrefix() + name, ValidationError::VALUE_OUT_OF_RANGE);

        if (allvals.size() > 0 && allvals.count(value) == 0)
            use->addError(getPrefix() + name, ValidationError::VALUE_DISALLOWED);
    }
    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

/*
 * confirm that a Policy parameter name-value combination is consistent 
 * with this dictionary.  This does not check occurrence compliance
 * @param name     the name of the parameter being checked
 * @param value    the value of the parameter to check.
 * @exception ValidationError   if the value does not conform.  The message
 *                 should explain why.
 */
void Definition::validate(const string& name, bool value, int curcount,
                          ValidationError *errs) const 
{ 
    validateBasic<bool>(name, value, curcount, errs);
}

void Definition::validate(const string& name, int value, int curcount,
                          ValidationError *errs) const 
{ 
    validateBasic<int>(name, value, curcount, errs);
}

void Definition::validate(const string& name, double value, int curcount,
                          ValidationError *errs) const 
{ 
    validateBasic<double>(name, value, curcount, errs);
}

void Definition::validate(const string& name, string value, int curcount,
                          ValidationError *errs) const 
{ 
    validateBasic<string>(name, value, curcount, errs);
}

void Definition::validate(const string& name, const Policy& value, 
                          int curcount, ValidationError *errs) const 
{ 
    validateBasic<Policy>(name, value, curcount, errs);
    validateRecurse(name, value, errs);
}

/*
 * confirm that a Policy parameter name-array value combination is 
 * consistent with this dictionary.  Unlike the scalar version, 
 * this does check occurrence compliance.  
 * @param name     the name of the parameter being checked
 * @param value    the value of the parameter to check.
 * @exception ValidationError   if the value does not conform.  The message
 *                 should explain why.
 */
void Definition::validate(const string& name, const Policy::BoolArray& value, 
                          ValidationError *errs) const 
{ 
    validateBasic<bool>(name, value, errs);
}

void Definition::validate(const string& name, const Policy::IntArray& value, 
                          ValidationError *errs) const 
{ 
    validateBasic<int>(name, value, errs);
}

void Definition::validate(const string& name, const Policy::DoubleArray& value,
                          ValidationError *errs) const 
{ 
    validateBasic<double>(name, value, errs);
}
void Definition::validate(const string& name, const Policy::StringArray& value, 
                          ValidationError *errs) const 
{ 
    validateBasic<string>(name, value, errs);
}

void Definition::validate(const string& name, const Policy::ConstPolicyPtrArray& value, 
                          ValidationError *errs) const 
{ 
    validateBasic<Policy::ConstPtr>(name, value, errs);
    validateRecurse(name, value, errs);
}

///////////////////////////////////////////////////////////
//  Dictionary
///////////////////////////////////////////////////////////

const char* Dictionary::KW_DICT = "dictionary";
const char* Dictionary::KW_DICT_FILE = "dictionaryFile";
const char* Dictionary::KW_TYPE = "type";
const char* Dictionary::KW_DESCRIPTION = "description";
const char* Dictionary::KW_DEFS = "definitions";
const char* Dictionary::KW_CHILD_DEF = "childDefinition";
const char* Dictionary::KW_ALLOWED = "allowed";
const char* Dictionary::KW_MIN_OCCUR = "minOccurs";
const char* Dictionary::KW_MAX_OCCUR = "maxOccurs";
const char* Dictionary::KW_MIN = "min";
const char* Dictionary::KW_MAX = "max";
const char* Dictionary::KW_VALUE = "value";

const regex Dictionary::FIELDSEP_RE("\\.");

/*
 * load a dictionary from a file
 */
Dictionary::Dictionary(const char *filePath) : Policy(filePath) { 
    if (!exists(KW_DEFS))
        throw LSST_EXCEPT(pexExcept::RuntimeErrorException, string(filePath) 
                          + ": does not contain a Dictionary");
}
Dictionary::Dictionary(const string& filePath) : Policy(filePath) { 
    if (!exists(KW_DEFS))
        throw LSST_EXCEPT(pexExcept::RuntimeErrorException, string(filePath) 
                          + ": does not contain a Dictionary");
}
Dictionary::Dictionary(const PolicyFile& filePath) : Policy(filePath) { 
    if (!exists(KW_DEFS))
        throw LSST_EXCEPT(pexExcept::RuntimeErrorException, filePath.getPath() 
                          + ": does not contain a Dictionary");
}

/*
 * return a definition for the named parameter.  The caller is responsible
 * for deleting the returned object.  This is slightly more efficient than
 * getDef().
 * @param name    the hierarchical name for the parameter
 */
Definition* Dictionary::makeDef(const string& name) const {
    Policy *p = const_cast<Dictionary*>(this);
    Policy::Ptr sp; // sub-policy

    // split the name
    sregex_token_iterator it = make_regex_token_iterator(name, FIELDSEP_RE, -1);
    sregex_token_iterator end;
    string find;
    bool isWildcard = false; // was the immediate parent a wildcard childDefinition?
    while (it != end) {
        find = *it;
        if (! p->isPolicy(KW_DEFS))
            throw LSST_EXCEPT(DictionaryError, "Definition for " + find 
                              + " not found.");
        sp = p->getPolicy(KW_DEFS);
        if (sp->isPolicy(find)) {
            sp = sp->getPolicy(find);
            isWildcard = false; // update each time, to get only immediate parent
        }
        else if (sp->isPolicy(Dictionary::KW_CHILD_DEF)) {
            if (sp->valueCount(Dictionary::KW_CHILD_DEF) > 1)
                throw LSST_EXCEPT
                    (DictionaryError, string("Multiple ") + KW_CHILD_DEF
                     + "s found " + "that match " + getPrefix() + name + ".");
            sp = sp->getPolicy(Dictionary::KW_CHILD_DEF);
            isWildcard = true;
        }
        else throw LSST_EXCEPT(NameNotFound, find);
        p = sp.get();
        if (++it != end) {
            if (! sp->isPolicy(Dictionary::KW_DICT))
                throw LSST_EXCEPT(DictionaryError, 
                                  find + "." + KW_DICT + " not found.");
            sp = sp->getPolicy(Dictionary::KW_DICT);
            p = sp.get();
        }
    }
    Definition* result = new Definition(name, sp);
    result->setWildcard(isWildcard);
    result->setPrefix(getPrefix());
    return result;
}

/**
 * Return a branch of this dictionary, if this dictionary describes a
 * complex policy structure -- that is, if it describes a policy with
 * sub-policies.
 */
Policy::DictPtr Dictionary::getSubDictionary(const string& name) const {
    string subname = string(KW_DEFS) + "." + name + ".dictionary";
    if (!exists(subname)) throw LSST_EXCEPT
        (pexExcept::LogicErrorException,
         string("sub-policy \"") + subname + "\" not found.");
    if (!isPolicy(subname)) throw LSST_EXCEPT
        (DictionaryError, subname + " is a " + getTypeName(subname) 
         + " instead of a " + Policy::typeName[Policy::POLICY] + ".");
    ConstPtr subpol = getPolicy(subname);
    Policy::DictPtr result = make_shared<Dictionary>(*subpol);
    result->setPrefix(_prefix + name + ".");
    return result;
}

int Dictionary::loadPolicyFiles(const fs::path& repository, bool strict) {
    int maxLevel = 16;
    int result = 0;
    // loop until we reach the leaves
    for (int level = 0; level < maxLevel; ++level) {
        // find the "dictionaryFile" parameters
        list<string> params;
        paramNames(params, false);
        list<string> toRemove;
        for (list<string>::const_iterator ni=params.begin(); ni != params.end(); ++ni) { 
            static string endswith = string(".") + KW_DICT_FILE;
            size_t p = ni->rfind(endswith);
            if (p == ni->length()-endswith.length()) {
                string parent = ni->substr(0, p);
                Policy::Ptr defin = getPolicy(parent);
                PolicyFile subd;
                
                // these will get dereferenced with the call to super method
                if (isFile(*ni)) 
                    defin->set(Dictionary::KW_DICT, getFile(*ni));
                else
                    defin->set(Dictionary::KW_DICT,
                               make_shared<PolicyFile>(getString(*ni)));
                
                toRemove.push_back(*ni);
            }
        }
        
        // if no new loads, then we've loaded everything
        int newLoads = Policy::loadPolicyFiles(repository, strict);
        
        // remove obsolete dictionaryFile references, to prevent re-loading
        // TODO: note reference to loaded filename?
        for (list<string>::iterator i = toRemove.begin(); i != toRemove.end(); ++i)
            remove(*i);

        if (newLoads == 0) return result;
        else result += newLoads;
    }
    throw LSST_EXCEPT
        (DictionaryError, string("Exceeded recursion limit (") 
         + lexical_cast<string>(maxLevel) 
         + ") loading policy files; does this dictionary contain a circular"
         " definition?");
}

/**
 * Check this Dictionary's internal integrity.  Load up all definitions and
 * sanity-check them.
 */
void Dictionary::check() const {
    PolicyPtrArray defs = getValueArray<Policy::Ptr>(KW_DEFS);
    if (defs.size() == 0)
        throw LSST_EXCEPT(DictionaryError, 
                          string("no \"") + KW_DEFS + "\" section found");
    if (defs.size() > 1)
        throw LSST_EXCEPT
            (DictionaryError, string("expected a single \"") + KW_DEFS 
             + "\" section; found " + lexical_cast<string>(defs.size()));
    Policy::StringArray names = defs[0]->names(false);
    for (Policy::StringArray::const_iterator i = names.begin();
         i != names.end(); ++i)
    {
        scoped_ptr<Definition> def(makeDef(*i));
        if (hasSubDictionary(*i))
            getSubDictionary(*i)->check();
    }
}

/*
 * validate a Policy against this Dictionary
 */
void Dictionary::validate(const Policy& pol, ValidationError *errs) const { 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;
    Policy::StringArray params = pol.names(true);

    // validate each item in policy
    for (Policy::StringArray::const_iterator i = params.begin();
         i != params.end(); ++i) 
    {
        try {
            scoped_ptr<Definition> def(makeDef(*i));
            def->validate(pol, *i, use);
        }
        catch (NameNotFound& e) {
            use->addError(getPrefix() + *i, ValidationError::UNKNOWN_NAME);
        }
    }

    // check definitions of missing elements for required elements
    Policy::ConstPtr defs = getDefinitions();
    Policy::StringArray dn = defs->names(false);
    for (Policy::StringArray::const_iterator i = dn.begin(); i != dn.end(); ++i) {
        const string& name = *i;
        if (!pol.exists(name)) { // item in dictionary, but not in policy
            scoped_ptr<Definition> def(makeDef(name));
            if (name != Dictionary::KW_CHILD_DEF && def->getMinOccurs() > 0)
                use->addError(getPrefix() + name,
                              ValidationError::MISSING_REQUIRED);
        }
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

//@endcond

} // namespace policy
} // namespace pex
} // namespace lsst
