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
#include <fstream>
#include <string>
#include <stdexcept>
#include "lsst/pex/policy.h"
#include "lsst/pex/policy/paf/PAFWriter.h"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::paf::PAFWriter;

#define Assert(b, m) tattle(b, m, __LINE__)

void tattle(bool mustBeTrue, const string& failureMsg, int line) {
    if (! mustBeTrue) {
        ostringstream msg;
        msg << __FILE__ << ':' << line << ":\n" << failureMsg << ends;
        throw runtime_error(msg.str());
    }
}

int main() {

    Policy p;
    p.set("foo", "bar");
    Assert(p.getString("foo") == "bar", "Failed to set string item");

    try {
        PAFWriter w("/tmp");
        Assert(false, "Write to directory failed to raise exception");
    }
    catch (std::ios_base::failure ex) { }

    try {
        PAFWriter w("/etc/motd");
        Assert(false, "Write to file without permission failed to raise exception");
    }
    catch (std::ios_base::failure ex) { }


}
