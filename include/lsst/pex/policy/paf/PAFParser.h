// -*- lsst-c++ -*-
/**
 * @class Lexer
 * 
 * @ingroup pex
 *
 * @brief an object for tokenizing a Policy file in PAF format.
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

using namespace std;
using lsst::daf::base::Citizen;
using lsst::pex::policy::Policy;
using lsst::pex::policy::PolicyParser;
using boost::regex;
using boost::match_results;
using boost::regex_search;
using boost::regex_match;
using boost::smatch;

/**
 * @brief  a parser for reading PAF-formatted data into a Policy object
 */
class PAFParser : public PolicyParser {
public: 

    //@{
    /**
     * create a parser to load a Policy
     * @param policy   the Policy object to load the parsed data into
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.  The 
     *                   default (set by PolicyParser) is true.
     */
    PAFParser(Policy& policy, bool strict);
    PAFParser(Policy& policy);
    //@}

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
    virtual int parse(istream& is);

private:
    // read next line from stream into the line string
    ios::iostate _nextLine(istream& is, string& line);

    // push a line back onto the stream
    void _pushBackLine(const string& line);

    int _parseIntoPolicy(istream& is, Policy& policy);
    int _addValue(const string& propname, string& value, 
                  Policy& policy, istream& is);

    static const regex COMMENT_LINE;
    static const regex SPACE_SRCH;
    static const regex PARAM_SRCH;
    static const regex NAME_MTCH;
    static const regex OPEN_SRCH;
    static const regex CLOSE_SRCH;
    static const regex DOUBLE_VALUE;
    static const regex INT_VALUE;
    static const regex ATRUE_VALUE;
    static const regex AFALSE_VALUE;
    static const regex QQSTRING_VALUE;
    static const regex QSTRING_VALUE;
    static const regex QQSTRING_START;
    static const regex QSTRING_START;
    static const regex QQSTRING_END;
    static const regex QSTRING_END;
    static const regex BARE_STRING_LINE;
    static const regex BARE_STRING;
    static const regex FILE_VALUE;

    // the policy reference, Policy& _pol, is a member of the parent class
    list<string> _buffer;
    int _lineno;
    int _depth;
};


}}}}   // end lsst::pex::policy::paf
#endif // LSST_PEX_POLICY_PAF_PAFPARSER_H
