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
    Policy::Ptr p(Policy::createPolicy(df));
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
    Assert(p2.getString("status") == "disabled", 
           "Wrong value for 'status': " + p2.getString("status"));

}
