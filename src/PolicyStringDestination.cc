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
 * @file PolicyDestination.cc
 * @author Ray Plante
 */
#include <sstream>

#include "lsst/pex/policy/PolicyStringDestination.h"

namespace lsst {
namespace pex {
namespace policy {

PolicyStringDestination::PolicyStringDestination() 
    : PolicyStreamDestination(
        PolicyStringDestination::StreamPtr(new std::ostringstream())
      ), _sstrm()
{ 
    _sstrm = dynamic_cast<std::ostringstream*>(_ostrm.get());
}

PolicyStringDestination::PolicyStringDestination(const std::string& str) 
    : PolicyStreamDestination(
        PolicyStringDestination::StreamPtr(new std::ostringstream(str))
      ), _sstrm()
{ 
    _sstrm = dynamic_cast<std::ostringstream*>(_ostrm.get());
}

PolicyStringDestination::~PolicyStringDestination() { }

}}}
