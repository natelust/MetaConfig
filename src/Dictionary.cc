/*
 * Dictionary
 */
#include "lsst/pex/policy/Dictionary.h"
#include "lsst/pex/policy/PolicyFile.h"
// #include "lsst/pex/utils/Trace.h"

#include <stdexcept>
#include <memory>
#include <string>
#include <set>
#include <boost/scoped_ptr.hpp>
#include <boost/regex.hpp>

using namespace std;

namespace lsst {
namespace pex {
namespace policy {

using boost::regex;
using boost::sregex_token_iterator;
using boost::scoped_ptr;

const string ValidationError::EMPTY;

map<int, string> ValidationError::_errmsgs;

void ValidationError::_loadMessages() {
    _errmsgs[OK] = EMPTY;
    _errmsgs[WRONG_TYPE] = "value has the incorrect type";
    _errmsgs[MISSING_REQUIRED] = "no value available for required parameter";
    _errmsgs[NOT_AN_ARRAY] = "value is not an array as required";
    _errmsgs[ARRAY_TOO_SHORT] = "insufficient number of array values";
    _errmsgs[TOO_FEW_VALUES] = "not enough values for parameter";
    _errmsgs[TOO_MANY_VALUES] = "too many values provided for parameter";
    _errmsgs[WRONG_OCCURANCE_COUNT]="incorrect number of values for parameter";
    _errmsgs[VALUE_DISALLOWED] = "value is not among defined set";
    _errmsgs[VALUE_OUT_OF_RANGE] = "value is out of range";
    _errmsgs[BAD_VALUE] = "illegal value";
    _errmsgs[UNKNOWN_ERROR] = "unknown error";
}

ValidationError::~ValidationError() throw() { }

///////////////////////////////////////////////////////////
//  Definition
///////////////////////////////////////////////////////////

Definition::~Definition() { }

Policy::ValueType Definition::_determineType() const {
    if (_policy->isString("type")) {
        const string& type = _policy->getString("type");
        if (type == Policy::typeName[Policy::BOOL]) 
            return Policy::BOOL;
        else if (type == Policy::typeName[Policy::INT]) 
            return Policy::INT;
        else if (type == Policy::typeName[Policy::DOUBLE]) 
            return Policy::DOUBLE;
        else if (type == Policy::typeName[Policy::STRING]) 
            return Policy::STRING;
        else if (type == Policy::typeName[Policy::POLICY]) 
            return Policy::POLICY;
    }

    return Policy::UNDEF;
}
    
/*
 * the default value into the given policy
 * @param policy   the policy object update
 * @param withName the name to look for the value under.  This must be 
 *                    a non-hierarchical name.
 */
void Definition::setDefaultIn(Policy& policy, const string& withName) const {
    if (! _policy->exists("default")) return;
    Policy::ValueType type = getType();
    if (type == Policy::UNDEF) 
        type = _policy->getValueType("default");

    switch (getType()) {
    case Policy::BOOL: 
    {
        const Policy::BoolArray& defs = _policy->getBoolArray("default");
        Policy::BoolArray::const_iterator it;
        for(it=defs.begin(); it != defs.end(); ++it) {
            if (it == defs.begin()) 
                // erase previous values
                policy.set(withName, *it);
            else 
                policy.add(withName, *it);
        }
        break;
    }

    case Policy::INT:
    {
        const Policy::IntArray& defs = 
            _policy->getIntArray("default");
        Policy::IntArray::const_iterator it;
        for(it=defs.begin(); it != defs.end(); ++it) {
            if (it == defs.begin()) 
                // erase previous values
                policy.set(withName, *it);
            else 
                policy.add(withName, *it);
        }
        break;
    }

    case Policy::DOUBLE:
    {
        const Policy::DoubleArray& defs = 
            _policy->getDoubleArray("default");
        Policy::DoubleArray::const_iterator it;
        for(it=defs.begin(); it != defs.end(); ++it) {
            if (it == defs.begin()) 
                // erase previous values
                policy.set(withName, *it);
            else 
                policy.add(withName, *it);
        }
        break;
    }

    case Policy::STRING:
    {
        const Policy::StringPtrArray& defs = 
            _policy->getStringArray("default");
        Policy::StringPtrArray::const_iterator it;
        for(it=defs.begin(); it != defs.end(); ++it) {
            if (it == defs.begin()) 
                // erase previous values
                policy.set(withName, **it);
            else 
                policy.add(withName, **it);
        }
        break;
    }

    case Policy::POLICY:
    {
        const Policy::PolicyPtrArray& defs = 
            _policy->getPolicyArray("default");
        Policy::PolicyPtrArray::const_iterator it;
        for(it=defs.begin(); it != defs.end(); ++it) {
            if (it == defs.begin()) 
                // erase previous values
                policy.set(withName, *it);
            else 
                policy.add(withName, *it);
        }
        break;
    }

    default:
        break;
    }
}

/*
 * confirm that a Policy parameter conforms this definition
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
            if (_policy->getInt("minOccurs") > 0)
                use->addError(name, ValidationError::MISSING_REQUIRED);
        }
        catch (NameNotFound&) { }
        return;
    }

    switch (policy.getValueType(name)) {
    case Policy::BOOL: 
        validate(name, _policy->getBoolArray("default"), use);
        break;

    case Policy::INT:
        validate(name, _policy->getIntArray("default"), use);
        break;

    case Policy::DOUBLE:
        validate(name, _policy->getDoubleArray("default"), use);
        break;

    case Policy::STRING:
        validate(name, _policy->getStringArray("default"), use);
        break;

    case Policy::POLICY:
        validate(name, _policy->getPolicyArray("default"), use);
        break;

    default:
        break;
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

/*
 * confirm that a Policy parameter name-value combination is consistent 
 * with this dictionary.  This does not check occurance compliance
 * @param name     the name of the parameter being checked
 * @param value    the value of the parameter to check.
 * @exception ValidationError   if the value does not conform.  The message
 *                 should explain why.
 */
void Definition::validate(const string& name, bool value, int curcount,
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check if we're going to get too many
    if (curcount >= 0) {
        int max = getMaxOccurs();
        if (max >= 0 && curcount + 1 > max) 
            use->addError(name, ValidationError::TOO_MANY_VALUES);
    }

    if (getType() != Policy::BOOL) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");
        set<bool> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { allvals.insert((*i)->getBool("value")); }
            catch (...) { }
        }
        if (allvals.size() > 0 && allvals.find(value) != allvals.end()) 
            use->addError(name, ValidationError::VALUE_DISALLOWED);
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

void Definition::validate(const string& name, int value, int curcount,
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check if we're going to get too many
    if (curcount >= 0) {
        int max = getMaxOccurs();
        if (max >= 0 && curcount + 1 > max) 
            use->addError(name, ValidationError::TOO_MANY_VALUES);
    }

    if (getType() != Policy::INT) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        try {
            if (value < allowed.back()->getInt("min"))
                use->addError(name, ValidationError::VALUE_OUT_OF_RANGE);
        } catch (...) { }
        try {
            if (value > allowed.back()->getInt("max"))
                use->addError(name, ValidationError::VALUE_OUT_OF_RANGE);
        } catch (...) { }

        set<int> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getInt("value")); 
            }
            catch (...) { }
        }
        if (allvals.size() > 0 && allvals.find(value) != allvals.end()) 
            use->addError(name, ValidationError::VALUE_DISALLOWED);
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

void Definition::validate(const string& name, double value, int curcount,
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check if we're going to get too many
    if (curcount >= 0) {
        int max = getMaxOccurs();
        if (max >= 0 && curcount + 1 > max) 
            use->addError(name, ValidationError::TOO_MANY_VALUES);
    }

    if (getType() != Policy::DOUBLE) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        try {
            if (value < allowed.back()->getDouble("min"))
                use->addError(name, ValidationError::VALUE_OUT_OF_RANGE);
        } catch (...) { }
        try {
            if (value > allowed.back()->getDouble("max"))
                use->addError(name, ValidationError::VALUE_OUT_OF_RANGE);
        } catch (...) { }

        set<double> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getDouble("value")); 
            }
            catch (...) { }
        }
        if (allvals.size() > 0 && allvals.find(value) != allvals.end()) 
            use->addError(name, ValidationError::VALUE_DISALLOWED);
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

