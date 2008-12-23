// -*- lsst-c++ -*-
/**
 * @class Policy
 * 
 * @brief an object for holding configuration data
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_POLICY_H
#define LSST_PEX_POLICY_POLICY_H

#include <string>
#include <vector>
#include <list>
#include <map>

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/exceptions.h"
#include <boost/shared_ptr.hpp>
#include <boost/filesystem/path.hpp>
#include <boost/filesystem/operations.hpp>

/*
#define FIX_ANY_POINTER_RTTI
*/
#ifdef FIX_ANY_POINTER_RTTI
#include "lsst/pex/policy/any.h"
#define ANYTYPE lsst::pex::policy::anyfix::any
#define ANYCAST lsst::pex::policy::anyfix::any_cast
#define BADANYCAST lsst::pex::policy::anyfix::bad_any_cast
#else
#include <boost/any.hpp>
#define ANYTYPE boost::any
#define ANYCAST boost::any_cast
#define BADANYCAST boost::bad_any_cast
#endif

namespace lsst {
namespace pex {
namespace policy {

namespace pexExcept = lsst::pex::exceptions;

// forward declaration
class PolicySource;
class PolicyFile;
class Dictionary;

using namespace std;
namespace fs = boost::filesystem;
using boost::shared_ptr;
using lsst::daf::base::Citizen;

/**
 * @brief  a container for holding hierarchical configuration data in memory.
 *
 * A policy is a set of named parameters that can be used to configure
 * the internal data and behavior of an object within an application.  An
 * important feature Policy objects is that the parameters can be
 * loaded in from a file.  Thus, it allows applications fine-grained
 * control of objects even if much of the configuration parameters they
 * provide are normally set to defaults and otherwise do not change.
 *
 * The Policy interface allows an application to pull out parameter values 
 * by name.  Typically, the application "knows" the names it needs from a 
 * Policy to configure itself--that is, these names and the use of their 
 * values are hard-coded into the application.  The application simply calls 
 * one of the get methods to retrieve a typed value for the parameter.  
 * (Nevertheless, if necessary, the parameter names contained in a policy 
 * can be retrieved via the \c names() member function.)
 * 
 * Policy parameters values are restricted to a limited set of types to ensure 
 * simple, well-defined ASCII text serialization format.  These types are 
 * In particular, a Policy parameter can be one of:
 *  - integer (int not long)
 *  - double
 *  - string
 *  - boolean (bool)
 *  - Policy
 *  - arrays of any of the above
 *
 * As implied by the inclusion of Policy as a value type, a Policy can be 
 * hierarchical (like a DataProperty).  Values deep within the hierarchy 
 * can be retrieved via a hiearchical name.  Such a name is made up of 
 * name fields delimited by dots (.) where each name field represents a 
 * level of the hierarchy.  The first field represents the top level of 
 * the hierarchy.  If a given name does not resolve to value, a NameNotFound
 * exception is thrown.  If one expects a different value type for a name 
 * than what is actually stored, (e.g. one calls \c getInt(name) for a 
 * parameter that is actually a string), a TypeError exception is thrown.
 * 
 * A hierarchical Policy allows an application to configure a whole 
 * hierarchy of objects, even if the object classes (and their 
 * associated policy parameters) were developed by different people.  In
 * particular, if an application that is configuring one of the objects it 
 * uses, it can either pull out the relevent values directly by their 
 * hierarchical names, or if that object supports configuration from a 
 * Policy, it can pull all of the values for the object by retrieving a 
 * Policy (via \c getPolicy(name) ) and passing it to the object.  
 * 
 * It is important to note that parameter names relative the Policy that 
 * contains them.  For example, suppose you have a parameter accessible via 
 * the name "foo.bar.zub".  This implies that the name "foo.bar" will 
 * resolve to a Policy object.  You can retrieve the "zub" parameter from 
 * that "sub-Policy" object by asking for "zub".  
 * 
 * Loading Data From a File
 *
 * Dictionaries
 *
 * 
 */
class Policy : public Citizen {
public:

