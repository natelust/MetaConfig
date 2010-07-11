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
 * @file Policy_4.cc
 *
 * This test tests the support for Dictionaries
 */
#include <sstream>
#include <fstream>
#include <iostream>
#include <string>
#include <memory>
#include <stdexcept>
#include "lsst/pex/policy.h"
#include "lsst/pex/policy/Dictionary.h"

using namespace std;
using lsst::pex::policy::Policy;
using lsst::pex::policy::PolicyFile;
using lsst::pex::policy::Dictionary;
using lsst::pex::policy::Definition;
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

    string files[] = { 
        string("examples/EventTransmitter_dict.paf"),
    };
    int nfiles = 1;

    if (argc > 1) {
        files[0] = argv[1];
        nfiles = 1;
    }

    std::auto_ptr<Policy> p;
    std::auto_ptr<Dictionary> d;

    for(int i=0; i < nfiles; i++) {

        d.reset(new Dictionary(files[i]));
        cout << *d << endl;

        Assert(d->exists("definitions"), "dictionary load error");
        const Policy::Ptr& defs = d->getDefinitions();
        Assert(defs->exists("standalone"), "missing parameter definition");

        std::auto_ptr<Definition> defp(d->makeDef("standalone"));
        cout << *defp << endl;
        Assert(defp->getType() == Policy::INT, "definition type error");
        Assert(defp->getMaxOccurs() == 1, "wrong maxOccurs");
        Assert(defp->getMinOccurs() == 0, "wrong minOccurs");

        d->loadPolicyFiles("examples", false);
        p.reset(new Policy(false, *d, "examples"));
        cout << *p << endl;
        Assert(p->getInt("standalone") == 0, "default loading error");

        p.reset(Policy::createPolicy(files[i]));
        cout << *p << endl;
        Assert(p->getInt("standalone") == 0, 
               "Policy factory creation method failed");
    }

}

