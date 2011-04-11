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
 * @file Policy_1.cc
 *
 * This test tests the basic access and update methods of the Policy class.
 */
#include <iostream>
#include <sstream>
#include <string>
#include <stdexcept>
#include "lsst/pex/policy/DefaultPolicyFile.h"
#include "boost/filesystem.hpp"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::DefaultPolicyFile;
using lsst::pex::policy::TypeError;
using lsst::pex::policy::NameNotFound;

namespace fs = boost::filesystem;

#define Assert(b, m) tattle(b, m, __LINE__)

void tattle(bool mustBeTrue, const string& failureMsg, int line) {
    if (! mustBeTrue) {
        ostringstream msg;
        msg << __FILE__ << ':' << line << ":\n" << failureMsg << ends;
        throw runtime_error(msg.str());
    }
}

int main() {

    fs::path ipath = DefaultPolicyFile::installPathFor("pex_policy");
    cout << "Policy installation directory: " << ipath << endl;
    Assert(fs::exists(ipath), "Policy installation directory does not exist");

    DefaultPolicyFile df("pex_policy", "EventTransmitter_policy.paf", 
                         "examples", true);
    ipath = df.getInstallPath("pex_policy");
    Assert(fs::exists(ipath), "DefaultPolicyFile failed to find product dir: "+
                              ipath.string());

    ipath = df.getPath();
    Assert(fs::exists(ipath), "DefaultPolicyFile failed to find file path: " +
                              ipath.string());

    Policy p(df);
    Assert(p.exists("standalone"), "Failed to load default data");

    // test failures
    try {
        ipath = DefaultPolicyFile::installPathFor("pex_goober");
        Assert(false, "Ignored undefined product name (pex_goober)");
    }
    catch (lsst::pex::exceptions::NotFoundException ex) {
        cout << "Detected missing product" << endl;
    }

    df = DefaultPolicyFile("pex_policy", "EventTransmitter_policy.paf", 
                           "goober", true);
    ipath = df.getPath();
    Assert(! fs::exists(ipath), "Failed to detect missing file: "+
                                ipath.string());
}
