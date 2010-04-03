/**
 * @file PolicyDestination.cc
 * @author Ray Plante
 */
#include <ostream>

#include "lsst/pex/policy/PolicyStreamDestination.h"

namespace lsst {
namespace pex {
namespace policy {

PolicyStreamDestination::PolicyStreamDestination(PolicyStreamDestination::StreamPtr ostrm) 
    : PolicyDestination(), _ostrm(ostrm) { }

PolicyStreamDestination::~PolicyStreamDestination() { }

std::ostream& PolicyStreamDestination::getOutputStream() {
    return *_ostrm;
}

}}}
