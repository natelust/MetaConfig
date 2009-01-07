/**
 * @class PAFParser
 * 
 * @ingroup pex
 *
 * @author Ray Plante
 * 
 */

#include "lsst/pex/policy/paf/PAFParser.h"
#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/parserexceptions.h"
#include <stdexcept>

namespace lsst {
namespace pex {
namespace policy {
namespace paf {

const regex PAFParser::COMMENT_LINE("^\\s*#");
const regex PAFParser::SPACE_SRCH("^(\\s+)");
const regex PAFParser::PARAM_SRCH("^(\\s*)(\\w[\\w\\d\\.]*)\\s*:\\s*");
const regex PAFParser::NAME_MTCH("\\w[\\w\\d]*(\\.\\w[\\w\\d])*");
const regex PAFParser::OPEN_SRCH("^\\{\\s*");
const regex PAFParser::CLOSE_SRCH("^\\s*\\}\\s*");
const regex PAFParser::DOUBLE_VALUE("^([\\+\\-]?((\\d+\\.\\d*)|(\\d*\\.\\d+))([eE][\\-\\+]?\\d{1,3})?)\\s*");
const regex PAFParser::INT_VALUE("^([+-]?\\d+)\\s*");
const regex PAFParser::ATRUE_VALUE("^(true)\\s*");
const regex PAFParser::AFALSE_VALUE("^(false)\\s*");
const regex PAFParser::QQSTRING_VALUE("^\"([^\"]+)\"\\s*");
const regex PAFParser::QSTRING_VALUE("^'([^']+)'\\s*");
const regex PAFParser::QQSTRING_START("^\"([^\"]*\\S)\\s*");
const regex PAFParser::QSTRING_START("^'([^']*\\S)\\s*");
const regex PAFParser::QQSTRING_END("^\\s*(\\S[^\"]*)\"\\s*");
const regex PAFParser::QSTRING_END("^\\s*(\\S[^']*)'\\s*");
const regex PAFParser::BARE_STRING_LINE("^\\s*(\\S(.*\\S)?)\\s*");
const regex PAFParser::BARE_STRING("^\\s*([^#\\}\\s]([^#\\}]*[^#\\}\\s])?)\\s*[#}]?");
const regex PAFParser::FILE_VALUE("^@");

/*
 * create a parser to load a Policy
 */
PAFParser::PAFParser(Policy& policy) 
    : PolicyParser(policy), _buffer(), _lineno(0), _depth(0)
{ }
PAFParser::PAFParser(Policy& policy, bool strict) 
    : PolicyParser(policy, strict), _buffer(), _lineno(0), _depth(0)
{ }

/*
 * delete this parser
 */
PAFParser::~PAFParser() { } 

/*
 * parse the data found on the given stream
 * @param strm    the stream to read PAF-encoded data from
 * @return int   the number of values primitive values parsed.
 */
int PAFParser::parse(istream& is) {
    int count = _parseIntoPolicy(is, _pol);
    // log count

    return count;
}

ios::iostate PAFParser::_nextLine(istream& is, string& line) {
    if (_buffer.size() > 0) {
        line = _buffer.front(); 
        _buffer.pop_front();
        _lineno++;
        return ios::iostate(0);
    }
    else {
        getline(is, line);
        if (!is.rdstate()) _lineno++;
        return is.rdstate();
    }
}

void PAFParser::_pushBackLine(const string& line) {
    _buffer.push_front(line);
    _lineno--;
}

int PAFParser::_parseIntoPolicy(istream& is, Policy& policy) {

    string line, name, value;
    smatch matched;
    int count = 0;

    while (!_nextLine(is, line)) {
        if (regex_search(line, COMMENT_LINE)) 
            continue;

        if (regex_search(line, matched, CLOSE_SRCH)) {
            _depth--;
            if (_depth < 0) {
                string msg = "extra '}' character encountered.";
                if (_strict) throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
                // log message
            }

            _pushBackLine(matched.suffix());
            return count;
        }
        else if (regex_search(line, matched, PARAM_SRCH)) {

            name = matched.str(2);
            if (! regex_search(name, NAME_MTCH)) {
                string msg = "Not a legal names designation: ";
                msg.append(name);
                if (_strict) 
                    throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
                // log warning
                continue;
            }

            value = matched.suffix();
            count += _addValue(name, value, policy, is);
        }
    }
    if (! is.eof() && is.fail()) throw LSST_EXCEPT(ParserError, "read error", _lineno);

    return count;
}

int PAFParser::_addValue(const string& propname, string& value, 
                         Policy& policy, istream& is) 
{
    string element, msg;
    smatch matched;
    int count = 0;

    if (value.size() == 0 || regex_search(value, COMMENT_LINE))
        // no value provide; ignore it.
        return count;

    if (regex_search(value, matched, OPEN_SRCH)) {
        _depth++;

        // make a sub-policy
        Policy::Ptr subpolicy(new Policy());
        policy.add(propname, subpolicy);

        // look for extra stuff on the line
        value = matched.suffix();
        if (value.size() > 0 && ! regex_search(value, COMMENT_LINE)) 
            _pushBackLine(value);

        // fill in the sub-policy
        count += _parseIntoPolicy(is, *subpolicy);
    }
    else if (regex_search(value, matched, DOUBLE_VALUE)) {
        do {
            element = matched.str(1);
            value = matched.suffix();

            char *unparsed;
            double d = strtod(element.c_str(), &unparsed);
            if (unparsed && (*unparsed)) {
                msg = "value contains unparsable non-numeric data: ";
                msg.append(element);
                if (_strict) throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
                break;
            }

            policy.add(propname, d);
            count++;
            if (value.size() > 0) {
                if (regex_search(value,COMMENT_LINE)) {
                    value.erase();
                    break;
                }
                else if (regex_search(value, CLOSE_SRCH)) {
                    _pushBackLine(value);
                    return count;
                }
            }
            else 
                break;
        } while (regex_search(value, matched, DOUBLE_VALUE));

        if (value.size() > 0) {
            msg = "Expecting double value, found: ";
            msg.append(value);
            if (_strict) throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
            // log message
        }
    }
    else if (regex_search(value, matched, INT_VALUE)) {
        do {
            element = matched.str(1);
            value = matched.suffix();

            char *unparsed;
            long lval = strtol(element.c_str(), &unparsed, 10);
            if (unparsed && (*unparsed)) {
                msg = "value contains unparsable non-integer data: ";
                msg.append(element);
                if (_strict) throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
                continue;
            }

            int ival = int(lval);
            if (lval-ival != 0) {
                // longs are unsupported
                msg = "unsupported long integer value found: ";
                msg.append(value);
                if (_strict) throw LSST_EXCEPT(UnsupportedSyntax, msg, _lineno);
                // log a message
            }

            policy.add(propname, ival);
            count++;

            if (value.size() > 0) {
                if (regex_search(value,COMMENT_LINE)) {
                    value.erase();
                    break;
                }
                else if (regex_search(value, CLOSE_SRCH)) {
                    _pushBackLine(value);
                    return count;
                }
            }
            else 
                break;
        } while (regex_search(value, matched, INT_VALUE));

        if (value.size() > 0) {
            msg = "Expecting integer value, found: ";
            msg.append(value);
            if (_strict) throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
            // log message
        }
    }
    else if (regex_search(value, matched, ATRUE_VALUE) ||
             regex_search(value, matched, AFALSE_VALUE))   
    {
        do {
            element = matched.str(1);
            value = matched.suffix();
            if (element[0] == 't')
                policy.add(propname, true);
            else
                policy.add(propname, false);
            count++;

            if (value.size() > 0) {
                if (regex_search(value,COMMENT_LINE)) {
                    value.erase();
                    break;
                }
                else if (regex_search(value, CLOSE_SRCH)) {
                    _pushBackLine(value);
                    return count;
                }
            }
            else 
                break;
        } while (regex_search(value, matched, ATRUE_VALUE) ||
                 regex_search(value, matched, AFALSE_VALUE));

        if (value.size() > 0) {
            msg = "Expecting boolean value, found: ";
            msg.append(value);
            if (_strict) 
                throw LSST_EXCEPT(FormatSyntaxError, msg, _lineno);
            // log message
        }
    }
    else if (regex_search(value, QQSTRING_START) ||
             regex_search(value, QSTRING_START)) 
    {
        do {
            if (regex_search(value, matched, QQSTRING_VALUE) ||
                regex_search(value, matched, QSTRING_VALUE))   
            {
                element = matched.str(1);
                value = matched.suffix();

                policy.add(propname, element);
                count++;

                if (value.size() > 0 && regex_search(value, COMMENT_LINE)) 
                    value.erase();
            }
            else if (regex_search(value, matched, QQSTRING_START)) {
                // start of multi-line string
                element = matched.str(1);
                while (!_nextLine(is, value)) {
                    element.append(" ");
                    if (regex_search(value, matched, QQSTRING_END)) {
                        element.append(matched.str(1));
                        policy.add(propname, element);
                        count++;
                        value = matched.suffix();
                        break;
                    }
                    else if (regex_search(value, matched, BARE_STRING_LINE)) {
                        element.append(matched.str(1));
                    }
                }
                if (is.fail()) 
                    throw LSST_EXCEPT(ParserError, "read error", _lineno);
                if (is.eof()) {
                    if (_strict) throw LSST_EXCEPT(EOFError, _lineno);
                    // log message
                }
            }
            else if (regex_match(value, matched, QSTRING_START)) {
                // start of multi-line string
                element = matched.str(1);
                while (!_nextLine(is, value)) {
                    element.append(" ");
                    if (regex_search(value, matched, QSTRING_END)) {
                        element.append(matched.str(1));
                        policy.add(propname, element);
                        count++;
                        value = matched.suffix();
                        break;
                    }
                    else if (regex_match(value, matched, BARE_STRING_LINE)) {
                        element.append(matched.str(1));
                    }
                }
                if (is.fail()) 
                    throw LSST_EXCEPT(ParserError, "read error", _lineno);
                if (is.eof()) {
                    if (_strict) throw LSST_EXCEPT(EOFError, _lineno);
                    // log message
                }
            }

            if (value.size() > 0) {
                if (regex_search(value,COMMENT_LINE)) {
                    value.erase();
                    break;
                }
                else if (regex_search(value, CLOSE_SRCH)) {
                    _pushBackLine(value);
                    return count;
                }
            }
            else 
                break;
        } while (regex_search(value, QQSTRING_START) ||
                 regex_search(value, QSTRING_START));
    }
    else if (regex_search(value, matched, BARE_STRING)) {
        string trimmed = matched.str(1);
        int resume = matched.position(1) + matched.length(1);
        if (regex_search(trimmed, matched, FILE_VALUE)) {
            policy.add(propname, 
                     Policy::FilePtr(new PolicyFile(matched.suffix().str())));
        }
        else {
            policy.add(propname, trimmed);
        }
        count++;
        value = value.substr(resume);
        if (regex_search(value, matched, CLOSE_SRCH)) {
            _pushBackLine(value);
        }
    }

    return count;
}



}}}}   // end lsst::pex::policy::paf
