/**
 * @class JSONParserFactory
 * 
 * @ingroup pex
 *
 * @author Ray Plante
 * 
 */

#include "lsst/pex/policy/json/JSONParserFactory.h"
#include "lsst/pex/policy/json/JSONParser.h"

namespace lsst {
namespace pex {
namespace policy {
namespace json {

using boost::regex_search;

/** 
 * a name for the format
 */
const string JSONParserFactory::FORMAT_NAME("JSON");

const regex JSONParserFactory::LEADER_PATTERN("^\\s*\\{");
const regex 
   JSONParserFactory::CONTENTID("^\\s*#\\s*<\\?cfg\\s+JSON(\\s+\\w+)*\\s*\\?>",
                                regex::icase);

/**
 * create a new PolicyParser class and return a pointer to it.  The 
 * caller is responsible for destroying the pointer.
 * @param  policy   the Policy object that data should be loaded into.
 */
PolicyParser* JSONParserFactory::createParser(Policy& policy, 
                                              bool strict) const 
{ 
    return new JSONParser(policy, strict);
}

/**
 * return the name for the format supported by the parser
 */
const string& JSONParserFactory::getFormatName() { return FORMAT_NAME; }

/**
 * analyze the given string assuming contains the leading characters 
 * from the data stream and return true if it is recognized as being in 
 * the format supported by this parser.  If it is, return the name of 
 * the this format; 
 */
bool JSONParserFactory::recognize(const string& leaders) const { 
    return (regex_search(leaders, contentid) || 
            regex_search(leaders, LEADER_PATTERN));
}

}}}}   // end lsst::pex::policy::json
