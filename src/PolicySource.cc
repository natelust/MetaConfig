/**
 * @class PolicySource
 * 
 * @ingroup pex
 *
 * @author Ray Plante
 * 
 */

#include "lsst/pex/policy/PolicySource.h"

namespace lsst {
namespace pex {
namespace policy {

PolicySource::~PolicySource() { }

SupportedFormats::Ptr PolicySource::defaultFormats(new SupportedFormats());

}}}   // end lsst::pex::policy
