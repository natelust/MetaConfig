// -*- lsst-c++ -*-

/* 
 * LSST Data Management System
 * Copyright 2008, 2009, 2010 LSST Corporation.
 * 
 * This product includes software developed by the
 * LSST Project (http://www.lsst.org/).
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the LSST License Statement and 
 * the GNU General Public License along with this program.  If not, 
 * see <http://www.lsstcorp.org/LegalNotices/>.
 */
 
/**
 * @file PolicyFile.h
 * 
 * @ingroup pex
 *
 * @brief definition of the PolicyFile class
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
#include "lsst/daf/base/Persistable.h"

namespace lsst {
namespace pex {
namespace policy {

namespace fs = boost::filesystem;
namespace dafBase = lsst::daf::base;

/**
 * @brief a representation of a file containing Policy parameter data.  
 * 
 * When this class represents a file that actually exists on disk, then it 
 * can determine which format it is in and load its contents into a Policy.
 */
class PolicyFile : public PolicySource, public dafBase::Persistable {
public:

    //@{
    /**
     * create a Policy file that points a file with given path.  Typically,
     * one need only provide a file path; this class will determine the 
     * type automatically using the default set of supported formats.  If 
     * you want to control what formats (and the particular parsers) to allow,
     * you can provide your own SupportedFormats instance.  To force 
     * interpretation as a particular format, you can a PolicyParserFactory 
     * instance in lieu of a SupportedFormats (see 
     * PolicyFile(const std::string&, const SupportedFormats::Ptr&) ).  
     * @param filepath       the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param fmts           a SupportedFormats object to use.  An instance 
     *                          encapsulates a configured set of known formats.
     */
    explicit PolicyFile(const std::string& filepath, 
                        const SupportedFormats::Ptr& fmts = defaultFormats);
    explicit PolicyFile(const char *filepath, 
                        const SupportedFormats::Ptr& fmts = defaultFormats);
    explicit PolicyFile(const fs::path& filepath, 
                        const SupportedFormats::Ptr& fmts = defaultFormats);
    //@}

    //@{
    /**
     * create a Policy file that points a file with given path.  These 
     * constructors allow you to force interpretation as a 
     * particular format by passing in the PolicyParserFactory to use.
     * @param filepath       the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param parserFactory  a PolicyParserFactory implementation to be used
     *                          in parsing the file, assuming a particular 
     *                          format.
     */
    PolicyFile(const std::string& filepath, 
               const PolicyParserFactory::Ptr& parserFactory);
    PolicyFile(const fs::path& filepath, 
               const PolicyParserFactory::Ptr& parserFactory);
    //@}

    //@{
    /**
     * create a Policy file that points a file with given path in a 
     * policy file repository.  Typically,
     * one need only provide a file path; this class will determine the 
     * type automatically using the default set of supported formats.  If 
     * you want to control what formats (and the particular parsers) to allow,
     * you can provide your own SupportedFormats instance.  To force 
     * interpretation as a particular format, you can a PolicyParserFactory 
     * instance in lieu of a SupportedFormats (see 
     * PolicyFile(const std::string&, const SupportedFormats::Ptr&) ).  
     * @param filepath       the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param reposDir       the policy repository directory to assume.  If 
     *                          \c filepath is a relative path, then the
     *                          full path to the file will be relative to 
     *                          this repository directory.  
     * @param fmts           a SupportedFormats object to use.  An instance 
     *                          encapsulates a configured set of known formats.
     */
    PolicyFile(const std::string& filepath, const fs::path& reposDir,
               const SupportedFormats::Ptr& fmts = defaultFormats);
    PolicyFile(const fs::path& filepath, const fs::path& reposDir,
               const SupportedFormats::Ptr& fmts = defaultFormats);
    //@}

    //@{
    /**
     * create a Policy file that points a file with given path in a 
     * policy file repository.  These 
     * constructors allow you to force interpretation as a 
     * particular format by passing in the PolicyParserFactory to use.
     * @param filepath       the path to the file, either as a string or a
     *                          boost::filesystem::path instance
     * @param reposDir       the policy repository directory to assume.  If 
     *                          \c filepath is a relative path, then the
     *                          full path to the file will be relative to 
     *                          this repository directory.  
     * @param parserFactory  a PolicyParserFactory implementation to be used
     *                          in parsing the file, assuming a particular 
     *                          format.
     */
    PolicyFile(const std::string& filepath, const fs::path& reposDir,
               const PolicyParserFactory::Ptr& parserFactory);
    PolicyFile(const fs::path& filepath, const fs::path& reposDir,
               const PolicyParserFactory::Ptr& parserFactory);
    //@}

    /**
     * create a "null" Policy file that points to an unspecified file.  
     * @param fmts           a SupportedFormats object to use.  An instance 
     *                          encapsulates a configured set of known formats.
     */
    PolicyFile(const SupportedFormats::Ptr& fmts = defaultFormats);


//     /*
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
    const std::string getPath() const { return _file.string(); }

    /**
     * return true if the file exists.  
     */
    bool exists() const {  return fs::exists(_file);  }

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
        return const_cast<PolicyFile*>(this)->getFormatName();
    }

    //@{
    /**
     * load the data from this Policy source into a Policy object
     * @param policy    the policy object to load the data into
     * @exception ParserException  if an error occurs while parsing the data
     * @exception IOError   if an I/O error occurs while reading from the 
     *                       source stream.
     */
    virtual void load(Policy& policy) const;
    virtual void load(Policy& policy) {
	((const PolicyFile*) this)->load(policy); // delegate to const version
    }
    //@}

    static const std::string EXT_PAF;   //! the PAF file extension, ".paf"
    static const std::string EXT_XML;   //! the XML file extension,  ".xml"

    static const boost::regex SPACE_RE;   //! reg-exp for an empty line
    static const boost::regex COMMENT;    //! reg-exp for the start of a comment

    /** 
     * reg-exp for a Policy content identifier, "<?cfg [format] [content] ?>"
     */
    static const boost::regex CONTENTID;  

protected:
    /**
     * the path to the underlying policy file
     */
    fs::path _file;

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

#endif // LSST_PEX_POLICY_FILE_H