    typedef boost::shared_ptr<Policy> Ptr;
    typedef boost::shared_ptr<PolicyFile> FilePtr;
    typedef boost::shared_ptr<string> StringPtr;
    typedef vector<bool> BoolArray;
    typedef vector<int> IntArray;
    typedef vector<double> DoubleArray;
    typedef vector<StringPtr> StringPtrArray;
    typedef vector<Ptr> PolicyPtrArray;
    typedef vector<FilePtr> FilePtrArray;

    /**
     * an enumeration for the supported policy types
     */
    enum ValueType {
        UNDEF,
        BOOL,
        INT,
        DOUBLE,
        STRING,
        POLICY,
        FILE
    };

    /**
     * c-string forms for the supported value types.  The ValueType 
     * enum values can be used a indexes into the array to return the 
     * name of the corresping type.  
     */
    static const char * const typeName[];

    /**
     * Create an empty policy
     */
    Policy();

    //@{
    /**
     * Create a Policy from a named file
     */
    Policy(const string& filePath);
    Policy(PolicyFile& filePath);
    //@}

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
    Policy(bool validate, const Dictionary& dict);

    /**
     * copy a Policy.  By default, this copy is shallow, which means that 
     * sub-policy objects are not copied but will be shared.  Thus, any 
     * change made to a sub-policy will be seen by all of its holders. 
     * To create a completely independent Policy, set deep=true.
     */
    Policy(const Policy& pol, bool deep=false);

    //@{
    /**
     * create a Policy from a file.  The caller is responsible for deleteing
     * the returned value.  This is the preferred way to obtain a Policy file 
     * if you don't care to know if the input file is an actual policy 
     * file or a policy dictionary.  If it turns out to be a dictionary 
     * file, the defined defaults will be loaded into the return policy.  
     * @param input       the input file or stream to load data from.
     * @param doIncludes  if true, any references found to external Policy 
     *                      files will be resolved into sub-policy values.  
     *                      The files will be looked for in a directory 
     *                      relative the current directory.
     * @param validate    if true and the input file is a policy dictionary,
     *                      it will be given to the returned policy and 
     *                      used to validate future updates to the Policy.
     */
    static Policy *createPolicy(PolicySource& input, bool doIncludes=true, 
                                bool validate=false);
    static Policy *createPolicy(const string& input, bool doIncludes=true,
                                bool validate=false);
    //@}

    //@{
    /**
     * create a Policy from a file.  The caller is responsible for deleteing
     * the returned value.  This is the preferred way to obtain a Policy file 
     * if you don't care to know if the input file is an actual policy 
     * file or a policy dictionary.  If it turns out to be a dictionary 
     * file, the defined defaults will be loaded into the return policy.  
     * @param input       the input file or stream to load data from.
     * @param repos       a directory to look in for the referenced files.  
     *                      Only when the name of the file to be included is an
     *                      absolute path will this.  
     * @param validate    if true and the input file is a policy dictionary,
     *                      it will be given to the returned policy and 
     *                      used to validate future updates to the Policy.
     */
    static Policy *createPolicy(PolicySource& input, const fs::path& repos, 
                                bool validate=false);
    static Policy *createPolicy(const string& input, const fs::path& repos,
                                bool validate=false);
    //@}

    /**
     * destroy this policy
     */
    virtual ~Policy();

