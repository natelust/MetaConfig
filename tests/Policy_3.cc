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
#include "lsst/mwi/policy/paf/PAFParser.h"
#include "lsst/mwi/policy/Policy.h"
#include "lsst/mwi/policy/PolicyFile.h"

using namespace std;
using lsst::mwi::policy::Policy;
using lsst::mwi::policy::PolicyFile;
using lsst::mwi::policy::TypeError;
using lsst::mwi::policy::NameNotFound;

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
        string("examples/policies/EventTranmitter_policy.json"),
        string("examples/policies/EventTranmitter_policy.paf"),
        string("examples/policies/pipeline_policy.paf") 
    };
    int nfiles = 3;

    if (argc > 1) {
        files[0] = argv[1];
        nfiles = 1;
    }

    for(int i=0; i < nfiles; i++) {
        PolicyFile pfile(files[i]);
        cout << "Contents of " << pfile.getFormatName() << " file, " 
             << files[i] << endl;

        Policy p(pfile);
        p.loadPolicyFiles("examples/policies");
        cout << p << endl;
    }

}
