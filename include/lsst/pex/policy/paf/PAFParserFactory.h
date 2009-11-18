// -*- lsst-c++ -*-
/**
 * @file PAFParserFactory.h
 * 
 * @ingroup pex
 *
 * @brief definition of the PAFParserFactory class
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_PAF_PAFPARSERFACTORY_H
#define LSST_PEX_POLICY_PAF_PAFPARSERFACTORY_H

#include "lsst/pex/policy/PolicyParserFactory.h"
#include <boost/regex.hpp>

namespace lsst {
namespace pex {
namespace policy {

// forward declaraction
class PolicyParser;

namespace paf {

namespace pexPolicy = lsst::pex::policy;

/**
 * a class for creating PAFParser objects
 */
class PAFParserFactory : public pexPolicy::PolicyParserFactory {
public:

    /**
     * create a new factory
     * @param contIdPatt   the pattern to use for recognizing a content 
     *                       identifier.  A content ID is encoded in a 
     *                       (#-leading) comment as the first line of the 
     *                       file.  The default is "<?cfg JSON ... ?>"
     */
    PAFParserFactory(const boost::regex& contIdPatt=CONTENTID) 
        : pexPolicy::PolicyParserFactory(), contentid(contIdPatt) { }

    /**
     * create a new PolicyParser class and return a pointer to it.  The 
     * caller is responsible for destroying the pointer.
     * @param  policy   the Policy object that data should be loaded into.
     * @param  strict   if true (default), make the returned PolicyParser 
     *                    be strict in reporting errors in file 
     *                    contents and syntax.  If false, errors will 
     *                    be ignored if possible; often, such errors will 
     *                    result in some data not getting loaded.  The 
     *                    default (set by PolicyParser) is true.
     */
    virtual pexPolicy::PolicyParser* createParser(pexPolicy::Policy& policy, 
                                                  bool strict=true) const;

    /**
     * analyze the given string assuming contains the leading characters 
     * from the data stream and return true if it is recognized as being in 
     * the format supported by this parser.  If it is, return the name of 
     * the this format; 
     */
    virtual bool isRecognized(const std::string& leaders) const;

    /**
     * return the name for the format supported by the parser
     */
    virtual const std::string& getFormatName();

    /** 
     * a name for the format
     */
    static const std::string FORMAT_NAME;

    /**
     * a pattern for the leading data characters for this format
     */
    static const boost::regex LEADER_PATTERN;

    /**
     * a default pattern for the content identifier.  The content ID
     * is encoded in a (#-leading) comment as the first line of the 
     * file.  This default is "<?cfg PAF ... ?>"
     */
    static const boost::regex CONTENTID;

private:
    boost::regex contentid;
};

}}}}   // end lsst::pex::policy::paf

#endif // LSST_PEX_POLICY_PAF_PAFPARSERFACTORY_H


