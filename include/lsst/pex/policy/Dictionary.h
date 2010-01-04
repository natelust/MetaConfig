// -*- lsst-c++ -*-
/**
 * @file Dictionary.h
 * @ingroup pex
 * @brief definition of the Dictionary class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_DICTIONARY_H
#define LSST_PEX_POLICY_DICTIONARY_H

#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/exceptions.h"
#include <boost/regex.hpp>
#include <sstream>

namespace pexExcept = lsst::pex::exceptions;
namespace dafBase = lsst::daf::base;

namespace lsst {
namespace pex {
namespace policy {

class PolicySource;
class PolicyFile;

/**
 * @brief an exception for holding errors detected while validating a Policy.
 *
 * The errors captured by this exception indicate that the value of one or
 * more Policy parameters do not conform with the definition given in a
 * Policy Dictionary.  Each error is represented by an enumeration constant
 * which maps to an error message.  
 */
class ValidationError : public pexExcept::LogicErrorException {
public:

    /**
     * the possible validation errors that could be encountered.  Theses
     * are intended to be bit-wise compared with the error value held in
     * a ValidationError.  
     */
    enum ErrorType {
        /** no error found */
        OK = 0,

        /** value has the incorrect type */
        WRONG_TYPE = 1,

        /** a required parameter was not specified */
        MISSING_REQUIRED = 2,

        /** a scalar was found where an array is required */
        NOT_AN_ARRAY = 4,

        /** array does not have enough values */
        ARRAY_TOO_SHORT = 8,

        /** 
         * parameter contains too few array values.  This bit-wise ORs 
         * MISSING_REQUIRED, ARRAY_TOO_SHORT, and NOT_AN_ARRAY
         */
        TOO_FEW_VALUES = 14, 

        /** parameter contains too many array values */
        TOO_MANY_VALUES = 16,

        /** 
         * array has an incorrect number of values.   This bit-wise ORs 
         * MISSING_REQUIRED, NOT_AN_ARRAY, ARRAY_TOO_SHORT, and 
         * TOO_MANY_VALUES.
         */
        WRONG_OCCURRENCE_COUNT = 30,

        /** the value is not one of the explicit values allowed. */
        VALUE_DISALLOWED = 32,

        /** 
         * the value is out of range, either below the minimum or above the 
         * maximum.
         */
        VALUE_OUT_OF_RANGE = 64,

        /**
         * the value falls outside of the supported domain of values.
         * This bit-wise ORs VALUE_DISALLOWED and VALUE_OUT_OF_RANGE.
         */
        BAD_VALUE = 96,

        /** The value's name is not recognized. */
        UNKNOWN_NAME = 128,

        /** The value's dictionary definition is malformed. */
        BAD_DEFINITION = 256,

        /** Policy sub-files have not been loaded -- need to call loadPolicyFiles(). */
        NOT_LOADED = 512,

        /** an unknown error.  This is the highest error number. */
        UNKNOWN_ERROR = 1024
    };

    static const std::string& getErrorMessageFor(ErrorType err) {
        if (_errmsgs.size() == 0) _loadMessages();
        MsgLookup::iterator it = _errmsgs.find(err);
        if (it != _errmsgs.end())
            return it->second;
        else {
            // if it's a compound error that we don't have a pre-written
            // description of, then compile a description
	    static std::string result; // avoid memory issues
	    // TODO: at cost of concurrence?
            std::ostringstream os;
	    bool first = true;
            for (std::map<int,std::string>::const_iterator j = _errmsgs.begin();
                 j != _errmsgs.end(); ++j) {
                if (j->first != OK && (err & j->first) == j->first) {
                    os << (first ? "" : "; ") << j->second;
		    first = false;
		}
	    }
	    result = os.str();
            return result;
	}
    }

    static const std::string EMPTY;

    // TODO: create way to change message when an error actually occurs
    /**
     * create an empty ValidationError message
     */
    ValidationError(char const* ex_file, int ex_line, char const* ex_func) 
	: pexExcept::LogicErrorException(ex_file, ex_line, ex_func,
					 "Policy has unknown validation errors"), 
       _errors() 
    { }

