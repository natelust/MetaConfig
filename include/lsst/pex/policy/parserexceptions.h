// -*- lsst-c++ -*-
/*
 * @ingroup pex
 *
 * @brief exceptions characterizing errors in the use of Policies
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_PARSER_EXCEPTIONS_H
#define LSST_PEX_POLICY_PARSER_EXCEPTIONS_H

#include <stdexcept>
#include <sstream>

namespace lsst {
namespace pex {
namespace policy {

using namespace std;

/**
 * an parent exception for errors that occur during the parsing of policy 
 * files.  
 */
class ParserError : public runtime_error {
public:
    //@{
    /**
     * Create an exception the exception with a given message.
     * @param msg     a message describing the problem.
     * @param lineno  a line number in the file (or stream) being parsed 
     *                  where the problem occurred.  The first line of the 
     *                  file is typically line 1.  
     */
    ParserError() : runtime_error("Unspecified parsing error encountered") { }
    ParserError(const string& msg) : runtime_error(msg) { }
    ParserError(const string& msg, int lineno) 
        : runtime_error(makeLocatedMessage(msg,lineno)) { }
    //@}

    static string makeLocatedMessage(const string& msg, int lineno) {
        ostringstream out;
        out << "Policy Parsing Error:" << lineno << ": " << msg << ends;
        return out.str();
    }
};

/**
 * an exception indicated that the stream being parsed ended prematurely.
 */
class EOFError : public ParserError {
public:
    //@{
    /**
     * Create an exception the exception with a given message.
     * @param msg     a message describing the problem.
     * @param lineno  a line number in the file (or stream) being parsed 
     *                  where the problem occurred.  The first line of the 
     *                  file is typically line 1.  
     */
    EOFError() : ParserError("Unexpected end of Policy data stream") { }
    EOFError(const string& msg) : ParserError(msg) { }
    EOFError(int lineno) 
        : ParserError("Unexpected end of Policy data stream", lineno) 
    { }
    EOFError(const string& msg, int lineno) : ParserError(msg, lineno) { }
    //@}
};

/**
 * an exception thrown because a general syntax error was encountered.
 */
class SyntaxError : public ParserError {
public:
    //@{
    /**
     * Create an exception the exception with a given message.
     * @param msg     a message describing the problem.
     * @param lineno  a line number in the file (or stream) being parsed 
     *                  where the problem occurred.  The first line of the 
     *                  file is typically line 1.  
     */
    SyntaxError() : ParserError("Unknonwn syntax error") { }
    SyntaxError(const string& msg) : ParserError(msg) { }
    SyntaxError(const string& msg, int lineno) : ParserError(msg, lineno) { }
    //@}
};

/**
 * an exception thrown because a syntax error specific to the format
 * being parsed was encountered.
 */
class FormatSyntaxError : public SyntaxError {
public:
    //@{
    /**
     * Create an exception the exception with a given message.
     * @param msg     a message describing the problem.
     * @param lineno  a line number in the file (or stream) being parsed 
     *                  where the problem occurred.  The first line of the 
     *                  file is typically line 1.  
     */
    FormatSyntaxError() : SyntaxError("Unknonwn syntax error") { }
    FormatSyntaxError(const string& msg) : SyntaxError(msg) { }
    FormatSyntaxError(const string& msg, int lineno) 
        : SyntaxError(msg, lineno) { }
    //@}
};

/**
 * an exception thrown because syntax was encountered that is legal for the 
 * format being parsed but which is not supported for encoding Policies.  
 */
class UnsupportedSyntax : public SyntaxError {
public:
    //@{
    /**
     * Create an exception the exception with a given message.
     * @param msg     a message describing the problem.
     * @param lineno  a line number in the file (or stream) being parsed 
     *                  where the problem occurred.  The first line of the 
     *                  file is typically line 1.  
     */
    UnsupportedSyntax() : SyntaxError("Unsupported syntax error") { }
    UnsupportedSyntax(const string& msg) : SyntaxError(msg) { }
    UnsupportedSyntax(const string& msg, int lineno) 
        : SyntaxError(msg, lineno) { }
    //@}
};




}}}  // end namespace lsst::pex::policy


#endif // LSST_PEX_POLICY_PARSER_EXCEPTIONS_H
