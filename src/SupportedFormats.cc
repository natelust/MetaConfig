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
 * @file PolicyParserFactory.cc
 * @ingroup pex
 * @author Ray Plante
 */

#include "lsst/pex/policy/SupportedFormats.h"
#include "lsst/pex/policy/paf/PAFParserFactory.h"
#include "lsst/pex/exceptions.h"

namespace lsst {
namespace pex {
namespace policy {

using lsst::pex::policy::paf::PAFParserFactory;
using lsst::pex::policy::PolicyParserFactory;

void SupportedFormats::initDefaultFormats(SupportedFormats& sf) { 
    sf.registerFormat(PolicyParserFactory::Ptr(new PAFParserFactory()));
}

/**
 * register a factory method for policy format parsers
 */
void SupportedFormats::registerFormat(const PolicyParserFactory::Ptr& factory) 
{
    if (factory.get() == 0) 
        throw LSST_EXCEPT(pexExcept::RuntimeErrorException, 
                          std::string("attempt to register null ") + 
                                               "PolicyParserFactory pointer");

    _formats[factory->getFormatName()] = factory;
}

/**
 * analyze the given string assuming contains the leading characters 
 * from the data stream and determine if it is recognized as being in 
 * the format supported by this parser.  If it is, return the name of 
 * the this format; if not return an empty string.  
 */
const std::string& 
SupportedFormats::recognizeType(const std::string& leaders) const {

    Lookup::const_iterator f;
    for(f=_formats.begin(); f != _formats.end(); ++f) {
        if (f->second->isRecognized(leaders))
            return f->second->getFormatName();
    }

    return PolicyParserFactory::UNRECOGNIZED;
}

/**
 * get a pointer to a factory with a given name.  A null pointer is 
 * returned if the name is not recognized.
 */
PolicyParserFactory::Ptr 
SupportedFormats::getFactory(const std::string& name) const {

    SupportedFormats *me = const_cast<SupportedFormats*>(this);

    Lookup::iterator found = me->_formats.find(name);
    return ((found != me->_formats.end()) ? found->second 
                                          : PolicyParserFactory::Ptr());
}

}}}  // end namespace lsst::pex::policy