    //@{
    /**
     * load the names of parameters into a given list.  \c names() returns
     * all names, \c paramNames() only returns the names that resolve to
     * non-Policy and non-PolicyFile type parameters, \c policyNames() 
     * only returns the Policy names, and fileNames() only returns PolicyFile
     * names.  
     * 
     * @param names         the list object to be loaded
     * @param topLevelOnly  if true, only parameter names at the top of the 
     *                         hierarchy will be returned; no hierarchical 
     *                         names will be included.
     * @param append        if false, the contents of the given list will 
     *                         be erased before loading the names.  
     * @return int  the number of names added
     */
    int names(list<string>& names, bool topLevelOnly=false, 
              bool append=false) const;
    int paramNames(list<string>& names, bool topLevelOnly=false, 
                   bool append=false) const;
    int policyNames(list<string>& names, bool topLevelOnly=false, 
                    bool append=false) const;
    int fileNames(list<string>& names, bool topLevelOnly=false, 
                  bool append=false) const;
    //@}

    /**
     * return true if it appears that this Policy actually contains dictionary
     * definition data.
     */
    bool isDictionary() {  return exists("definitions");  }

    /**
     * return the number of values currently associated with a given name
     * @param name   the (possibly) hierarchical name of the property of 
     *                  interest.
     */
    size_t valueCount(const string& name) const;

    /**
     * return true if multiple values can be retrieved via the given name.
     * False is returned if the name does not exist.  This is equivalent to
     * (valueCount(name) > 1).
     * @param name   the (possibly) hierarchical name of the property of 
     *                  interest.
     */
    bool isArray(const string& name) const {
        return (valueCount(name) > 1);
    }

    /**
     * return true if a value exists in this policy for the given name. 
     * This is semantically equivalent to (valuecount(name) > 0) (though
     * its implementation is slightly more efficient).
     * @param name   the (possibly) hierarchical name of the property of 
     *                  interest.
     */
    bool exists(const string& name) const;              // inlined below

    /**
     * return true if the value pointed to by the given name is a boolean
     */
    bool isBool(const string& name) const;               // inlined below

    /**
     * return true if the value pointed to by the given name is an integer
     */
    bool isInt(const string& name) const;               // inlined below

    /**
     * return true if the value pointed to by the given name is a double
     */
    bool isDouble(const string& name) const;            // inlined below

    /**
     * return true if the value pointed to by the given name is a string
     */
    bool isString(const string& name) const;            // inlined below

    /**
     * return true if the value pointed to by the given name is a Policy
     */
    bool isPolicy(const string& name) const;            // inlined below

    /**
     * return true if the value pointed to by the given name is a PolicyFile
     */
    bool isFile(const string& name) const;              // inlined below

    /**
     * return the type information for the underlying type associated with
     * a given name.  
     */
    const std::type_info& getTypeInfo(const string& name) const;

    /**
     * return the ValueType enum identifier for the underlying type associated 
     * with a given name.  If a parameter with that name has not been set, 
     * Policy::UNDEF is returned.  
     */
    ValueType getValueType(const string& name) const;

    /**
     * return a string name for the type associated with the parameter of
     * a given name.  If a parameter with that name has not been set, the 
     * returned string will be "undefined".  
     */
    const char *getTypeName(const string& name) const {
        try {  return typeName[getValueType(name)]; }
        catch (NameNotFound&) { return typeName[UNDEF]; }
    }

    //@{
    /**
     * return a "sub-Policy" identified by a given name.  
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a Policy type.  
     */
    const Ptr& getPolicy(const string& name) const;     // inlined below
    Ptr& getPolicy(const string& name);                 // inlined below
    //@}

    //@{
    /**
     * return a PolicyFile (a reference to a file with "sub-Policy" data) 
     * identified by a given name.  
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a Policy type.  
     */
    const FilePtr& getFile(const string& name) const;     // inlined below
    FilePtr& getFile(const string& name);                 // inlined below
    //@}

    //@{
    /**
     * return a boolean value associated with the given name.  If the 
     * underlying value is an array, only the last value added will be 
     * returned.  
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a boolean type.  
     */
    bool getBool(const string& name) const;               // inlined below
    bool getBool(const string& name, bool defval) const {
        try { return getBool(name); }
        catch (NameNotFound&) { return defval; }
    }
    //@}

