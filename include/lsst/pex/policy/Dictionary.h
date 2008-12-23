// -*- lsst-c++ -*-
/**
 * @class Dictionary
 * 
 * @ingroup pex
 *
 * @brief an object for holding configuration data
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_DICTIONARY_H
#define LSST_PEX_POLICY_DICTIONARY_H

#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/exceptions.h"
#include <boost/regex.hpp>

namespace pexExcept = lsst::pex::exceptions;

namespace lsst {
namespace pex {
namespace policy {

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
         * MISSING_REQUIRED, NOT_AN_ARRAY, and ARRAY_TOO_SHORT
         */
        TOO_FEW_VALUES = 14, 

        /** parameter contains too many array values */
        TOO_MANY_VALUES = 16,

        /** 
         * array has an incorrect number of values.   This bit-wise ORs 
         * MISSING_REQUIRED, NOT_AN_ARRAY, ARRAY_TOO_SHORT, and 
         * TOO_MANY_VALUES.
         */
        WRONG_OCCURANCE_COUNT = 30,

        /** the value is not one of the explicit values allowed. */
        VALUE_DISALLOWED = 32,

        /** 
         * the value is out of range, either below the minimum or above the 
         * maximum.
         */
        VALUE_OUT_OF_RANGE = 64,

        /**
         * the value false outside of the supported domain of values.
         * This bit-wise ORs VALUE_DISALLOWED and VALUE_OUT_OF_RANGE.
         */
        BAD_VALUE = 96, 

        /**
         * an unknown error.  This is the highest error number.
         */
        UNKNOWN_ERROR = 128
    };

    static const string& getErrorMessageFor(ErrorType err) {
        if (_errmsgs.size() == 0) _loadMessages();
        MsgLookup::iterator it = _errmsgs.find(err);
        if (it != _errmsgs.end())
            return it->second;
        else 
            return EMPTY;
    }

    static const string EMPTY;

    /**
     * create an empty ValidationError message
     */
    ValidationError(POL_EARGS_TYPED) 
       : pexExcept::LogicErrorException(POL_EARGS_UNTYPED, 
                                        "policy has unknown validation errors"), 
       _errors() 
    { }

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
    void paramNames(list<string> names) const {
        ParamLookup::const_iterator it;
        for(it = _errors.begin(); it != _errors.end(); it++)
            names.push_back(it->first);
    }

    /**
     * get the errors encountered for the given parameter name
     */
    int getErrors(const string& name) const {
        ParamLookup::const_iterator it = _errors.find(name);
        if (it != _errors.end()) 
            return it->second;
        else
            return 0;
    }

    /**
     * add an error code to this exception
     */
    void addError(const string& name, ErrorType e) {
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

protected:
    typedef map<int, string> MsgLookup;
    typedef map<string, int> ParamLookup;

    static MsgLookup _errmsgs;

    static void _loadMessages();

    ParamLookup _errors;
};

/**
 * @brief a convenience convenience container for a single parameter 
 * definition from a dictionary.
 */
class Definition : public Citizen {
public:

    /**
     * create an empty definition
     * @param paramName   the name of the parameter being defined.
     */
    Definition(const string& paramName = "")
        : Citizen(typeid(*this)), _type(Policy::UNDEF), 
          _name(paramName), _policy()
    {
        _policy.reset(new Policy());
    }

    /**
     * create a definition from a data contained in a Policy
     * @param paramName   the name of the parameter being defined.
     * @param defn        the policy containing the definition data
     */
    Definition(const string& paramName, const Policy::Ptr& defn) 
        : Citizen(typeid(*this)), _type(Policy::UNDEF), 
          _name(paramName), _policy(defn)
    { }

    /**
     * create a definition from a data contained in a Policy
     * @param defn        the policy containing the definition data
     */
    Definition(const Policy::Ptr& defn) 
        : Citizen(typeid(*this)), _type(Policy::UNDEF), 
          _name(), _policy(defn)
    { }

