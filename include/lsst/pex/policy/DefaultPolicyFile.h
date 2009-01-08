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

#ifndef LSST_PEX_POLICY_DEFAULTPOLICYFILE_H
#define LSST_PEX_POLICY_DEFAULTPOLICYFILE_H

#include "lsst/pex/policy/PolicyFile.h"

namespace lsst {
namespace pex {
namespace policy {

/**
 * @brief a representation of a default Policy file that is stored as a 
 * file in the installation directory of an LSST product.  An instance
 * is constructed from a package name and a relative file path.  To 
 * construct the true path to the file, the constructor looks for an 
 * environment variable of the form, PACKAGENAME_DIR (where PACKAGENAME 
 * is the given package name converted to all upper case) which names the 
 * directory where the product is installed.  The relative file path is 
 * location of the file within this directory.  
 *
 * The policy file can reference other files; these will be automatically 
 * opened and loaded when load() is called.  The paths stored in the ...
 */
class DefaultPolicyFile : public PolicyFile {
public:

    /**
     * define a default policy file
     */
    DefaultPolicyFile(const char const* packageName, std::string filepath) 
        : PolicyFile(makeFullPath(packageName, filepath)) 
    { }

    /**
     * construct the full file path to a default policy file found in 
     */
    static fs::path makeFullPath(const char const* packageName, 
                                 std::string filepath);

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

};

}}}  // end namespace lsst::pex::policy



#endif
