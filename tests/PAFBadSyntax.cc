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
 * @file PAFBadSyntax.cc
 *
 * This test exercises PAF parsing of all variations of expressing values
 */

#include <stdexcept>
#include "lsst/pex/policy.h"

using namespace std;
using lsst::pex::policy::Policy;

#define Assert(b, m) tattle(b, m, __LINE__)

void tattle(bool mustBeTrue, const string& failureMsg, int line) {
    if (! mustBeTrue) {
        ostringstream msg;
        msg << __FILE__ << ':' << line << ":\n" << failureMsg << ends;
        throw runtime_error(msg.str());
    }
}

int main(int argc, char** argv) {

    try {
        Policy p = Policy("tests/PAFBadSyntax_1.paf");
        throw runtime_error("Failed to detect bad PAF syntax (comma delimiters)");
    }
    catch (lsst::pex::policy::FormatSyntaxError e) {   }

    try {
        Policy p = Policy("tests/PAFBadSyntax_2.paf");
        throw runtime_error("Failed to detect bad PAF syntax (parameter w/spaces)");
    }
    catch (lsst::pex::policy::FormatSyntaxError e) {   }

    try {
        Policy p = Policy("tests/PAFBadSyntax_3.paf");
        throw runtime_error("Failed to detect bad PAF syntax (bad sub-policy)");
    }
    catch (lsst::pex::policy::FormatSyntaxError e) {   }

    try {
        Policy p = Policy("tests/PAFBadSyntax_4.paf");
        throw runtime_error("Failed to detect bad PAF syntax (mixed types)");
    }
    catch (lsst::pex::policy::FormatSyntaxError e) {   }

    try {
        Policy p = Policy("tests/PAFBadSyntax_4.paf");
        throw runtime_error("Failed to detect bad PAF syntax (bad sub-policy)");
    }
    catch (lsst::pex::policy::FormatSyntaxError e) {   }
}
