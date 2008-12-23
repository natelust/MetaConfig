// -*- lsst-c++ -*-
/*
 * @ingroup pex
 *
 * @brief exceptions characterizing errors in the use of Policies
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_EXCEPTIONS_H
#define LSST_PEX_POLICY_EXCEPTIONS_H

#include "lsst/pex/exceptions.h"

#define POL_EARGS_TYPED char const* ex_file, int ex_line, char const* ex_func
#define POL_EARGS_UNTYPED ex_file, ex_line, ex_func

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
};

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
};

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
};

}}}  // end namespace lsst::pex::policy


#endif // LSST_PEX_POLICY_EXCEPTIONS_H