void Definition::validate(const string& name, string value, int curcount,
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check if we're going to get too many
    if (curcount >= 0) {
        int max = getMaxOccurs();
        if (max >= 0 && curcount + 1 > max) 
            use->addError(name, ValidationError::TOO_MANY_VALUES);
    }

    if (getType() != Policy::STRING) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        set<string> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getString("value")); 
            }
            catch (...) { }
        }
        if (allvals.size() > 0 && allvals.find(value) != allvals.end()) 
            use->addError(name, ValidationError::VALUE_DISALLOWED);
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

void Definition::validate(const string& name, const Policy& value, 
                          int curcount, ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check if we're going to get too many
    if (curcount >= 0) {
        int max = getMaxOccurs();
        if (max >= 0 && curcount + 1 > max) 
            use->addError(name, ValidationError::TOO_MANY_VALUES);
    }

    if (getType() != Policy::POLICY) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }

    try {
        Policy::Ptr dp = _policy->getPolicy("dictionary");
        std::auto_ptr<Dictionary> nd;
        Dictionary *d = 0;
        if ((d = dynamic_cast<Dictionary *>(dp.get())) != 0) {
            nd.reset(new Dictionary(*dp));
            d = nd.get();
        }
        d->validate(value, errs);
    }
    catch (...) { }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

