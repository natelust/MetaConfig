// -*- lsst-c++ -*-
%define policy_DOCSTRING
"
Access to the policy classes from the pex module
"
%enddef

%feature("autodoc", "1");
%module(package="lsst.pex.policy", docstring=policy_DOCSTRING) policyLib

// Supress warnings
#pragma SWIG nowarn=314     // print is a python keyword (--> _print)


%{
#include "lsst/daf/base.h"
#include "lsst/pex/policy/exceptions.h"
#include "lsst/pex/policy/Policy.h"
#include "lsst/pex/policy/PolicyFile.h"
#include <sstream>

using lsst::pex::policy::SupportedFormats;
using lsst::pex::policy::PolicyParserFactory;
%}

%inline %{
namespace boost { namespace filesystem { } }
%}

// For now, pex_policy does not use the standard LSST exception classes,
// so disable the associated SWIG exception handling machinery
#define NO_SWIG_LSST_EXCEPTIONS

%include "lsst/p_lsstSwig.i"

%import "lsst/daf/base/baseLib.i"

%typemap(out) std::vector<double,std::allocator<double > >& {
    int len = (*$1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i,PyFloat_FromDouble((*$1)[i]));
    }
}

%typemap(out) std::vector<int,std::allocator<int > >& {
    int len = (*$1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i,PyInt_FromLong((*$1)[i]));
    }
}

%typemap(out) std::vector<boost::shared_ptr<std::string > >& {
    int len = (*$1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i,PyString_FromString((*$1)[i]->c_str()));
    }
}

%typemap(out) std::vector<bool,std::allocator<bool > >& {
    int len = (*$1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        PyList_SetItem($result,i, ( ((*$1)[i]) ? Py_True : Py_False ) );
    }
}

%typemap(out) std::vector<boost::shared_ptr<lsst::pex::policy::Policy > >& {
    int len = (*$1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        boost::shared_ptr<lsst::pex::policy::Policy> * smartresult =
            new boost::shared_ptr<lsst::pex::policy::Policy>((*$1)[i]);
        PyObject * obj = SWIG_NewPointerObj(SWIG_as_voidptr(smartresult),
            SWIGTYPE_p_boost__shared_ptrT_lsst__pex__policy__Policy_t,
            SWIG_POINTER_NEW | SWIG_POINTER_OWN);
        PyList_SetItem($result, i, obj);
    }
}

%typemap(out) std::vector<boost::shared_ptr<lsst::pex::policy::PolicyFile > >& {
    int len = (*$1).size();
    $result = PyList_New(len);
    for (int i = 0; i < len; i++) {
        boost::shared_ptr<lsst::pex::policy::PolicyFile> * smartresult =
            new boost::shared_ptr<lsst::pex::policy::PolicyFile>((*$1)[i]);
        PyObject * obj = SWIG_NewPointerObj(SWIG_as_voidptr(smartresult),
            SWIGTYPE_p_boost__shared_ptrT_lsst__pex__policy__PolicyFile_t,
            SWIG_POINTER_NEW | SWIG_POINTER_OWN);
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

%exception {
    try {
        $action;
    } catch (lsst::pex::policy::NameNotFound &e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    } catch (lsst::pex::policy::TypeError &e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    } catch (lsst::pex::policy::BadNameError &e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    } catch (lsst::pex::policy::IOError &e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    } catch (std::exception &e) {
        SWIG_exception(SWIG_RuntimeError, 
            std::string(e.what()).append(" (").append(typeid(e).name()).append(")").c_str());
    } catch (...) {
       SWIG_exception(SWIG_RuntimeError, "unknown error while handling policy");
    }
}

%template(NameList) std::list<std::string >;

SWIG_SHARED_PTR(Policy, lsst::pex::policy::Policy)
SWIG_SHARED_PTR(PolicySource, lsst::pex::policy::PolicySource)
SWIG_SHARED_PTR_DERIVED(PolicyFile, lsst::pex::policy::PolicySource, lsst::pex::policy::PolicyFile)

%newobject lsst::pex::policy::Policy::createPolicy;

%include "lsst/pex/policy/Policy.h"

%extend lsst::pex::policy::Policy {
    std::string toString() {
       std::ostringstream msg;
       self->print(msg);
       return msg.str();
    }
}

%pythoncode %{
Policy.__str__ = Policy.toString

def _Policy_get(p, name, defval=None):
    type = p.getValueType(name);
    if (type == p.UNDEF):  return defval

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

def _Policy_getArray(p, name, defarray=None):
    type = p.getValueType(name);
    if (type == p.UNDEF):  return defarray

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

Policy.get = _Policy_get
Policy.getArray = _Policy_getArray
%}

%ignore lsst::pex::policy::PolicySource::defaultFormats;
%include "lsst/pex/policy/PolicySource.h"
%include "lsst/pex/policy/PolicyFile.h"

