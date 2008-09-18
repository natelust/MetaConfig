/**
 * @class PolicyParserFactory
 * 
 * @ingroup pex
 *
 * @author Ray Plante
 * 
 */

#include "lsst/pex/policy/SupportedFormats.h"
#include "lsst/pex/policy/paf/PAFParserFactory.h"

namespace lsst {
namespace pex {
namespace policy {

using lsst::pex::policy::paf::PAFParserFactory;

/*
#include "lsst/pex/utils/Trace.h"
#define EXEC_TRACE  20
static void execTrace( string s, int level = EXEC_TRACE ){
    lsst::pex::utils::Trace( "pex.policy.PolicyParserFactory", level, s );
}
*/

void SupportedFormats::initDefaultFormats(SupportedFormats& sf) { 
    sf.registerFormat(PolicyParserFactory::Ptr(new PAFParserFactory()));
}

/**
 * register a factory method for policy format parsers
 */
void SupportedFormats::registerFormat(const PolicyParserFactory::Ptr& factory) 
{
    if (factory.get() == 0) 
        throw runtime_error(string("attempt to register null ") + 
                            "PolicyParserFactory pointer");

    _formats[factory->getFormatName()] = factory;
}

/**
 * analyze the given string assuming contains the leading characters 
 * from the data stream and determine if it is recognized as being in 
 * the format supported by this parser.  If it is, return the name of 
 * the this format; if not return an empty string.  
 */
const string& SupportedFormats::recognizeType(const string& leaders) const {

    Lookup::const_iterator f;
    for(f=_formats.begin(); f != _formats.end(); ++f) {
        if (f->second->recognize(leaders))
            return f->second->getFormatName();
    }

    return PolicyParserFactory::UNRECOGNIZED;
}

/**
 * get a pointer to a factory with a given name.  A null pointer is 
 * returned if the name is not recognized.
 */
PolicyParserFactory::Ptr SupportedFormats::getFactory(const string& name) const
{
    SupportedFormats *me = const_cast<SupportedFormats*>(this);

    Lookup::iterator found = me->_formats.find(name);
    return ((found != me->_formats.end()) ? found->second 
                                          : PolicyParserFactory::Ptr());
}

}}}  // end namespace lsst::pex::policy



