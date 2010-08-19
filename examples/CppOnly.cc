#include <iostream>
#include <stdio.h>
#include <assert.h>

#include <Python.h>
#include <boost/shared_ptr.hpp>
#include "lsst/pex/policy/Policy.h"

using namespace std;
namespace pexPolicy = lsst::pex::policy;

int main(int argc, char** args) {
  PyObject *pName, *pModule, *pFunc;
  PyObject *pArgs;
  PyObject *confString;
  PyObject* pPolicy;
  PyObject* pPtr, *pPtr2;

  Py_Initialize();

  // Import pypolicy
  pName = PyString_FromString("lsst.pex.policy.pypolicy");
  assert(pName);
  pModule = PyImport_Import(pName);
  Py_DECREF(pName);
  if (!pModule) {
    fprintf(stderr, "Failed to load lsst.pex.policy.pypolicy\n");
    return -1;
  }
  // Find pypolicy.create_policy_from_string
  pFunc = PyObject_GetAttrString(pModule, "create_policy_from_string");
  assert(pFunc);

  // Call it.
  confString = PyString_FromString("dict(a=4, b=6)");
  pArgs = PyTuple_Pack(1, confString);
  assert(pArgs);
  pPolicy = PyObject_CallObject(pFunc, pArgs);
  Py_DECREF(pArgs);
  if (!pPolicy) {
    fprintf(stderr, "call to create_policy_from_string() failed.\n");
    PyErr_Print();
    return -1;
  }

  // pPolicy is a swig wrapper of a boost::shared_ptr<pexPolicy::Policy>*
  // Hold on to your socks while we dereference that mofo.

  // Get policy.this
  pPtr = PyObject_GetAttrString(pPolicy, "this");
  //PyObject_Print(pPtr, stdout, 0);

  // SwigObject obeys the Number Protocol, it turns out.
  assert(PyNumber_Check(pPtr));
  // This may not be *strictly* necessary -- PyInt_AsLong(pPtr) works too, but maybe just by coincidence.
  pPtr2 = PyNumber_Int(pPtr);

  // Evil cast.  Recall that Policy::Ptr is a boost::shared_ptr<Policy>.  Here, we're:
  //  -converting pPtr from a swig object to a python int (pPtr2)
  //  -getting a long, and treating it as a pointer
  //  -casting that to a boost::shared_ptr*  (note the evil extra * there)
  //  -dereferencing it.
  // Better living through indirection, indeed.
  pexPolicy::Policy::Ptr pp = *(reinterpret_cast<pexPolicy::Policy::Ptr*>(PyInt_AsLong(pPtr2)));

  cout << pp->toString() << endl;

  Py_DECREF(pPtr2);
  Py_DECREF(pPtr);
  Py_DECREF(pPolicy);
  Py_DECREF(confString);
  Py_DECREF(pFunc);
  Py_DECREF(pModule);

  // Shut this party down.
  Py_Finalize();
  return 0;
}
