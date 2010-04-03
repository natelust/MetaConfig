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
#include "lsst/pex/policy/PolicyString.h"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::PolicyString;

#define Assert(b, m) tattle(b, m, __LINE__)

void tattle(bool mustBeTrue, const string& failureMsg, int line) {
    if (! mustBeTrue) {
        ostringstream msg;
        msg << __FILE__ << ':' << line << ":\n" << failureMsg << ends;
        throw runtime_error(msg.str());
    }
}

int main() {

    string data("#<?cfg paf policy ?>\nint: 7\ndbl: -1.0");
    PolicyString ps(data);
    Policy *p = Policy::createPolicy(ps);
    Assert(p->getInt("int") == 7, "Failed to load data");
    Assert(p->getDouble("dbl") == -1.0, "Failed to load data");
}
