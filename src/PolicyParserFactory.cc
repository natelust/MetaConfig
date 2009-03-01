/**
 * @file PolicyParserFactory.cc
 * @ingroup pex
 * @author Ray Plante
 */

#include "lsst/pex/policy/PolicyParserFactory.h"

namespace lsst {
namespace pex {
namespace policy {

/*
#include "lsst/pex/utils/Trace.h"
#define EXEC_TRACE  20
static void execTrace( string s, int level = EXEC_TRACE ){
    lsst::pex::utils::Trace( "pex.policy.PolicyParserFactory", level, s );
}
*/

const std::string PolicyParserFactory::UNRECOGNIZED;

PolicyParserFactory::~PolicyParserFactory() { }

/**
 * return the name for the format supported by the parser
 */
const std::string& PolicyParserFactory::getFormatName() { 
    return UNRECOGNIZED; 
}

}}}  // end namespace lsst::pex::policy

