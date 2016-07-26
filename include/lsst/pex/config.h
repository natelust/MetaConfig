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
 
#ifndef LSST_PEX_CONFIG_H
#define LSST_PEX_CONFIG_H

/**
 *  A preprocessor macro used to define fields in C++ "control object" structs.  These objects
 *  can then be wrapped into full-fledged Config objects by the functions in lsst.pex.config.wrap.
 *
 *  The defaults for the config class will be set properly if and only if the control class is
 *  default-constructable.
 *
 *  See lsst.pex.config.wrap.makeConfigClass for a complete example of how to use this macro.
 */
#define LSST_CONTROL_FIELD(NAME, TYPE, DOC)             \
    static char const * _doc_ ## NAME() {               \
        static char const * doc = DOC;                  \
        return doc;                                     \
    }                                                   \
    static char const * _type_ ## NAME() {              \
        static char const * type = #TYPE;               \
        return type;                                    \
    }                                                   \
    TYPE NAME

/**
 *  A preprocessor macro used to define fields in C++ "control object" structs, for nested control
 *  objects.  These can be wrapped into Config objects by the functions in lsst.pex.config.wrap.
 *
 *  The nested object will be held as a regular, by-value data member (there's currently no way to use
 *  smart pointers or getters/setters instead).
 *
 *  The nested control object class must also be wrapped into a config object, and the Python module
 *  of the wrapped nested control object must be passed as the MODULE argument to the macro.  When
 *  a wrapped control object is used as a nested field in the same package it is defined in, the
 *  MODULE argument must refer to the actual wrapped module, not the just the package, even
 *  if the name is lifted into the package namespace.
 *
 *  See lsst.pex.config.wrap.makeConfigClass for a complete example of how to use this macro.
 */
#define LSST_NESTED_CONTROL_FIELD(NAME, MODULE, TYPE, DOC)       \
    static char const * _doc_ ## NAME() {                        \
        static char const * doc = DOC;                           \
        return doc;                                              \
    }                                                            \
    static char const * _type_ ## NAME() {                       \
        static char const * type = #TYPE;                        \
        return type;                                             \
    }                                                            \
    static char const * _module_ ## NAME() {                     \
        static char const * mod = #MODULE;                       \
        return mod;                                              \
    }                                                            \
    TYPE NAME

#endif
