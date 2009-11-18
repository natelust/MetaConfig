/**
 * @file Policy_2.cc
 *
 * This test tests the format-specific parsers for Policies.  
 */
#include <sstream>
#include <fstream>
#include <string>
#include <stdexcept>
#include <list>
#include "lsst/pex/policy/paf/PAFParser.h"
#include "lsst/pex/policy.h"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::paf::PAFParser;
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

    Policy p2;
    PAFParser pp(p2);
    ifstream is("examples/EventTransmitter_policy.paf");

    pp.parse(is);

    cout << "Contents of PAF file:" << endl;
    cout << p2 << endl;

    string dataerror("Incorrect data found for ");
    Assert(p2.getString("receiver.logVerbosity") == "debug", 
           dataerror+"receiver.logVerbosity");
    Assert(p2.getString("transmitter.logVerbosity") == "debug", 
           dataerror+"transmitter.logVerbosity");
    Assert(p2.getString("transmitter.serializationFormat") == "deluxe", 
           dataerror+"transmitter.serializationFormat");
    Assert(p2.getBool("standalone"), dataerror+"standalone");
    Assert(p2.getDouble("threshold") == 4.5, /* parasoft-suppress LsstDm-5-12-1 */
	   dataerror+"threshold");

//     list<string> names;
//     p.paramNames(names);

//     for(list<string>::iterator i=names.begin(); i!=names.end(); ++i) 
//         cout << *i << endl;

}
