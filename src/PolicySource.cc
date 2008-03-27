/**
 * @class PolicySource
 * 
 * @ingroup mwi
 *
 * @author Ray Plante
 * 
 */

#include "lsst/mwi/policy/PolicySource.h"

namespace lsst {
namespace mwi {
namespace policy {

PolicySource::~PolicySource() { }

SupportedFormats::Ptr PolicySource::defaultFormats(new SupportedFormats());

}}}   // end lsst::mwi::policy
