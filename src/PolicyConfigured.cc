/**
 * \file PolicyConfigured.cc
 */
#include "lsst/pex/policy/PolicyConfigured.h"

namespace lsst {
namespace pex {
namespace policy {

PolicyConfigured::~PolicyConfigured() { }

void PolicyConfigured::done() {
    configured();
    forgetPolicy(); 
}

}}}  // end namespace lsst::pex::policy

