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
 * @file PolicyWriter.h
 * @ingroup pex
 * @brief the definition of the PolicyWriter class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_POLICYWRITER_H
#define LSST_PEX_POLICY_POLICYWRITER_H

#include "lsst/pex/policy/Policy.h"
#include <ostream>

#define NULL_FILENAME "/dev/null"

namespace lsst {
namespace pex {
namespace policy {

/**
 * An abstract interface for writing policy data to streams
 */
class PolicyWriter {
public: 

    /**
     * create a writer attached to an output stream.  If no stream is 
     * provided, it will write policy data to an internal string stream; 
     * toString() can be used to retrieve the results.  
     * @param out     the output stream to write data to
     */
    PolicyWriter(std::ostream *out = 0);

    /**
     * create a writer attached to a file.  This file will be immediately 
     * opened for writing.
     * @param file     the path to the output file
     * @param append   if true, open the file to append.  (default is false.)
     */
    PolicyWriter(const std::string& file, bool append=false);

    /**
     * delete this writer
     */
    virtual ~PolicyWriter();

    /**
     * write the contents of a policy the attached stream.  Each top-level
     * parameter will be recursively printed.
     * @param policy     the policy data to write
     * @param doDecl     if true, precede the data with the appropriate 
     *                     file format type. 
     */
    virtual void write(const Policy& policy, bool doDecl=false);

    //@{
    /**
     * write the given property out as policy data
     * @param name    the name to save the property as.  This may be a 
     *                  hierarchical name; however, an implementation is 
     *                  not guaranteed to support it.  If it cannot, 
     *                  it should raise an exception.
     * @param value   the value to save under that name.
     */
    virtual void writeBool(const std::string& name, bool value);
    virtual void writeInt(const std::string& name, int value);
    virtual void writeDouble(const std::string& name, double value);
    virtual void writeString(const std::string& name, 
                             const std::string& value);
    virtual void writePolicy(const std::string& name, const Policy& value);
    virtual void writeFile(const std::string& name, const PolicyFile& value);
    //@}

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
                            const Policy::BoolArray& values) = 0;
    virtual void writeInts(const std::string& name, 
                           const Policy::IntArray& values) = 0;
    virtual void writeDoubles(const std::string& name, 
                              const Policy::DoubleArray& values) = 0;
    virtual void writeStrings(const std::string& name, 
                              const Policy::StringArray& values) = 0;
    virtual void writePolicies(const std::string& name, 
                               const Policy::PolicyPtrArray& values) = 0;
    virtual void writeFiles(const std::string& name, 
                            const Policy::FilePtrArray& values) = 0;
    //@}

    /**
     * close the output stream.  This has no effect if the attached 
     * stream is not a file stream.  
     */
    void close();

    /**
     * return the written data as a string.  This string will be non-empty 
     * only if this class was was instantiated without an attached stream.
     */
    std::string toString();
        

private:
    std::ostream *_myos;
protected:

    /**
     * the output stream.  This should always be non-null.
     */
    std::ostream *_os;
};




}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_POLICYWRITER_H

