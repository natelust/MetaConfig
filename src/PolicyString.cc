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
 * @file PolicyString.cc
 * @author Ray Plante
 */
#include <sstream>
// #include <iosfwd>

#include <boost/scoped_ptr.hpp>

#include "lsst/pex/policy/PolicyString.h"
#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/PolicyParser.h"
#include "lsst/pex/policy/exceptions.h"
#include "lsst/pex/policy/parserexceptions.h"
#include "lsst/pex/policy/paf/PAFParserFactory.h"

namespace lsst {
namespace pex {
namespace policy {

//@cond

using std::string;
using std::ifstream;
using boost::regex;
using boost::regex_match;
using boost::regex_search;
using boost::scoped_ptr;
using lsst::pex::policy::paf::PAFParserFactory;

namespace pexExcept = lsst::pex::exceptions;

const regex PolicyString::SPACE_RE("^\\s*$");
const regex PolicyString::COMMENT("^\\s*#");
const regex 
        PolicyString::CONTENTID("^\\s*#\\s*<\\?cfg\\s+\\w+(\\s+\\w+)*\\s*\\?>",
                                regex::icase);

/*
 * create a "null" Policy formed from an empty string.  
 * @param fmts           a SupportedFormats object to use.  An instance 
 *                          encapsulates a configured set of known formats.
 */
PolicyString::PolicyString(const SupportedFormats::Ptr& fmts) 
    : PolicySource(fmts), Persistable(), _data(), _pfact() 
{ }

/*
 * create a "null" Policy formed from an empty string.  
 * @param fmts           a SupportedFormats object to use.  An instance 
 *                          encapsulates a configured set of known formats.
 */
PolicyString::PolicyString(const std::string& data,
                           const SupportedFormats::Ptr& fmts) 
    : PolicySource(fmts), Persistable(), _data(data), _pfact() 
{ }

#define PolStr_ERROR_MSG(use, msg, input)   \
    std::ostringstream use;                 \
    use << msg << ": '";                    \
    if (input.length() > 40)                \
        use << input;                       \
    else                                    \
        use << input.substr(0,40) << "..."; \
    use << "'";                             

/*
 * return the name of the format that the data is stored in.  This may 
 * cause the first few records of the source to be read.
 * @exception IOError   if an error occurs while reading the first few
 *                      characters of the source stream.
 */
const string& PolicyString::getFormatName() {

    // try reading the initial characters
    std::istringstream is(_data);
    if (is.fail()) {
        PolStr_ERROR_MSG(msg, "failure opening input Policy string", _data);
        throw LSST_EXCEPT(pexExcept::IoErrorException, msg.str());
    }

    // skip over comments
    string line;
    getline(is, line);
    while (is.good() && 
           (regex_match(line, SPACE_RE) || 
            (regex_search(line, COMMENT) && !regex_search(line, COMMENT))))
    { }
            
    if (is.fail()) {
        PolStr_ERROR_MSG(msg, "failure reading input Policy string", _data);
        throw LSST_EXCEPT(pexExcept::IoErrorException, msg.str());
    }
    if (is.eof() && 
        (regex_match(line, SPACE_RE) || 
         (regex_search(line, COMMENT) && !regex_search(line, COMMENT))))
    {
        // empty file; let's just assume PAF (but don't cache the name).
        return PAFParserFactory::FORMAT_NAME;
    }
    return cacheName(_formats->recognizeType(line));
}

/*
 * load the data from this Policy source into a Policy object
 * @param policy    the policy object to load the data into
 * @exception ParserError  if an error occurs while parsing the data
 * @exception IOError   if an I/O error occurs while reading from the 
 *                       source stream.
 */
void PolicyString::load(Policy& policy) { 

    PolicyParserFactory::Ptr pfactory = _pfact;
    if (! pfactory.get()) {
        const string& fmtname = getFormatName();
        if (fmtname.empty()) {
            PolStr_ERROR_MSG(ms,"Unknown Policy format for string data",_data);
            throw LSST_EXCEPT(pexExcept::IoErrorException, ms.str());
        }
        pfactory = _formats->getFactory(fmtname);
    }

    scoped_ptr<PolicyParser> parser(pfactory->createParser(policy));

    std::istringstream is(_data);
    if (is.fail()) {
        PolStr_ERROR_MSG(msg, "failure opening Policy string", _data);
        throw LSST_EXCEPT(pexExcept::IoErrorException, msg.str());
    }
    parser->parse(is);
}

//@endcond

}}}   // end lsst::pex::policy
