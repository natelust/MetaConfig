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
 
%define policy_DOCSTRING
"
Access to the policy classes from the pex module
"
%enddef

%feature("autodoc", "1");
%module(package="lsst.pex.policy", docstring=policy_DOCSTRING) policyLib

// Supress warnings
#pragma SWIG nowarn=314     // print is a python keyword (--> _print)
#pragma SWIG nowarn=362     // operator= ignored
#pragma SWIG nowarn=451     // const char* may leak memory
#pragma SWIG nowarn=509     // overloaded method is shadowed

%{
#include "boost/filesystem/path.hpp"
#include "lsst/daf/base.h"
#include "lsst/pex/policy/exceptions.h"
#include "lsst/pex/policy/parserexceptions.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/Dictionary.h"
#include "lsst/pex/policy/PolicyFile.h"
#include "lsst/pex/policy/DefaultPolicyFile.h"
#include "lsst/pex/policy/UrnPolicyFile.h"
#include "lsst/pex/policy/PolicyString.h"
#include "lsst/pex/policy/PolicyStreamDestination.h"
#include "lsst/pex/policy/PolicyStringDestination.h"
#include "lsst/pex/policy/paf/PAFWriter.h"
#include <sstream>

using lsst::pex::policy::SupportedFormats;
using lsst::pex::policy::PolicyParserFactory;
%}

%inline %{
namespace boost { namespace filesystem { } }
%}

// For now, pex_policy does not use the standard LSST exception classes,
// so disable the associated SWIG exception handling machinery
// #define NO_SWIG_LSST_EXCEPTIONS

%include "lsst/p_lsstSwig.i"

%import "lsst/daf/base/baseLib.i"
%import "lsst/pex/exceptions/exceptionsLib.i"    // for Exceptions

%typemap(out) std::vector<double,std::allocator<double > > {
    int len = ($1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i,PyFloat_FromDouble(($1)[i]));
    }
}

%typemap(out) std::vector<int,std::allocator<int > > {
    int len = ($1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i,PyInt_FromLong(($1)[i]));
    }
}

%typemap(out) std::vector<std::string > {
    int len = ($1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i,PyString_FromString(($1)[i].c_str()));
    }
}

%typemap(out) std::vector<bool,std::allocator<bool > > {
    int len = ($1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
       if (($1)[i]) {
           Py_INCREF(Py_True);
           PyList_SetItem($result, i, Py_True);
       } else {
           Py_INCREF(Py_False);
           PyList_SetItem($result, i, Py_False);
       }
    }
}

%typemap(out) std::vector<boost::shared_ptr<lsst::pex::policy::Policy > > {
    int len = ($1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        boost::shared_ptr<lsst::pex::policy::Policy> * smartresult =
            new boost::shared_ptr<lsst::pex::policy::Policy>(($1)[i]);
        PyObject * obj = SWIG_NewPointerObj(SWIG_as_voidptr(smartresult),
            SWIGTYPE_p_boost__shared_ptrT_lsst__pex__policy__Policy_t,
            SWIG_POINTER_OWN);
        PyList_SetItem($result, i, obj);
    }
}

%typemap(out) std::vector<boost::shared_ptr<lsst::pex::policy::PolicyFile > > {
    int len = (*(&$1)).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        boost::shared_ptr<lsst::pex::policy::PolicyFile> * smartresult =
            new boost::shared_ptr<lsst::pex::policy::PolicyFile>((*(&$1))[i]);
        PyObject * obj = SWIG_NewPointerObj(SWIG_as_voidptr(smartresult),
            SWIGTYPE_p_boost__shared_ptrT_lsst__pex__policy__PolicyFile_t,
            SWIG_POINTER_OWN);
        PyList_SetItem($result, i, obj);
    }
}

%typemap(in,numinputs=0) std::list<std::string > &names (std::list<std::string > temp) {
    $1 = &temp;
}

%typemap(argout) std::list<std::string > &names {
    int len = (*$1).size();
    $result = PyList_New(len);
    std::list<std::string >::iterator sp;
    int i = 0;
    for (sp = (*$1).begin(); sp != (*$1).end(); sp++, i++) {
        PyList_SetItem($result,i,PyString_FromString(sp->c_str()));
    }
}

// Tell SWIG that boost::filesystem::path is equivalent to a string for typechecking purposes
%typemap(typecheck) const lsst::pex::policy::fs::path & = char *;

%typemap(out) const boost::filesystem::path& {
   $result = PyString_FromString($1->string().c_str());
} 

%typemap(out) const lsst::pex::policy::fs::path& {
   $result = PyString_FromString($1->string().c_str());
} 

// Convert Python strings to boost::filesystem::path objects
%typemap(in) const lsst::pex::policy::fs::path & {
    std::string * temp;
    int cnvRes = SWIG_AsPtr_std_string($input, &temp);
    if (!SWIG_IsOK(cnvRes)) {
        SWIG_exception_fail(SWIG_ArgError(cnvRes), "failed to convert Python input to C++ string");
    }
    if (!temp) {
        SWIG_exception_fail(SWIG_ValueError, "invalid null reference in input");
    }
    $1 = new boost::filesystem::path(*temp);
    delete temp;
}

// Make sure temporary created above is freed inside wrapper code
%typemap(freearg) const lsst::pex::policy::fs::path & {
    delete $1;
}


%template(NameList) std::list<std::string >;