    //@{
    /**
     * return an integer value associated with the given name.  If the 
     * underlying value is an array, only the last value added will be 
     * returned.  
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             an integer type.  
     */
    int getInt(const string& name) const;               // inlined below
    int getInt(const string& name, int defval) const {
        try { return getInt(name); }
        catch (NameNotFound&) { return defval; }
    }
    //@}

    //@{
    /**
     * return a double value associated with the given name.  If the 
     * underlying value is an array, only the last value added will be 
     * returned.  
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a double type.  
     */
    double getDouble(const string& name) const;        // inlined below
    double getDouble(const string& name, double defval) const {
        try { return getDouble(name); }
        catch (NameNotFound&) { return defval; }
    }
    //@}

    /**
     * return a string value associated with the given name .  If the 
     * underlying value is an array, only the last value added will be 
     * returned.  
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             an integer type.  
     */
    const string& getString(const string& name) const;    // inlined below
    const string& getString(const string& name, const string& defval) const {
        try { return getString(name); }
        catch (NameNotFound&) { return defval; }
    }

    //@{
    /**
     * return an array of Policy pointers associated with the given name.  
     * 
     * Adding an element to the returned array (using push_back()) is 
     * equivalent adding a value with add(const string&, const Policy::Ptr&). 
     * 
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a Policy type.  
     */
    const PolicyPtrArray& getPolicyArray(const string& name) const;  //inlined
    PolicyPtrArray& getPolicyArray(const string& name);              //inlined
    //@}

    //@{
    /**
     * return an array of PolicyFile pointers associated with the given name.  
     * 
     * Adding an element to the returned array (using push_back()) is 
     * equivalent adding a value with 
     * add(const string&, const Policy::FilePtr&). 
     * 
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a Policy type.  
     */
    const FilePtrArray& getFileArray(const string& name) const;   //inlined
    FilePtrArray& getFileArray(const string& name);               //inlined
    //@}

    /**
     * return an array of booleans associated with the given name
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             an boolean type.  
     */
    const BoolArray& getBoolArray(const string& name) const;  // inlined below
    
    /**
     * return an array of integers associated with the given name
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             an integer type.  
     */
    const IntArray& getIntArray(const string& name) const;    // inlined below
    
    /**
     * return an array of doubles associated with the given name
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a double type.  
     */
    const DoubleArray& getDoubleArray(const string& name) const;   // inlined
    
    /**
     * return an array of strings associated with the given name
     * @param name     the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @exception NameNotFound  if no value is associated with the given name.
     * @exception TypeError     if the value associated the given name is not
     *                             a string type.  
     */
    const StringPtrArray& getStringArray(const string& name) const;  //inlined

    //@{
    /**
     * add a value with a given name.  
     * Any previous value set with the same name will be overwritten.  In 
     * particular, if the property previously pointed to an array of values,
     * all those values will be forgotten.
     * Note that \code set(const string&, const string&) \endcode and 
     * \code set(const string&, const char *) \endcode are equivalent.
     * @param name       the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @param value      the value--int, double, string or Policy--to 
     *                    associate with the name.  
     * @exception TypeError  if this Policy is controlled by a Dictionary but 
     *                    the value type does not match the definition 
     *                    associated with the name. 
     */
    void set(const string& name, const Ptr& value);        // inlined below
    void set(const string& name, const FilePtr& value);    // inlined below
    void set(const string& name, bool value);              // inlined below
    void set(const string& name, int value);               // inlined below
    void set(const string& name, double value);            // inlined below
    void set(const string& name, const string& value);     // inlined below
    void set(const string& name, const char *value) {
        set(name, string(value));
    }
    //@}

