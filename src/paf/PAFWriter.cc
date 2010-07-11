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
 * \file PolicyWriter.cc
 */
#include "lsst/pex/policy/paf/PAFWriter.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyFile.h"

namespace lsst {
namespace pex {
namespace policy {
namespace paf {

//@cond
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
void PAFWriter::writeBools(const std::string& name, 
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
void PAFWriter::writeInts(const std::string& name, 
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
void PAFWriter::writeDoubles(const std::string& name, 
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
void PAFWriter::writeStrings(const std::string& name, 
                             const Policy::StringArray& values) {
    (*_os) << _indent << name << ": ";
    Policy::StringArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << '"' << *vi << '"';
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
void PAFWriter::writePolicies(const std::string& name, 
                              const Policy::PolicyPtrArray& values) {
    PAFWriter subwrtr(_os, _indent+"  ");

    Policy::PolicyPtrArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << _indent << name << ": {" << std::endl;
        subwrtr.write(**vi);
        (*_os) << _indent << "}" << std::endl;
    }
}

void PAFWriter::writeFiles(const std::string& name, 
                           const Policy::FilePtrArray& values) 
{
    (*_os) << _indent << name << ": ";
    Policy::FilePtrArray::const_iterator vi;
    for(vi = values.begin(); vi != values.end(); ++vi) {
        (*_os) << '@' << (*vi)->getPath();
        if (vi+1 != values.end()) (*_os) << " ";
    }
    (*_os) << std::endl;
}
    
//@endcond
}}}} // end lsst::pex::policy::paf