    virtual pexExcept::Exception *clone() const;
    virtual char const *getType(void) const throw();

    /**
     * Copy constructor.
     */
    ValidationError(const ValidationError& that) 
	: pexExcept::LogicErrorException(that), _errors(that._errors) 
    { }

    ValidationError& operator=(const ValidationError& that) {
	LogicErrorException::operator=(that);
	_errors = that._errors;
	return *this;
    }

// Swig is having trouble with this macro
//    ValidationError(POL_EARGS_TYPED) 
//       : pexExcept::LogicErrorException(POL_EARGS_UNTYPED, 
//                                        "policy has unknown validation errors"), 
//       _errors() 
//    { }

    /**
     * destroy the exception
     */
    virtual ~ValidationError() throw();

    /**
     * return the number of named parameters containing validation problems
     */
    int getParamCount() const { return _errors.size(); }

    /**
     * load the names of the parameters that had problems into the given 
     * list
     */
    void paramNames(std::list<std::string>& names) const {
        ParamLookup::const_iterator it;
        for(it = _errors.begin(); it != _errors.end(); it++)
            names.push_back(it->first);
    }

    /**
     * The names of the parameters that had problems.
     * Same functionality as paramNames(), but more SWIGable.
     */
    std::vector<std::string> getParamNames() const;

    /**
     * get the errors encountered for the given parameter name
     */
    int getErrors(const std::string& name) const {
        ParamLookup::const_iterator it = _errors.find(name);
        if (it != _errors.end()) 
            return it->second;
        else
            return 0;
    }

    /**
     * add an error code to this exception
     */
    void addError(const std::string& name, ErrorType e) {
        _errors[name] |= e;
    }

    /**
     * get all the errors collectively encountered for all parameters 
     * examined.  
     */
    int getErrors() const {
        int out = 0;
        ParamLookup::const_iterator it;
        for(it = _errors.begin(); it != _errors.end(); it++)
            out |= it->second;
        return out;
    }

    /**
     * Describe this validation error in human-readable terms.  Each parameter
     * that has an error is given one line, delimited by a newline character.
     * @param prefix appended to beginning of each line of output
     */
    std::string describe(std::string prefix = "") const;

    /**
     * Override lsst::pex::exceptions::Exception::what()
     */
    virtual char const* what(void) const throw();

protected:
    typedef std::map<int, std::string> MsgLookup;
    typedef std::map<std::string, int> ParamLookup;

    static MsgLookup _errmsgs;

    static void _loadMessages();

    ParamLookup _errors;
};

/**
 * @brief a convenience container for a single parameter definition from a
 * dictionary.
 */
class Definition : public dafBase::Citizen {
public:

    /**
     * create an empty definition
     * @param paramName   the name of the parameter being defined.
     */
    Definition(const std::string& paramName = "")
        : dafBase::Citizen(typeid(*this)), _type(Policy::UNDETERMINED), 
	_name(paramName), _policy(), _wildcard(false)
    {
        _policy.reset(new Policy());
    }

    /**
     * create a definition from a data contained in a Policy
     * @param paramName   the name of the parameter being defined.
     * @param defn        the policy containing the definition data
     */
    Definition(const std::string& paramName, const Policy::Ptr& defn) 
        : dafBase::Citizen(typeid(*this)), _type(Policy::UNDETERMINED), 
          _name(paramName), _policy(defn), _wildcard(false)
    { }

    /**
     * create a definition from a data contained in a Policy
     * @param defn        the policy containing the definition data
     */
    Definition(const Policy::Ptr& defn) 
        : dafBase::Citizen(typeid(*this)), _type(Policy::UNDETERMINED), 
          _name(), _policy(defn), _wildcard(false)
    { }

    /**
     * create a copy of a definition
     */
    Definition(const Definition& that) 
        : dafBase::Citizen(typeid(*this)), _type(Policy::UNDETERMINED), 
          _name(that._name), _policy(that._policy), _wildcard(false)
    { }

    /**
     * reset this definition to another one
     */
    Definition& operator=(const Definition& that) {
        _type = Policy::UNDETERMINED;
        _name = that._name;
        _policy = that._policy;
	_prefix = that._prefix;
	_wildcard = that._wildcard;
        return *this;
    }

