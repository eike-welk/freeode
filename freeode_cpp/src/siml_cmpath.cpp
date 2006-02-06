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
#include "boost/tuple/tuple.hpp"

#include <sstream>


using std::string;
using std::list;
using std::ostringstream;
using boost::tuples::tie;  // same:  using boost::tie;
using boost::tuples::ignore;


/*!Default constructor*/
siml::CmPath::CmPath():
        m_TimeDerivative(false)
{
}


/*!
Initialize with one component.
No parsing is done.
*/
siml::CmPath::CmPath(std::string const & contentsNew)/*:
        m_TimeDerivative(false)*/
{
    *this = CmPath();
    append(contentsNew);
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
        string pathStr = toString(".", "");
        return pathStr == inString;
    }
}


/*!Compare all components.
@return true if all components are equal, false otherwise.
*/
bool siml::CmPath::isEqual(CmPath const & inPath) const
{
    return  (m_Component == inPath.m_Component) &&
            (m_TimeDerivative == inPath.m_TimeDerivative);
}


/*!
Test if *this is fully contained in the last some elements of inPath.
If both paths are equal this function also returns true.

The function compares the paths' components starting from the end.
*/
bool siml::CmPath::isTailOf( CmPath const & inPath) const
{

    //compare the strings starting from the end
    StringList::const_reverse_iterator itThis, itOther;
    for(    itThis = m_Component.rbegin(), itOther = inPath.m_Component.rbegin();
            itThis != m_Component.rend() && itOther != inPath.m_Component.rend();
            ++itThis, ++itOther )
    {
        if( *itThis != *itOther ) { return false; }
    }

    //here one of the paths is contained in the other
    //test if all elements of this were compared, otherwise it is not fully contained in inPath
    if( itThis != m_Component.rend() ) { return false; }

    return true;
}


/*!
Test if *this is lexicaly smaller than inPath.

Corner case:
If *this is fully contained in inPath and inPath is longer, then the funcion also returns true.
*/
bool siml::CmPath::operator<( CmPath const & inPath) const
{
    StringList::const_iterator itThis, itOther;
    for(    itThis = m_Component.begin(), itOther = inPath.m_Component.begin();
            itThis != m_Component.end() && itOther != inPath.m_Component.end();
            ++itThis, ++itOther )
    {
        if     ( *itThis < *itOther ) { return true; }
        else if( *itThis > *itOther ) { return false; }
        //else { the components are equal: test the next components}
    }

    //here one of the paths is contained in the other
    //see if the other path is longer.
    if( m_Component.size() < inPath.m_Component.size() ) { return true; }

    return false;
}


/*!remove all components*/
siml::CmPath & siml::CmPath::clear()
{
    *this = CmPath();
//     m_Component.clear();
//     m_TimeDerivative = false;
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


/*!Replace contents by a new path if a replacement is found in inReplacements*/
void siml::CmPath::replace( ReplaceMap const & inReplacements)
{
    ReplaceMap::const_iterator it = inReplacements.find( *this );

    //see if this object is in the map
    if( it == inReplacements.end() ) { return; }

    //replace the contents.
    CmPath const & newPath = (*it).second;
    m_Component = newPath.m_Component;
}


/*!If true the path is a time derivative e.g: "$x" otherwise "x"*/
siml::CmPath & siml::CmPath::setTimeDerivative( bool deriv)
{
    m_TimeDerivative = deriv;
    return *this;
}


/*!
Convert the path object to a string that looks like: "plant.reactor1.p".
The separator string (the "." in this example) can be chosen.

@param  separatorStr separator between the path's components. (Default ".")
@param  derivativeMark character to symbolize derivation.
@return String representation of path.
*/
std::string siml::CmPath::toString(
        std::string const & separatorStr,
        std::string const & derivativeMark ) const
{
    ostringstream   outputStream;
    StringList::const_iterator itS;

    //print the indicator for time derivation
//     string const derivativeMark("$");
    if( isTimeDerivative() ) { outputStream << derivativeMark; }

    if( m_Component.empty() ) { return outputStream.str(); }

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

