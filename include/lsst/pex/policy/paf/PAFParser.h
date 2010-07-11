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
 * @file PAFParser.h
 * 
 * @ingroup pex
 *
 * @brief definition of the PAFParser class
 * 
 * @author Ray Plante
 * 
 */
#ifndef LSST_PEX_POLICY_PAF_TOKENIZER_H
#define LSST_PEX_POLICY_PAF_TOKENIZER_H

#include <iostream>

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/PolicyParser.h"
#include "lsst/pex/policy/Policy.h"

#include <boost/regex.hpp>

namespace lsst {
namespace pex {
namespace policy {
namespace paf {

namespace dafBase = lsst::daf::base;
namespace pexPolicy = lsst::pex::policy;

/**
 * @brief  a parser for reading PAF-formatted data into a Policy object
 */
class PAFParser : public pexPolicy::PolicyParser {
public: 

    /**
     * create a parser to load a Policy
     * @param policy   the Policy object to load the parsed data into
     */
    PAFParser(pexPolicy::Policy& policy);

    /**
     * @copydoc PAFParser(pexPolicy::Policy&)
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.  The 
     *                   default (set by PolicyParser) is true.
     */
    PAFParser(pexPolicy::Policy& policy, bool strict);

    /**
     * delete this parser
     */
    virtual ~PAFParser();

    /**
     * parse the data found on the given stream
     * @param is      the stream to read PAF-encoded data from
     * @returns int   the number of parameters values loaded.  This does not
     *                   include sub-Policy objects.  
     */
    virtual int parse(std::istream& is);

private:
    // read next line from stream into the line string
    std::ios::iostate _nextLine(std::istream& is, std::string& line);

    // push a line back onto the stream
    void _pushBackLine(const std::string& line);

    int _parseIntoPolicy(std::istream& is, pexPolicy::Policy& policy);
    int _addValue(const std::string& propname, std::string& value, 
                  pexPolicy::Policy& policy, std::istream& is);

    static const boost::regex COMMENT_LINE;
    static const boost::regex EMPTY_LINE;
    static const boost::regex SPACE_SRCH;
    static const boost::regex PARAM_SRCH;
    static const boost::regex NAME_MTCH;
    static const boost::regex OPEN_SRCH;
    static const boost::regex CLOSE_SRCH;
    static const boost::regex DOUBLE_VALUE;
    static const boost::regex INT_VALUE;
    static const boost::regex ATRUE_VALUE;
    static const boost::regex AFALSE_VALUE;
    static const boost::regex QQSTRING_VALUE;
    static const boost::regex QSTRING_VALUE;
    static const boost::regex QQSTRING_START;
    static const boost::regex QSTRING_START;
    static const boost::regex QQSTRING_EMPTYSTART;
    static const boost::regex QSTRING_EMPTYSTART;
    static const boost::regex QQSTRING_END;
    static const boost::regex QSTRING_END;
    static const boost::regex BARE_STRING_LINE;
    static const boost::regex BARE_STRING;
    static const boost::regex URN_VALUE;
    static const boost::regex FILE_VALUE;

    // the policy reference, Policy& _pol, is a member of the parent class
    std::list<std::string> _buffer;
    int _lineno;
    int _depth;
};


}}}}   // end lsst::pex::policy::paf
#endif // LSST_PEX_POLICY_PAF_PAFPARSER_H
