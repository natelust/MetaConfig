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
    : Citizen(typeid(this)), Persistable(), _data(new PropertySet()) 
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
    int have = 0, count = 0;
    if (want == 1) {
        src = _data->propertySetNames(topLevelOnly);
        have = 1;
        check = false;
    }
    else if (want == 7) 
        src = _data->names(topLevelOnly);
    else 
        src = _data->paramNames(topLevelOnly);

    if (!append) names.erase(names.begin(), names.end());

    StringArray::iterator i;
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
    bool check = true;
    std::vector<std::string> src;
    int have = 0, count = 0;
    if (want == 1) {
        src = _data->propertySetNames(topLevelOnly);
        have = 1;
        check = false;
    }
    else if (want == 7) 
        src = _data->names(topLevelOnly);
    else 
        src = _data->paramNames(topLevelOnly);

    if (!append) names.erase(names.begin(), names.end());

    StringArray::iterator i;
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
            throw LSST_EXCEPT(pexExcept::LogicErrorException, string("Policy: illegal type held by PropertySet: ") + tp.name());
        }
    } catch (pexExcept::NotFoundException&) {
        return UNDEF;
    }
}

Policy::PolicyPtrArray Policy::getPolicyArray(const std::string& name) const {
    PolicyPtrArray out;
    std::vector<PropertySet::Ptr> psa = _getPropSetList(name);
    std::vector<PropertySet::Ptr>::const_iterator i;
    for(i=psa.begin(); i != psa.end(); ++i) 
        out.push_back(Ptr(new Policy(*i)));
    return out;
}

Policy::FilePtr Policy::getFile(const std::string& name) const {
    FilePtr out = 
        boost::dynamic_pointer_cast<PolicyFile>(_data->getAsPersistablePtr(name));
    if (! out.get()) 
        throw LSST_EXCEPT(TypeError, name, std::string(typeName[FILE]));
    return out;
}

Policy::FilePtrArray Policy::getFileArray(const std::string& name) const
{
    FilePtrArray out;
    vector<Persistable::Ptr> pfa = _getPersistList(name);
    vector<Persistable::Ptr>::const_iterator i;
    FilePtr fp;
    for(i = pfa.begin(); i != pfa.end(); ++i) {
        fp = boost::dynamic_pointer_cast<PolicyFile>(*i);
        if (! fp.get())
            throw LSST_EXCEPT(TypeError, name, string(typeName[FILE]));
        out.push_back(fp);
    }

    return out;
}

void Policy::set(const std::string& name, const FilePtr& value) {
    _data->set(name, boost::dynamic_pointer_cast<Persistable>(value));
}

void Policy::add(const std::string& name, const FilePtr& value) {
    _data->add(name, boost::dynamic_pointer_cast<Persistable>(value));
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

            pols.push_back(policy);
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
    // TODO: alter repos?; record name of source file? 
    policyNames(names, true);
    for(list<string>::iterator it=names.begin(); it != names.end(); it++) {
        PolicyPtrArray policies = getPolicyArray(*it);

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
        else if (tp == typeid(std::string)) {
            StringArray s = _data->getArray<std::string>(name);
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
        else if (tp == typeid(FilePtr)) {
            FilePtrArray f = getFileArray(name);
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