    //@{
    /**
     * add a value to an array of values with a given name.  
     * If a value was previously set using the set() function, that previous
     * value will be retained as the first value of the array.
     * Note that \code add(const string&, const string&) \endcode and 
     * \code add(const string&, const char *) \endcode are equivalent.
     * @param name       the name of the parameter.  This can be a hierarchical
     *                    name with fields delimited with "."
     * @param value      the value--int, double, string or Policy--to 
     *                    associate with the name.  
     * @exception TypeError  if the existing array of values is not of the 
     *                    requested type, or 
     *                    if this Policy is controlled by a Dictionary but 
     *                    the value type does not match the definition 
     *                    associated with the name. 
     */
    void add(const string& name, const Ptr& value);        // inlined below
    void add(const string& name, const FilePtr& value);    // inlined below
    void add(const string& name, bool value);              // inlined below
    void add(const string& name, int value);               // inlined below
    void add(const string& name, double value);            // inlined below
    void add(const string& name, const string& value);     // inlined below
    void add(const string& name, const char *value) {
        add(name, string(value));
    }
    //@}

    //@{
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
     *                      absolute path will this.  If empty or not provided,
     *                      the directorywill be assumed to be the current one.
     * @param strict      if true, throw an exception if an error occurs 
     *                      while reading and/or parsing the file.  Otherwise,
     *                      an unrecoverable error will result in the failing
     *                      PolicyFile being replaced with an incomplete
     *                      Policy.  
     */
    void loadPolicyFiles(const fs::path& repository, bool strict=false);
    void loadPolicyFiles() { loadPolicyFiles(fs::path()); }
    //@}

    /**
     * return a string representation of the value given by a name.  The
     * string "<null>" is printed if the name does not exist.
     * @param name     the name of the parameter to string-ify
     * @param indent  a string to prepend each line with.  If the string 
     *                 includes embedded newline characters, each line 
     *                 should be preceded by this indent string.
     */
    virtual string str(const string& name, const string& indent="") const;

    /**
     * print the contents of this policy to an output stream.  This 
     * is mainly intended for debugging purposes.  
     * @param out     the output stream to write contents to
     * @param label   a labeling string to lead the listing with.
     * @param indent  a string to prepend each line with.
     */
    virtual void print(ostream& out, const string& label="Policy", 
                       const string& indent="") const;

    /**
     * convert the entire contents of this policy to a string.  This 
     * is mainly intended for debugging purposes.  
     */
    string toString() const;

protected:

    enum Mode { BEST, STRICT, ENSURE };

    /**
     * return the Policy object that holds the property given 
     * by relname, a hierarchical name.  
     * @param mode        the search behavior mode.  If set to STRICT, an 
     *                      NameNotFound is thrown if a Policy is not found for
     *                      the full name.  If set to ENSURE, any missing 
     *                      Policies will be created.  If set to BEST and a 
     *                      Policy is not found, the nearest ancestor will 
     *                      be returned.  
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
     *                    exist (and ensure is false), the closest ancestor 
     *                    Policy.  
     * @exception TypeError if one of the intermediate property names does 
     *                      not resolve to a Policy object.
     * @exception BadNameError  if the given name is not legal.
     */
    virtual Policy& _getPolicyFor(Mode mode, string& relname, 
                                  string& parentname);

    /**
     * return the value associated with a given name.  
     * @exception NameNotFound  if no value is associated with the given name.
     */
    virtual ANYTYPE& _getValue(const string& name);

    template <typename T>
    void _addValue(const string& name, const T& newval, 
                   const string& expectedType, bool override);

    template <class T>
    vector<T>& _getList(const string& name, const string& expectedType) {
        try {
            return ANYCAST<vector<T>&>(_getValue(name));
        } catch (BADANYCAST&) {
            throw LSST_EXCEPT(TypeError, name, expectedType);
        } 
    }        

    template <class T> 
    T& _getScalarValue(const string& name, const string& expectedType) {
        try {
            return _getList<T>(name, expectedType).back();
        } catch (std::out_of_range&) {
            throw LSST_EXCEPT(pexExcept::LogicErrorException, "internal policy data not initialized");
        }
    }

private:
    typedef map<string, ANYTYPE> Lookup;
    Lookup _data;

