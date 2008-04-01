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

#include <stdexcept>

namespace lsst {
namespace pex {
namespace policy {

using namespace std;

/**
 * an exception thrown when Policy parameter name has an illegal form.  This
 * usually means that it contains zero-length fields.  In other words, it 
 * either starts with a period, ends with a period, or contains two or more
 * consecutive periods.
 */
class BadNameError : public invalid_argument {
public:
    BadNameError() : invalid_argument("Illegal Policy parameter name") { }
    BadNameError(const string& badname) : 
        invalid_argument(string("Illegal Policy parameter name: ") + badname) 
    { }
};

class NameNotFound : public domain_error {
public:
    NameNotFound() : domain_error("Policy parameter name not found") { }
    NameNotFound(const string& parameter) : 
        domain_error(string("Policy parameter name not found: ") + parameter) 
    { }
};

class TypeError : public runtime_error {
public:
    TypeError() : runtime_error("Parameter has wrong type") { }
    TypeError(const string& parameter, const string& expected) : 
        runtime_error(string("Parameter \"") + parameter + 
                      "\" has wrong type; expecting " + expected + ".") 
    { }
};

class IOError : public runtime_error {
public:
    IOError() : runtime_error("Unknown I/O error while handling a policy") { }
    IOError(const string& msg) : runtime_error(msg) { }
};

}}}  // end namespace lsst::pex::policy


#endif // LSST_PEX_POLICY_EXCEPTIONS_H
