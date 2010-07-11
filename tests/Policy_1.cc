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

int main() {

    Policy p;

    // tests on an empty policy
    Assert(! p.exists("foo"), "empty existence test failed");
    Assert(p.valueCount("foo.bar") == 0, "empty valueCount test failed");
    Assert(! p.isInt("foo"), "empty existence type test failed");

    try {
        p.getTypeInfo("foo");
        Assert(false, "type info available for non-existent value");
    }
    catch (NameNotFound&) { }

    // disallow null values
    try {
        const char *nothing = NULL;
        p.set("foo", nothing);
        Assert(false, "no error when setting value to NULL");
    }
    catch (lsst::pex::exceptions::InvalidParameterException e) { }

    p.set("doall", "true");

    // non-existence tests on a non-empty policy
    Assert(! p.exists("foo"), "non-empty non-existence test failed");
    Assert(p.valueCount("foo.bar") == 0, "empty valueCount test failed");
    Assert(! p.isInt("foo"), "non-empty non-existence type test failed");

    try {
        p.getTypeInfo("foo");
        Assert(false, "type info available for non-existent value");
    }
    catch (NameNotFound& e) { 
        cout << "foo confirmed not to exist: " << e.what() << endl;
    }

    // existence tests
    Assert(p.exists("doall"), "non-empty existence test failed");
    Assert(p.valueCount("doall") == 1, "single valueCount test failed");

    // test out our newly added parameter
    try {  p.getInt("doall"); }
    catch (TypeError& e) { 
        cout << "doall confirmed not an Int: " << e.what() << endl;
    }
    try {  p.getDoubleArray("doall"); }
    catch (TypeError&) { }

    cout << "doall: " << p.getString("doall") << endl;
    Assert(p.getString("doall") == "true", "top-level getString failed");
    p.set("doall", "duh");
    cout << "doall: " << p.getString("doall") << endl;
    Assert(p.getString("doall") == "duh", "top-level reset failed");

    // test that we can access this property as an array
    vector<std::string> ary = p.getStringArray("doall");
    Assert(ary.size() == 1, "scalar property has more than one value");
    Assert(ary[0] == "duh", "scalar access via array failed");

    p.add("doall", "never");
    cout << "doall: " << p.getString("doall") << endl;

    Assert(p.valueCount("doall") == 2, "2-elem. valueCount test failed");

    // make sure that we can access an array as a scalar properly
    Assert(p.getString("doall") == "never", "top-level add failed");

    // test array access
    ary = p.getStringArray("doall");
    cout << "doall (" << ary.size() << "):";
    for(vector<std::string>::iterator pi=ary.begin();pi!=ary.end();++pi) 
        cout << ' ' << *pi;
    cout << endl;
    Assert(ary.size() == 2, "scalar property has wrong number of values");
    Assert(ary[0] == "duh", "scalar access via (2-el) array failed");
    Assert(ary.back() == "never", "scalar access via (2-el) array failed");

    // test type support
    p.set("pint", 5);
    Assert(p.getInt("pint") == 5, "support for type int failed");
    p.set("pdbl", 5.1);
    Assert(abs(p.getDouble("pdbl") - 5.1) < 0.0000001, 
           "support for type double failed");
    p.set("ptrue", true);
    Assert(p.getBool("ptrue"), "support for boolean true failed");
    p.set("pfalse", false);
    Assert(! p.getBool("pfalse"), "support for boolean false failed");

    // test PolicyFile type
    string pfile("test.paf");
    p.add("test", Policy::FilePtr(new PolicyFile(pfile)));
    Assert(p.getValueType("test") == Policy::FILE, 
           "Wrong ValueType for PolicyFile");
    Assert(p.isFile("test"), "PolicyFile's type not recognized");
    Policy::FilePtr pf = p.getFile("test");
    Assert(pf->getPath() == pfile, "Corrupted PolicyFile name");
        
    // test hierarchical access
    string standalone("Dictionary.definition.standalone");
    string minOccurs = standalone+".minOccurs";
    p.set(minOccurs, 1);
    cout << minOccurs << ": " << p.getInt(minOccurs) << endl;
    Assert(p.getInt(minOccurs) == 1, "hierarchical property set failed");
    Assert(p.exists(minOccurs), "hierarchical existence test failed");
    Assert(p.valueCount(minOccurs) == 1,"hierarchical valueCount test failed");

    Policy::Ptr sp = p.getPolicy(standalone);
    sp->set("type", "int");
    cout <<  standalone+".type"<< ": " << p.getString(standalone+".type") 
         << endl;
    Assert(p.getString(standalone+".type") == "int", "encapsulated set failed");
    sp->set("required", false);
    cout << standalone+".required"<< ": " << p.getBool(standalone+".required") 
         << endl;
    Assert(!p.getBool(standalone+".required"), "boolean set failed");

    sp->add("score", 3.4);
    cout <<  standalone+".score"<< ": " << p.getDouble(standalone+".score") 
         << endl;
    Assert(sp->getDouble("score") - 3.4 < 0.0000000000001, 
           "double type set failed");

    // list names
    list<string> names;
    int npol = p.policyNames(names);
    int nprm = p.paramNames(names);
    int nfile = p.fileNames(names);
    int nall = p.names(names);
    cout << "policy now has " << nall << " names (" << npol << " policies, "
         << nprm << " parameters):" << endl;
    for(list<string>::iterator i=names.begin(); i!=names.end(); ++i) 
        cout << "   " << *i << ": " << p.getTypeName(*i) << endl;
    Assert(npol + nfile + nprm == nall, "name listing failed");

    // show Types
    cout << "Types:" << endl;
    cout << "\tdoall: " << p.getTypeInfo("doall").name() << endl;
    cout << "\tminOccurs: " << sp->getTypeInfo("minOccurs").name() << endl;
    cout << "\tscore: " << sp->getTypeInfo("score").name() << endl;
    cout << "\trequired: " << sp->getTypeInfo("required").name() << endl;
    cout << "\tstandalone: " 
         << p.getTypeInfo("Dictionary.definition.standalone").name() << endl;
    cout << "\ttest: " << p.getTypeInfo("test").name() << endl;

    // Test shallow and deep copies
    Policy shallow(p);
    const Policy& cp = p;
    Policy deep(cp);
    sp->add("score", 1.355);
    double deepscore = deep.getDouble(standalone + ".score");
    double shallowscore = shallow.getDouble(standalone + ".score");
    cout << "shallow copy score: " << shallowscore << endl;
    cout << "deep copy score: " << deepscore << endl;
    Assert(abs(shallowscore - 1.355) < 0.000000001,
           "shallow copy failure: score should = 1.355");
    Assert(abs(deepscore - 3.4) < 0.000000001,
           "deep copy failure: score should = 3.4");
}
