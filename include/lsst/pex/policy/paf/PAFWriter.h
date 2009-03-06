// -*- lsst-c++ -*-
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
    PAFWriter(std::ostream *out = 0) 
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

    /**
     * create a writer attached to an output file
     * @param file     the output file
     */
    PAFWriter(const std::string& file) 
        : pexPolicy::PolicyWriter(file), _indent() { }

    /**
     * delete this writer
     */
    virtual ~PAFWriter();

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
     * write an array of property values with a given name
     * @param name    the name to save the values as.  This may be a 
     *                  hierarchical name; however, an implementation is 
     *                  not guaranteed to support it.  If it cannot, 
     *                  it should raise an exception.
     * @param values   the values to save under that name.
     */
    virtual void write(const std::string& name, 
                       const pexPolicy::Policy::BoolArray& values);
    virtual void write(const std::string& name, 
                       const pexPolicy::Policy::IntArray& values);
    virtual void write(const std::string& name, 
                       const pexPolicy::Policy::DoubleArray& values);
    virtual void write(const std::string& name, 
                       const pexPolicy::Policy::StringArray& values);
    virtual void write(const std::string& name, 
                       const pexPolicy::Policy::PolicyPtrArray& values);
    virtual void write(const std::string& name, 
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
