/**
 * \file PolicyWriter.cc
 */
#include "lsst/pex/policy/paf/PAFWriter.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyFile.h"

namespace lsst {
namespace pex {
namespace policy {
namespace paf {

using lsst::pex::policy::Policy;
using lsst::pex::policy::PolicyWriter;

/*
 * delete this writer
 */
PAFWriter::~PAFWriter() { }

/*
 * write an array of property values with a given name
 * @param name    the name to save the values as.  This may be a 
 *                  hierarchical name; however, an implementation is 
 *                  not guaranteed to support it.  If it cannot, 
 *                  it should raise an exception.
 * @param values   the values to save under that name.
 */
void PAFWriter::write(const std::string& name, 
                      const Policy::BoolArray& values) 
{
    (*_os) << _indent << name << ": ";
    Policy::BoolArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << ((*vi) ? "true" : "false");
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
void PAFWriter::write(const std::string& name, 
                      const Policy::IntArray& values) 
{
    (*_os) << _indent << name << ": ";
    Policy::IntArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << *vi;
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
void PAFWriter::write(const std::string& name, 
                      const Policy::DoubleArray& values) 
{
    (*_os) << _indent << name << ": ";
    Policy::DoubleArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << *vi;
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
void PAFWriter::write(const std::string& name, 
                      const Policy::StringArray& values) {
    (*_os) << _indent << name << ": ";
    Policy::StringArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << '"' << *vi << '"';
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
void PAFWriter::write(const std::string& name, 
                      const Policy::PolicyPtrArray& values) {
    PAFWriter subwrtr(_os, _indent+"  ");

    Policy::PolicyPtrArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << _indent << name << ": {" << std::endl;
        subwrtr.write(**vi);
        (*_os) << _indent << "}" << std::endl;
    }
}

/*
 * write the contents of a policy the attached stream.  Each top-level
 * parameter will be recursively printed.
 * @param policy     the policy data to write
 */
void PAFWriter::write(const Policy& policy, bool doDecl) {
    PolicyWriter::write(policy, doDecl);
}

void PAFWriter::write(const std::string& name, 
                      const Policy::FilePtrArray& values) {
    (*_os) << _indent << name << ": ";
    Policy::FilePtrArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << '@' << (*vi)->getPath();
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
    






}}}} // end lsst::pex::policy::paf