/*
 * confirm that a Policy parameter name-array value combination is 
 * consistent with this dictionary.  Unlike the scalar version, 
 * this does check occurance compliance.  
 * @param name     the name of the parameter being checked
 * @param value    the value of the parameter to check.
 * @exception ValidationError   if the value does not conform.  The message
 *                 should explain why.
 */
void Definition::validate(const string& name, const Policy::BoolArray& value, 
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check that we have the number of values
    int lim = getMaxOccurs();
    if (lim >= 0 && int(value.size()) > lim) 
        use->addError(name, ValidationError::TOO_MANY_VALUES);
    lim = getMinOccurs();
    if (int(value.size()) < lim) {
        if (value.size() == 0) 
            use->addError(name, ValidationError::MISSING_REQUIRED);
        else if (value.size() == 1) 
            use->addError(name, ValidationError::NOT_AN_ARRAY);
        else 
            use->addError(name, ValidationError::ARRAY_TOO_SHORT);
    }

    if (getType() != Policy::INT) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        set<bool> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getBool("value")); 
            }
            catch (...) { }
        }

        if (allvals.size() > 0) {
            Policy::BoolArray::const_iterator it;
            for (it = value.begin(); it != value.end(); ++it) {
                if (allvals.find(*it) != allvals.end()) 
                    use->addError(name, ValidationError::VALUE_DISALLOWED);
            }
        }
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}
void Definition::validate(const string& name, const Policy::IntArray& value, 
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check that we have the number of values
    int lim = getMaxOccurs();
    if (lim >= 0 && int(value.size()) > lim) 
        use->addError(name, ValidationError::TOO_MANY_VALUES);
    lim = getMinOccurs();
    if (int(value.size()) < lim) {
        if (value.size() == 0) 
            use->addError(name, ValidationError::MISSING_REQUIRED);
        else if (value.size() == 1) 
            use->addError(name, ValidationError::NOT_AN_ARRAY);
        else 
            use->addError(name, ValidationError::ARRAY_TOO_SHORT);
    }

    if (getType() != Policy::INT) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        int min=-1, max=-1;
        try {  min = allowed.back()->getInt("min");  }
        catch (...) { }
        try {  max = allowed.back()->getInt("max");  }
        catch (...) { }

        set<int> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getInt("value")); 
            }
            catch (...) { }
        }

        Policy::IntArray::const_iterator it;
        for (it = value.begin(); it != value.end(); ++it) {
            if (allvals.size() > 0 && allvals.find(*it) != allvals.end()) 
                use->addError(name, ValidationError::VALUE_DISALLOWED);
            if ((min >= 0 && *it < min) ||
                (max <= 0 && *it > max))
                use->addError(name, ValidationError::VALUE_OUT_OF_RANGE);
        }
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}
void Definition::validate(const string& name, const Policy::DoubleArray& value,
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check that we have the number of values
    int lim = getMaxOccurs();
    if (lim >= 0 && int(value.size()) > lim) 
        use->addError(name, ValidationError::TOO_MANY_VALUES);
    lim = getMinOccurs();
    if (int(value.size()) < lim) {
        if (value.size() == 0) 
            use->addError(name, ValidationError::MISSING_REQUIRED);
        else if (value.size() == 1) 
            use->addError(name, ValidationError::NOT_AN_ARRAY);
        else 
            use->addError(name, ValidationError::ARRAY_TOO_SHORT);
    }

    if (getType() != Policy::DOUBLE) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        double min=-1, max=-1;
        try {  min = allowed.back()->getDouble("min");  }
        catch (...) { }
        try {  max = allowed.back()->getDouble("max");  }
        catch (...) { }

        set<double> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getDouble("value")); 
            }
            catch (...) { }
        }

        Policy::DoubleArray::const_iterator it;
        for (it = value.begin(); it != value.end(); ++it) {
            if (allvals.size() > 0 && allvals.find(*it) != allvals.end()) 
                use->addError(name, ValidationError::VALUE_DISALLOWED);
            if ((min >= 0 && *it < min) ||
                (max <= 0 && *it > max))
                use->addError(name, ValidationError::VALUE_OUT_OF_RANGE);
        }
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}
void Definition::validate(const string& name, 
                          const Policy::StringPtrArray& value, 
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check that we have the number of values
    int lim = getMaxOccurs();
    if (lim >= 0 && int(value.size()) > lim) 
        use->addError(name, ValidationError::TOO_MANY_VALUES);
    lim = getMinOccurs();
    if (int(value.size()) < lim) {
        if (value.size() == 0) 
            use->addError(name, ValidationError::MISSING_REQUIRED);
        else if (value.size() == 1) 
            use->addError(name, ValidationError::NOT_AN_ARRAY);
        else 
            use->addError(name, ValidationError::ARRAY_TOO_SHORT);
    }

    if (getType() != Policy::INT) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else if (_policy->isPolicy("allowed")) {
        Policy::PolicyPtrArray allowed = _policy->getPolicyArray("allowed");

        set<string> allvals;
        Policy::PolicyPtrArray::iterator i;
        for(i = allowed.begin(); i != allowed.end(); ++i) {
            try { 
                allvals.insert((*i)->getString("value")); 
            }
            catch (...) { }
        }

        if (allvals.size() > 0) {
            Policy::StringPtrArray::const_iterator it;
            for (it = value.begin(); it != value.end(); ++it) {
                if (allvals.find(**it) != allvals.end()) 
                    use->addError(name, ValidationError::VALUE_DISALLOWED);
            }
        }
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

void Definition::validate(const string& name, 
                          const Policy::PolicyPtrArray& value, 
                          ValidationError *errs) const 
{ 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    // check that we have the number of values
    int lim = getMaxOccurs();
    if (lim >= 0 && int(value.size()) > lim) 
        use->addError(name, ValidationError::TOO_MANY_VALUES);
    lim = getMinOccurs();
    if (int(value.size()) < lim) {
        if (value.size() == 0) 
            use->addError(name, ValidationError::MISSING_REQUIRED);
        else if (value.size() == 1) 
            use->addError(name, ValidationError::NOT_AN_ARRAY);
        else 
            use->addError(name, ValidationError::ARRAY_TOO_SHORT);
    }

    if (getType() != Policy::POLICY) {
        use->addError(name, ValidationError::WRONG_TYPE);
    }
    else {
        Policy::PolicyPtrArray::const_iterator it;
        for (it = value.begin(); it != value.end(); ++it) {
            validate(name, **it, -1, errs);
        }
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

///////////////////////////////////////////////////////////
//  Dictionary
///////////////////////////////////////////////////////////

const regex Dictionary::FIELDSEP_RE("\\.");

/*
 * load a dictionary from a file
 */
Dictionary::Dictionary(const char *filePath) : Policy(filePath) { 
    if (!exists("definitions"))
        throw LSST_EXCEPT(pexExcept::RuntimeErrorException, string(filePath) + ": does not contain a dictionary");
}
Dictionary::Dictionary(PolicyFile filePath) : Policy(filePath) { 
    if (!exists("definitions"))
        throw LSST_EXCEPT(pexExcept::RuntimeErrorException, filePath.getPath() + ": does not contain a dictionary");
}

/*
 * return a definition for the named parameter.  The caller is responsible
 * for deleting the returned object.  This is slightly more efficient the 
 * getDef().
 * @param name    the hierarchical name for the parameter
 */
Definition* Dictionary::makeDef(const string& name) const {
    Policy *p = const_cast<Dictionary*>(this);
    Policy::Ptr sp;

    // split the name
    sregex_token_iterator it = make_regex_token_iterator(name,FIELDSEP_RE, -1);
    sregex_token_iterator end;
    string find;
    while (it != end) {
        if (! p->isPolicy("definitions")) throw LSST_EXCEPT(NameNotFound, *it);
        sp = p->getPolicy("definitions");
        find = *it;
        if (! sp->isPolicy(find)) throw LSST_EXCEPT(NameNotFound, find);
        sp = sp->getPolicy(find);
        p = sp.get();
        if (++it != end) {
            if (! sp->isPolicy("dictionary")) 
                throw LSST_EXCEPT(NameNotFound, find+".dictionary");
            sp = sp->getPolicy("dictionary");
            p = sp.get();
        }
    }
    return new Definition(name, sp);
}

/*
 * validate a Policy against this Dictionary
 */
void Dictionary::validate(const Policy& pol, ValidationError *errs) const { 
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    list<string> params;
    pol.names(params, true);

    try {
        list<string>::iterator ni;
        for(ni = params.begin(); ni != params.end(); ++ni) {
            scoped_ptr<Definition> def(makeDef(*ni));
            def->validate(pol, *ni, use);
        }
    }
    catch (NameNotFound& e) {
        throw LSST_EXCEPT(pexExcept::LogicErrorException, string("Programmer Error: Param went missing: ") + e.what());
    }
    catch (TypeError& e) {
        throw LSST_EXCEPT(pexExcept::LogicErrorException, string("Programmer Error: Param's type morphed: ") + e.what());
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}



} // namespace policy
} // namespace pex
} // namespace lsst
