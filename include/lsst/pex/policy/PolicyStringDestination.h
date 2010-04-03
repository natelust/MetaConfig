// -*- lsst-c++ -*-
/**
 * @file PolicyStringDestination.h
 * 
 * @ingroup pex
 * @brief definition of the PolicyStringDestination class
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_STRDEST_H
#define LSST_PEX_POLICY_STRDEST_H

#include <ostream>
#include <boost/shared_ptr.hpp>

#include "lsst/pex/policy/PolicyStreamDestination.h"

namespace lsst {
namespace pex {
namespace policy {

/**
 * a generic stream destination for policy data 
 */
class PolicyStringDestination : public PolicyStreamDestination {
public: 

    /**
     * create the destination
     */
    PolicyStringDestination();

    /**
     * create the destination, initialized with the given string
     * @param str   initial contents for the output string
     */
    PolicyStringDestination(const std::string& str);

    /**
     * release resource associated with the destination
     */
    virtual ~PolicyStringDestination();

    /**
     * return the data written so far as a string
     */
    std::string getData() {
        return _sstrm->str();
    }

private:
    std::ostringstream *_sstrm;
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_STRDEST_H
