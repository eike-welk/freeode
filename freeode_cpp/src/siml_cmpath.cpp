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

/*!Default constructor*/
siml::CmPath::CmPath()
{
}
/*!
Initialize with one component.
No parsing is done.
*/
siml::CmPath::CmPath(std::string const & contentsNew)
{
    assign(contentsNew);
}


siml::CmPath::~CmPath()
{
}


/*!
Convert the path to a string (with toString(".") ) and compare with inString.
The separator for the conversion is ".";
@return true if equal, false otherwise.
*/
bool  siml::CmPath::isEqual(std::string const & inString) const
{
    if( m_Component.size() == 1 )
    {   //shortcut for one component paths.
        return m_Component.front() == inString;
    }
    else
    {   //the normal case
        string pathStr = toString(".");
        return pathStr == inString;
    }
}
/*!Compare all components.
@return true if all components are equal, false otherwise.
*/
bool siml::CmPath::isEqual(CmPath const & inPath) const
{
    return m_Component == inPath.m_Component;
}


/*!remove all components*/
siml::CmPath & siml::CmPath::clear()
{
    m_Component.clear();
    return *this;
}


/*!Let path contain one single string*/
siml::CmPath & siml::CmPath::assign(std::string const & contentsNew)
{
    clear();
    append(contentsNew);
    return *this;
}
/*!Copy all components*/
siml::CmPath & siml::CmPath::assign(CmPath const & contentsNew)
{
    m_Component = contentsNew.m_Component;
    return *this;
}


/*!Add string at begining*/
siml::CmPath & siml::CmPath::prepend(std::string const & compo)
{
    m_Component.push_front(compo);
    return *this;
}
/*!Add path at begining*/
siml::CmPath & siml::CmPath::prepend(CmPath const & inPath)
{
    m_Component.insert(m_Component.begin(), inPath.m_Component.begin(), inPath.m_Component.end());
    return *this;
}


/*!Add string at end*/
siml::CmPath & siml::CmPath::append(std::string const & compo)
{
    m_Component.push_back(compo);
    return *this;
}
/*!Add path at end*/
siml::CmPath & siml::CmPath::append(CmPath const & inPath)
{
    m_Component.insert(m_Component.end(), inPath.m_Component.begin(), inPath.m_Component.end());
    return *this;
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

/*!For printing: convert the object to a string (using "." as cmponent separator), then put
the string into the stream.*/
std::ostream& siml::operator<<(std::ostream& out, siml::CmPath const & path)
{
    string strPath = path.toString();
    out << strPath;
    return out;
}

