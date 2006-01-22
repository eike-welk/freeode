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
#include "siml_cmpath.h"

// #include <boost/format.hpp>
#include <sstream>

using std::string;
using std::list;
using std::ostringstream;

siml::CmPath::CmPath()
{
}


siml::CmPath::~CmPath()
{
}


/*!Add string at begining*/
void siml::CmPath::prepend(std::string const & compo)
{
    m_Component.push_front(compo);
}


/*!Add path at begining*/
void siml::CmPath::prepend(CmPath const & inPath)
{
    m_Component.insert(m_Component.begin(), inPath.m_Component.begin(), inPath.m_Component.end());
}


/*!Add string at end*/
void siml::CmPath::append(std::string const & compo)
{
    m_Component.push_back(compo);
}


/*!Add path at end*/
void siml::CmPath::append(CmPath const & inPath)
{
    m_Component.insert(m_Component.end(), inPath.m_Component.begin(), inPath.m_Component.end());
}


/*!
Convert the path object to a string that looks like: "plant.reactor1.p".
The separator string (the "." in this example) can be chosen.

@param  separatorStr separator between the path's components. (Default ".")
@return String representation of path.
*/
std::string siml::CmPath::toString(std::string const separatorStr) const
{
    ostringstream   outputStream;
    StringList::const_iterator itS;

    //special handling for first component: no "." in front of it.
    itS = m_Component.begin();
    outputStream << *itS;
    ++itS;

    //all other components have a "." in front of it.
    for( ; itS != m_Component.end(); ++itS)
    {
        outputStream << separatorStr << *itS;
    }

    return outputStream.str();
}



