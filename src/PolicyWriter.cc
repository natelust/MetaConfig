/**
 * \file PolicyWriter.cc
 */
#include "lsst/pex/policy/PolicyWriter.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyFile.h"

#include <fstream>

namespace lsst {
namespace pex {
namespace policy {

using lsst::daf::base::PropertySet;
using lsst::daf::base::Persistable;

/*
 * create a writer attached to an output stream
 * @param out     the output stream to write data to
 */
PolicyWriter::PolicyWriter(std::ostream *out) : _nullos(0), _os(out) {
    if (! out) {
        _nullos = new std::ofstream(NULL_FILENAME);
        _os = _nullos;
    }
}

PolicyWriter::~PolicyWriter() {
    if (_nullos) delete _nullos;
}

/*
 * write the contents of a policy the attached stream.  Each top-level
 * parameter will be recursively printed.
 * @param policy     the policy data to write
 */
void PolicyWriter::write(const Policy& policy, bool doDecl) {
    if (doDecl) 
        (*_os) << "#<?cfg paf policy ?>" << std::endl;

    Policy::StringArray names = policy.names(true);
    Policy::StringArray::const_iterator ni;
    for(ni=names.begin(); ni != names.end(); ++ni) {
        try {
            const std::type_info& tp = policy.typeOf(*ni);
            if (tp == typeid(bool)) {
                write(*ni, policy.getBoolArray(*ni));
            }
            else if (tp == typeid(int)) {
                write(*ni, policy.getIntArray(*ni));
            }
            else if (tp == typeid(double)) {
                write(*ni, policy.getDoubleArray(*ni));
            }
            else if (tp == typeid(std::string)) {
                write(*ni, policy.getStringArray(*ni));
            }
            else if (tp == typeid(PropertySet::Ptr)) {
                write(*ni, policy.getPolicyArray(*ni));
            }
            else if (tp == typeid(Persistable::Ptr)) {
                write(*ni, policy.getFileArray(*ni));
            }
            else {
                throw LSST_EXCEPT(pexExcept::LogicErrorException, "Policy: unexpected type for name=" + *ni);
            }
        }
        catch (NameNotFound&) {
            // shouldn't happen
            write(*ni, "<missing data>");
        }
    }

}

#define PW_WRITE_PRIMITIVE(vtype) \
void PolicyWriter::write(const std::string& name, vtype value) {    \
    std::vector<vtype> vals;                                        \
    vals.push_back(value); \
    write(name, vals); \
}

PW_WRITE_PRIMITIVE(int)
PW_WRITE_PRIMITIVE(double)
PW_WRITE_PRIMITIVE(bool)

void PolicyWriter::write(const std::string& name, const std::string& value) {
    std::vector<std::string> vals; 
    vals.push_back(value); 
    write(name, vals); 
}

void PolicyWriter::write(const std::string& name, const Policy& value) {   
    std::vector<Policy::Ptr> vals; 
    vals.push_back(Policy::Ptr(new Policy(value))); 
    write(name, vals); 
}

void PolicyWriter::write(const std::string& name, const PolicyFile& value) {   
    std::vector<Policy::FilePtr> vals; 
    vals.push_back(Policy::FilePtr(new PolicyFile(value))); 
    write(name, vals); 
}




}}}  // end lsst::pex::policy