SWIG_SHARED_PTR(Policy, lsst::pex::policy::Policy)
SWIG_SHARED_PTR_DERIVED(Dictionary, lsst::pex::policy::Policy, lsst::pex::policy::Dictionary)
SWIG_SHARED_PTR(Definition, lsst::pex::policy::Definition)
SWIG_SHARED_PTR(PolicySource, lsst::pex::policy::PolicySource)
SWIG_SHARED_PTR_DERIVED(PolicyFile, lsst::pex::policy::PolicySource, lsst::pex::policy::PolicyFile)
SWIG_SHARED_PTR_DERIVED(DefaultPolicyFile, lsst::pex::policy::PolicyFile, lsst::pex::policy::DefaultPolicyFile)
SWIG_SHARED_PTR_DERIVED(UrnPolicyFile, lsst::pex::policy::PolicyFile, lsst::pex::policy::UrnPolicyFile)
SWIG_SHARED_PTR_DERIVED(PolicyString, lsst::pex::policy::PolicySource, lsst::pex::policy::PolicyString)
SWIG_SHARED_PTR(PolicyDestination, lsst::pex::policy::PolicyDestination)
SWIG_SHARED_PTR_DERIVED(PolicyStreamDestination, lsst::pex::policy::PolicyDestination, lsst::pex::policy::PolicyStreamDestination)
SWIG_SHARED_PTR_DERIVED(PolicyStringDestination, lsst::pex::policy::PolicyStreamDestination, lsst::pex::policy::PolicyStringDestination)

%newobject lsst::pex::policy::Policy::createPolicy;
%newobject lsst::pex::policy::Policy::createPolicyFromUrn;
%newobject lsst::pex::policy::Dictionary::makeDef;
%feature("notabstract") lsst::pex::policy::paf::PAFWriter;

%ignore lsst::pex::policy::Policy::Policy(const Policy& pol);

%include "lsst/pex/policy/Policy.h"
%include "lsst/pex/policy/Dictionary.h"
%include "lsst/pex/policy/PolicyWriter.h"
%include "lsst/pex/policy/PolicySource.h"
%include "lsst/pex/policy/PolicyFile.h"
%include "lsst/pex/policy/DefaultPolicyFile.h"
%include "lsst/pex/policy/UrnPolicyFile.h"
%include "lsst/pex/policy/paf/PAFWriter.h"
%include "lsst/pex/policy/exceptions.h"
%include "lsst/pex/policy/parserexceptions.h"

%template(vector_Policy_Ptr) std::vector<boost::shared_ptr<lsst::pex::policy::Policy> >;

%extend lsst::pex::policy::Policy {
    void _setBool(const std::string& name, bool value) {
       self->set(name, value);
    }

    void _addBool(const std::string& name, bool value) {
       self->add(name, value);
    }
}

%pythoncode %{
Policy.__str__ = Policy.toString

def _Policy_get(p, name):
    type = p.getValueType(name);
    if (type == p.UNDEF):
        return p.getInt(name) # will raise an exception
        # raise NameNotFound("Policy parameter name not found: " + name)

    if (type == p.INT):
        return p.getInt(name)
    elif (type == p.DOUBLE):
        return p.getDouble(name)
    elif (type == p.BOOL):
        return p.getBool(name)
    elif (type == p.STRING):
        return p.getString(name)
    elif (type == p.POLICY):
        return p.getPolicy(name)
    elif (type == p.FILE):
        return p.getFile(name)

def _Policy_getArray(p, name):
    type = p.getValueType(name);
    if (type == p.UNDEF):
        return p.getIntArray(name) # will raise an exception
        # raise NameNotFound("Policy parameter name not found: " + name)

    if (type == p.INT):
        return p.getIntArray(name)
    elif (type == p.DOUBLE):
        return p.getDoubleArray(name)
    elif (type == p.BOOL):
        return p.getBoolArray(name)
    elif (type == p.STRING):
        return p.getStringArray(name)
    elif (type == p.POLICY):
        return p.getPolicyArray(name)
    elif (type == p.FILE):
        return p.getFileArray(name)

Policy.get = _Policy_get
Policy.getArray = _Policy_getArray

_Policy_wrap_set = Policy.set
def _Policy_set(p, name, value):
    if isinstance(value, bool):
        p._setBool(name, value)
    elif (value == None):
        raise RuntimeError("Attempt to set value of \"" + name + "\" to None.  Values must be non-None.  Use remove() instead.")
#        raise lsst.pex.exceptions.InvalidParameterException("Value of " + name + " cannot be None.")
    else:
        _Policy_wrap_set(p, name, value)
Policy.set = _Policy_set

_Policy_wrap_add = Policy.add
def _Policy_add(p, name, value):
    if isinstance(value, bool):
        p._addBool(name, value)
    else:
        _Policy_wrap_add(p, name, value)
Policy.add = _Policy_add
%}

%ignore lsst::pex::policy::PolicySource::defaultFormats;
%ignore lsst::pex::policy::PolicyFile::SPACE_RE;
%ignore lsst::pex::policy::PolicyFile::COMMENT;
%ignore lsst::pex::policy::PolicyFile::CONTENTID;
%ignore lsst::pex::policy::PolicyString::SPACE_RE;
%ignore lsst::pex::policy::PolicyString::COMMENT;
%ignore lsst::pex::policy::PolicyString::CONTENTID;
%include "lsst/pex/policy/PolicySource.h"
%include "lsst/pex/policy/PolicyFile.h"
%include "lsst/pex/policy/DefaultPolicyFile.h"
%include "lsst/pex/policy/UrnPolicyFile.h"
%include "lsst/pex/policy/PolicyString.h"
#if 0                                   // needed, but needs to propagate up to e.g. afw
%include "lsst/pex/policy/PolicyDestination.h"
#endif
%include "lsst/pex/policy/PolicyStreamDestination.h"
%include "lsst/pex/policy/PolicyStringDestination.h"
