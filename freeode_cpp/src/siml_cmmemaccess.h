/***************************************************************************
 *   Copyright (C) 2005 by Eike Welk   *
 *   eike.welk@post.rwth-aachen.de   *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/
#ifndef SIML_CMREFFERENCE_H
#define SIML_CMREFFERENCE_H


#include "siml_cmpath.h"

#include <iostream>


namespace siml {

/**
@short Encode access to Memory

This is basicly a Path with additional information. It can express time (and
someday space) derivation as well as subscripts. Subscripts are access to only parts
of a distributed variable.

CmMemAccess should one day be able to express all of the following, and sensible combinations:
- r001.v001.X                       : simple path
- $r001.v001.X                      : time derivation
-       -------------   not implemented from here on     -------------
- r001.v001.X[0:50.2]               : partial access, possibly multi dimensional
- PARTIAL(r001.v001.X, h1)          : space derivation
- PARTIAL(r001.v001.X[0:50.2], h1)  : space derivation of a part
- DIFF(r001.v001.X, h1)             : alternative syntax for space derivation
- DIFF(r001.v001.X, Time)           : derivation in time direction, without integration of variable

@note This class is currently a quick hack because only time derivation is implemented.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class CmMemAccess{
public:
    CmMemAccess();

    ~CmMemAccess();

    //!Change time derivative propperty. If true: e.g: "$x" otherwise "x"
    void setTimeDerivative( bool deriv) { m_TimeDerivative = deriv; }
    //!If true the object is a time derivative e.g: "$x" otherwise "x"
    bool isTimeDerivative() const { return m_TimeDerivative; }
    //!Change the path - the variable name
    void setPath( const CmPath& theValue) { m_Path = theValue; }
    //!Return the m_path propperty - the variable name
    CmPath path() const { return m_Path; }

    //!Replace the path with an other path. A transformation from old path to new path is given in inReplacements
    void replacePath( CmPath::ReplaceMap const & inReplacements) { m_Path.replace( inReplacements); }
    //!Put some path fragment in front of the current path
    void prependPath( CmPath const & prefix ) { m_Path.prepend( prefix); }

    //!Convert to string
    std::string toString(   std::string const & separatorStr = ".",
                            std::string const & derivativeStr = "$"      ) const;

private:
    //!The path (variable name)
    CmPath m_Path;
    //!Object is time derivative "$path"
    bool m_TimeDerivative;
};

//!Stream output
std::ostream& operator<<(std::ostream& out, siml::CmMemAccess const & access);

}

#endif
