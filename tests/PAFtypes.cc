/**
 * @file PAFtypes.cc
 *
 * This test exercises PAF parsing of all variations of expressing values
 */

#include <cmath>
#include <sstream>
#include <fstream>
#include <string>
#include <stdexcept>
#include <list>
#include "lsst/pex/policy/paf/PAFParser.h"
#include "lsst/pex/policy.h"
#include "lsst/pex/policy/PolicyFile.h"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::PolicyFile;
using lsst::pex::policy::TypeError;
using lsst::pex::policy::NameNotFound;

#define Assert(b, m) tattle(b, m, __LINE__)

void tattle(bool mustBeTrue, const string& failureMsg, int line) {
    if (! mustBeTrue) {
        ostringstream msg;
        msg << __FILE__ << ':' << line << ":\n" << failureMsg << ends;
        throw runtime_error(msg.str());
    }
}

#define TYPETEST(mustBeTrue, which, expected, found) \
    if (! mustBeTrue) {                              \
        ostringstream msg;                           \
        msg << __FILE__ << ':' << __LINE__ << ":\n"      \
            << "Value number " << which << " !=  "   \
            << expected << ": " << found << ends;    \
        throw runtime_error(msg.str());              \
    } 

#define TYPED_VALUE_IS(ary, item, val)  TYPETEST((ary[item] == val), item, val, ary[item])
#define TYPED_VALUE_NEAR(ary, item, val)  TYPETEST((fabs(ary[item] - val) < 1.0e-14), item, val, ary[item])

int main(int argc, char** argv) {

    Policy p = Policy("examples/types.paf");

    Policy::IntArray vi = p.getIntArray("int");
    int i=0;
    TYPED_VALUE_IS(vi, i++, -11);
    TYPED_VALUE_IS(vi, i++,   0);
    TYPED_VALUE_IS(vi, i++,  +3);
    TYPED_VALUE_IS(vi, i++,  42);
    TYPED_VALUE_IS(vi, i++, -11);
    TYPED_VALUE_IS(vi, i++,   0);
    TYPED_VALUE_IS(vi, i++,  +3);
    TYPED_VALUE_IS(vi, i++,  42);
    TYPED_VALUE_IS(vi, i++,   0);
    TYPED_VALUE_IS(vi, i++,   0);

    Assert(p.getBool("true"), "'true' != true");
    Assert(! p.getBool("false"), "'false' != false");

    Policy::DoubleArray vd = p.getDoubleArray("dbl");
    i=0;
    TYPED_VALUE_NEAR(vd, i++,    -1.0);
    TYPED_VALUE_NEAR(vd, i++,   -65.78);
    TYPED_VALUE_NEAR(vd, i++,   -14.0);
    TYPED_VALUE_NEAR(vd, i++,    -0.12);
    TYPED_VALUE_NEAR(vd, i++,    -0.12);
    TYPED_VALUE_NEAR(vd, i++,     1.0);
    TYPED_VALUE_NEAR(vd, i++,    65.78);
    TYPED_VALUE_NEAR(vd, i++,    14.0);
    TYPED_VALUE_NEAR(vd, i++,     0.12);
    TYPED_VALUE_NEAR(vd, i++,     0.12);
    TYPED_VALUE_NEAR(vd, i++,     1.0);
    TYPED_VALUE_NEAR(vd, i++,    65.78);
    TYPED_VALUE_NEAR(vd, i++,    14.0);
    TYPED_VALUE_NEAR(vd, i++,     0.12);
    TYPED_VALUE_NEAR(vd, i++,     0.12);
    TYPED_VALUE_NEAR(vd, i++,   -1.0e10);
    TYPED_VALUE_NEAR(vd, i++, -65.78e6);
    TYPED_VALUE_NEAR(vd, i++,  -14.0e-3);
    TYPED_VALUE_NEAR(vd, i++,  -0.12e14);
    TYPED_VALUE_NEAR(vd, i++,  -0.12e-11);

    Policy::StringArray vs = p.getStringArray("str");
    i=0;
    TYPED_VALUE_IS(vs, i++, "word");
    TYPED_VALUE_IS(vs, i++, "two words");
    TYPED_VALUE_IS(vs, i++, "quoted ' words");
    TYPED_VALUE_IS(vs, i++, "quoted \" words");
    TYPED_VALUE_IS(vs, i++, "a very long, multi-line description");
    TYPED_VALUE_IS(vs, i++, "happy");
    TYPED_VALUE_IS(vs, i++, "birthday");

    Policy::FilePtrArray vf = p.getFileArray("file");
    Policy::StringArray vfs;
    for(Policy::FilePtrArray::iterator vfi=vf.begin(); vfi!=vf.end(); ++vfi) 
        vfs.push_back((*vfi)->getPath());
    i=0;
    TYPED_VALUE_IS(vfs, i++, "EventTransmitter_policy.paf");
    TYPED_VALUE_IS(vfs, i++, "CacheManager_dict.paf");

    Policy::PolicyPtrArray vp = p.getPolicyArray("pol");
    Assert(vp[0]->getInt("int") == 1, "policy int not 1");
    Assert(fabs(vp[0]->getDouble("dbl") - 3.0e-4) < 1.0e-14, 
           "policy dbl not 3.0e-4");

    Policy::IntArray vi2 = p.getIntArray("pol.int");
    TYPED_VALUE_IS(vi2, 0, 1); 
    TYPED_VALUE_IS(vi2, 1, 2); 
    Policy::DoubleArray vd2 = p.getDoubleArray("pol.dbl");
    TYPED_VALUE_NEAR(vd2, 0, 0.0003); 
    TYPED_VALUE_NEAR(vd2, 1, -5.2); 

    Assert(p.getString("pol.pol.label") == "hank", 
           "pol.pol.label != 'hank': " + p.getString("pol.pol.label"));

}
