/**
 * \file Policy.cc
 */
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/PolicySource.h"
#include "lsst/pex/policy/Dictionary.h"
#include "lsst/pex/policy/parserexceptions.h"
// #include "lsst/pex/logging/Trace.h"

#include <boost/make_shared.hpp>
#include <boost/scoped_ptr.hpp>
#include <boost/filesystem/path.hpp>

#include <stdexcept>
#include <string>
#include <cctype>
#include <algorithm>
#include <sstream>

using namespace std;
using namespace boost;
namespace fs = boost::filesystem;
namespace pexExcept = lsst::pex::exceptions;
namespace dafBase = lsst::daf::base;

namespace lsst {
namespace pex {
namespace policy {

//@cond

using dafBase::PropertySet;
using dafBase::Persistable;

const char * const Policy::typeName[] = {
    "undefined",
    "bool",
    "int",
    "double",
    "string",
    "Policy",
    "PolicyFile"
};

/*
 * Create an empty policy
 */
Policy::Policy() 
    : Citizen(typeid(this)), Persistable(), _data(new PropertySet()) 
{ }

/*
 * Create policy
 */
Policy::Policy(const PolicyFile& file) 
    : Citizen(typeid(this)), Persistable(), _data(new PropertySet()) 
{ 
    file.load(*this);
}

/*
 * Create a Policy from a named file
 */
Policy::Policy(const string& filePath) 
    : Citizen(typeid(this)), Persistable(), _data(new PropertySet()) 
{
    PolicyFile file(filePath);
    file.load(*this);
}

/*
 * Create a Policy from a named file
 */
Policy::Policy(const char *filePath) 
    : Citizen(typeid(this)), Persistable(), _data(new PropertySet()) 
{
    PolicyFile file(filePath);
    file.load(*this);
}

/* Extract defaults from dict into target.  Note any errors in ve. */
void extractDefaults(Policy& target, const Dictionary& dict, ValidationError& ve) {
    list<string> names;
    dict.definedNames(names);

    for(list<string>::iterator it = names.begin(); it != names.end(); ++it) {
        const string& name = *it;
        std::auto_ptr<Definition> def(dict.makeDef(name));
        def->setDefaultIn(target, &ve);
        // recurse into sub-dictionaries
        if (def->getType() == Policy::POLICY && dict.hasSubDictionary(name)) {
            Policy::Ptr subp = make_shared<Policy>();
            extractDefaults(*subp, *dict.getSubDictionary(name), ve);
            if (subp->nameCount() > 0)
                target.add(name, subp);
        }
    }
}

/**
 * Create a default Policy from a Dictionary.  If the Dictionary references
 * files containing dictionaries for sub-Policies, an attempt is made to
 * open them and extract the default data, and if that attempt fails, an
 * exception is thrown.
 *
 * @param validate    if true, a shallow copy of the Dictionary will be
 *                    held onto by this Policy and used to validate future
 *                    updates.
 * @param dict        the Dictionary to load defaults from
 * @param repository  the directory to look for dictionary files referenced
 *                    in \c dict.  The default is the current directory.
 */
Policy::Policy(bool validate, const Dictionary& dict, 
               const fs::path& repository)
    : Citizen(typeid(this)), Persistable(), _data(new PropertySet()) 
{ 
    DictPtr loadedDict; // the dictionary that has all policy files loaded
    if (validate) { // keep loadedDict around for future validation
        setDictionary(dict);
        loadedDict = _dictionary;
    }
    else { // discard loadedDict when we finish constructor
        loadedDict.reset(new Dictionary(dict));
    }
    loadedDict->loadPolicyFiles(repository, true);

    ValidationError ve(LSST_EXCEPT_HERE);
    extractDefaults(*this, *loadedDict, ve);
    if (ve.getParamCount() > 0) throw ve;
}

/*
 * copy a Policy.  Sub-policy objects will not be shared.  
 */
Policy::Policy(const Policy& pol) 
    : Citizen(typeid(this)), Persistable(), _data() 
{
    _data = pol._data->deepCopy();
}

/*
 * copy a Policy.  Sub-policy objects will be shared unless deep is true
 */
Policy::Policy(Policy& pol, bool deep) 
    : Citizen(typeid(this)), Persistable(), _data() 
{
    if (deep)
        _data = pol._data->deepCopy();
    else
        _data = pol._data;
}

Policy* Policy::_createPolicy(PolicySource& source, bool doIncludes, 
                              const fs::path& repository, bool validate) 
{
    auto_ptr<Policy> pol(new Policy());
    source.load(*pol);

    if (pol->isDictionary()) {
        Dictionary d(*pol);
        pol.reset(new Policy(validate, d, repository));
    }

    if (doIncludes) pol->loadPolicyFiles(repository, true);

    return pol.release();
}

Policy* Policy::_createPolicy(const string& input, bool doIncludes, 
                              const fs::path& repository, bool validate) 
{
    fs::path repos = repository;
    if (repos.empty()) {
        fs::path filepath(input);
        if (filepath.has_parent_path()) repos = filepath.parent_path();
    }
    PolicyFile file(input);
    return _createPolicy(file, doIncludes, repos, validate);
}

/*
 * Create an empty policy
 */
Policy::~Policy() { }

/**
 * Can this policy validate itself -- that is, does it have a dictionary
 * that it can use to validate itself?  If true, then set() and add()
 * operations will be checked against it.
 */
bool Policy::canValidate() const {
    return _dictionary;
}

/**
 * The dictionary (if any) that this policy uses to validate itself,
 * including checking set() and add() operations for validity.
 */
const Policy::ConstDictPtr Policy::getDictionary() const {
    return _dictionary;
}

/**
 * Update this policy's dictionary that it uses to validate itself.  Note
 * that this will *not* trigger validation -- you will need to call \code
 * validate() \endcode afterwards.
 */
void Policy::setDictionary(const Dictionary& dict) {
    _dictionary = make_shared<Dictionary>(dict);
}

/**
 * Validate this policy, using its stored dictionary.  If \code
 * canValidate() \endcode is false, this will throw a LogicErrorException.
 *
 * If validation errors are found and \code err \endcode is null, a
 * ValidationError will be thrown.
 *
 * @param errs if non-null, any validation errors will be stored here
 * instead of being thrown.
 */
void Policy::validate(ValidationError *errs) const {
    if (!_dictionary) throw LSST_EXCEPT(DictionaryError, "No dictionary set.");
    else _dictionary->validate(*this, errs);
}

/** 
 * Given the human-readable name of a type ("bool", "int", "policy", etc),
 * what is its ValueType (BOOL, STRING, etc.)?  Throws BadNameError if
 * unknown.
 */
Policy::ValueType Policy::getTypeByName(const string& name) {
    static map<string, Policy::ValueType> nameTypeMap;

    if (nameTypeMap.size() == 0) {
        map<string, Policy::ValueType> tmp;
        int n = sizeof(Policy::typeName) / sizeof(char *);
        for (int i = 0; i < n; ++i) {
            // remember both capitalized and lowercase versions (eg Policy)
            tmp[Policy::typeName[i]] = (Policy::ValueType) i;
            string lowered(Policy::typeName[i]);
            transform(lowered.begin(), lowered.end(), lowered.begin(), ::tolower);
            tmp[lowered] = (Policy::ValueType) i;
        }
        // a few extras
        tmp["file"] = Policy::FILE;
        tmp["boolean"] = Policy::BOOL;
        tmp["integer"] = Policy::INT;
        tmp["undef"] = Policy::UNDEF;
        // assign after initializationto avoid concurrency problems
        nameTypeMap = tmp;

        if (tmp.count(name) == 1) return tmp[name];
    }
    else
        if (nameTypeMap.count(name) == 1) return nameTypeMap[name];
    
    throw LSST_EXCEPT(BadNameError, name);
}

/*
 * load the names of parameters into a given list.  
 * 
 * @param prepend       the names string to prepend to any names found.
 * @param names         the list object to be loaded
 * @param topLevelOnly  if true, only parameter names at the top of the 
 *                         hierarchy will be returned; no hierarchical 
 *                         names will be included.
 * @param append        if false, the contents of the given list will 
 *                         be erased before loading the names.  
 * @param want          a bit field indicating which is desired (1=Policies,
 *                         2=PolicyFiles, 4=parameters, 7=all).
 * @return int  the number of names added
 */
int Policy::_names(vector<string>& names, 
                   bool topLevelOnly, bool append, int want) const
{
    bool shouldCheck = true;
    vector<string> src;
    int have = 0, count = 0;
    if (want == 1) {
        src = _data->propertySetNames(topLevelOnly);
        have = 1;
        shouldCheck = false;
    }
    else if (want == 7) 
        src = _data->names(topLevelOnly);
    else 
        src = _data->paramNames(topLevelOnly);

    if (!append) names.erase(names.begin(), names.end());

    StringArray::iterator i;
    for(i = src.begin(); i != src.end(); ++i) {
        if (shouldCheck) {
            if (isPolicy(*i)) 
                have = 1;
            else if (isFile(*i)) 
                have = 2;
            else 
                have = 4;
        }
        if ((have&want) > 0) {
            names.push_back(*i);
            count++;
        }
    }

    return count;
}

/*
 * load the names of parameters into a given list.  
 * 
 * @param prepend       the names string to prepend to any names found.
 * @param names         the list object to be loaded
 * @param topLevelOnly  if true, only parameter names at the top of the 
 *                         hierarchy will be returned; no hierarchical 
 *                         names will be included.
 * @param append        if false, the contents of the given list will 
 *                         be erased before loading the names.  
 * @param want          a bit field indicating which is desired (1=Policies,
 *                         2=PolicyFiles, 4=parameters, 7=all).
 * @return int  the number of names added
 */
int Policy::_names(list<string>& names, 
                   bool topLevelOnly, bool append, int want) const
{
    bool shouldCheck = true;
    vector<string> src;
    int have = 0, count = 0;
    if (want == 1) {
        src = _data->propertySetNames(topLevelOnly);
        have = 1;
        shouldCheck = false;
    }
    else if (want == 7) 
        src = _data->names(topLevelOnly);
    else 
        src = _data->paramNames(topLevelOnly);

    if (!append) names.erase(names.begin(), names.end());

    StringArray::iterator i;
    for(i = src.begin(); i != src.end(); ++i) {
        if (shouldCheck) {
            if (isPolicy(*i)) 
                have = 1;
            else if (isFile(*i)) 
                have = 2;
            else 
                have = 4;
        }
        if ((have&want) > 0) {
            names.push_back(*i);
            count++;
        }
    }

    return count;
}

template <class T> void Policy::_validate(const std::string& name, const T& value, int curCount) {
    if (_dictionary) {
        try {
            scoped_ptr<Definition> def(_dictionary->makeDef(name));
            def->validateBasic(name, value, curCount);
        } catch(NameNotFound& e) {
            ValidationError ve(LSST_EXCEPT_HERE);
            ve.addError(name, ValidationError::UNKNOWN_NAME);
            throw ve;
        }
    }
}

/*
 * return the type information for the underlying type associated with
 * a given name.  
 */
Policy::ValueType Policy::getValueType(const string& name) const {
    try {
        const std::type_info& tp = _data->typeOf(name);

        // handle the special case of FilePtr first
        if (tp == typeid(Persistable::Ptr)) {
            try {  
                getFile(name); 
                return FILE;
            } catch(...) { }
        }

        if (tp == typeid(bool)) {
            return BOOL;
        }
        else if(tp == typeid(int)) {
            return INT;
        }
        else if (tp == typeid(double)) {
            return DOUBLE;
        }
        else if (tp == typeid(string)) {
            return STRING;
        }
        else if (tp == typeid(PropertySet::Ptr)) {
            return POLICY;
        }
        else {
            throw LSST_EXCEPT
                (pexExcept::LogicErrorException,
                 string("Policy: illegal type held by PropertySet: ") + tp.name());
        }
    } catch (pexExcept::NotFoundException&) {
        return UNDEF;
    }
}

template <> bool Policy::getValue <bool> (const string& name) const {
    return getBool(name);
}
template <> int Policy::getValue <int> (const string& name) const {
    return getInt(name);
}
template <> double Policy::getValue <double> (const string& name) const {
    return getDouble(name);
}
template <> string Policy::getValue <string> (const string& name) const {
    return getString(name);
}
template <>
Policy::FilePtr Policy::getValue <Policy::FilePtr> (const string& name) const {
    return getFile(name);
}
template <>
Policy::ConstPtr Policy::getValue <Policy::ConstPtr> (const string& name) const {
    return getPolicy(name);
}

template <> vector<bool> Policy::getValueArray(const string& name) const {
    return getBoolArray(name);
}
template <> vector<int> Policy::getValueArray(const string& name) const {
    return getIntArray(name);
}
template <> vector<double> Policy::getValueArray(const string& name) const {
    return getDoubleArray(name);
}
template <> vector<string> Policy::getValueArray(const string& name) const {
    return getStringArray(name);
}
template <> Policy::FilePtrArray Policy::getValueArray(const string& name) const {
    return getFileArray(name);
}
template <> Policy::PolicyPtrArray Policy::getValueArray(const string& name) const {
    return getPolicyArray(name);
}
template <> Policy::ConstPolicyPtrArray Policy::getValueArray(const string& name) const {
    return getConstPolicyArray(name);
}

template <> Policy::ValueType Policy::getValueType<bool>() { return BOOL; }
template <> Policy::ValueType Policy::getValueType<int>() { return INT; }
template <> Policy::ValueType Policy::getValueType<double>() { return DOUBLE; }
template <> Policy::ValueType Policy::getValueType<string>() { return STRING; }
template <> Policy::ValueType Policy::getValueType<Policy>() { return POLICY; }
template <> Policy::ValueType Policy::getValueType<Policy::FilePtr>() { return FILE; }
template <> Policy::ValueType Policy::getValueType<Policy::Ptr>() { return POLICY; }
template <> Policy::ValueType Policy::getValueType<Policy::ConstPtr>() { return POLICY; }

template <> void Policy::setValue(const string& name, const bool& value) {
    set(name, value); }
template <> void Policy::setValue(const string& name, const int& value) {
    set(name, value); }
template <> void Policy::setValue(const string& name, const double& value) {
    set(name, value); }
template <> void Policy::setValue(const string& name, const string& value) {
    set(name, value); }
template <> void Policy::setValue(const string& name, const Ptr& value) {
    set(name, value); }
template <> void Policy::setValue(const string& name, const FilePtr& value) {
    set(name, value); }

template <> void Policy::addValue(const string& name, const bool& value) {
    add(name, value); }
template <> void Policy::addValue(const string& name, const int& value) {
    add(name, value); }
template <> void Policy::addValue(const string& name, const double& value) {
    add(name, value); }
template <> void Policy::addValue(const string& name, const string& value) {
    add(name, value); }
template <> void Policy::addValue(const string& name, const Ptr& value) {
    add(name, value); }
template <> void Policy::addValue(const string& name, const FilePtr& value) {
    add(name, value); }

Policy::ConstPolicyPtrArray Policy::getConstPolicyArray(const string& name) const {
    ConstPolicyPtrArray out;
    vector<PropertySet::Ptr> psa = _getPropSetList(name);
    vector<PropertySet::Ptr>::const_iterator i;
    for(i=psa.begin(); i != psa.end(); ++i) 
        out.push_back(ConstPtr(new Policy(*i)));
    return out;
}

Policy::PolicyPtrArray Policy::getPolicyArray(const string& name) const {
    PolicyPtrArray out;
    vector<PropertySet::Ptr> psa = _getPropSetList(name);
    vector<PropertySet::Ptr>::const_iterator i;
    for(i=psa.begin(); i != psa.end(); ++i) 
        out.push_back(Ptr(new Policy(*i)));
    return out;
}

Policy::FilePtr Policy::getFile(const string& name) const {
    FilePtr out = 
        dynamic_pointer_cast<PolicyFile>(_data->getAsPersistablePtr(name));
    if (! out.get()) 
        throw LSST_EXCEPT(TypeError, name, string(typeName[FILE]));
    return out;
}

Policy::FilePtrArray Policy::getFileArray(const string& name) const
{
    FilePtrArray out;
    vector<Persistable::Ptr> pfa = _getPersistList(name);
    vector<Persistable::Ptr>::const_iterator i;
    FilePtr fp;
    for(i = pfa.begin(); i != pfa.end(); ++i) {
        fp = dynamic_pointer_cast<PolicyFile>(*i);
        if (! fp.get())
            throw LSST_EXCEPT(TypeError, name, string(typeName[FILE]));
        out.push_back(fp);
    }

    return out;
}

void Policy::set(const string& name, const FilePtr& value) {
    _data->set(name, dynamic_pointer_cast<Persistable>(value));
}

void Policy::add(const string& name, const FilePtr& value) {
    _data->add(name, dynamic_pointer_cast<Persistable>(value));
}

/**
 * Recursively replace all PolicyFile values with the contents of the 
 * files they refer to.  The type of a parameter containing a PolicyFile
 * will consequently change to a Policy upon successful completion.  If
 * the value is an array, all PolicyFiles in the array must load without
 * error before the PolicyFile values themselves are erased.
 * @param strict      If true, throw an exception if an error occurs 
 *                    while reading and/or parsing the file.  Otherwise,
 *                    replace the file reference with a partial or empty
 *                    (that is, "{}") sub-policy.
 * @param repository  a directory to look in for the referenced files.  
 *                    Only when the name of the file to be included is an
 *                    absolute path will this.  If empty or not provided,
 *                    the directorywill be assumed to be the current one.
 */
int Policy::loadPolicyFiles(const fs::path& repository, bool strict) {
    fs::path repos = repository;
    int result = 0;
    if (repos.empty()) repos = ".";

    // iterate through the top-level names in this Policy
    list<string> names;
    fileNames(names, true);
    for(list<string>::iterator it=names.begin(); it != names.end(); it++) {

        // iterate through the files in the value array
        const FilePtrArray& pfiles = getFileArray(*it);
        PolicyPtrArray pols;
        pols.reserve(pfiles.size());

        FilePtrArray::const_iterator pfi;
        for(pfi=pfiles.begin(); pfi != pfiles.end(); pfi++) {

            fs::path path = (*pfi)->getPath();
            if (! path.is_complete()) {
                // if this is a relative path
                path = repos / (*pfi)->getPath();
            }

            Ptr policy = make_shared<Policy>();
            PolicyFile pf(path.file_string());

            try {
                // increment even if fail, since we will remove the file record
                ++result;
                pf.load(*policy);
            }
            catch (pexExcept::IoErrorException& e) {
                if (strict) {
                    throw e;
                }
                // TODO: log a problem
            }
            catch (ParserError& e) {
                if (strict) {
                    throw e;
                }
                // TODO: log a problem
            }
            // everything else will get sent up the stack

            pols.push_back(policy);
        }

        remove(*it);
        for (PolicyPtrArray::iterator pi = pols.begin(); pi != pols.end(); ++pi)
            add(*it, *pi);
    }

    // Now iterate again to recurse into sub-Policy values
    // TODO: alter repos?; record name of source file? 
    policyNames(names, true);
    for(list<string>::iterator it=names.begin(); it != names.end(); it++) {
        PolicyPtrArray policies = getPolicyArray(*it);

        // iterate through the Policies in this array
        PolicyPtrArray::iterator pi;
        for(pi = policies.begin(); pi != policies.end(); pi++)
            result += (*pi)->loadPolicyFiles(repos, strict);
    }

    return result;
}


/**
 * use the values found in the given policy as default values for parameters not
 * specified in this policy.  This function will iterate through the parameter
 * names in the given policy, and if the name is not found in this policy, the
 * value from the given one will be copied into this one.  No attempt is made to
 * match the number of values available per name.
 * @param defaultPol  the policy to pull default values from.  This may be a
 *                    Dictionary; if so, the default values will drawn from the
 *                    appropriate default keyword.
 * @param keepForValidation if true, and if defaultPol is a Dictionary, keep
 *                    a reference to it for validation future updates to
 *                    this Policy.
 * @param errs        an exception to load errors into -- only relevant if
 *                    defaultPol is a Dictionary or if this Policy already has a
 *                    dictionary to validate against; if a validation error is
 *                    encountered, it will be added to errs if errs is non-null,
 *                    and an exception will not be raised; however, if errs is
 *                    null, an exception will be thrown if a validation error is
 *                    encountered.
 * @return int        the number of parameter names copied over
 */
int Policy::mergeDefaults(const Policy& defaultPol, bool keepForValidation, 
                          ValidationError *errs) 
{
    int added = 0;

    // if defaultPol is a dictionary, extract the default values
    auto_ptr<Policy> pol(0);
    const Policy *def = &defaultPol;
    if (def->isDictionary()) {
        // extract default values from dictionary
        pol.reset(new Policy(false, Dictionary(*def)));
        def = pol.get();
    }

    list<string> params;
    def->paramNames(params);
    list<string>::iterator nm;
    for(nm = params.begin(); nm != params.end(); ++nm) {
        if (! exists(*nm)) {
            const std::type_info& tp = def->getTypeInfo(*nm);
            if (tp == typeid(bool)) {
                BoolArray a = def->getBoolArray(*nm);
                BoolArray::iterator vi;
                for(vi=a.begin(); vi != a.end(); ++vi) 
                    add(*nm, *vi);
            }
            else if (tp == typeid(int)) {
                IntArray a = def->getIntArray(*nm);
                IntArray::iterator vi;
                for(vi=a.begin(); vi != a.end(); ++vi) 
                    add(*nm, *vi);
            }
            else if (tp == typeid(double)) {
                DoubleArray a = def->getDoubleArray(*nm);
                DoubleArray::iterator vi;
                for(vi=a.begin(); vi != a.end(); ++vi) 
                    add(*nm, *vi);
            }
            else if (tp == typeid(string)) {
                StringArray a = def->getStringArray(*nm);
                StringArray::iterator vi;
                for(vi=a.begin(); vi != a.end(); ++vi) 
                    add(*nm, *vi);
            }
            else if (def->isFile(*nm)) {
                FilePtrArray a = def->getFileArray(*nm);
                FilePtrArray::iterator vi;
                for(vi=a.begin(); vi != a.end(); ++vi) 
                    add(*nm, *vi);
            }
            else {
                // should not happen
                throw LSST_EXCEPT(pexExcept::LogicErrorException,
                                  string("Unknown type for \"") + *nm 
                                  + "\": \"" + getTypeName(*nm) + "\"");
                // added--;
            }
            added++;
        }
    }

    // if a dictionary is available, validate after all defaults are added
    // propagate dictionary?  If so, look for one and use it to validate
    if (keepForValidation) {
	if (defaultPol.isDictionary())
	    setDictionary(Dictionary(defaultPol));
	else if (defaultPol.canValidate())
	    setDictionary(*defaultPol.getDictionary());
	// if we couldn't find a dictionary, don't complain -- the API should
	// work with default values even if defaultPol is a Policy without an
	// attached Dictionary
	if (canValidate())
	    getDictionary()->validate(*this, errs);
    }
    // don't keep a dictionary around, but validate anyway only if defaultPol is
    // a Dictionary (if keepForValidation is false, there is a possibility that
    // we don't want to use the attached Dictionary for validation)
    else if (defaultPol.isDictionary())
	Dictionary(defaultPol).validate(*this, errs);

    return added;
}

/*
 * return a string representation of the value given by a name.  The
 * string "<null>" is printed if the name does not exist.
 */
string Policy::str(const string& name, const string& indent) const {
    ostringstream out;

    try {
        const std::type_info& tp = _data->typeOf(name);
        if (tp == typeid(bool)) {
            BoolArray b = getBoolArray(name);
            BoolArray::iterator vi;
            for(vi=b.begin(); vi != b.end(); ++vi) {
                out << *vi;
                if (vi+1 != b.end()) out << ", ";
            }
        }
        else if (tp == typeid(int)) {
            IntArray i = getIntArray(name);
            IntArray::iterator vi;
            for(vi=i.begin(); vi != i.end(); ++vi) {
                out << *vi;
                if (vi+1 != i.end()) out << ", ";
            }
        }
        else if (tp == typeid(double)) {
            DoubleArray d = getDoubleArray(name);
            DoubleArray::iterator vi;
            for(vi=d.begin(); vi != d.end(); ++vi) {
                out << *vi;
                if (vi+1 != d.end()) out << ", ";
            }
        }
        else if (tp == typeid(string)) {
            StringArray s = _data->getArray<string>(name);
            StringArray::iterator vi;
            for(vi= s.begin(); vi != s.end(); ++vi) {
                out << '"' << *vi << '"';
                if (vi+1 != s.end()) out << ", ";
            }
        }
        else if (tp == typeid(PropertySet::Ptr)) {
            vector<PropertySet::Ptr> p = 
                _data->getArray<PropertySet::Ptr>(name);
            vector<PropertySet::Ptr>::iterator vi;
            for(vi= p.begin(); vi != p.end(); ++vi) {
                out << "{\n";
                Policy(*vi).print(out, "", indent+"  ");
                out << indent << "}";
                if (vi+1 != p.end()) out << ", ";
                out.flush();
            }
        }
        else if (tp == typeid(Persistable::Ptr)) {
            FilePtrArray f = getFileArray(name);
            FilePtrArray::iterator vi;
            for(vi= f.begin(); vi != f.end(); ++vi) {
                out << "FILE:" << (*vi)->getPath();
                if (vi+1 != f.end()) out << ", ";
                out.flush();
            }
        }
        else {
            throw LSST_EXCEPT(pexExcept::LogicErrorException,
                              "Policy: unexpected type held by any");
        }
    }
    catch (NameNotFound&) {
        out << "<null>";
    }

    // out << ends;   // unnecessary but problematic, according to #316
    return out.str();
}

/*
 * print the contents of this policy to an output stream
 */
void Policy::print(ostream& out, const string& label, 
                   const string& indent) const 
{
    list<string> nms;
    names(nms, true);
    if (label.size() > 0) 
        out << indent << label << ":\n";
    for(list<string>::iterator n = nms.begin(); n != nms.end(); ++n) {
        out << indent << "  " << *n << ": " << str(*n, indent+"  ") << endl;
    }
}

/*
 * convert the entire contents of this policy to a string.  This 
 * is mainly intended for debugging purposes.  
 */
string Policy::toString() const {
    ostringstream os;
    print(os);
    return os.str();
}

//@endcond

} // namespace policy
} // namespace pex
} // namespace lsst
