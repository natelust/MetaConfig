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
#include "lsst/pex/policy.h"
#include "lsst/pex/policy/DefaultPolicyFile.h"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::DefaultPolicyFile;

#define Assert(b, m) tattle(b, m, __LINE__)

void tattle(bool mustBeTrue, const string& failureMsg, int line) {
    if (! mustBeTrue) {
        ostringstream msg;
        msg << __FILE__ << ':' << line << ":\n" << failureMsg << ends;
        throw runtime_error(msg.str());
    }
}

int main() {

    DefaultPolicyFile df("pex_policy", "CacheManager_dict.paf", 
                         "examples", true);
    Policy::Ptr p(Policy::createPolicy(df, "examples"));
    Assert(p->exists("freeSpaceBuffer"), 
           "Failed to extract top-level defaults from Dictionary");
    Assert(p->exists("itemType.lifetimeFactor"), 
           "Failed to extract sub-policy data from Dictionary");
    Assert(p->getString("status") == "active", 
           "Wrong value for 'status': " + p->getString("status"));

    Policy p2;
    p2.set("status", "disabled");
    p2.mergeDefaults(*p);
    Assert(p2.exists("freeSpaceBuffer"), "Failed to load integer default");
    Assert(p2.exists("itemType.lifetimeFactor"), 
           "Failed to load double default");
    Assert(p2.exists("itemType2.lifetimeFactor"), 
           "Failed to load double default via std file include");
    Assert(p2.exists("itemType3.lifetimeFactor"), 
           "Failed to load double default via dictionaryFile");
    Assert(p2.getString("status") == "disabled", 
           "Wrong value for 'status': " + p2.getString("status"));

}

/*
 * The presence of this function definition can demonstrate a (now-fixed)
 * error stemming from declarartions of template specializations for 
 * Policy::getValueArray<T>().
 *
 */
void foo(lsst::pex::policy::Definition *defn, const Policy& policy, const string& name)
{ 
    policy.getValueArray<double>("bar");
//    defn->validateBasic<double>(name, policy);
}

