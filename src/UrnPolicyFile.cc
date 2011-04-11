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
 
/*
 * UrnPolicyFile
 */
#include "lsst/pex/policy/UrnPolicyFile.h"
#include "lsst/pex/exceptions.h"

#include <string>
#include <vector>

namespace lsst {
namespace pex {
namespace policy {

//@cond

using namespace std;

const string UrnPolicyFile::URN_PREFIX("urn:eupspkg:");
const string UrnPolicyFile::URN_PREFIX_ABBREV("@");

/**
 * Remove [@+][urn:eupspkg:].  That is,
 * "@urn:eupspkg:product:repos:file.paf", "urn:eupspkg:product:repos:file.paf",
 * "@@product:repos:file.paf", and "@product:repos:file.paf" all return the same
 * thing, "product:repos:file.paf".
 *
 * Note: pass urn by value because we're going to modify it anyway.
 */
string stripPrefixes(string urn, bool strict) {
    // strip @'s
    int numAts = 0;
    while (urn.length() > 0 && urn.find(UrnPolicyFile::URN_PREFIX_ABBREV) == 0) {
	urn = urn.substr(UrnPolicyFile::URN_PREFIX_ABBREV.length());
	++numAts;
    }

    // strip urn:eupspkg:
    string lowered(urn);
    transform(lowered.begin(), lowered.end(), lowered.begin(), ::tolower);
    bool hasPrefix = (lowered.find(UrnPolicyFile::URN_PREFIX) == 0);
    if (hasPrefix)
	urn = urn.substr(UrnPolicyFile::URN_PREFIX.length());

    // validate, if requested
    if (strict && (numAts > 1 || !hasPrefix))
	throw LSST_EXCEPT(BadNameError, ("URN must start with \"urn:eupspkg:\" or \"@urn:eupspkg:\""));

    return urn;
}

/**
 * Remove prefixes, split at colons, and check that the number of terms in the
 * address is valid.  For example, "@urn:eupspkg:product:repos:file",
 * "@@product:repos:file" and "product:repos:file" all become [product, repos,
 * file].
 * @param urn    the URN to parse and split
 * @param a      components of the URN are push_back()'ed onto this vector
 * @param strict if true, require a urn that starts with "urn:eupspkg:" or
 *               "@urn:eupspkg:".
 */
void splitAndValidate(const string& urn, vector<string>& a, bool strict) {
    // strip prefixes
    string stripped = stripPrefixes(urn, strict);

    // split
    while (true) {
	size_t i = stripped.find(":");
	if (i == string::npos) {
	    if (stripped.length() > 0) a.push_back(stripped);
	    break;
	}
	else {
	    a.push_back(stripped.substr(0, i));
	    stripped = stripped.substr(i + 1);
	}
    }

    // validate
    // - min size is 2 -- product:file
    // - max size is 3 -- product:repos:file
    if (a.size() < 2 || a.size() > 3)
	throw LSST_EXCEPT
	    (BadNameError,
	     "Wrong number of terms in policy file urn \"" + urn + "\".  "
	     + "The expected form is "
	     + "@urn:eupspkg:<product>:[<repository>:]<file> or "
	     + "@@<product>:[<repository>:]<file>.  "
	     + "Is there a typo in the urn?");
}

/**
 * Extract the product name from a URN.  For example,
 *  - @urn:eupspkg:PRODUCT:repos:path/to/file.paf
 *  - @@PRODUCT:repos:path/to/file.paf
 *  - @PRODUCT:path/to/file.paf
 */
string UrnPolicyFile::productNameFromUrn(const string& urn, bool strictUrn) {
    vector<string> split;
    splitAndValidate(urn, split, strictUrn);
    return split[0];
}

/**
 * Extract the local file path from a URN.  For example,
 *  - @urn:eupspkg:product:repos:PATH/TO/FILE.PAF
 *  - @@product:repos:PATH/TO/FILE.PAF
 *  - @product:PATH/TO/FILE.PAF
 */
string UrnPolicyFile::filePathFromUrn(const string& urn, bool strictUrn) {
    vector<string> split;
    splitAndValidate(urn, split, strictUrn);
    return split.back();
}

/**
 * Extract the repository name from a URN, or "" if none.  For example,
 *  - @urn:eupspkg:product:REPOS:path/to/file.paf
 *  - @@product:REPOS:path/to/file.paf
 *  - @product:path/to/file.paf -- no repository, so ""
 */
string UrnPolicyFile::reposFromUrn(const string& urn, bool strictUrn) {
    vector<string> split;
    splitAndValidate(urn, split, strictUrn);
    if (split.size() == 3) return split[1];
    else return "";
}

/**
 * Does `s` look like a URN?  That is, does it start with URN_PREFIX or
 * URN_PREFIX_ABBREV?
 * @param s the string to be tested
 * @param strict if false, "@" will be accepted as a substitute for
 *               "urn:eupspkg:"; if true, urn:eupspkg must be present.
 */
bool UrnPolicyFile::looksLikeUrn(const string& s, bool strict) {
    if (strict) {
	string lc(s);
	transform(lc.begin(), lc.end(), lc.begin(), ::tolower);
	while (lc[0] == '@') lc = lc.substr(1);
	if (lc.find(UrnPolicyFile::URN_PREFIX) != 0) return false;
    }
    const string& stripped = stripPrefixes(s, strict);
    return s.length() != stripped.length() && s.find(":") != s.npos;
}

//@endcond

} // namespace policy
} // namespace pex
} // namespace lsst
