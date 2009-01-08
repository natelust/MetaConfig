/**
 * \file Policy.cc
 */
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/PolicySource.h"
#include "lsst/pex/policy/Dictionary.h"
#include "lsst/pex/policy/parserexceptions.h"
/*
#include "lsst/pex/logging/Trace.h"
*/

#include <boost/filesystem/path.hpp>

#include <stdexcept>
#include <string>
#include <sstream>

using namespace std;
namespace fs = boost::filesystem;
namespace pexExcept = lsst::pex::exceptions;
namespace dafBase = lsst::daf::base;

namespace lsst {
namespace pex {
namespace policy {

using dafBase::PropertySet;

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
Policy::Policy() : Citizen(typeid(this)), _data(new PropertySet()) { }

/*
 * Create policy
 */
Policy::Policy(const PolicyFile& file) 
    : Citizen(typeid(this)), _data(new PropertySet()) 
{ 
    file.load(*this);
}

/*
 * Create a Policy from a named file
 */
Policy::Policy(const string& filePath) 
    : Citizen(typeid(this)), _data(new PropertySet()) 
{
    PolicyFile file(filePath);
    file.load(*this);
}

/*
 * Create a default Policy from a Dictionary.  
 *
 * Note:  validation is not implemented yet.
 *
 * @param validate  if true, a (shallow) copy of the Dictionary will be 
 *                    held onto by this Policy and used to validate 
 *                    future updates.  
 * @param dict      the Dictionary file load defaults from
 */
Policy::Policy(bool validate, const Dictionary& dict) 
    : Citizen(typeid(this)), _data(new PropertySet()) 
{ 
    list<string> names;
    dict.definedNames(names);

    std::auto_ptr<Definition> def;
    for(list<string>::iterator it = names.begin(); it != names.end(); ++it) {
        def.reset(dict.makeDef(*it));
        def->setDefaultIn(*this);
    }
}

/*
 * copy a Policy.  Sub-policy objects will not be shared.  
 */
Policy::Policy(const Policy& pol) 
    : Citizen(typeid(this)), _data() 
{
    _data = pol.getPropertySetPtr()->deepCopy();
}

/*
 * copy a Policy.  Sub-policy objects will be shared unless deep is true
 */
Policy::Policy(Policy& pol, bool deep) 
    : Citizen(typeid(this)), _data() 
{
    if (deep)
        _data = pol.getPropertySetPtr()->deepCopy();
    else
        _data = pol.getPropertySetPtr();
}

Policy* Policy::_createPolicy(PolicySource& source, bool doIncludes, 
                              const fs::path& repository, bool validate) 
{
    auto_ptr<Policy> pol(new Policy());
    source.load(*pol);

    if (pol->exists("definitions")) {
        Dictionary d(*pol);
        pol.reset(new Policy(validate, d));
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
    bool check = true;
    std::vector<std::string> src;
    if (want == 1) {
        src = _data->propertySetNames(topLevelOnly);
        have = 1;
        check = false;
    }
    else if (want == 7) 
        src = _data->names(topLevelOnly);
    else 
        src = _data->parameterNames(topLevelOnly);

    if (!append) names.erase(names.begin(), names.end());

    StringArray::iterator i;
    int have;
    for(i = src.begin(); i != src.end(); ++i) {
        if (check) {
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


template <typename T>
bool Policy::_getScalarValue(const string& name) const {
    try {
        return _data->get<T>(name);
    } catch (pexExcept::NotFoundException&) {
        throw LSST_EXCEPT(NameNotFound, name);
    } catch (BADANYCAST&) {
        throw LSST_EXCEPT(TypeError, name, string(getTypeName(name)));
    }
}

template <class T>
std::vector<T> Policy::_getList(const string& name) {
    try {
        return _data->getArray<T>(name);
    } catch (pexExcept::NotFoundException&) {
        throw LSST_EXCEPT(NameNotFound, name);
    } catch (BADANYCAST&) {
        throw LSST_EXCEPT(TypeError, name, string(getTypeName(name)));
    } 
}        

/*
 * return the type information for the underlying type associated with
 * a given name.  
 */
Policy::ValueType Policy::getValueType(const string& name) const {
    try {
        std::type_info& tp = _data->typeOf(name);
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
        else if (tp == typeid(FilePtr)) {
            return FILE;
        }
        else {
            throw LSST_EXCEPT(pexExcept::LogicErrorException, string("Policy: illegal type held by PropertySet: ") + tp.name());
        }
    } catch (NameNotFound&) {
        return UNDEF;
    }
}

Policy::ConstPolicyPtrArray Policy::getPolicyArray(const std::string& name) const {
    ConstPolicyPtrArray out;
    PolicyPtrArray src = getPolicyArray(name);
    PolicyPtrArray::const_iterator i;
    for(i=_data->begin(); i != _data->end(); ++i) 
        out.push_back(*i);
    return out;
}

Policy::ConstStringPtrArray Policy::getStringArray(const std::string& name) const {
    ConstStringPtrArray out;
    StringPtrArray src = getStringArray(name);
    StringPtrArray::const_iterator i;
    for(i=_data->begin(); i != _data->end(); ++i) 
        out.push_back(*i);
    return out;
}

Policy::StringArray getStrings(const std::string& name) const {
    StringArray out;
    StringPtrArray src = _data->getArray<StringPtr>(name);
    for(StringArray::iterator i = src.begin(); i != src.end(); ++i) 
        out.push_back(*(i->get()));
    return out;
}


/*
 * recursively replace all PolicyFile values with the contents of the 
 * files they refer to.  The type of a parameter containing a PolicyFile
 * will consequently change to a Policy upon successful completion.  If
 * the value is an array, all PolicyFiles in the array must load without
 * error before the PolicyFile values themselves are erased (unless 
 * strict=true; see arguments below).  
 *
 * @param repository  a directory to look in for the referenced files.  
 *                      Only when the name of the file to be included is an
 *                      absolute path will this.  If empty, the directory
 *                      will be assumed to be the current one.  
 * @param strict      if true, throw an exception if an error occurs 
 *                      while reading and/or parsing the file.  Otherwise,
 *                      an unrecoverable error will result in the failing
 *                      PolicyFile being replaced with an incomplete
 *                      Policy.  
 */
void Policy::loadPolicyFiles(const fs::path& repository, bool strict) {

    fs::path repos = repository;
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

            Ptr policy(new Policy());
            PolicyFile pf(path.file_string());

            try {
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

            pols.push_back(policy->getPropertySetPtr());
        }

        if (pols.size() > 0) {   // shouldn't actually be zero
            PolicyPtrArray::iterator pi = pols.begin();
            set(*it, *pi);
            while(++pi != pols.end()) {
                add(*it, *pi);
            }
        }
    }

    // Now iterate again to recurse into sub-Policy values
    policyNames(names, true);
    for(list<string>::iterator it=names.begin(); it != names.end(); it++) {
        PolicyPtrArray& policies = getPolicyArray(*it);

        // iterate through the Policies in this array
        PolicyPtrArray::iterator pi;
        for(pi = policies.begin(); pi != policies.end(); pi++) {
            (*pi)->loadPolicyFiles(repos, strict);
        }
    }
}


/*
 * return a string representation of the value given by a name.  The
 * string "<null>" is printed if the name does not exist.
 */
string Policy::str(const string& name, const string& indent) const {
    Policy *me = const_cast<Policy*>(this);
    ostringstream out;

    try {
        std::type_info& tp = _data->typeOf(name);
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
        else if (tp == typeid(StringPtr)) {
            StringPtrArray s = _data->getArray<StringPtr>(name);
            StringPtrArray::iterator vi;
            for(vi= s.begin(); vi != s.end(); ++vi) {
                out << '"' << **vi << '"';
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
        else if (tp == typeid(FilePtr)) {
            FilePtrArray f = _data->getArray<StringPtr>(name);
            FilePtrArray::iterator vi;
            for(vi= f.begin(); vi != f.end(); ++vi) {
                out << "FILE:" << (*vi)->getPath();
                if (vi+1 != f.end()) out << ", ";
                out.flush();
            }
        }
        else {
            throw LSST_EXCEPT(pexExcept::LogicErrorException, "Policy: unexpected type held by any");
        }
    }
    catch (NameNotFound&) {
        out << "<null>";
    }

    out << ends;
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



} // namespace policy
} // namespace pex
} // namespace lsst
