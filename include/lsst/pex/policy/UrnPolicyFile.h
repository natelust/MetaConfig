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
 * @file UrnPolicyFile.h
 * 
 * @ingroup pex
 *
 * @brief the definition of the UrnPolicyFile class
 * 
 * @author Bill Baker
 */

#ifndef LSST_PEX_POLICY_URNPOLICYFILE_H
#define LSST_PEX_POLICY_URNPOLICYFILE_H

#include "lsst/pex/policy/DefaultPolicyFile.h"

namespace fs = boost::filesystem;

namespace lsst {
namespace pex {
namespace policy {

/**
 * @brief A Policy file in the installation directory of an LSST product,
 * referred to using a URN.
 *
 * For use of URN references in PAF-formatted policy files, see \ref pagePAF
 * "Policy Authoring Format".
 *
 * The syntax is urn:eupspkg:[PRODUCT_NAME][:REPOSITORY]:PATH, although
 * "urn:eupspkg:" may optionally be abbreviated with "@".  PRODUCT_NAME is the
 * name of an LSST product (see DefaultPolicyFile for more details on LSST
 * product installation dirs), and REPOSITORY is a subdirectory, which other
 * references within the Policy will be relative to (see Policy for more details
 * on repositories).
 *
 * For example:
 *  - \@urn:eupspkg:some_product:some/repos:local/path/to/file.paf
 *  - \@\@some_product:some/repos:local/path/to/file.paf
 *  - \@some_product:some/repos:local/path/to/file.paf
 *  - \@some_product:local/path/to/file.paf
 *  - some_product:local/path/to/file.paf
 *
 * Caveat: Only supports Dictionary's "DictionaryFile" directive if the value is
 * prefixed like a normal URN reference with "@urn:eupspkg:" or "@@".
 */
class UrnPolicyFile : public DefaultPolicyFile {
public:

    /**
     * Construct a new policy file reference from a URN.
     * Basically, the only required element is a colon, separating the product
     * directory from the local path.
     * @param urn The URN of the policy file.
     *            A prefix such as "urn:eupspkg:" or "@" is optional.
     * @param strictUrn if true, the URN must strictly begin with
     *            "@urn:eupspkg:" or "urn:eupspkg:".
     * @param strictLoads if true (default), load() will throw an exception if it
     *            encounters recoverable parsing errors in the underlying file
     *            (or any of the files it references).  Otherwise, the loaded
     *            Policy will be incomplete.  This is identical to the strict
     *            argument to Policy's loadPolicyFiles().
     */
    explicit UrnPolicyFile(const std::string& urn,
			   bool strictUrn=false, bool strictLoads=true)
	// TODO: oops, this is a segfault waiting to happen -- pass a string instead?
	: DefaultPolicyFile(productNameFromUrn(urn, strictUrn).c_str(),
			    filePathFromUrn(urn, strictUrn),
			    reposFromUrn(urn, strictUrn),
			    strictLoads),
	_urn(urn) {}

    /**
     * Extract the product name from a URN.  For example,
     *  - \@urn:eupspkg:PRODUCT:repos:path/to/file.paf
     *  - \@\@PRODUCT:repos:path/to/file.paf
     *  - \@PRODUCT:path/to/file.paf
     */
    static std::string productNameFromUrn(const std::string& urn,
					  bool strictUrn=false);

    /**
     * Extract the local file path from a URN.  For example,
     *  - "@urn:eupspkg:product:repos:PATH/TO/FILE.PAF"
     *  - "@@product:repos:PATH/TO/FILE.PAF"
     *  - "@product:PATH/TO/FILE.PAF"
     */
    static std::string filePathFromUrn(const std::string& urn,
				       bool strictUrn=false);

    /**
     * Extract the repository name from a URN, or "" if none.  For example,
     *  - "@urn:eupspkg:product:REPOS:path/to/file.paf"
     *  - "@@product:REPOS:path/to/file.paf"
     *  - "@product:path/to/file.paf" -- no repository, returns ""
     */
    static std::string reposFromUrn(const std::string& urn, 
				    bool strictUrn=false);

    //@{
    /**
     * The prefix that a Policy URN starts with.  May be abbreviated as "@".
     */
    static const std::string URN_PREFIX; // "urn:eupspkg:";
    static const std::string URN_PREFIX_ABBREV; // "@";
    //@}


    /**
     * Does `s` look like a URN?  That is, does it start with URN_PREFIX or
     * URN_PREFIX_ABBREV?
     * @param s the string to be tested
     * @param strict if false, "@" will be accepted as a substitute for
     *               "urn:eupspkg:"; if true, urn:eupspkg must be present.
     */
    static bool looksLikeUrn(const std::string& s, bool strict=false);

private:
    const std::string _urn;
};

}}} // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_URNPOLICYFILE_H
