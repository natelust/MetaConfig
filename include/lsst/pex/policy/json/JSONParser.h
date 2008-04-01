// -*- lsst-c++ -*-
/**
 * @class JSONParser
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_JSON_JSONPARSER_H
#define LSST_PEX_POLICY_JSON_JSONPARSER_H

#include <sstream>
#include <map>

#include "lsst/pex/policy/PolicyParser.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/parserexceptions.h"
#include <jaula/jaula_parse.h>
#include <boost/regex.hpp>

namespace lsst {
namespace pex {
namespace policy {
namespace json {

using namespace lsst::pex::policy;
using namespace std;
using boost::regex;

/**
 * @brief   a parser for reading JSON-formatted data into a Policy object
 */
class JSONParser : public PolicyParser {
public:

    //@{
    /**
     * create a parser to load a Policy
     * @param policy   the Policy object to load the parsed data into
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.
     */
    JSONParser(Policy& policy);
    JSONParser(Policy& policy, bool strict);
    //@}

    /**
     * delete this parser
     */
    virtual ~JSONParser();

    /**
     * parse the data found on the given stream
     * @param strm    the stream to read JSON-encoded data from
     * @returns int   the number of parameters values loaded.  This does not
     *                   include sub-Policy objects.  
     */
    virtual int parse(istream& is);

protected:

    enum parser_states {
        /** initial state */
        START,
        /** a new item for an array has been read */
        array_addItem,
        /** an inter-item delimiter for an array has been read */
        array_nextItem,
        /** 
         *  error condition detected (pseudostate that launches an 
         *  exception terminating the process) 
         */
        error,
        /** a boolean false value constant has been read (pseudostate) */
        false_value,
        /** a null value constant has been read (pseudostate) */
        null_value,
        /** a numeric (integer) value has been read (pseudostate) */
        number_int_value,
        /** a numeric (float) value has been read (pseudostate) */
        number_value,
        /** an object initial delimiter has been read */
        property_begin,
        /** an object property name has been read */
        property_name,
        /** an object property delimiter has been read */
        property_value,
        /** an inter-property delimiter for an object has been read */
        property_next,
        /** a string value has been read (pseudostate) */
        string_value,
        /** a boolean true value constant has been read (pseudostate) */
        true_value,
        /** final state (pseudostate) */
        END
    };

    /**
     * generate a value for the last set of otokens 
     * @param lexer   the Jaula lexer object that provides tokens from the 
     *                  stream
     * @param token   the id of the last token read
     * @param prop    the name of the property currently being loaded
     * @param policy  the Policy object to load the value into
     * @returns int   the number of parameters values loaded.  This does not
     *                   include sub-Policy objects.  
     */
    int parseValue(JAULA::Lexan& lexer, unsigned int token, 
                   Policy& policy, const string& prop=string(), 
                   unsigned int arraytype=0);

    /**
     * creates an error message indicating that there is something 
     * syntactically wrong with a primitive value.  This is intended to be
     * passed to a FormatSyntaxError exception constructor.  
     * @param tokenData    the string containing the illegal value
     * @param tokenId      the Jaula JSON parser's token ID for the type 
     *                        of value expected.  The default is 0 (unknown).
     */
    string valSyntaxError(const string& tokenData, unsigned int tokenId = 0);

    /** 
     * creates an error message indicating that a long integer value was 
     * found (but not supported).  This is intended to be
     * passed to a UnsupportedSyntax exception constructor.  
     * @param tokenData    the string containing the illegal value
     */
    string longFound(const string& tokenData);

    /**
     * creates an generic error message indicating that syntax error was
     * found.  This is intended to be
     * passed to a FormatSyntaxError exception constructor.  
     * @param tokenData    the string containing the illegal value
     */
    string badFormat(const string& tokenData);

    /**
     * creates an error message indicating a attempt to mix types in a 
     * single array.  This is intended to be
     * passed to a UnsupportedSyntax exception constructor.  
     * @param tokenData    the string containing the illegal value
     * @param tokenId      the Jaula JSON parser's token ID for the type 
     *                        of value expected.  The default is 0 (unknown).
     */
    string wrongArrayType(const string& tokenData, unsigned int expectedToken, 
                          unsigned int tokenId);

    /**
     * creates an error message indicating that there is something 
     * syntactically wrong with a property name.  This is intended to be
     * passed to a FormatSyntaxError exception constructor.  
     * @param tokenData    the string containing the illegal value
     * @param tokenId      the Jaula JSON parser's token ID for the type 
     *                        of value expected.  The default is 0 (unknown).
     */
    string badPropName(const string& tokenData, unsigned int tokenId);

    /**
     * creates an error message indicating that a badly formed property
     * found.  This is intended to be
     * passed to a FormatSyntaxError exception constructor.  
     * @param tokenData    the string containing the illegal value
     */
    string badProp(const string& tokenData);

    /**
     * creates an error message indicating that a badly formed property
     * found.  This is intended to be
     * passed to a FormatSyntaxError exception constructor.  
     * @param tokenData    the string containing the illegal value
     */
    string badArray(const string& tokenData);

    static void _initTokenNames();
    static map<int, string> _tokenName;
    static const regex FILE_PREFIX;

private:
    // the Policy object is a member of the parent class
};

}}}}   // end lsst::pex::policy::json
#endif // LSST_PEX_POLICY_JSON_JSONPARSER_H