    /**
     * create a copy of a definition
     */
    Definition(const Definition& that) 
        : Citizen(typeid(*this)), _type(Policy::UNDEF), 
          _name(that._name), _policy(that._policy)
    { }

    /**
     * reset this definition to another one
     */
    Definition& operator=(const Definition& that) {
        _type = Policy::UNDEF;
        _name = that._name;
        _policy = that._policy;
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
    const string& getName() const { return _name; }

    /**
     * set the name of the parameter.  Note that this will not effect the 
     * name in Dictionary that this Definition came from.  
     */
    void setName(const string& newname) { _name = newname; }

    /**
     * return the definition data as a Policy pointer
     */
    const Policy::Ptr& getData() const { return _policy; }

    /**
     * return the definition data as a Policy pointer
     */
    void setData(const Policy::Ptr& defdata) { 
        _type = Policy::UNDEF;
        _policy = defdata; 
    }

    /**
     * return the type identifier for the parameter
     */
    Policy::ValueType getType() const {
        if (_type == Policy::UNDEF) _type = _determineType();
        return _type;
    }

    /**
     * return the default value as a string
     */
    string getDefault() const {
        return _policy->str("default");
    }

    /**
     * return the semantic definition for the parameter
     */
    const string& getDescription() const {
        if (! _policy->isString("description")) 
            return ValidationError::EMPTY;
        return _policy->getString("description");
    }

    /**
     * return the maximum number of occurances allowed for this parameter, 
     * or -1 if there is no limit.
     */
    const int getMaxOccurs() const {
        try {  return _policy->getInt("maxOccurs");  }
        catch (NameNotFound& ex) {  return -1;  }
    }

    /**
     * return the minimum number of occurances allowed for this parameter.
     * Zero is returned if a minimum is not specified.
     */
    const int getMinOccurs() const {
        try {  return _policy->getInt("minOccurs");  }
        catch (NameNotFound& ex) {  return 0;  }
    }

    //@{
    /**
     * the default value into the given policy
     * @param policy    the policy object update
     * @param withName  the name to look for the value under.  If not given
     *                    the name set in this definition will be used.
     */
    void setDefaultIn(Policy& policy, const string& withName) const;
    void setDefaultIn(Policy& policy) const {
        setDefaultIn(policy, _name);
    }
    //@}

    //@}
    /**
     * confirm that a Policy parameter conforms to this definition.  
     *   If a ValidationError instance is provided, any errors detected 
     *   and will be loaded into it.  If no ValidationError is provided,
     *   then any errors detected will cause a ValidationError exception
     *   to be thrown.  
     * @param policy   the policy object to inspect
     * @param name     the name to look for the value under.  If not given
     *                  the name set in this definition will be used.
     * @param errs     a pointer to a ValidationError instance to load errors 
     *                  into. 
     * @exception ValidationError   if errs is not provided and the value 
     *                  does not conform.  
     */
    void validate(const Policy& policy, const string& name, 
                  ValidationError *errs=0) const;
    void validate(Policy& policy, ValidationError *errs=0) const {
        validate(policy, _name, errs);
    }
    //@}

    //@{
    /**
     * confirm that a Policy parameter name-value combination is consistent 
     * with this dictionary.  This does not check the minimum occurance 
     * requirement; however, it will check if adding this will exceed the 
     * maximum, assuming that there are currently curcount values.  This 
     * method is intended for use by the Policy object to do on-the-fly
     * validation.
     *
     * If a ValidationError instance is provided, any errors detected 
     * and will be loaded into it.  If no ValidationError is provided,
     * then any errors detected will cause a ValidationError exception
     * to be thrown.  
     *
     * @param name      the name of the parameter being checked
     * @param value     the value of the parameter to check.
     * @param curcount  the number of values assumed to already stored under
     *                     the given name.  If < 0, limit checking is not
     *                     done.  
     * @exception ValidationError   if the value does not conform.  The message
     *                 should explain why.
     */
    void validate(const string& name, bool value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const string& name, int value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const string& name, double value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const string& name, string value, int curcount=-1, 
                  ValidationError *errs=0) const;
    void validate(const string& name, const Policy& value, int curcount=-1, 
                  ValidationError *errs=0) const;
    //@}

    //@{
    /**
     * confirm that a Policy parameter name-array value combination is 
     * consistent with this dictionary.  Unlike the scalar version, 
     * this does check occurance compliance.  
     *
     * If a ValidationError instance is provided, any errors detected 
     * and will be loaded into it.  If no ValidationError is provided,
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
    void validate(const string& name, const Policy::BoolArray& value, 
                  ValidationError *errs=0) const;
    void validate(const string& name, const Policy::IntArray& value, 
                  ValidationError *errs=0) const;
    void validate(const string& name, const Policy::DoubleArray& value, 
                  ValidationError *errs=0) const;
    void validate(const string& name, 
                  const Policy::StringPtrArray& value, 
                  ValidationError *errs=0) const;
    void validate(const string& name, 
                  const Policy::PolicyPtrArray& value, 
                  ValidationError *errs=0) const;
    //@}

protected:
    Policy::ValueType _determineType() const;

    static const string EMPTY;

private:
    mutable Policy::ValueType _type;
    string _name;
    Policy::Ptr _policy;
};

inline ostream& operator<<(ostream& os, const Definition& d) {
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
 *                                      "policy".  If not provided, any type
 *                                      ("undefined") should be assumed.  If 
 *                                      The type is Policy, a dictionary for 
 *                                      its terms can be provided via 
 *                                      "dictionary"/"dictionaryFile".
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
 * -------------------------------------------------------------------------
 * *the type must be that specified by the type parameter. 
 * \endverbatim
 *
 */
class Dictionary : public Policy {
public:

    /**
     * return an empty dictionary.  This can be passed to a parser to be 
     * filled.
     */
    Dictionary() : Policy() { }

    /**
     * return a dictionary that is a copy of the given Policy.  It is assumed
     * that the Policy object follows the Dictionary schema.  If the 
     * policy has a top-level Policy parameter called "dictionary", it's 
     * contents will be copied into this dictionary.
     */
    Dictionary(const Policy& pol) 
        : Policy( (pol.isPolicy("dictionary")) ? *(pol.getPolicy("dictionary"))
                                               : pol )
    { }

    /**
     * return a dictionary that is a copy of another policy
     */
    Dictionary(const Dictionary& dict) : Policy(dict) { }

    //@{
    /**
     * load a dictionary from a file
     */
    Dictionary(const char *filePath);
    Dictionary(PolicyFile filePath);
    //@}

    //@{
    /**
     * return the parameter name definitions as a Policy object
     */
    const Policy::Ptr getDefinitions() const {
        return getPolicy("definitions");
    }
    Policy::Ptr getDefinitions() {
        return getPolicy("definitions");
    }
    //@}

    /**
     * load the top-level parameter names defined in this Dictionary into 
     * a given list.  
     */
    int definedNames(list<string>& names, bool append=false) const {
        return getDefinitions()->names(names, true, append); 
    }

    /**
     * return a definition for the named parameter
     * @param name    the hierarchical name for the parameter
     */
    Definition getDef(const string& name) {
        Definition *def = makeDef(name);
        Definition out(*def);
        delete def;
        return out;
    }

    /**
     * return a definition for the named parameter.  The caller is responsible
     * for deleting the returned object.  This is slightly more efficient the 
     * getDef().
     * @param name    the hierarchical name for the parameter
     */
    Definition* makeDef(const string& name) const;

    /**
     * validate a Policy against this Dictionary.
     *
     * If a ValidationError instance is provided, any errors detected 
     * and will be loaded into it.  If no ValidationError is provided,
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

protected:
    static const boost::regex FIELDSEP_RE;

};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_POLICY_H
