#include <iostream>
#include <stdio.h>
#include <assert.h>

#include <Python.h>
#include <boost/shared_ptr.hpp>
#include "lsst/pex/policy/Policy.h"

using namespace std;
namespace pexPolicy = lsst::pex::policy;

int main(int argc, char** args) {
  PyObject *pName, *pModule, *pDict, *pFunc;
  PyObject *pArgs, *pValue;
  PyObject *policyClass;
  PyObject *confString;
  PyObject* pPolicy;
  PyObject* pPtr;
  int i;
  void* vp;

  if (argc < 2) {
    fprintf(stderr, "Usage: %s <config-file.py>\n", args[0]);
    return 1;
  }

  Py_Initialize();

  //pName = PyString_FromString("lsst.pex.policy.pypolicy");

  pName = PyString_FromString("strpolicy");
  assert(pName);
  pModule = PyImport_Import(pName);
  Py_DECREF(pName);
  if (!pModule) {
    fprintf(stderr, "Failed to load strpolicy\n");
    return -1;
  }

  pFunc = PyObject_GetAttrString(pModule, "strpolicy");
  assert(pFunc);

  confString = PyString_FromString("dict(a=4, b=6)");
  pArgs = PyTuple_Pack(1, confString);
  assert(pArgs);

  pValue = PyObject_CallObject(pFunc, pArgs);
  Py_DECREF(pArgs);
  if (!pValue) {
    fprintf(stderr, "call to strpolicy() failed.\n");
    PyErr_Print();
    return -1;
  }

  // not req'd, probably...
  pPolicy = PyTuple_GetItem(pValue, 0);

  pPtr = PyTuple_GetItem(pValue, 1);

  //vp = static_cast<void*>(PyInt_AsLong(pValue));
  //vp = reinterpret_cast<void*>(PyInt_AsLong(pValue));
  vp = reinterpret_cast<void*>(PyInt_AsLong(pPtr));
  printf("vp %p\n", vp);

  //pexPolicy::Policy::Ptr pp = *((pexPolicy::Policy::Ptr*)vp);
  pexPolicy::Policy::Ptr* pp = reinterpret_cast<pexPolicy::Policy::Ptr*>(vp);
  printf("pp %p\n", pp);
  printf("%p\n", pp->get());

  pexPolicy::Policy* pp2 = pp->get();

  cout << pp2->toString() << endl;


#if 0
  // first load python lsst.pex.policy.pypolicy
  pName = PyString_FromString("lsst.pex.policy.pypolicy");
  assert(pName);
  pModule = PyImport_Import(pName);
  Py_DECREF(pName);
  if (!pModule) {
    fprintf(stderr, "Failed to load lsst.pex.policy.pypolicy\n"); //.Policy\n");
    return -1;
  }

  pFunc = PyObject_GetAttrString(pModule, "create_policy");
  assert(pFunc);

  confString = PyString_FromString("dict(a=4, b=6)");
  pArgs = PyTuple_Pack(1, confString);
  assert(pArgs);

  pValue = PyObject_CallObject(pFunc, pArgs);
  Py_DECREF(pArgs);
  if (!pValue) {
    fprintf(stderr, "call to Policy.frompython() failed.\n");
    return -1;
  }

#endif
#if 0
  // first load python lsst.pex.policy.Policy
  pName = PyString_FromString("lsst.pex.policy"); //.Policy");
  assert(pName);
  pModule = PyImport_Import(pName);
  Py_DECREF(pName);
  if (!pModule) {
    fprintf(stderr, "Failed to load lsst.pex.policy\n"); //.Policy\n");
    return -1;
  }

  policyClass = PyObject_GetAttrString(pModule, "Policy");
  assert(policyClass);

  confString = PyString_FromString("dict(a=4, b=6)");

  //pFunc = PyObject_GetAttrString(pModule, "frompython");
  pFunc = PyObject_GetAttrString(policyClass, "frompython");
  assert(pFunc);
  pArgs = PyTuple_Pack(1, confString);
  assert(pArgs);

  pValue = PyObject_CallObject(pFunc, pArgs);
  Py_DECREF(pArgs);
  if (!pValue) {
    fprintf(stderr, "call to Policy.frompython() failed.\n");
    return -1;
  }
#endif
#if 0
  if (pValue != NULL) {
    printf("Result of call: %ld\n", PyInt_AsLong(pValue));
    Py_DECREF(pValue);
  }
  else {
    Py_DECREF(pFunc);
    Py_DECREF(pModule);
    PyErr_Print();
    fprintf(stderr,"Call failed\n");
    return 1;
  }
}
 else {
   if (PyErr_Occurred())
     PyErr_Print();
   fprintf(stderr, "Cannot find function \"%s\"\n", argv[2]);
 }
Py_XDECREF(pFunc);
Py_DECREF(pModule);
}
    else {
      PyErr_Print();
      fprintf(stderr, "Failed to load \"%s\"\n", argv[1]);
      return 1;
    }
#endif



Py_Finalize();
return 0;
}
