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
 
%define testLib_DOCSTRING
"
Various swigged-up C++ classes for testing
"
%enddef

%feature("autodoc", "1");
%module(package="testLib", docstring=testLib_DOCSTRING) testLib

%pythonnondynamic;
%naturalvar;  // use const reference typemaps

%include "lsst/p_lsstSwig.i"
%include "std_vector.i"

%lsst_exceptions()

%{
#include "lsst/pex/config.h"
%}

%include "lsst/pex/config.h"

%template(StringVec) std::vector<std::string>;

%inline %{

    struct InnerControlObject {
        LSST_CONTROL_FIELD(p, double, "a double field");

        explicit InnerControlObject(double p_ = 2.0) : p(p_) {}
    };

    struct OuterControlObject {
        LSST_NESTED_CONTROL_FIELD(a, testLib, InnerControlObject, "a nested control field");
        LSST_CONTROL_FIELD(b, int, "a integer field");

        OuterControlObject(int b_ = 0) : b(b_) {}
    };

    struct ControlObject {
        LSST_CONTROL_FIELD(foo, int, "an integer field");
        LSST_CONTROL_FIELD(bar, std::vector<std::string>, "a list of strings field");

        explicit ControlObject(int foo_=1) : foo(foo_), bar() {}
    };

    bool checkControl(ControlObject const & ctrl, int fooVal, std::vector<std::string> const & barVal) {
        return fooVal == ctrl.foo && barVal == ctrl.bar;
    }

    bool checkNestedControl(OuterControlObject const & ctrl, double apVal, int bVal) {
        return ctrl.a.p == apVal && ctrl.b == bVal;
    }

%}

%pythoncode %{

import lsst.pex.config
InnerConfigObject = lsst.pex.config.makeConfigClass(InnerControlObject)
OuterConfigObject = lsst.pex.config.makeConfigClass(OuterControlObject)
ConfigObject = lsst.pex.config.makeConfigClass(ControlObject)

%}
