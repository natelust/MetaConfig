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
 * @file PolicyParser.h
 * @ingroup pex
 * @brief definition of the PolicyParser class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_PARSER_H
#define LSST_PEX_POLICY_PARSER_H

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyParserFactory.h"

namespace lsst {
namespace pex {
namespace policy {

namespace dafBase = lsst::daf::base;

/**
 * @brief an abstract class for parsing serialized Policy data and loading
 * it into a Policy object.  
 */
class PolicyParser : public dafBase::Citizen {
public: 

    /**
     * Create a Parser attached to a policy object to be loaded.
     * @param policy   the Policy object to load the parsed data into
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.
     */
    PolicyParser(Policy& policy, bool strict=true) 
        : dafBase::Citizen(typeid(this)), _pol(policy), _strict(strict) { }

    /**
     * destroy this factory
     */
    virtual ~PolicyParser();

    /**
     * return true if this parser will be strict in adhering to syntax 
     * rules.  In this case, exceptions will be thrown if any syntax errors 
     * are detected.  Otherwise, some syntax errors may be ignored.
     */
    bool isStrict() { return _strict; }

    /**
     * set whether this parser will be strict in adhering to syntax rules.  
     * If set to true, exceptions will be thrown if any syntax errors 
     * are detected.  Otherwise, some syntax errors may be ignored.
     */
    void setStrict(bool strict) { _strict = strict; }

    /**
     * parse data from the input stream and load results into the attached 
     * Policy.  
     * @param is      the stream to read encoded data from
     * @returns int   the number of parameters values loaded.  This does not
     *                   include sub-Policy objects.  
     */
    virtual int parse(std::istream& is) = 0;

    //@{
    /**
     * return the policy object
     */
    Policy& getPolicy() { return _pol; }
    const Policy& getPolicy() const { return _pol; }
    //@}

protected: 

    Policy& _pol;
    bool _strict;
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_PARSER_H
