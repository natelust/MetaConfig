// -*- lsst-c++ -*-
/*
 * LSST Data Management System
 * See COPYRIGHT file at the top of the source tree.
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

#ifndef LSST_PEX_CONFIG_PYTHON_H
#define LSST_PEX_CONFIG_PYTHON_H

/**
 * Macro used to wrap fields declared by `LSST_CONTROL_FIELD` using Pybind11.
 *
 * Example:
 *
 *     LSST_DECLARE_CONTROL_FIELD(clsFoo, Foo, myField)
 *
 * @param WRAPPER The py::class_ object representing the control class being
 *                wrapped.
 * @param CLASS The control class. Must be a C++ identifier (not a string),
 *              properly namespace-qualified for the context where this macro
 *              is being called.
 * @param NAME The control field. Must be a C++ identifier (not a string), and
 *             must match the `NAME` argument of the original
 *             `LSST_CONTROL_FIELD` macro.
 */
#define LSST_DECLARE_CONTROL_FIELD(WRAPPER, CLASS, NAME)         \
    WRAPPER.def_readwrite(#NAME, &CLASS::NAME);                  \
    WRAPPER.def_static("_doc_" #NAME, &CLASS::_doc_ ## NAME);    \
    WRAPPER.def_static("_type_" #NAME, &CLASS::_type_ ## NAME);

/**
 * Macro used to wrap fields declared by `LSST_NESTED_CONTROL_FIELD` using
 * Pybind11.
 *
 * Example:
 *
 *     LSST_DECLARE_NESTED_CONTROL_FIELD(clsFoo, Foo, myField)
 *
 * @param WRAPPER The py::class_ object representing the control class being
 *                wrapped.
 * @param CLASS The control class. Must be a C++ identifier (not a string),
 *              properly namespace-qualified for the context where this macro
 *              is being called.
 * @param NAME The control field. Must be a C++ identifier (not a string), and
 *             must match the `NAME` argument of the original
 *             `LSST_CONTROL_FIELD` macro.
 */
#define LSST_DECLARE_NESTED_CONTROL_FIELD(WRAPPER, CLASS, NAME)  \
    WRAPPER.def_readwrite(#NAME, &CLASS::NAME);                  \
    WRAPPER.def_static("_doc_" #NAME, &CLASS::_doc_ ## NAME);    \
    WRAPPER.def_static("_type_" #NAME, &CLASS::_type_ ## NAME);  \
    WRAPPER.def_static("_module_" #NAME, &CLASS::_module_ ## NAME);

#endif

