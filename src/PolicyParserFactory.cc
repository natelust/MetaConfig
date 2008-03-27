/**
 * @class PolicyParserFactory
 * 
 * @ingroup mwi
 *
 * @author Ray Plante
 * 
 */

#include "lsst/mwi/policy/PolicyParserFactory.h"

namespace lsst {
namespace mwi {
namespace policy {

/*
#include "lsst/mwi/utils/Trace.h"
#define EXEC_TRACE  20
static void execTrace( string s, int level = EXEC_TRACE ){
    lsst::mwi::utils::Trace( "mwi.policy.PolicyParserFactory", level, s );
}
*/

const string PolicyParserFactory::UNRECOGNIZED;

PolicyParserFactory::~PolicyParserFactory() { }

/**
 * return the name for the format supported by the parser
 */
const string& PolicyParserFactory::getFormatName() { return UNRECOGNIZED; }

}}}  // end namespace lsst::mwi::policy

