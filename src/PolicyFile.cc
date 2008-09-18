/**
 * @class PolicyFile
 * 
 * @ingroup pex
 *
 * @author Ray Plante
 * 
 */
#include <fstream>

#include <boost/scoped_ptr.hpp>
#include <boost/filesystem/convenience.hpp>

#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/PolicyParser.h"
#include "lsst/pex/policy/exceptions.h"
#include "lsst/pex/policy/parserexceptions.h"
#include "lsst/pex/policy/paf/PAFParserFactory.h"

namespace lsst {
namespace pex {
namespace policy {

using boost::regex_match;
using boost::regex_search;
using boost::scoped_ptr;
using lsst::pex::policy::paf::PAFParserFactory;

const string PolicyFile::EXT_PAF(".paf");
const string PolicyFile::EXT_XML(".xml");

const regex PolicyFile::SPACE_RE("^\\s*$");
const regex PolicyFile::COMMENT("^\\s*#");
const regex 
          PolicyFile::CONTENTID("^\\s*#\\s*<\\?cfg\\s+\\w+(\\s+\\w+)*\\s*\\?>",
                                regex::icase);

/**
 * create a Policy file that points a file with given path.
 * @param filepath   the path to the file
 */
PolicyFile::PolicyFile(const SupportedFormats::Ptr& fmts) 
    : PolicySource(fmts), _file(PolicyParserFactory::UNRECOGNIZED) 
{ }

PolicyFile::PolicyFile(const string& filepath, 
                       const SupportedFormats::Ptr& fmts) 
    : PolicySource(fmts), _file(filepath) 
{ }

PolicyFile::PolicyFile(const fs::path& filepath, 
                       const SupportedFormats::Ptr& fmts) 
    : PolicySource(fmts), _file(filepath), _format(), _pfact()
{ }

PolicyFile::PolicyFile(const string& filepath, 
                       const PolicyParserFactory::Ptr& parserFactory)
    : PolicySource(), _file(filepath), _format(), _pfact(parserFactory)
{ 
    if (! _pfact.get()) _format = _pfact->getFormatName();
}

PolicyFile::PolicyFile(const fs::path& filepath, 
                       const PolicyParserFactory::Ptr& parserFactory)
    : PolicySource(), _file(filepath), _format(), _pfact(parserFactory) 
{ 
    if (! _pfact.get()) _format = _pfact->getFormatName();
}

/**
 * return the name of the format that the data is stored in.  This may 
 * cause the first few records of the source to be read.
 * @exception IOError   if an error occurs while reading the first few
 *                      characters of the source stream.
 */
const string& PolicyFile::getFormatName() {
    if (_format.size() != 0) return _format;
    if (_file.empty()) return PolicyParserFactory::UNRECOGNIZED;

    // check the extension first
    string ext = fs::extension(_file);
    if (! ext.empty()) {
        if (ext == EXT_PAF) {
            if (_formats->supports(PAFParserFactory::FORMAT_NAME)) 
                return cacheName(PAFParserFactory::FORMAT_NAME);
        }
        else if (ext == EXT_XML) {
            return cacheName("XML");
        }
    }

    // try reading the initial characters
    if (fs::exists(_file)) {
        ifstream is(_file.string().c_str());
        if (is.fail()) 
            throw IOError("failure opening Policy file: " + 
                          fs::complete(_file).string());

        // skip over comments
        string line;
        getline(is, line);
        while (is.good() && 
               (regex_match(line, SPACE_RE) || 
                (regex_search(line, COMMENT) && !regex_search(line, COMMENT))))
        { }
            
        if (is.fail()) 
            throw IOError("failure reading Policy file: " + 
                          fs::complete(_file).string());
        if (is.eof() && 
            (regex_match(line, SPACE_RE) || 
             (regex_search(line, COMMENT) && !regex_search(line, COMMENT))))
        {
            // empty file; let's just assume PAF (but don't cache the name).
            return PAFParserFactory::FORMAT_NAME;
        }

        return cacheName(_formats->recognizeType(line));
    }

    return PolicyParserFactory::UNRECOGNIZED;
}

/**
 * load the data from this Policy source into a Policy object
 * @param policy    the policy object to load the data into
 * @exception ParserError  if an error occurs while parsing the data
 * @exception IOError   if an I/O error occurs while reading from the 
 *                       source stream.
 */
void PolicyFile::load(Policy& policy) { 

    PolicyParserFactory::Ptr pfactory = _pfact;
    if (! pfactory.get()) {
        const string& fmtname = getFormatName();
        if (fmtname.empty()) 
            throw ParserError("Unknown Policy format: " + _file.string());

        pfactory = _formats->getFactory(fmtname);
    }

    scoped_ptr<PolicyParser> parser(pfactory->createParser(policy));

    ifstream fs(_file.string().c_str());
    if (fs.fail()) 
        throw IOError("failure opening Policy file: " + 
                      fs::complete(_file).string());

    parser->parse(fs);
    fs.close();
}

}}}   // end lsst::pex::policy
