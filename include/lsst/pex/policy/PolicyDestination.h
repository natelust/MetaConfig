// -*- lsst-c++ -*-
/**
 * @file PolicyDestination.h
 * 
 * @ingroup pex
 * @brief definition of the PolicyDestination class
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_DEST_H
#define LSST_PEX_POLICY_DEST_H

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/Policy.h"

namespace lsst {
namespace pex {
namespace policy {

namespace dafBase = lsst::daf::base;

/**
 * a class representing a destination to serialize Policy parameter
 * data to.  This might be a file, a string, or a stream; sub-classes handle 
 * the different possibilities.  This class has no control over the format 
 * going to the destination; this is a matter for the PolicyWriter, which 
 * can take a PolicyDestination as a constructor input.
 */
class PolicyDestination : public dafBase::Citizen {
public:

    /**
     * create a destination
     */
    PolicyDestination() : dafBase::Citizen(typeid(this)) { }

    /**
     * release resource associated with the destination
     */
    virtual ~PolicyDestination();

    /**
     * return a stream that can be used to write the data to.
     */
    virtual std::ostream& getOutputStream() = 0;

protected:
    /**
     * create a copy of this destination
     */
    PolicyDestination(const PolicyDestination& that) 
        : dafBase::Citizen(typeid(this)) { }

};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_DEST_H


