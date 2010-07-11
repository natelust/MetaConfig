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
 * @file SupportedFormats.h
 *
 * @ingroup pex
 * @brief definition of the SupportedFormats class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_SUPPORTEDFORMATS_H
#define LSST_PEX_POLICY_SUPPORTEDFORMATS_H

#include <map>

#include "lsst/pex/policy/PolicyParserFactory.h"

#include <boost/shared_ptr.hpp>

namespace lsst {
namespace pex {
namespace policy {

namespace dafBase = lsst::daf::base;

// class SupportedFormats : public Citizen { // causes problems in construction

/**
 * @brief a list of supported Policy formats.  It can be used to determine 
 * the format type for a Policy data stream.
 */
class SupportedFormats {
public: 

    typedef boost::shared_ptr<SupportedFormats> Ptr;

//    SupportedFormats() : Citizen(typeid(this)), _formats() { }

    SupportedFormats() : _formats() { }

    /**
     * register a factory method for policy format parsers
     */
    void registerFormat(const PolicyParserFactory::Ptr& factory);

    /**
     * analyze the given string assuming contains the leading characters 
     * from the data stream and return true if it is recognized as being in 
     * the format supported by this parser.  If it is, return the name of 
     * the this format; 
     */
    const std::string& recognizeType(const std::string& leaders) const;

    /**
     * return true if the name resolves to a registered format
     */
    bool supports(const std::string& name) const {
        return (_formats.find(name) != _formats.end());
    }

    /**
     * get a pointer to a factory with a given name.  A null pointer is 
     * returned if the name is not recognized.
     */
    PolicyParserFactory::Ptr getFactory(const std::string& name) const;

    /**
     * initialize a given SupportFormats instance with the formats known
     * by default.  
     */
    static void initDefaultFormats(SupportedFormats& sf);

    /**
     * return the number formats currently registered
     */
    int size() { return _formats.size(); } 

private:
    typedef std::map<std::string, PolicyParserFactory::Ptr> Lookup;
    Lookup _formats;
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_SUPPORTEDFORMATS_H


