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
 * @file PolicyConfigured.h
 * @ingroup pex
 * @brief definition of the PolicyConfigured interface class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_POLICYCONFIGURED_H
#define LSST_PEX_POLICY_POLICYCONFIGURED_H

#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/Policy.h"

namespace lsst {
namespace pex {
namespace policy {

/**
 * @brief an interface to indicate that a class is configured with a Policy
 * 
 * The purpose of this class is to provide a uniform way of delivering 
 * a Policy instance to an object that needs one.  A class that expects 
 * to configure itself with a Policy should inherit from this class 
 * (typically via multi-inheritance).  It should also provide a constructor
 * that takes a const PolicyPtr reference as a parameter (which it can 
 * passed to the PolicyConfigured constructor).  
 *
 * The intended workflow for use of this API allows for uniform collaboration 
 * between the class to be configured--the target--and the object that will 
 * create an instance of the class--the user.  The user first calls the 
 * target class's getDefaultPolicySource() static function.  The user uses
 * this to construct an initial Policy.  The policy data is then overridden
 * by the user based either on a runtime-specified Policy file or via a Policy 
 * it has been given.  The user then constructs the target instance, passing
 * in the updated Policy object to the target's constructor.  
 *
 * The target is then free to use Policy data as it needs to by first calling 
 * its getPolicy() function.  A few other functions (some of which are 
 * protected so that only the target can call them) are provided to help 
 * manage the configuration process.  When the configuration is complete, it 
 * may call configured(); its isConfigured() function (which initially returns 
 * false) will now return true.  Alternatively, it may call its done() method,
 * which both calls configured() and releases its copy of the policy pointer 
 * (via forgetPolicy()).  Subclasses may override this done() to trigger other
 * post-configuration activities.  The target is not obligated to ever call 
 * configured() or done() (currently no pex-related module depends on it); 
 * however, the target itself or its collaborators may find this useful.  
 *
 * The driving use case is pex/harness module which uses this API to configure 
 * Stage objects that make up a pipeline.  
 * 
 */
class PolicyConfigured {
public: 
    typedef Policy::Ptr PolicyPtr;
    typedef Policy::ConstPtr ConstPolicyPtr;
    typedef boost::shared_ptr<PolicySource> PolicySourcePtr;

    /**
     * configure this class with a policy.  
     * @param policy   a pointer (which may be null) pointing to a policy
     *                    that should be used to configure this class.
     */
    PolicyConfigured(const PolicyPtr& policy) : _policy(policy) { }

    /**
     * construct without configuration from a policy
     */
    PolicyConfigured() : _policy() { }

    /**
     * delete this interface
     */
    virtual ~PolicyConfigured();

    /**
     * return the policy that is being used to configure this object.
     * This is usually the policy that was passed to this object at 
     * construction time.  The returned pointer may be null if no such 
     * policy is available.  The const return type is to indicate that 
     * external users should not attempt to update the contents of the 
     * returned policy.
     */
    ConstPolicyPtr getPolicy() const { return _policy; }

    /**
     * return true if this object has been configured
     */
    bool isConfigured() const { return _configured; }

    /**
     * return a PolicySource pointer that can be used to create a 
     * default Policy for instances of this class.  This implementation 
     * returns a null pointer.  Subclasses may override this function,
     * usually returning a pointer to a DefaultPolicyFile.
     */
    static PolicySourcePtr getDefaultPolicySource() {
        return PolicySourcePtr();
    }

protected:

    /**
     * return the policy that should be used to configure this object.
     * The returned pointer may be null.  This class may change it contents 
     * for internal purposes.  
     */
    PolicyPtr getPolicy() { return _policy; }

    /**
     * set the policy pointer to null
     */
    void forgetPolicy() { _policy.reset((Policy*)0); }

    /**
     * indicate that this object is now configured.  This will cause 
     * isConfigured() to return true
     */
    void configured() { _configured = true; }
    
    /**
     * indicate that this object is done with the policy provided in 
     * the constructor.  The default implementation does two things: 
     * (1) calls configured(), and (2) calls forgetPolicy().  Subclasses 
     * may override this function.
     */
    virtual void done();

private:
    PolicyPtr _policy;
    bool _configured;

};

}}}  // end namespace lsst::pex::policy



#endif  // LSST_PEX_POLICY_POLICYCONFIGURED_H