    /**
     * reset this definition's data to another one.  The name of the parameter
     * will remain the same.
     */
    Definition& operator=(const Policy::Ptr& defdata) { 
        setData(defdata);
        return *this;
    }

    virtual ~Definition();

    /**
     * return the name of the parameter
     */
    const std::string& getName() const { return _name; }

    //@{
    /**
     * The prefix to this definition's parameter name -- relevant to validation
     * of sub-policies.
     */
    const std::string getPrefix() const { return _prefix; }
    void setPrefix(const std::string& prefix) { _prefix = prefix; }
    //@}

    //@{
    /**
     * Was this definition created from a wildcard "childDefinition" definition
     * in a Dictionary?  Default false.
     */
    const bool isChildDefinition() const { return _wildcard; }
    void setChildDefinition(bool wildcard) { _wildcard = wildcard; }
    const bool isWildcard() const { return _wildcard; }
    void setWildcard(bool wildcard) { _wildcard = wildcard; }
    //@}

    /**
     * set the name of the parameter.  Note that this will not effect the 
     * name in Dictionary that this Definition came from.  
     */
    void setName(const std::string& newname) { _name = newname; }

    /**
     * return the definition data as a Policy pointer
     */
    const Policy::Ptr& getData() const { return _policy; }

    /**
     * return the definition data as a Policy pointer
     */
    void setData(const Policy::Ptr& defdata) { 
        _type = Policy::UNDETERMINED;
        _policy = defdata; 
    }

    /**
     * return the type identifier for the parameter
     */
    Policy::ValueType getType() const {
        if (_type == Policy::UNDETERMINED) _type = _determineType();
        return _type;
    }

    /**
     * The human-readable name of this definition's type
     * ("string", "double", etc.).
     */
    std::string getTypeName() const {
	return Policy::typeName[getType()];
    }

    /**
     * return the default value as a string
     */
    std::string getDefault() const {
        return _policy->str("default");
    }

    /**
     * Return the semantic definition for the parameter, empty string if none is
     * specified, or throw a TypeError if it is the wrong type.
     */
    const std::string getDescription() const;

    /**
     * return the maximum number of occurrences allowed for this parameter, 
     * or -1 if there is no limit.
     */
    const int getMaxOccurs() const;

    /**
     * return the minimum number of occurrences allowed for this parameter.
     * Zero is returned if a minimum is not specified.
     */
    const int getMinOccurs() const;

    /**
     * Insert the default value into the given policy
     * @param policy  the policy object update
     * @param errs  a validation error to add complaints to, if there are any.
     * @exception ValidationError if the value does not conform to this definition.
     */
    void setDefaultIn(Policy& policy, ValidationError* errs=0) const {
        setDefaultIn(policy, _name, errs);
    }

    /**
     * @copydoc setDefaultIn(Policy&) const
     * @param withName  the name to look for the value under.  If not given
     *                    the name set in this definition will be used.
     */
    void setDefaultIn(Policy& policy, const std::string& withName,
		      ValidationError* errs=0) const;

    /**
     * @copydoc setDefaultIn(Policy&) const
     */
    template <typename T> void setDefaultIn(Policy& policy,
					    const std::string& withName,
					    ValidationError* errs=0) const;

    /**
     * confirm that a Policy parameter conforms to this definition.  
     *   If a ValidationError instance is provided, any errors detected will be
     *   loaded into it.  If no ValidationError is provided, then any errors
     *   detected will cause a ValidationError exception to be thrown.
     * @param policy   the policy object to inspect
     * @param name     the name to look for the value under.  If not given
     *                 the name set in this definition will be used.
     * @param errs     a pointer to a ValidationError instance to load errors 
     *                 into. 
     * @exception ValidationError   if errs is not provided and the value 
     *                 does not conform.  
     */
    void validate(const Policy& policy, const std::string& name, 
                  ValidationError *errs=0) const;

