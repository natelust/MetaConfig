/**
 * \file DefaultPolicyFile.cc
 */
#include "lsst/pex/policy/DefaultPolicyFile.h"
#include "lsst/pex/exceptions.h"

#include <algorithm>
#include <cctype>
#include <functional>

namespace pexExcept = lsst::pex::exceptions;

namespace lsst {
namespace pex {
namespace policy {

DefaultPolicyFile::DefaultPolicyFile(const char* const productName, 
                                     const std::string& filepath,
                                     const std::string& repos,
                                     bool strict)
    : PolicyFile(), _repos(), _strict(strict)
{ 
    _repos = getInstallPath(productName);
    if (repos.length() > 0) _repos /= repos;
    _file = _repos / filepath;
}

fs::path DefaultPolicyFile::getInstallPath(const char* const productName) {
    return DefaultPolicyFile::installPathFor(productName);
}

/*
 * return the file path to the installation directory of a given
 * named product.  The installation directory will be taken from 
 * the value of an environment variable PRODUCTNAME_DIR where 
 * PRODUCTNAME is the given name of the product with all letters 
 * converted to upper case.  
 * @exception lsst::pex::exception::NotFoundException  if the 
 *    environement variable is not defined.
 */
fs::path DefaultPolicyFile::installPathFor(const char* const productName) {
    std::string productName_DIR(productName);

    // transform to upper case
    std::transform(productName_DIR.begin(), productName_DIR.end(),
                   productName_DIR.begin(), 
                   std::ptr_fun<int, int>( std::toupper ));

    // append _DIR
    productName_DIR += "_DIR";

    // get installation directory from environment
    const char *ipath = getenv(productName_DIR.c_str());
    if (ipath == 0) 
        throw LSST_EXCEPT(pexExcept::NotFoundException, 
			  productName_DIR + ": environment variable not set");

    return fs::path(ipath);
}

/*
 * load the data from this Policy source into a Policy object.  This
 * implementation will automatically de-reference any file include
 * directives in the policy file.  
 * @param policy    the policy object to load the data into
 * @exception ParserException  if an error occurs while parsing the data
 * @exception IOError   if an I/O error occurs while reading from the 
 *                       source stream.
 */
void DefaultPolicyFile::load(Policy& policy) const {
    PolicyFile::load(policy);
    policy.loadPolicyFiles(_repos, _strict);
}

}}}  // end namespace lsst::pex::policy
