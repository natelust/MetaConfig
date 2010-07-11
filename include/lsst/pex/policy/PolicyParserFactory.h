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
 * @file PolicyParserFactory.h
 * @ingroup pex
 * @brief a definition of the PolicyParserFactory class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_PARSERFACTORY_H
#define LSST_PEX_POLICY_PARSERFACTORY_H

#include <string>

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/Policy.h"

#include <boost/shared_ptr.hpp>

namespace lsst {
namespace pex {
namespace policy {

// forward declaration
class PolicyParser;

namespace dafBase = lsst::daf::base;

// class PolicyParserFactory : public Citizen {  // causing deletion problems

/**
 * @brief an abstract factory class for creating PolicyParser instances.  
 * This class is used by the PolicySource class to determine the format
 * of a stream of serialized Policy data and then parse it into a Policy 
 * instance.  It is intended that for supported each format there is an
 * implementation of this class and a corresponding PolicyParser class.  
 */
class PolicyParserFactory {
public: 

    typedef boost::shared_ptr<PolicyParserFactory> Ptr;

    /**
     * create a factory
     */
    PolicyParserFactory() { }

//    PolicyParserFactory() : Citizen(typeid(this)) { }

    /**
     * destroy this factory
     */
    virtual ~PolicyParserFactory();

    /**
     * create a new PolicyParser class and return a pointer to it.  The 
     * caller is responsible for destroying the pointer.
     * @param policy   the Policy object that data should be loaded into.
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.  The 
     *                   default is true.
     */
    virtual PolicyParser* createParser(Policy& policy, 
                                       bool strict=true) const = 0;

    /**
     * analyze the given string assuming contains the leading characters 
     * from the data stream and return true if it is recognized as being in 
     * the format supported by this parser.  If it is, return the name of 
     * the this format; 
     */
    virtual bool isRecognized(const std::string& leaders) const = 0;

    /**
     * return the name for the format supported by the parser
     */
    virtual const std::string& getFormatName();

    /** 
     * an empty string representing an unrecognized format
     */
    static const std::string UNRECOGNIZED;
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_PARSERFACTORY_H


