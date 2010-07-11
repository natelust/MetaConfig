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
 * @file PAFParserFactory.cc
 * @ingroup pex
 * @author Ray Plante
 */

#include "lsst/pex/policy/paf/PAFParserFactory.h"
#include "lsst/pex/policy/paf/PAFParser.h"

namespace lsst {
namespace pex {
namespace policy {
namespace paf {

//@cond

using boost::regex_search;
using boost::regex;
using std::string;
using lsst::pex::policy::Policy;
using lsst::pex::policy::PolicyParser;

/* 
 * a name for the format
 */
const string PAFParserFactory::FORMAT_NAME("PAF");

const regex PAFParserFactory::LEADER_PATTERN("^\\s*\\w");
const regex 
     PAFParserFactory::CONTENTID("^\\s*#\\s*<\\?cfg\\s+PAF(\\s+\\w+)*\\s*\\?>",
                                regex::icase);

/*
 * create a new PolicyParser class and return a pointer to it.  The 
 * caller is responsible for destroying the pointer.
 * @param  policy   the Policy object that data should be loaded into.
 */
PolicyParser* PAFParserFactory::createParser(Policy& policy, 
                                             bool strict) const 
{ 
    return new PAFParser(policy, strict);
}

/*
 * return the name for the format supported by the parser
 */
const string& PAFParserFactory::getFormatName() { return FORMAT_NAME; }

/*
 * analyze the given string assuming contains the leading characters 
 * from the data stream and return true if it is recognized as being in 
 * the format supported by this parser.  If it is, return the name of 
 * the this format; 
 */
bool PAFParserFactory::isRecognized(const string& leaders) const { 
    return (regex_search(leaders, contentid) || 
            regex_search(leaders, LEADER_PATTERN));
}


//@endcond

}}}}   // end lsst::pex::policy::paf
