// -*- lsst-c++ -*-
/**
 * @class SupportedFormats
 * 
 * @brief a representation of a src of serialized Policy parameter data
 * 
 * @author Ray Plante
 * 
 */

#ifndef LSST_PEX_POLICY_SUPPORTEDFORMATS_H
#define LSST_PEX_POLICY_SUPPORTEDFORMATS_H

#include <map>

#include "lsst/pex/policy/PolicyParserFactory.h"

#include <boost/shared_ptr.hpp>

namespace lsst {
namespace pex {
namespace policy {

using namespace std;

// class SupportedFormats : public Citizen { // causes problems in construction

/**
 * @brief a list of supported Policy formats.  It can be used to determine 
 * the format type for a Policy data stream.
 */
class SupportedFormats {
public: 

    typedef shared_ptr<SupportedFormats> Ptr;

//    SupportedFormats() : Citizen(typeid(this)), _formats() { }

    SupportedFormats() : _formats() { }

    /**
     * register a factory method for policy format parsers
     */
    void registerFormat(const PolicyParserFactory::Ptr& factory);

    /**
     * analyze the given string assuming contains the leading characters 
     * from the data stream and return true if it is recognized as being in 
     * the format supported by this parser.  If it is, return the name of 
     * the this format; 
     */
    const string& recognizeType(const string& leaders) const;

    /**
     * return true if the name resolves to a registered format
     */
    bool supports(const string& name) const {
        return (_formats.find(name) != _formats.end());
    }

    /**
     * get a pointer to a factory with a given name.  A null pointer is 
     * returned if the name is not recognized.
     */
    PolicyParserFactory::Ptr getFactory(const string& name) const;

    /**
     * initialize a given SupportFormats instance with the formats known
     * by default.  
     */
    static void initDefaultFormats(SupportedFormats& sf);

    /**
     * return the number formats currently registered
     */
    int size() { return _formats.size(); } 

private:
    typedef map<string, PolicyParserFactory::Ptr> Lookup;
    Lookup _formats;
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_SUPPORTEDFORMATS_H