    /**
     * confirm that a Policy parameter conforms to this definition.  
     *   If a ValidationError instance is provided, any errors detected 
     *   will be loaded into it.  If no ValidationError is provided,
     *   then any errors detected will cause a ValidationError exception
     *   to be thrown.  
     * @param policy   the policy object to inspect
     * @param errs     a pointer to a ValidationError instance to load errors 
     *                  into. 
     * @exception ValidationError   if errs is not provided and the value 
     *                  does not conform.  
     */
    void validate(const Policy& policy, ValidationError *errs=0) const {
        validate(policy, _name, errs);
    }

    //@{
    /**
     * confirm that a Policy parameter name-value combination is consistent 
     * with this dictionary.  This does not check the minimum occurrence 
     * requirement; however, it will check if adding this will exceed the 
     * maximum, assuming that there are currently curcount values.  This 
     * method is intended for use by the Policy object to do on-the-fly
     * validation.
     *
     * If a ValidationError instance is provided, any errors detected 
     * will be loaded into it.  If no ValidationError is provided,
     * then any errors detected will cause a ValidationError exception
     * to be thrown.  
     *
     * @param name      the name of the parameter being checked
     * @param value     the value of the parameter to check.
     * @param curcount  the number of values assumed to already stored under
     *                  the given name.  If < 0, limit checking is not done.
     * @param errs      a pointer to a ValidationError instance to load errors 
     *                  into. 
     * @exception ValidationError   if the value does not conform.  The message
     *                 should explain why.
     */

    void validate(const std::string& name, bool value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, int value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, double value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, std::string value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, const Policy& value, int curcount=-1, 
                  ValidationError *errs=0) const;
    //@}

    //@{
    /**
     * confirm that a Policy parameter name-array value combination is 
     * consistent with this dictionary.  Unlike the scalar version, 
     * this does check occurrence compliance.  
     *
     * If a ValidationError instance is provided, any errors detected 
     * will be loaded into it.  If no ValidationError is provided,
     * then any errors detected will cause a ValidationError exception
     * to be thrown.  
     *
     * @param name     the name of the parameter being checked
     * @param value    the value of the parameter to check.
     * @param errs     a pointer to a ValidationError instance to load errors 
     *                  into. 
     * @exception ValidationError   if the value does not conform.  The message
     *                 should explain why.
     */
    void validate(const std::string& name, const Policy::BoolArray& value, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, const Policy::IntArray& value, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, const Policy::DoubleArray& value, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, 
                  const Policy::StringArray& value, 
                  ValidationError *errs=0) const;
    void validate(const std::string& name, 
                  const Policy::ConstPolicyPtrArray& value, 
                  ValidationError *errs=0) const;
    //@}

    /**
     * confirm that a Policy parameter name-array value combination is 
     * consistent with this dictionary.  Unlike the scalar version, 
     * this does check occurrence compliance.  
     *
     * If a ValidationError instance is provided, any errors detected 
     * will be loaded into it.  If no ValidationError is provided,
     * then any errors detected will cause a ValidationError exception
     * to be thrown.
     *
     * Only does basic validation (min, max, minOccurs, maxOccurs, allowed
     * values); doesn't recursively check sub-dictionaries.
     *
     * @param name     the name of the parameter being checked
     * @param policy   the policy whose named parameter is being checked
     * @param errs     the ValidationError instance to load errors into
     * @exception ValidationError   if the value does not conform.  The message
     *                 should explain why.
     */
    template <typename T> void validateBasic
	(const std::string& name, const Policy& policy,
	 ValidationError *errs=0) const;

    //@{
    /**
     * Confirm that a policy value is consistent with this dictionary; does
     * basic checks (min, max, minOccurs, maxOccurs, allowed values), but does
     * not recurse if \code value \endcode is itself a Policy with a
     * sub-dictionary.
     *
     * Equivalent to <tt>validate(name, value, errs)</tt> for basic types, but
     * not for Policies.
     */
    template <typename T> void validateBasic
	(const std::string& name, const T& value, int curcount=-1,
	 ValidationError *errs=0) const;
    template <typename T> void validateBasic
	(const std::string& name, const std::vector<T>& value,
	 ValidationError *errs=0) const;
    //@}

