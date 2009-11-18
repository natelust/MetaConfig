// -*- lsst-c++ -*-
/**
 * @file PolicyParserFactory.h
 * @ingroup pex
 * @brief a definition of the PolicyParserFactory class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_PARSERFACTORY_H
#define LSST_PEX_POLICY_PARSERFACTORY_H

#include <string>

#include "lsst/daf/base/Citizen.h"
#include "lsst/pex/policy/Policy.h"

#include <boost/shared_ptr.hpp>

namespace lsst {
namespace pex {
namespace policy {

// forward declaration
class PolicyParser;

namespace dafBase = lsst::daf::base;

// class PolicyParserFactory : public Citizen {  // causing deletion problems

/**
 * @brief an abstract factory class for creating PolicyParser instances.  
 * This class is used by the PolicySource class to determine the format
 * of a stream of serialized Policy data and then parse it into a Policy 
 * instance.  It is intended that for supported each format there is an
 * implementation of this class and a corresponding PolicyParser class.  
 */
class PolicyParserFactory {
public: 

    typedef boost::shared_ptr<PolicyParserFactory> Ptr;

    /**
     * create a factory
     */
    PolicyParserFactory() { }

//    PolicyParserFactory() : Citizen(typeid(this)) { }

    /**
     * destroy this factory
     */
    virtual ~PolicyParserFactory();

    /**
     * create a new PolicyParser class and return a pointer to it.  The 
     * caller is responsible for destroying the pointer.
     * @param policy   the Policy object that data should be loaded into.
     * @param strict   if true, be strict in reporting errors in file 
     *                   contents and syntax.  If false, errors will be 
     *                   ignored if possible; often, such errors will 
     *                   result in some data not getting loaded.  The 
     *                   default is true.
     */
    virtual PolicyParser* createParser(Policy& policy, 
                                       bool strict=true) const = 0;

    /**
     * analyze the given string assuming contains the leading characters 
     * from the data stream and return true if it is recognized as being in 
     * the format supported by this parser.  If it is, return the name of 
     * the this format; 
     */
    virtual bool isRecognized(const std::string& leaders) const = 0;

    /**
     * return the name for the format supported by the parser
     */
    virtual const std::string& getFormatName();

    /** 
     * an empty string representing an unrecognized format
     */
    static const std::string UNRECOGNIZED;
};

}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_PARSERFACTORY_H


