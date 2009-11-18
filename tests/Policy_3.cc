/**
 * @file Policy_3.cc
 *
 * This test tests format detection and format-agnostic loading of policy 
 * data.  
 */
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

int main(int argc, char** argv) {

    Policy p;
    string files[] = { 
        string("examples/EventTransmitter_policy.paf"),
        string("examples/pipeline_policy.paf") 
    };
    int nfiles = 2;

    if (argc > 1) {
        files[0] = argv[1];
        nfiles = 1;
    }

    for(int i=0; i < nfiles; i++) {
        PolicyFile pfile(files[i]);
        cout << "Contents of " << pfile.getFormatName() << " file, " 
             << files[i] << endl;

        Policy p(pfile);
        p.loadPolicyFiles("examples", false);
        cout << p << endl;

        if (i==0) {
            Assert(p.getBool("standalone"), "wrong value: standalone");
            Assert(p.getDouble("threshold") == 4.5, /* parasoft-suppress LsstDm-5-12-1 */
                   "wrong value: threshold");
            Assert(p.getInt("offsets") == 313, "wrong value: offsets");
            Assert(p.valueCount("offsets") == 8,
                   "wrong # of values: offsets");
            Assert(p.getString("receiver.logVerbosity") == "debug",
                   "wrong value: receiver.logVerbosity");
            Assert(p.getString("transmitter.logVerbosity") == "debug",
                   "wrong value: transmitter.logVerbosity");
            Assert(p.getString("transmitter.serializationFormat") == "deluxe",
                   "wrong value: transmitter.serializationFormat");
            Assert(p.getString("polish") == "fancy","wrong value: polish");
        }
    }

}