    //@{
    /**
     * Recursively validate \code value \endcode, using a sub-definition, if
     * present in this Dictionary.
     * @param name  the name of the parameter being checked
     * @param value the value being checked against name's definition
     * @param errs  used to store errors that are found (not allowed to be null)
     */
    void validateRecurse(const std::string& name, Policy::ConstPolicyPtrArray value,
			 ValidationError *errs) const;

    void validateRecurse(const std::string& name, const Policy& value,
			 ValidationError *errs) const;
    //@}

protected:
    Policy::ValueType _determineType() const;

    /**
     * Validate the number of values for a field. Used internally by the
     * validate() functions. 
     * @param name   the name of the parameter being checked
     * @param count  the number of values this name actually has
     * @param errs   report validation errors here (must exist)
     */
    void validateCount(const std::string& name, int count,
		       ValidationError *errs) const;

    static const std::string EMPTY;

private:
    mutable Policy::ValueType _type;
    std::string _prefix; // for recursive validation, eg "foo.bar."
    std::string _name;
    Policy::Ptr _policy;
    bool _wildcard;
};

inline std::ostream& operator<<(std::ostream& os, const Definition& d) {
    d.getData()->print(os, d.getName());
    return os;
}

/**
 * @brief   a class representing the allowed or expected contents of a Policy
 *
 * This class keeps in memory a definition of a Policy "schema".  In other
 * words, it provides definitions of each name that is expected or allowed 
 * in a conforming Policy not only in terms of its semantic meaning but also
 * its value type, default and allowed values, and how often it must or can 
 * occur.  
 *  
 * A Dictionary is envisioned to play two important roles.  First, its 
 * serialized form can provide the documentation for the Policy parameters 
 * that a Policy-supporting class will be looking for.  Second, it can be 
 * used to validate that an instance of a Policy is conformant with the 
 * expectations of such a class.  
 *
 * A Dictionary is a specialization of the Policy class itself.  This means
 * that not only can a Dictionary be handled as any other Policy, but also
 * any Policy format can be used to author a Dictionary.  
 *
 * A Dictionary policy, however, is assumed to follow a specific schema.  
 * The expected parameter names at the top level are:
 * \verbatim
 * Name          Required?    Type    Defintion
 * ------------- -----------  ------  --------------------------------------
 * target        recommended  string  The name of an object or system that 
 *                                      this dictionary is intended for
 * definitions   required     Policy  The definitions of each term, where 
 *                                      each parameter name is a Policy
 *                                      parameter being defined.
 * \endverbatim
 * 
 * Each of the parameters contained under definitions represents a term 
 * being defined and is of type Policy.  Each definition is expected to 
 * follow the following schema:
 * \verbatim
 * Name          Required?    Type    Defintion
 * ------------- -----------  ------  --------------------------------------
 * type          recommended  string  the type of the value expected, one of
 *                                      "int", "bool", "double", "string", and
 *                                      "Policy".  If not provided, any type
 *                                      ("undefined") should be assumed.  If 
 *                                      The type is Policy, a dictionary for 
 *                                      its terms can be provided via 
 *                                      "dictionary"/"dictionaryFile".
 *                                      Note that "PolicyFile" is not allowed;
 *                                      "Policy" should be used in its place,
 *                                      and policy.loadPolicyFiles() should
 *                                      be called before validating a policy.
 * description   recommended  string  The semantic meaning of the term or 
 *                                      explanation of how it will be used.
 * minOccurs     optional     int     The minimun number of values expected.
 *                                      0 means that the parameter is optional,
 *                                      > 0 means that it is required,
 *                                      > 1 means that a vector is required.
 *                                      If not specified or < 0, 0 should be 
 *                                      assumed.
 * maxOccurs     optional     int     The maximun number of values expected.
 *                                      0 means that the parameter is forbidden
 *                                      to occur, 1 means that the value must
 *                                      be a scalar, and > 1 means that an
 *                                      array value is allowed.  If 
 *                                      not specified or < 0, any number of 
 *                                      of values is allowed; the user should
 *                                      assume a vector value.  
 * default       optional     *       A value that will be assumed if none is 
 *                                      provided.  
 * dictionaryFile  optional   string  A file path to the definition of the 
 *                                      sub-policy parameters.  This is ignored
 *                                      unless "type" equals "Policy".
 * dictionary    optional     Policy  the dictionary policy object that defines
 *                                      sub-policy parameters using this above,
 *                                      top-level schema.  
 * allowed       optional     Policy  A description of the allowed values.  
 * allowed.value   optional   *       One allowed value.  This should not be an
 *                                      an array of values.
 * allowed.description  opt.  *       a description of what this value 
 *                                      indicates.
 * allowed.min   optional     *       The minimum allowed value, used for 
 *                                      int and double typed parameters.
 * allowed.max   optional     *       The maximum allowed value, used for 
 *                                      int and double typed parameters.
 * childDefinition optional   Policy    A general definition for wildcard policy
 *                                      elements whose names may or may not be
 *                                      known ahead of time; all such elements
 *                                      must be of uniform type
 * -------------------------------------------------------------------------
 * *the type must be that specified by the type parameter. 
 * \endverbatim
 *
 */
