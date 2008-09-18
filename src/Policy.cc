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

/*
#define EXEC_TRACE  20
static void execTrace( string s, int level = EXEC_TRACE ){
    lsst::pex::utils::Trace( "pex.policy.Policy", level, s );
}
*/

namespace lsst {
namespace pex {
namespace policy {

const char * const Policy::typeName[] = {
    "undefined",
    "bool",
    "int",
    "double",
    "string",
    "Policy",
    "PolicyFile"
};

/**
 * Create an empty policy
 */
Policy::Policy() : Citizen(typeid(this)), _data() { }

/**
 * Create policy
 */
Policy::Policy(PolicyFile& file) : Citizen(typeid(this)), _data() { 
    file.load(*this);
}

/**
 * Create a Policy from a named file
 */
Policy::Policy(const string& filePath) : Citizen(typeid(this)), _data() {
    PolicyFile file(filePath);
    file.load(*this);
}

/**
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
    : Citizen(typeid(this)), _data() 
{ 
    list<string> names;
    dict.definedNames(names);

    std::auto_ptr<Definition> def;
    for(list<string>::iterator it = names.begin(); it != names.end(); ++it) {
        def.reset(dict.makeDef(*it));
        def->setDefaultIn(*this);
    }
}

/**
 * copy a Policy.  Sub-policy objects will be shared.  
 */
Policy::Policy(const Policy& pol, bool deep) 
    : Citizen(typeid(this)), _data(pol._data) 
{
    // copy Policy objects
    if (deep) {
        Lookup::iterator i;
        PolicyPtrArray *p = 0;
        Ptr policyp;
        for(i = _data.begin(); i != _data.end(); ++i) {
            if (p = ANYCAST<PolicyPtrArray>(&(i->second))) {
                PolicyPtrArray::iterator pi;
                for(pi = p->begin(); pi != p->end(); ++pi) {
                    policyp = *pi;
                    *pi = Ptr(new Policy(*policyp, true));
                }
            }
        }
    }
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

/**
 * Create an empty policy
 */
Policy::~Policy() { }

/**
 * load the names of parameters into a given list.  \c names() returns
 * all names, \c paramNames() only returns the names that resolve to
 * non-Policy type parameters, and \c policyNames() only returns the 
 * Policy names. 
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
int Policy::_names(const string& prepend, list<string>& names, 
                   bool topLevelOnly, bool append, int want) const
{
    if (!append) names.erase(names.begin(), names.end());

    string pre((prepend.size() > 0) ? prepend + string(".") : prepend);
    int count = 0;

    Policy *me = const_cast<Policy*>(this);

    Lookup::iterator i;
    int have;
    PolicyPtrArray *p;
    FilePtrArray *f;
    for(i = me->_data.begin(); i != me->_data.end(); ++i) {
        p = ANYCAST<PolicyPtrArray>(&(i->second));
        if (p) {
            have = 1;
        }
        else {
            f = ANYCAST<FilePtrArray>(&(i->second));
            have = (f) ? 2 : 4;
        }
        if ((have&want) > 0) {
            names.push_back(pre + i->first);
            count++;
        }
        if (! topLevelOnly && p) {
            count += p->back()->_names(pre+i->first, names, topLevelOnly, 
                                       true, want);
        }
    }

    return count;
}


/**
 * return the Policy object that holds the property given 
 * by relname, a hierarchical name.  
 * @param mode        the search behavior mode.  If set to STRICT, an 
 *                      NameNotFound is thrown if a Policy is not found for
 *                      the full name.  If set to ENSURE, any missing Policies
 *                      will be created.  If set to BEST and a Policy is not
 *                      found, the nearest ancestor will be returned.  
 * @param relname     (input/output) the hierarchical name of the 
 *                      property of interest relative to this Policy.  
 *                      Upon return, this parameter will be updated to the 
 *                      name of the property relative to the returned 
 *                      Policy object.
 * @param parentname  (input/output) the property name for this Policy.  
 *                      This is used if a TypeError is encountered to 
 *                      provide some context to the error message.  Upon 
 *                      return, this this parameter will be updated to 
 *                      the name of the returned Policy relative to the
 *                      original context.
 * @return Policy   the Policy object containing the property pointed to 
 *                    by relname, or if the requested Policy does not 
 *                    exist (and mode is BEST), the closest ancestor 
 *                    Policy.  
 * @exception TypeError if one of the intermediate property names does 
 *                      not resolve to a Policy object.
 * @exception BadNameError  if the given name is not legal.
 */
Policy& Policy::_getPolicyFor(Mode mode, string& relname, 
                              string& parentname) 
{
    // find the last dot; everything prior to it represents a Policy node
    size_t dot = relname.rfind('.');
    if (dot == string::npos) 
        // not a hierarchical name; we're done
        return *this;

    if (dot == 0 || dot >= relname.size()-1)
        // name begins or ends with a dot--not nice
        throw BadNameError(relname);

    dot = relname.find('.');
    string head = (dot == string::npos) ? relname : relname.substr(0,dot);

    Lookup::iterator childptr = _data.find(head);
    if (childptr != _data.end()) {
        if (dot >= 0) relname.erase(0, dot+1);
        if (parentname.size() > 0) parentname.append(1, '.');
        parentname.append(head);

        try {
            PolicyPtrArray& child = 
                ANYCAST<PolicyPtrArray&>(childptr->second);

            // recurse: descend into child policy
            return child.back()->_getPolicyFor(mode, relname,parentname);
        }
        catch (BADANYCAST&) {
            throw new TypeError(parentname, typeName[POLICY]);
        }
    }
    else if (mode == ENSURE) {
        if (dot >= 0) relname.erase(0, dot+1);
        if (parentname.size() > 0) parentname.append(1, '.');
        parentname.append(head);

        // create the child policy
        _data[head] = PolicyPtrArray(1);

        try {
            PolicyPtrArray& child = 
                ANYCAST<PolicyPtrArray&>(_data[head]);
            child[0] = shared_ptr<Policy>(new Policy());

            // recurse: create descendent policies
            return child[0]->_getPolicyFor(mode, relname, parentname);
        }
        catch (BADANYCAST& e) {
            // shouldn't happen!
            throw logic_error("Policy: unexpected type held by any");
        }
    }
    else if (mode == STRICT) {
        if (dot >= 0) relname.erase(0, dot+1);
        if (parentname.size() > 0) parentname.append(1, '.');
        parentname.append(head);

        throw NameNotFound(parentname);
    }

    // can't/shouldn't recurse further, so stop here.
    return *this;
}

/**
 * return the value associated with a given name.  
 * @exception NameNotFound  if no value is associated with the given name.
 */
ANYTYPE& Policy::_getValue(const string& name) {
    string fullname = name;
    string policyname;
    Policy& parent = _getPolicyFor(STRICT, fullname, policyname);

    Lookup::iterator childptr = parent._data.find(fullname);
    if (childptr == parent._data.end()) {
        if (policyname.size() > 0) policyname.append(1,'.');
        policyname.append(fullname);
        throw NameNotFound(policyname);
    }
    return childptr->second;
}

/**
 * return the number of values currently associated with a given name.  Zero
 * is returned if the value has not been set.  
 */
size_t Policy::valueCount(const string& name) const {
    size_t out = 0;
    Policy *me = const_cast<Policy*>(this);

    try {
        ANYTYPE& val = me->_getValue(name);

        BoolArray *b;  
        IntArray *i;  
        DoubleArray *d;   
        StringPtrArray *s;
        PolicyPtrArray *p;
    
        if (b = ANYCAST<BoolArray>(&val)) {
            out = b->size();
        }
        else if (i = ANYCAST<IntArray>(&val)) {
            out = i->size();
        }
        else if (d = ANYCAST<DoubleArray>(&val)) {
            out = d->size();
        }
        else if (s = ANYCAST<StringPtrArray>(&val)) {
            out = s->size();
        }
        else if (p = ANYCAST<PolicyPtrArray>(&val)) {
            out = p->size();
        }
        else {
            throw logic_error("Policy: unexpected type held by any");
        }
    }
    catch (NameNotFound&) { }

    return out;
}

/**
 * return the type information for the underlying type associated with
 * a given name
 */
const std::type_info& Policy::getTypeInfo(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    ANYTYPE& val = me->_getValue(name);

    BoolArray *b;  
    IntArray *i;  
    DoubleArray *d;   
    StringPtrArray *s;
    PolicyPtrArray *p;
    FilePtrArray *f;
    
    if (b = ANYCAST<BoolArray>(&val)) {
        bool v = b->back();
        return typeid(v);
    }
    else if (i = ANYCAST<IntArray>(&val)) {
        return typeid(i->back());
    }
    else if (d = ANYCAST<DoubleArray>(&val)) {
        return typeid(d->back());
    }
    else if (s = ANYCAST<StringPtrArray>(&val)) {
        return typeid(*(s->back()));
    }
    else if (p = ANYCAST<PolicyPtrArray>(&val)) {
        return typeid(*(p->back()));
    }
    else if (f = ANYCAST<FilePtrArray>(&val)) {
        return typeid(*(f->back()));
    }
    else {
        throw logic_error("Policy: unexpected type held by any");
    }
}

/**
 * return the type information for the underlying type associated with
 * a given name.  
 */
Policy::ValueType Policy::getValueType(const string& name) const {
    try {
        Policy *me = const_cast<Policy*>(this);
        ANYTYPE& val = me->_getValue(name);

        BoolArray *b;  
        IntArray *i;  
        DoubleArray *d;   
        StringPtrArray *s;
        PolicyPtrArray *p;
        FilePtrArray *f;
    
        if (b = ANYCAST<BoolArray>(&val)) {
            return BOOL;
        }
        else if (i = ANYCAST<IntArray>(&val)) {
            return INT;
        }
        else if (d = ANYCAST<DoubleArray>(&val)) {
            return DOUBLE;
        }
        else if (s = ANYCAST<StringPtrArray>(&val)) {
            return STRING;
        }
        else if (p = ANYCAST<PolicyPtrArray>(&val)) {
            return POLICY;
        }
        else if (f = ANYCAST<FilePtrArray>(&val)) {
            return FILE;
        }
        else {
            throw logic_error("Policy: unexpected type held by any");
        }
    } catch (NameNotFound&) {
        return UNDEF;
    }
}

/**
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
            catch (IOError& e) {
                if (strict) {
                    // TODO: use LSST exceptions
                    throw e;
                }
                // TODO: log a problem
            }
            catch (ParserError& e) {
                if (strict) {
                    // TODO: use LSST exceptions
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


/**
 * return a string representation of the value given by a name.  The
 * string "<null>" is printed if the name does not exist.
 */
string Policy::str(const string& name, const string& indent) const {
    Policy *me = const_cast<Policy*>(this);
    ostringstream out;

    try {
        ANYTYPE& val = me->_getValue(name);

        BoolArray *b;  
        IntArray *i;  
        DoubleArray *d;   
        StringPtrArray *s;
        PolicyPtrArray *p;
        FilePtrArray *f;
    
        if (b = ANYCAST<BoolArray>(&val)) {
            BoolArray::iterator vi;
            for(vi=b->begin(); vi != b->end(); ++vi) {
                out << *vi;
                if (vi+1 != b->end()) out << ", ";
            }
        }
        else if (i = ANYCAST<IntArray>(&val)) {
            IntArray::iterator vi;
            for(vi=i->begin(); vi != i->end(); ++vi) {
                out << *vi;
                if (vi+1 != i->end()) out << ", ";
            }
        }
        else if (d = ANYCAST<DoubleArray>(&val)) {
            DoubleArray::iterator vi;
            for(vi=d->begin(); vi != d->end(); ++vi) {
                out << *vi;
                if (vi+1 != d->end()) out << ", ";
            }
        }
        else if (s = ANYCAST<StringPtrArray>(&val)) {
            StringPtrArray::iterator vi;
            for(vi= s->begin(); vi != s->end(); ++vi) {
                out << '"' << **vi << '"';
                if (vi+1 != s->end()) out << ", ";
            }
        }
        else if (p = ANYCAST<PolicyPtrArray>(&val)) {
            PolicyPtrArray::iterator vi;
            for(vi= p->begin(); vi != p->end(); ++vi) {
                out << "{\n";
                (*vi)->print(out, "", indent+"  ");
                out << indent << "}";
                if (vi+1 != p->end()) out << ", ";
                out.flush();
            }
        }
        else if (f = ANYCAST<FilePtrArray>(&val)) {
            FilePtrArray::iterator vi;
            for(vi= f->begin(); vi != f->end(); ++vi) {
                out << "FILE:" << (*vi)->getPath();
                if (vi+1 != f->end()) out << ", ";
                out.flush();
            }
        }
        else {
            throw logic_error("Policy: unexpected type held by any");
        }
    }
    catch (NameNotFound&) {
        out << "<null>";
    }

    out << ends;
    return out.str();
}

/**
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

/**
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
