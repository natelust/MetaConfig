// -*- lsst-c++ -*-
/**
 * @class PAFParserFactory
 * 
 * @ingroup mwi
 *
 * @author Ray Plante
 * 
 */

#ifndef LSST_MWI_POLICY_PAF_PAFPARSERFACTORY_H
#define LSST_MWI_POLICY_PAF_PAFPARSERFACTORY_H

#include "lsst/mwi/policy/PolicyParserFactory.h"
#include <boost/regex.hpp>

namespace lsst {
namespace mwi {
namespace policy {

// forward declaraction
class PolicyParser;

namespace paf {

using namespace std;
using lsst::mwi::policy::Policy;
using lsst::mwi::policy::PolicyParser;
using boost::regex;

/**
 * a class for creating PAFParser objects
 */
class PAFParserFactory : public PolicyParserFactory {
public:

    /**
     * create a new factory
     * @param contIdPatt   the pattern to use for recognizing a content 
     *                       identifier.  A content ID is encoded in a 
     *                       (#-leading) comment as the first line of the 
     *                       file.  The default is "<?cfg JSON ... ?>"
     */
    PAFParserFactory(const regex& contIdPatt=CONTENTID) 
        : PolicyParserFactory(), contentid(contIdPatt) { }

    /**
     * create a new PolicyParser class and return a pointer to it.  The 
     * caller is responsible for destroying the pointer.
     * @param  policy   the Policy object that data should be loaded into.
     */
    virtual PolicyParser* createParser(Policy& policy, 
                                       bool strict=true) const;

    /**
     * analyze the given string assuming contains the leading characters 
     * from the data stream and return true if it is recognized as being in 
     * the format supported by this parser.  If it is, return the name of 
     * the this format; 
     */
    virtual bool recognize(const string& leaders) const;

    /**
     * return the name for the format supported by the parser
     */
    virtual const string& getFormatName();

    /** 
     * a name for the format
     */
    static const string FORMAT_NAME;

    /**
     * a pattern for the leading data characters for this format
     */
    static const regex LEADER_PATTERN;

    /**
     * a default pattern for the content identifier.  The content ID
     * is encoded in a (#-leading) comment as the first line of the 
     * file.  This default is "<?cfg PAF ... ?>"
     */
    static const regex CONTENTID;

private:
    regex contentid;
};

}}}}   // end lsst::mwi::policy::paf

#endif // LSST_MWI_POLICY_PAF_PAFPARSERFACTORY_H


