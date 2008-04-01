/**
 * @class JSONParser
 * 
 * @ingroup pex
 *
 * @author Ray Plante
 * 
 */

#include "lsst/pex/policy/json/JSONParser.h"
#include "lsst/pex/policy/PolicyFile.h"
#include <stdexcept>

/*
#include "lsst/pex/utils/Trace.h"
#define EXEC_TRACE  20
static void execTrace( string s, int level = EXEC_TRACE ){
    lsst::pex::utils::Trace( "pex.policy.json.JSONParser", level, s );
}
*/

namespace lsst {
namespace pex {
namespace policy {
namespace json {

using boost::regex_search;
using boost::smatch;

/**
 * create a parser to load a Policy
 */
JSONParser::JSONParser(Policy& policy) : PolicyParser(policy) { 
    if (_tokenName.size() == 0) _initTokenNames();
}
JSONParser::JSONParser(Policy& policy, bool strict) 
    : PolicyParser(policy, strict)
{ 
    if (_tokenName.size() == 0) _initTokenNames();
}

const regex JSONParser::FILE_PREFIX("^@");

/**
 * delete this parser
 */
JSONParser::~JSONParser() { } 

map<int, string> JSONParser::_tokenName;

void JSONParser::_initTokenNames() {
    _tokenName[0]                = "unknown-type";
    _tokenName[NULL_VALUE]       = "null";
    _tokenName[FALSE_VALUE]      = "boolean";
    _tokenName[TRUE_VALUE]       = "boolean";
    _tokenName[NUMBER_VALUE]     = "double";
    _tokenName[NUMBER_INT_VALUE] = "integer";
    _tokenName[STRING_VALUE]     = "string";
    _tokenName['{']              = "{";
    _tokenName['}']              = "}";
    _tokenName[':']              = ":";
    _tokenName[',']              = ",";
    _tokenName['[']              = "[";
    _tokenName[']']              = "]";       
}

/**
 * parse the data found on the given stream
 * @param strm    the stream to read JSON-encoded data from
 * @return int   the number of values primitive values parsed.
 */
int JSONParser::parse(istream& is) {

    JAULA::Lexan lexer(is, true);

    unsigned int firstToken = lexer.yylex();

    try {
        return parseValue(lexer, firstToken, _pol);
    }
    catch (TypeError& e) {
        // maybe change this to a log message, _pol should still be intact
        throw logic_error(string("Programmer error: unexpected TypeError: ") +
                          e.what());
    }
}
        
/**
 * generate a value for the last set of otokens 
 * @param lexer   the Jaula lexer object that provides tokens from the 
 *                  stream
 * @param token   the id of the last token read
 * @param policy  the Policy object to load the value into
 * @return int   the number of values primitive values parsed.
 */
int JSONParser::parseValue(JAULA::Lexan& lexer, unsigned int token, 
                           Policy& policy, const string& prop, 
                           unsigned int arraytype) 
{
    string propname = prop;
    int    count    = 0;

    if (propname.size() == 0 && token != '{') {
        ostringstream msg;
        msg << "property value (" << _tokenName[token] 
            << ") cannot be loaded without a property name" << ends;
        throw UnsupportedSyntax(msg.str(), lexer.lineno());
    }

    for (parser_states state = START; state != END; token = lexer.yylex()) {

        switch (state) {
        case START:
            // an arbitrary parsing starting point.  
            // A Policy file will start with a '{' token.  Other tokens
            // are typically parsed here as part of a recursion; here, 
            // we will actually save data to the Policy object.
            switch (token) {
            case 0: 
                throw EOFError(lexer.lineno());
                break;
            case '{':
                state = property_begin;
                break;
            case '[':
                state = array_addItem;
                break;
            case NULL_VALUE:
                // skip over null values
                return count;
            case FALSE_VALUE:
                policy.add(propname, false);
                return count++;
            case TRUE_VALUE:
                policy.add(propname, true);
                return count++;
            case STRING_VALUE: {
                smatch matched;
                if (regex_search(lexer.getTokenData(), matched,FILE_PREFIX)) {
                  policy.add(propname,
                      Policy::FilePtr(new PolicyFile(matched.suffix().str())));
                }
                else {
                  policy.add(propname, lexer.getTokenData());
                }
                return count++;
            }
            case NUMBER_VALUE: {
                char *unparsed;
                double val = strtod(lexer.getTokenData().c_str(), &unparsed);
                if (unparsed && (*unparsed)) {
                   throw FormatSyntaxError(valSyntaxError(lexer.getTokenData(),
                                                          token),
                                           lexer.lineno());
                }
                policy.add(propname, val);
                return count++;
            }

            case NUMBER_INT_VALUE: {
                char *unparsed;
                long lval = strtol(lexer.getTokenData().c_str(), &unparsed,10);
                if (unparsed && (*unparsed)) {
                    // syntax error
                   throw FormatSyntaxError(valSyntaxError(lexer.getTokenData(),
                                                          token),
                                           lexer.lineno());
                }
                int val = int(lval);
                if (lval-val != 0) {
                    // longs are unsupported
                    throw UnsupportedSyntax(longFound(lexer.getTokenData()),
                                            lexer.lineno());
                }
                policy.add(propname, val);
                return count++;
            }

            default:
                // unexpected token
                throw FormatSyntaxError(badFormat(lexer.getTokenData()), 
                                                  lexer.lineno());
                break;
            }  // end switch(token)
            break;

        case array_addItem :
            // we are expecting another element in an array.  We check to 
            // make sure the types of all the elements are the same.  
            switch (token) {
            case 0: 
                EOFError(lexer.lineno());
                break;

            case ']' :
                return count;

            case NULL_VALUE :
                // do nothing
                break;

            case FALSE_VALUE :
            case TRUE_VALUE :
            case NUMBER_VALUE :
            case NUMBER_INT_VALUE :
            case STRING_VALUE :
            case '{' :                // Policy type
                if (!arraytype) arraytype = token;
                if (arraytype == FALSE_VALUE) arraytype = TRUE_VALUE;
                if (arraytype == token) {
                    count += parseValue(lexer, token, policy, propname);
                }
                else if (_strict) 
                   throw UnsupportedSyntax(wrongArrayType(lexer.getTokenData(),
                                                          arraytype, token),
                                            lexer.lineno());
                state = array_nextItem;
                break;

            case '[' :
                // for now we are flattening multi-dimensional arrays
                count += parseValue(lexer, token, policy, propname, arraytype);
                state = array_nextItem;
                break;

            default:
                // unexpected token
                throw FormatSyntaxError(badFormat(lexer.getTokenData()),
                                        lexer.lineno());
                break;
            }                          // array_addItem state switch
            break;

        case array_nextItem :
            // an array value was just set; we now expect either an array
            // value delimiter or the end of the array.
            switch (token) {
            case 0 :
                EOFError(lexer.lineno());
                break;

            case ']' :
                return count;

            case ',' :
                state = array_addItem;
                break;

            default :
                // unexpected token
                throw FormatSyntaxError(badArray(lexer.getTokenData()),
                                        lexer.lineno());
                break;
            }                          // array_nextItem state switch
            break;

        case property_begin :
            // we just encountered the start of a new policy object (i.e.
            // we just consumed a '{'); we now expect a property name.
            switch (token) {
            case 0 :
                EOFError(lexer.lineno());
                break;

            case '}' :
                return count; 

            case STRING_VALUE :
                propname = lexer.getTokenData();
                state = property_name;
                break;

            default :
                // unexpected token
                throw FormatSyntaxError(badPropName(lexer.getTokenData(),
                                                    token),
                                        lexer.lineno());
                break;
            }                          // property_begin state switch
            break;

        case property_name :
            // we just acquired the property name, look for the colon
            // separator
            switch (token) {
            case 0 :
                EOFError(lexer.lineno());
                break;

            case ':' :
                arraytype = 0;
                state = property_value;
                break;

            default :
                // unexpected token
                throw FormatSyntaxError(badProp(lexer.getTokenData()),
                                        lexer.lineno());
                break;
            }                          // property_name state switch
            break;

        case property_value :
            // we are now expecting a legal property value.  
            switch (token) {
            case 0 :
                EOFError(lexer.lineno());
                break;

            case '[' :
            case NULL_VALUE :
            case FALSE_VALUE :
            case TRUE_VALUE :
            case NUMBER_VALUE :
            case NUMBER_INT_VALUE :
            case STRING_VALUE :
                count += parseValue(lexer, token, policy, propname);
                state = property_next;
                break;

            case '{' : {
                Policy::Ptr subpolicy(new Policy());
                policy.add(propname, subpolicy);
                count += parseValue(lexer, token, *subpolicy, propname);
                state = property_next;
                break;
            }
                
            default : {
                // unexpected token
                throw FormatSyntaxError(badFormat(lexer.getTokenData()),
                                        lexer.lineno());
                break;
            }                          // property_name state switch
            }
            break;

        case property_next :
            // we are ready for the next property to appear
            switch (token) {
            case 0 :
                EOFError(lexer.lineno());
                break;

            case '}' :
                return count;

            case ',' :
                state = property_begin;
                break;

            default :
                // unexpected token
                throw FormatSyntaxError(badProp(lexer.getTokenData()),
                                        lexer.lineno());
                break;
            }                          // property_name state switch
            break;

        default:
            // unexpected token
            throw FormatSyntaxError(badProp(lexer.getTokenData()),
                                    lexer.lineno());
            break;
        }
    }

    throw logic_error("programmer error: escaped from infinite parser loop");
}

/**
 * creates an error message indicating that there is something 
 * syntactically wrong with a primitive value.  This is intended to be
 * passed to a FormatSyntaxError exception constructor.  
 * @param tokenData    the string containing the illegal value
 * @param tokenId      the Jaula JSON parser's token ID for the type 
 *                        of value expected.  The default is 0 (unknown).
 */
string JSONParser::valSyntaxError(const string& tokenData, 
                                  unsigned int tokenId) 
{
    ostringstream msg;
    if (tokenId) 
        msg << _tokenName[tokenId] << ' ';
    msg << "value contains unparsable data: " << tokenData << ends;
    return msg.str();
}

/**
 * creates an error message indicating that a long integer value was 
 * found (but not supported).  This is intended to be
 * passed to a UnsupportedSyntax exception constructor.  
 * @param tokenData    the string containing the illegal value
 */
string JSONParser::longFound(const string& tokenData) {

    ostringstream msg;
    msg << "unsupported long integer value found: " << tokenData << ends;
    return msg.str();
}

/**
 * creates an generic error message indicating that syntax error was
 * found.  This is intended to be
 * passed to a FormatSyntaxError exception constructor.  
 * @param tokenData    the string containing the illegal value
 */
string JSONParser::badFormat(const string& tokenData) {

    ostringstream msg;
    msg << "Unrecognized token found: " << tokenData << ends;
    return msg.str();
}

/**
 * creates an error message indicating a attempt to mix types in a 
 * single array.  This is intended to be
 * passed to a UnsupportedSyntax exception constructor.  
 * @param tokenData    the string containing the illegal value
 * @param tokenId      the Jaula JSON parser's token ID for the type 
 *                        of value expected.  The default is 0 (unknown).
 */
string JSONParser::wrongArrayType(const string& tokenData, 
                                  unsigned int expectedToken, 
                                  unsigned int tokenid) 
{
    ostringstream msg;
    msg << "attempting to add ";
    if (tokenid) 
        msg << _tokenName[tokenid] << " type data (";
    else 
        msg << "incorrect data type to an ";
    msg << tokenData;
    if (tokenid) 
        msg << ") to a " << _tokenName[expectedToken] << " array";
    else
        msg << ") to an existing array";

    return msg.str();
}

/**
 * creates an error message indicating that there is something 
 * syntactically wrong with a property name.  This is intended to be
 * passed to a FormatSyntaxError exception constructor.  
 * @param tokenData    the string containing the illegal value
 * @param tokenId      the Jaula JSON parser's token ID for the type 
 *                        of value expected.  The default is 0 (unknown).
 */
string JSONParser::badPropName(const string& tokenData, unsigned int tokenId) {

    ostringstream msg;
    if (tokenId) 
        msg << _tokenName[tokenId] << ' ';
    msg << "illegal property name: " << tokenData << ends;
    return msg.str();
}

/**
 * creates an error message indicating that a badly formed property
 * found.  This is intended to be
 * passed to a FormatSyntaxError exception constructor.  
 * @param tokenData    the string containing the illegal value
 */
string JSONParser::badProp(const string& tokenData) {

    ostringstream msg;
    msg << "Bad property format: expected ':', found '" << tokenData 
        << "'" << ends;
    return msg.str();
}

/**
 * creates an error message indicating that a badly formed property
 * found.  This is intended to be
 * passed to a FormatSyntaxError exception constructor.  
 * @param tokenData    the string containing the illegal value
 */
string JSONParser::badArray(const string& tokenData) {

    ostringstream msg;
    msg << "Bad array format: expected ',' or ']', found '" << tokenData 
        << "'" << ends;
    return msg.str();
}





}}}}   // end lsst::pex::policy::json
