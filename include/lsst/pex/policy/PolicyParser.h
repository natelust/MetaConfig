// -*- lsst-c++ -*-
/**
 * @class PolicyParser
 * 
 * @ingroup mwi
 *
 * @brief a class that can parse serialized Policy data from a stream.
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_MWI_POLICY_PARSER_H
#define LSST_MWI_POLICY_PARSER_H

#include "lsst/mwi/data/Citizen.h"
#include "lsst/mwi/policy/Policy.h"
#include "lsst/mwi/policy/PolicyParserFactory.h"

namespace lsst {
namespace mwi {
namespace policy {

using namespace std;

/**
 * @brief an abstract class for parsing serialized Policy data and loading
 * it into a Policy object.  
 */
class PolicyParser : public Citizen {
public: 

    /**
     * Create a Parser attached to a policy object to be loaded.
     * @param policy   the Policy object to load the parsed data into
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.
     */
    PolicyParser(Policy& policy, bool strict=true) 
        : Citizen(typeid(this)), _pol(policy), _strict(strict) { }

    /**
     * destroy this factory
     */
    virtual ~PolicyParser();

    /**
     * return true if this parser will be strict in adhering to syntax 
     * rules.  In this case, exceptions will be thrown if any syntax errors 
     * are detected.  Otherwise, some syntax errors may be ignored.
     */
    bool isStrict() { return _strict; }

    /**
     * set whether this parser will be strict in adhering to syntax rules.  
     * If set to true, exceptions will be thrown if any syntax errors 
     * are detected.  Otherwise, some syntax errors may be ignored.
     */
    void setStrict(bool strict) { _strict = strict; }

    /**
     * parse data from the input stream and load results into the attached 
     * Policy.  
     * @param strm    the stream to read JSON-encoded data from
     * @returns int   the number of parameters values loaded.  This does not
     *                   include sub-Policy objects.  
     */
    virtual int parse(istream& is) = 0;

    //@{
    /**
     * return the policy object
     */
    Policy& getPolicy() { return _pol; }
    const Policy& getPolicy() const { return _pol; }
    //@}

protected: 

    Policy& _pol;
    bool _strict;
};

}}}  // end namespace lsst::mwi::policy

#endif // LSST_MWI_POLICY_PARSER_H
