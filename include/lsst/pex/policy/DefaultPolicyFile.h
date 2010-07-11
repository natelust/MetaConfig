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
 * @file DefaultPolicyFile.h
 * 
 * @ingroup pex
 *
 * @brief the definition of the DefaultPolicyFile class
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_DEFAULTPOLICYFILE_H
#define LSST_PEX_POLICY_DEFAULTPOLICYFILE_H

#include "lsst/pex/policy/PolicyFile.h"

namespace fs = boost::filesystem;

namespace lsst {
namespace pex {
namespace policy {

/**
 * @brief a representation of a default Policy file that is stored as a 
 * file in the installation directory of an LSST product.  
 *
 * An instance is constructed from a product name, a relative path 
 * to a subdirectory representing a policy repository within the installed 
 * package, and a relative file path.  To construct the full path to the 
 * file, the constructor looks for an environment variable of the form, 
 * PRODUCTNAME_DIR (where PRODUCTNAME is the given package name converted 
 * to all upper case) which names the directory where the product is 
 * installed.  The full path, then, is the product installation directory
 * concatonated with the repository directory, followed by the file path.
 *
 * The policy file can reference other files; these will be automatically 
 * opened and loaded when load() is called.  The paths stored in the policy 
 * files must be relative to the repository subdirectory within the product
 * installation directory.  
 *
 * This class is the recommended PolicySource type to return in the 
 * PolicyConfigured interface's getDefaultPolicySource().  
 *
 * This class can be subclassed to provide a different implementation of 
 * determining the installation directory by overriding getInstallPath().
 */
class DefaultPolicyFile : public PolicyFile {
public:

    /**
     * define a default policy file
     * @param productName    the name of the product that the default 
     *                         policy is installed as part of
     * @param filepath       the relative pathname to the policy file.  
     * @param repos          the subdirectory with the product's install
     *                         directory where policy files are stored.
     *                         If an empty string (default), the filepath
     *                         argument is relative to the installation
     *                         directory.
     * @param strict         if true (default), load() will throw an exception
     *                         if it encounters recoverable parsing errors in
     *                         the underlying file (or any of the files it
     *                         references).  Otherwise, the loaded Policy will
     *                         be incomplete.  This is identical to the strict
     *                         argument to Policy's loadPolicyFiles().  
     */
    DefaultPolicyFile(const char* const productName, 
                      const std::string& filepath,
                      const std::string& repos="",
                      bool strict=true);

    /**
     * return the file path to the installation directory of a given
     * named product.  This implementation uses the implementation 
     * provided by DefaultPolicyFile::installPathFor().
     * @exception lsst::pex::exception::NotFoundException  if the 
     *    environement variable is not defined.
     */
    virtual fs::path getInstallPath(const char* const productName);

    /**
     * return the full file path to the repository directory where this
     * file will found.  
     */
    const fs::path& getRepositoryPath() const { return _repos; }

    /**
     * return the file path to the installation directory of a given
     * named product.  In this implementation, the installation directory 
     * will be taken from the value of an environment variable 
     * PRODUCTNAME_DIR where PRODUCTNAME is the given name of the product 
     * with all letters converted to upper case.  
     */
    static fs::path installPathFor(const char* const productName);
        

    /**
     * load the data from this Policy source into a Policy object.  This
     * implementation will automatically de-reference any file include
     * directives in the policy file.  
     * @param policy    the policy object to load the data into
     * @exception ParserException  if an error occurs while parsing the data
     * @exception IOError   if an I/O error occurs while reading from the 
     *                       source stream.
     */
    virtual void load(Policy& policy) const;

private:
    fs::path _repos;
    bool _strict;
};

}}}  // end namespace lsst::pex::policy



#endif
