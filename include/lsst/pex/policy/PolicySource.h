// -*- lsst-c++ -*-
/**
 * @class PolicySource
 * 
 * @ingroup pex
 *
 * @brief a representation of a src of serialized Policy parameter data
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_SOURCE_H
#define LSST_PEX_POLICY_SOURCE_H

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyParserFactory.h"
#include "lsst/pex/policy/SupportedFormats.h"

namespace lsst {
namespace pex {
namespace policy {

using namespace std;

using lsst::daf::base::Citizen;

/**
 * @brief an abstract class representing a source of serialized Policy 
 * parameter data.  This might be a file or a stream; sub-classes handle 
 * the different possibilities.  This class can determine which format the
 * data is in (which may involve reading the first few characters) and 
 * load it into a Policy.
 */
class PolicySource : public Citizen {
public:

    /**
     * create a Policy file that points a file with given path.
     * @param fmts   the list of formats to support
     */
    PolicySource(SupportedFormats::Ptr fmts=defaultFormats) 
        : Citizen(typeid(this)), _formats(fmts) 
    { 
        if (defaultFormats->size() == 0) 
            SupportedFormats::initDefaultFormats(*defaultFormats);
    }

    /**
     * destroy the source
     */
    virtual ~PolicySource();

//     /**
//      * identifiers for the different supported formats
//      */
//     enum FormatType {

//         /**  Unknown and unsupported */
//         UNSUPPORTED,

//         /**  XML format  */
//         XML,

//         /**  Policy authoring format (PAF)  */
//         PAF,

//         /**  Supported format but unknown  */
//         UNKNOWN
//     };

//     /**
//      * determine the format that the data is stored in and return its format
//      * type identifier.  Note that UNKNOWN will be returned
//      * if the format is supported--that is, the data can be read into a 
//      * Policy object--but otherwise does not have a defined type identifier 
//      * defined.  This may cause the first few records of the source to 
//      * be read.
//      * @exception IOError   if an error occurs while reading the first few
//      *                      characters of the source stream.
//      */
//     virtual FormatType getFormatType();

    /**
     * return the name of the format that the data is stored in.  This may 
     * cause the first few records of the source to be read.
     * @exception IOError   if an error occurs while reading the first few
     *                      characters of the source stream.
     */
    virtual const string& getFormatName() = 0;

    /**
     * load the data from this Policy source into a Policy object
     * @param policy    the policy object to load the data into
     * @exception ParserException  if an error occurs while parsing the data
     * @exception IOError   if an I/O error occurs while reading from the 
     *                       source stream.
     */
    virtual void load(Policy& policy) = 0;

//     /**
//      * returns true if the given string containing a content identifier
//      * indicates that it contains dictionary data.  Dictionary data has
//      * a content id of "<?cfg ... dictionary ?>" (where ... indicates 
//      * the format); policy data has an id of "<?cfg ... policy ?>".  
//      */
//     static bool indicatesDictionary(const string& contentid) {
//         return regex_search(contentid, DICTIONARY_CONTENT);
//     }

    /**
     * a default set of formats
     */
    static SupportedFormats::Ptr defaultFormats;

//     static const regex DICTIONARY_CONTENT;

protected:


    SupportedFormats::Ptr _formats;   
};


}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_SOURCE_H


