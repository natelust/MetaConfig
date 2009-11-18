// -*- lsst-c++ -*-
/**
 * @file exceptions.h
 * @ingroup pex
 * @brief definition of Policy-specific exceptions classes
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_EXCEPTIONS_H
#define LSST_PEX_POLICY_EXCEPTIONS_H

#include "lsst/pex/exceptions.h"

#define POL_EARGS_TYPED char const* ex_file, int ex_line, char const* ex_func
#define POL_EARGS_UNTYPED ex_file, ex_line, ex_func
#define POL_EXCEPT_VIRTFUNCS(etn) \
char const *etn::getType(void) const throw() { return #etn " *"; } \
lsst::pex::exceptions::Exception *etn::clone(void) const { \
    return new etn(*this); \
}

namespace lsst {
namespace pex {
namespace policy {

namespace pexExcept = lsst::pex::exceptions;

/**
 * an exception thrown when Policy parameter name has an illegal form.  This
 * usually means that it contains zero-length fields.  In other words, it 
 * either starts with a period, ends with a period, or contains two or more
 * consecutive periods.
 */
class BadNameError : public pexExcept::RuntimeErrorException {
public:
    BadNameError(POL_EARGS_TYPED) 
        : pexExcept::RuntimeErrorException(POL_EARGS_UNTYPED, 
                                           "Illegal Policy parameter name") 
    { }
    BadNameError(POL_EARGS_TYPED, const std::string& badname) 
        : pexExcept::RuntimeErrorException(POL_EARGS_UNTYPED, 
              std::string("Illegal Policy parameter name: ") + badname) 
    { }
    virtual char const *getType(void) const throw();
    virtual pexExcept::Exception *clone() const;
};

/**
 * There is a problem with a dictionary.
 */
class DictionaryError : public pexExcept::DomainErrorException {
public:
    DictionaryError(POL_EARGS_TYPED)
        : pexExcept::DomainErrorException(POL_EARGS_UNTYPED,
                                           "Malformed dictionary")
    { }
    DictionaryError(POL_EARGS_TYPED, const std::string& msg)
        : pexExcept::DomainErrorException(POL_EARGS_UNTYPED,
            std::string("Malformed dictionary: ") + msg)
    { }
    virtual char const *getType(void) const throw();
    virtual pexExcept::Exception *clone() const;
};

/**
 * an exception indicating that a policy parameter of a given name can
 * not be found in a Policy object.
 */
class NameNotFound : public pexExcept::NotFoundException {
public:
    NameNotFound(POL_EARGS_TYPED) 
        : pexExcept::NotFoundException(POL_EARGS_UNTYPED, 
                                       "Policy parameter name not found") 
    { }
    NameNotFound(POL_EARGS_TYPED, const std::string& parameter) 
        : pexExcept::NotFoundException(POL_EARGS_UNTYPED, 
                  std::string("Policy parameter name not found: ") + parameter) 
    { }
    virtual char const *getType(void) const throw();
    virtual pexExcept::Exception *clone() const;
};

/**
 * an exception indicating that a policy parameter with a given name has a
 * type different from the one that was requested.
 */
class TypeError : public pexExcept::DomainErrorException {
public:
    TypeError(POL_EARGS_TYPED) 
        : pexExcept::DomainErrorException(POL_EARGS_UNTYPED, 
                                          "Parameter has wrong type") 
    { }
    TypeError(POL_EARGS_TYPED, 
              const std::string& parameter, const std::string& expected)  
        : pexExcept::DomainErrorException(POL_EARGS_UNTYPED, 
                               std::string("Parameter \"") + parameter + 
                               "\" has wrong type; expecting " + expected + ".") 
    { }
    virtual char const *getType(void) const throw();
    virtual pexExcept::Exception *clone() const;
};

}}}  // end namespace lsst::pex::policy


#endif // LSST_PEX_POLICY_EXCEPTIONS_H
