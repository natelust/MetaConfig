// -*- lsst-c++ -*-
/**
 * @file PolicyString.h
 * @brief  definition of the PolicyString class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_STRING_H
#define LSST_PEX_POLICY_STRING_H

#include <boost/shared_ptr.hpp>
#include <boost/regex.hpp>

#include "lsst/pex/policy/PolicySource.h"
#include "lsst/pex/policy/SupportedFormats.h"
#include "lsst/daf/base/Persistable.h"

namespace lsst {
namespace pex {
namespace policy {

namespace dafBase = lsst::daf::base;

/**
 * @brief a representation of a string containing Policy parameter data
 *
 * This class facilitates reading data from a string.  This class is 
 * especially useful for supporting string I/O from Python.  The data is
 * encoded in a supported format (just like the contents of a policy file).  
 */
class PolicyString : public PolicySource, public dafBase::Persistable {
public:

    /**
     * create a PolicyString that's wrapped around a given string.
     * @param data          the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param fmts           a SupportedFormats object to use.  An instance 
     *                          encapsulates a configured set of known formats.
     */
    explicit PolicyString(const std::string& data,
                          const SupportedFormats::Ptr& fmts = defaultFormats);

    /**
     * create a "null" Policy formed from an empty string.  
     * @param fmts           a SupportedFormats object to use.  An instance 
     *                          encapsulates a configured set of known formats.
     */
    PolicyString(const SupportedFormats::Ptr& fmts = defaultFormats);

    /**
     * return the wrapped policy data as a string
     */
    const std::string& getData() const { return _data; }

    //@{
    /**
     * return the name of the format that the data is stored in.  This may 
     * cause the first few records of the source to be read.  In this 
     * implementation, once the format is definitely determined, the format
     * name is cached internally, preventing re-determination on the next 
     * call to this function.  
     * @exception IOError   if an error occurs while reading the first few
     *                      characters of the source stream.
     */
    virtual const std::string& getFormatName();
    const std::string& getFormatName() const {
        return const_cast<PolicyString*>(this)->getFormatName();
    }
    //@}

    //@{
    /**
     * load the data from this Policy source into a Policy object
     * @param policy    the policy object to load the data into
     * @exception ParserException  if an error occurs while parsing the data
     * @exception IOError   if an I/O error occurs while reading from the 
     *                       source stream.
     */
    virtual void load(Policy& policy);
    void load(Policy& policy) const { 
        const_cast<PolicyString*>(this)->load(policy);
    }
    //@}

    static const boost::regex SPACE_RE;   //! reg-exp for an empty line
    static const boost::regex COMMENT;    //! reg-exp for the start of a comment
    /** 
     * reg-exp for a Policy content identifier, "<?cfg [format] [content] ?>"
     */
    static const boost::regex CONTENTID;  

protected:
    /**
     * the policy data
     */
    std::string _data;

private:
    const std::string& cacheName(const std::string& name) {
        _format = name;
        return _format;
    }

    std::string _format;
    PolicyParserFactory::Ptr _pfact;

    // inherits SupportedFormats _formats from PolicySource
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_STRING_H


