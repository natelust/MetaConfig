// -*- lsst-c++ -*-

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
 * @file PAFWriter.h
 * @ingroup pex
 * @brief definition of the PAFWriter class
 * @author Ray Plante
 */
#ifndef LSST_PEX_POLICY_PAF_WRITER_H
#define LSST_PEX_POLICY_PAF_WRITER_H

#include "lsst/pex/policy/PolicyWriter.h"

namespace lsst {
namespace pex {
namespace policy {
namespace paf {

namespace pexPolicy = lsst::pex::policy;

/**
 * An abstract interface for writing policy data to streams
 */
class PAFWriter : public pexPolicy::PolicyWriter {
public: 

    /**
     * create a writer attached to an output stream
     * @param out     the output stream to write data to
     */
    explicit PAFWriter(std::ostream *out = 0) 
        : pexPolicy::PolicyWriter(out), _indent() { }

    /**
     * create a writer attached to an output stream
     * @param out     the output stream to write data to
     * @param indent  a string (of spaces) to used as indentation for each
     *                  line printed out.  
     */
    PAFWriter(std::ostream *out, const std::string indent) 
        : pexPolicy::PolicyWriter(out), _indent(indent) 
    { }

    //@{
    /**
     * create a writer attached to an output file
     * @param file     the output file
     */
    explicit PAFWriter(const std::string& file) 
        : pexPolicy::PolicyWriter(file), _indent() { }
    explicit PAFWriter(const char *file) 
        : pexPolicy::PolicyWriter(file), _indent() { }
    //@}

    /**
     * delete this writer
     */
    virtual ~PAFWriter();

    //@{
    /**
     * write an array of property values with a given name
     * @param name    the name to save the values as.  This may be a 
     *                  hierarchical name; however, an implementation is 
     *                  not guaranteed to support it.  If it cannot, 
     *                  it should raise an exception.
     * @param values   the values to save under that name.
     */
    virtual void writeBools(const std::string& name, 
                            const pexPolicy::Policy::BoolArray& values);
    virtual void writeInts(const std::string& name, 
                           const pexPolicy::Policy::IntArray& values);
    virtual void writeDoubles(const std::string& name, 
                              const pexPolicy::Policy::DoubleArray& values);
    virtual void writeStrings(const std::string& name, 
                              const pexPolicy::Policy::StringArray& values);
    virtual void writePolicies(const std::string& name, 
                              const pexPolicy::Policy::PolicyPtrArray& values);
    virtual void writeFiles(const std::string& name, 
                            const pexPolicy::Policy::FilePtrArray& values);
    //@}

protected:

    /**
     * the indentation string
     */
    std::string _indent;
};


}}}}  // end lsst::pex::policy::paf

#endif // end LSST_PEX_POLICY_PAF_WRITER_H
