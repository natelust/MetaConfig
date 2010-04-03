/**
 * @file PolicyDestination.cc
 * @author Ray Plante
 */
#include <sstream>

#include "lsst/pex/policy/PolicyStringDestination.h"

namespace lsst {
namespace pex {
namespace policy {

PolicyStringDestination::PolicyStringDestination() 
    : PolicyStreamDestination(
        PolicyStringDestination::StreamPtr(new std::ostringstream())
      ), _sstrm()
{ 
    _sstrm = dynamic_cast<std::ostringstream*>(_ostrm.get());
}

PolicyStringDestination::PolicyStringDestination(const std::string& str) 
    : PolicyStreamDestination(
        PolicyStringDestination::StreamPtr(new std::ostringstream(str))
      ), _sstrm()
{ 
    _sstrm = dynamic_cast<std::ostringstream*>(_ostrm.get());
}

PolicyStringDestination::~PolicyStringDestination() { }

}}}
