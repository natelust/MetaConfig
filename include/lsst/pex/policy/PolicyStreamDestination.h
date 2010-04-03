// -*- lsst-c++ -*-
/**
 * @file PolicyStringDestination.h
 * 
 * @ingroup pex
 * @brief definition of the PolicyStringDestination class
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_STRMDEST_H
#define LSST_PEX_POLICY_STRMDEST_H

#include <ostream>
#include <boost/shared_ptr.hpp>

#include "lsst/pex/policy/PolicyDestination.h"

namespace lsst {
namespace pex {
namespace policy {

/**
 * a generic stream destination for policy data 
 */
class PolicyStreamDestination : public PolicyDestination {
public:

    typedef boost::shared_ptr<std::ostream> StreamPtr;

    /**
     * create the destination
     */
    PolicyStreamDestination(StreamPtr ostrm);

    /**
     * release resource associated with the destination
     */
    virtual ~PolicyStreamDestination();

    /**
     * return a stream that can be used to write the data to.
     */
    virtual std::ostream& getOutputStream();

protected:
    StreamPtr _ostrm;

};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_STRMDEST_H