class Dictionary : public Policy {
public:

    // keywords
    static const char *KW_DICT;
    static const char *KW_DICT_FILE;
    static const char *KW_TYPE;
    static const char *KW_DESCRIPTION;
    static const char *KW_DEFS;
    static const char *KW_CHILD_DEF;
    static const char *KW_ALLOWED;
    static const char *KW_MIN_OCCUR;
    static const char *KW_MAX_OCCUR;
    static const char *KW_MIN;
    static const char *KW_MAX;
    static const char *KW_VALUE;

    /**
     * return an empty dictionary.  This can be passed to a parser to be 
     * filled.
     */
    Dictionary() : Policy() { }

    /**
     * return a dictionary that is a copy of the given Policy.  It is assumed
     * that the Policy object follows the Dictionary schema.  If the 
     * policy has a top-level Policy parameter called "dictionary", its 
     * contents will be copied into this dictionary.
     */
    Dictionary(const Policy& pol) 
        : Policy( (pol.isPolicy("dictionary")) ? *(pol.getPolicy("dictionary"))
                                               : pol )
    { }

    /**
     * return a dictionary that is a copy of another dictionary
     */
    Dictionary(const Dictionary& dict) : Policy(dict) { }

    //@{
    /**
     * load a dictionary from a file
     */
    explicit Dictionary(const char *filePath);
    explicit Dictionary(const std::string& filePath);
    explicit Dictionary(const PolicyFile& filePath);
    //@}

    //@{
    /**
     * return the parameter name definitions as a Policy object
     */
    Policy::ConstPtr getDefinitions() const {
        return getPolicy("definitions");
    }
    Policy::Ptr getDefinitions() {
        return getPolicy("definitions");
    }
    //@}

    /**
     * Check this Dictionary's internal integrity.  Load up all definitions and
     * sanity-check them.
     */
    void check() const;

    /**
     * load the top-level parameter names defined in this Dictionary into 
     * a given list.  
     */
    int definedNames(std::list<std::string>& names, bool append=false) const {
        return getDefinitions()->names(names, true, append); 
    }

    /**
     * return the top-level parameter names defined in this Dictionary
     */
    StringArray definedNames() const {
        return getDefinitions()->names(true); 
    }

    /**
     * return a definition for the named parameter
     * @param name    the hierarchical name for the parameter
     */
    Definition getDef(const std::string& name) {
        Definition *def = makeDef(name);
        Definition out(*def);
        delete def;
        return out;
    }

    /**
     * return a definition for the named parameter.  The caller is responsible
     * for deleting the returned object.  This is slightly more efficient than
     * getDef().
     * @param name    the hierarchical name for the parameter
     * @exception     NameNotFoundError if no definition by this name exists
     *                DictionaryError if this dictionary is found to be malformed
     */
    Definition* makeDef(const std::string& name) const;

    /**
     * Does this dictionary have a branch named \code name \endcode that is also
     * a dictionary?
     * @see getSubDictionary
     */
    bool hasSubDictionary(const std::string& name) const {
	std::string key = std::string("definitions.") + name + ".dictionary";
	// could also check isPolicy(key), but we would rather have
	// getSubDictionary(name) fail with a DictionaryError if the
	// sub-dictionary is the wrong type
	return exists(key);
    }