    int _names(const string& prepend, list<string>& names, 
               bool topLevelOnly=false, bool append=false, int want=3) const;

    static Policy *_createPolicy(PolicySource& input, bool doIncludes,
                                 const fs::path& repos, bool validate);
    static Policy *_createPolicy(const string& input, bool doIncludes,
                                 const fs::path& repos, bool validate);
};

inline ostream& operator<<(ostream& os, const Policy& p) {
    p.print(os);
    return os;
}

inline int Policy::names(list<string>& names, bool topLevelOnly, 
                         bool append) const
{
    return _names("", names, topLevelOnly, append, 7);
}
inline int Policy::paramNames(list<string>& names, bool topLevelOnly, 
                              bool append) const
{
    return _names("", names, topLevelOnly, append, 4);
}
inline int Policy::policyNames(list<string>& names, bool topLevelOnly, 
                               bool append) const
{
    return _names("", names, topLevelOnly, append, 1);
}
inline int Policy::fileNames(list<string>& names, bool topLevelOnly, 
                             bool append) const
{
    return _names("", names, topLevelOnly, append, 2);
}

inline bool Policy::exists(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    try {
        me->_getValue(name);
    }
    catch (NameNotFound&) {
        return false;
    }
    return true;
}

inline bool Policy::isBool(const string& name) const {
    try {
        getBoolArray(name);
        return true;
    }
    catch (...) {
        return false;
    }
}

inline bool Policy::isInt(const string& name) const {
    try {
        getIntArray(name);
        return true;
    }
    catch (...) {
        return false;
    }
}

inline bool Policy::isDouble(const string& name) const {
    try {
        getDoubleArray(name);
        return true;
    }
    catch (...) {
        return false;
    }
}

inline bool Policy::isString(const string& name) const {
    try {
        getStringArray(name);
        return true;
    }
    catch (...) {
        return false;
    }
}

inline bool Policy::isPolicy(const string& name) const {
    try {
        getPolicyArray(name);
        return true;
    }
    catch (...) {
        return false;
    }
}

inline bool Policy::isFile(const string& name) const {
    try {
        getFileArray(name);
        return true;
    }
    catch (...) {
        return false;
    }
}

inline const Policy::Ptr& Policy::getPolicy(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getScalarValue<Ptr>(name, typeName[POLICY]);
}
inline Policy::Ptr& Policy::getPolicy(const string& name) {
    return _getScalarValue<Ptr>(name, typeName[POLICY]);
}

inline const Policy::FilePtr& Policy::getFile(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getScalarValue<FilePtr>(name, typeName[FILE]);
}
inline Policy::FilePtr& Policy::getFile(const string& name) {
    return _getScalarValue<FilePtr>(name, typeName[FILE]);
}

inline bool Policy::getBool(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    try {
        return me->_getList<bool>(name, typeName[BOOL]).back();
    } catch (std::out_of_range&) {
        throw LSST_EXCEPT(pexExcept::LogicErrorException, "internal policy data not initialized");
    }
}

inline int Policy::getInt(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getScalarValue<int>(name, typeName[INT]);
}

inline double Policy::getDouble(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getScalarValue<double>(name, typeName[DOUBLE]);
}

inline const string& Policy::getString(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return *(me->_getScalarValue<StringPtr>(name, typeName[STRING]));
}

inline const Policy::PolicyPtrArray& Policy::getPolicyArray(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getList<Ptr>(name, typeName[POLICY]);
}
inline Policy::PolicyPtrArray& Policy::getPolicyArray(const string& name) {
    return _getList<Ptr>(name, typeName[POLICY]);
}

inline const Policy::FilePtrArray& Policy::getFileArray(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getList<FilePtr>(name, typeName[FILE]);
}
inline Policy::FilePtrArray& Policy::getFileArray(const string& name) {
    return _getList<FilePtr>(name, typeName[FILE]);
}

inline const Policy::BoolArray& Policy::getBoolArray(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getList<bool>(name, typeName[BOOL]);
}

inline const Policy::IntArray& Policy::getIntArray(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getList<int>(name, typeName[INT]);
}

inline const Policy::DoubleArray& Policy::getDoubleArray(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getList<double>(name, typeName[DOUBLE]);
}

inline const Policy::StringPtrArray& Policy::getStringArray(const string& name) const {
    Policy *me = const_cast<Policy*>(this);
    return me->_getList<StringPtr>(name, typeName[STRING]);
}

inline void Policy::set(const string& name, const Policy::Ptr& value) {
    _addValue(name, value, typeName[POLICY], true);
}
inline void Policy::set(const string& name, const Policy::FilePtr& value) {
    _addValue(name, value, typeName[FILE], true);
}
inline void Policy::set(const string& name, bool value) {
    _addValue(name, value, typeName[BOOL], true);
}
inline void Policy::set(const string& name, int value) {
    _addValue(name, value, typeName[INT], true);
}
inline void Policy::set(const string& name, double value) {
    _addValue(name, value, typeName[DOUBLE], true);
}
inline void Policy::set(const string& name, const string& value) {
    StringPtr use(new string(value));
    _addValue(name, use, typeName[STRING], true);
}

inline void Policy::add(const string& name, const Policy::Ptr& value) {
    _addValue(name, value, typeName[POLICY], false);
}
inline void Policy::add(const string& name, const Policy::FilePtr& value) {
    _addValue(name, value, typeName[FILE], false);
}
inline void Policy::add(const string& name, bool value) {
    _addValue(name, value, typeName[BOOL], false);
}
inline void Policy::add(const string& name, int value) {
    _addValue(name, value, typeName[INT], false);
}
inline void Policy::add(const string& name, double value) {
    _addValue(name, value, typeName[DOUBLE], false);
}
inline void Policy::add(const string& name, const string& value) {
    StringPtr use(new string(value));
    _addValue(name, use, typeName[STRING], false);
}

template <typename T>
void Policy::_addValue(const string& name, const T& newval, 
                       const string& expectedType, bool override) 
{
    string fullname = name;
    string policyname;
    Policy& parent = _getPolicyFor(ENSURE, fullname, policyname);

    Lookup::iterator out = parent._data.end();
    if (! override) out = parent._data.find(fullname);

    if (out == parent._data.end()) {

        // create a new property
        parent._data[fullname] = vector<T>(1);

        try {
            vector<T>& prop = 
                ANYCAST<vector<T>&>(parent._data[fullname]);
            prop[0] = newval;
        }
        catch (BADANYCAST& e) {
            // shouldn't happen!
            throw LSST_EXCEPT(pexExcept::LogicErrorException, "Policy: unexpected type held by any");
        }
    }
    else {
        try {
            vector<T>& prop = ANYCAST<vector<T>&>(out->second);
            prop.push_back(newval);
        }
        catch (BADANYCAST&) {
            throw LSST_EXCEPT(TypeError, name, expectedType);
        }
    }
}

inline Policy* Policy::createPolicy(PolicySource& input, bool doIncludes, 
                                    bool validate) 
{
    return _createPolicy(input, doIncludes, fs::path(), validate);
} 

inline Policy* Policy::createPolicy(const string& input, bool doIncludes, 
                                    bool validate) 
{
    return _createPolicy(input, doIncludes, fs::path(), validate);
} 

inline Policy* Policy::createPolicy(PolicySource& input, 
                                    const fs::path& repository, bool validate) 
{
    return _createPolicy(input, true, repository, validate);
}

inline Policy* Policy::createPolicy(const string& input, 
                                    const fs::path& repository, bool validate) 
{
    return _createPolicy(input, true, repository, validate);
}

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_POLICY_H
