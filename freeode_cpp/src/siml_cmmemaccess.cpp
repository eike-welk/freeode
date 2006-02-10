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


#include "siml_cmmemaccess.h"

#include <sstream>


using std::string;
using std::ostringstream;


siml::CmMemAccess::CmMemAccess():
        m_TimeDerivative(false)
{
}


siml::CmMemAccess::~CmMemAccess()
{
}

/*!
Convert the CmMemAccess object to a string that looks like: "$plant.reactor1.p".
The separator string (the "." in this example) and the derivation operator can be chosen.

@param  separatorStr separator between the path's components. (Default ".")
@param  derivativeStr string to symbolize derivation.
@return String representation of path.
 */
std::string siml::CmMemAccess::toString(
        std::string const & separatorStr,
        std::string const & derivativeStr ) const
{
    ostringstream   outputStream;

    //print the indicator for time derivation
    if( timeDerivative() ) { outputStream << derivativeStr; }

    outputStream << m_Path.toString( separatorStr);

    return outputStream.str();
}

/*!For printing: convert the object to a string, then put
the string into the stream.*/
std::ostream& siml::operator<<(std::ostream& out, siml::CmMemAccess const & access)
{
    string strPath = access.toString();
    out << strPath;
    return out;
}

