// -*- lsst-c++ -*-
/**
 * @class PolicyFile
 * 
 * @ingroup pex
 *
 * @brief a representation of a file containing Policy parameter data
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_FILE_H
#define LSST_PEX_POLICY_FILE_H

#include <boost/shared_ptr.hpp>
#include <boost/regex.hpp>
#include <boost/filesystem/path.hpp>
#include <boost/filesystem/operations.hpp>

#include "lsst/pex/policy/PolicySource.h"
#include "lsst/pex/policy/SupportedFormats.h"

namespace lsst {
namespace pex {
namespace policy {

using namespace std;
namespace fs = boost::filesystem;

/**
 * @brief a representation of a file containing Policy parameter data.  When
 * this class represents a file that actually exists on disk, then it can 
 * determine which format it is in and load its contents into a Policy.
 */
class PolicyFile : public PolicySource {
public:

    //@{
    /**
     * create a Policy file that points a file with given path.  Typically,
     * one need only provide a file path; this class will determine the 
     * type automatically using the default set of supported formats.  If 
     * you want to control what formats (and the particular parsers) to allow,
     * you can provide your own SupportedFormats instance.  To force 
     * interpretation as a particular format, you can a PolicyParserFactory 
     * instance in lieu of a SupportedFormats.  
     * @param filepath       the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param fmts           a SupportedFormats object to use.  An instance 
     *                          encapsulates a configured set of known formats.
     */
    PolicyFile(const string& filepath, 
               const SupportedFormats::Ptr& fmts = defaultFormats);
    PolicyFile(const fs::path& filepath, 
               const SupportedFormats::Ptr& fmts = defaultFormats);
    //@}

    //@{
    /**
     * create a Policy file that points a file with given path.  Typically,
     * one need only provide a file path; this class will determine the 
     * type automatically using the default set of supported formats.  If 
     * you want to control what formats (and the particular parsers) to allow,
     * you can provide your own SupportedFormats instance.  To force 
     * interpretation as a particular format, you can a PolicyParserFactory 
     * instance in lieu of a SupportedFormats.  
     * @param filepath       the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param parserFactory  a PolicyParserFactory implementation to be used
     *                          in parsing the file, assuming a particular 
     *                          format.
     */
    PolicyFile(const string& filepath, 
               const PolicyParserFactory::Ptr& parserFactory);
    PolicyFile(const fs::path& filepath, 
               const PolicyParserFactory::Ptr& parserFactory);
    PolicyFile(const SupportedFormats::Ptr& fmts = defaultFormats);
    //@}

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
     * return the file path as a string
     */
    const string getPath() { return _file.string(); }

    /**
     * return true if the file exists.  
     */
    bool exists() {  return fs::exists(_file);  }

    /**
     * return the name of the format that the data is stored in.  This may 
     * cause the first few records of the source to be read.  In this 
     * implementation, once the format is definitely determined, the format
     * name is cached internally, preventing re-determination on the next 
     * call to this function.  
     * @exception IOError   if an error occurs while reading the first few
     *                      characters of the source stream.
     */
    virtual const string& getFormatName();

    /**
     * load the data from this Policy source into a Policy object
     * @param policy    the policy object to load the data into
     * @exception ParserException  if an error occurs while parsing the data
     * @exception IOError   if an I/O error occurs while reading from the 
     *                       source stream.
     */
    virtual void load(Policy& policy);

    static const string EXT_PAF;   //! the PAF file extension, ".paf"
    static const string EXT_XML;   //! the XML file extension,  ".xml"

    static const boost::regex SPACE_RE;   //! reg-exp for an empty line
    static const boost::regex COMMENT;    //! reg-exp for the start of a comment

    /** 
     * reg-exp for a Policy content identifier, "<?cfg [format] [content] ?>"
     */
    static const boost::regex CONTENTID;  

private:
    const string& cacheName(const string& name) {
        _format = name;
        return _format;
    }

    fs::path _file;
    string _format;
    PolicyParserFactory::Ptr _pfact;

    // inherits SupportedFormats _formats from PolicySource
};


}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_FILE_H