    //@{
    /**
     * Return a branch of this dictionary, if this dictionary describes a
     * complex policy structure -- that is, if it describes a policy with
     * sub-policies.
     */
    DictPtr getSubDictionary(const std::string& name) const;
    // DictPtr getSubDictionary(const std::string& name) const;
    //@}

    /**
     * Validate a Policy against this Dictionary.  All relevant file references
     * in the dictionary, including "dictionaryFile" references, must be
     * resolved first, or else a DictionaryError will be thrown.
     *
     * If a ValidationError instance is provided, any errors detected 
     * will be loaded into it.  If no ValidationError is provided,
     * then any errors detected will cause a ValidationError exception
     * to be thrown.  
     *
     * @param pol    the policy to validate
     * @param errs   a pointer to a ValidationError instance to load errors 
     *                 into. 
     * @exception ValidationError   if the value does not conform.  The message
     *                 should explain why.
     */
    void validate(const Policy& pol, ValidationError *errs=0) const;

    // C++ inheritance & function overloading limitations require us to
    // re-declare this here, even though an identical function is declared in
    // Policy
    /**
     * Recursively replace all PolicyFile values with the contents of the 
     * files they refer to.  The type of a parameter containing a PolicyFile
     * will consequently change to a Policy upon successful completion.  If
     * the value is an array, all PolicyFiles in the array must load without
     * error before the PolicyFile values themselves are erased.
     * @param strict      If true, throw an exception if an error occurs 
     *                    while reading and/or parsing the file (probably an
     *                    IoErrorException or ParseError).  Otherwise, replace
     *                    the file reference with a partial or empty sub-policy
     *                    (that is, "{}").
     * @return            the number of files loaded
     */
    int loadPolicyFiles(bool strict=true) {
	return loadPolicyFiles(fs::path(), strict);
    }

    /**
     * \copydoc loadPolicyFiles()
     * @param repository  a directory to look in for the referenced files.  
     *                    Only when the name of the file to be included is an
     *                    absolute path will this.  If empty or not provided,
     *                    the directorywill be assumed to be the current one.
     * @return            the number of files loaded
     */
    virtual int loadPolicyFiles(const fs::path& repository, bool strict=true);

    //@{
    /**
     * The prefix to this Dictionary's parameter names, for user messages during
     * validation of sub-policies.
     */
    const std::string getPrefix() const { return _prefix; }
    void setPrefix(const std::string& prefix) { _prefix = prefix; }
    //@}


protected:
    static const boost::regex FIELDSEP_RE;

private:
    std::string _prefix; // for recursive validation, eg "foo.bar."
};

template <typename T>
void Definition::validateBasic(const std::string& name, const Policy& policy,
			       ValidationError *errs) const
{
    validateBasic(name, policy.getValueArray<T>(name), errs);
}

template <typename T>
void Definition::validateBasic(const std::string& name, const std::vector<T>& value,
			       ValidationError *errs) const
{
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = &ve;
    if (errs != 0) use = errs;

    validateCount(name, value.size(), use);

    for (typename std::vector<T>::const_iterator i = value.begin();
	 i != value.end();
	 ++i)
	validateBasic<T>(name, *i, -1, use);

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

template <typename T>
void Definition::setDefaultIn(Policy& policy, const std::string& withName,
			      ValidationError *errs) const 
{
    ValidationError ve(LSST_EXCEPT_HERE);
    ValidationError *use = (errs == 0 ? &ve : errs);

    if (_policy->exists("default")) {
	const std::vector<T> defs = _policy->getValueArray<T>("default");
	validateBasic(withName, defs, use);
	if (use->getErrors(withName) == ValidationError::OK) {
	    policy.remove(withName);
	    for (typename std::vector<T>::const_iterator i = defs.begin();
		 i != defs.end();
		 ++i)
		policy.addValue<T>(withName, *i);
	}
    }

    if (errs == 0 && ve.getParamCount() > 0) throw ve;
}

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_POLICY_H
