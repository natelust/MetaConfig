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
