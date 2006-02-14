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
#include "siml_cmformula.h"


using std::string;


siml::CmFormula::CmFormula()
{
}


/*!Do a shallow copy. Only the list of pointers is copied, not the formula items.*/
siml::CmFormula::CmFormula( CmFormula const & inFormula):
        m_commands( inFormula.m_commands)
{
}


siml::CmFormula::~CmFormula()
{
}


/*!Do a shallow copy. Only the list of pointers is copied, not the formula items.*/
siml::CmFormula & siml::CmFormula::operator= ( CmFormula const & inFormula)
{
    if( this != &inFormula ) {
        m_commands = inFormula.m_commands;
    }
    return *this;
}


/*!Remove all elements from the list*/
siml::CmFormula & siml::CmFormula::clear()
{
    //the smart pointers will delete the stored objects if necessary.
    m_commands.clear();
    return *this;
}


/*!Put formula item at end of list list*/
// siml::CmFormula & siml::CmFormula::append( CommandPtr inItem)
// {
//     m_commands.push_back( inItem);
//     return *this;
// }


//!Put operator item into list
siml::CmFormula & siml::CmFormula::pushBackMathOperator( std::string const & inSymbol, uint inOps)
{
    CommandPtr item( new MathOperatorCmd(inSymbol, inOps));
    m_commands.push_back( item);
    return *this;
}


//!Put number item into list
siml::CmFormula & siml::CmFormula::pushBackNumber( std::string const & inString)
{
    CommandPtr item( new NumberCmd( inString));
    m_commands.push_back( item);
    return *this;
}


//!Put path item into list
siml::CmFormula & siml::CmFormula::pushBackMemAccess(CmMemAccess const & inAccess)
{
    CommandPtr item( new MemAccessCmd( inAccess));
    m_commands.push_back( item);
    return *this;
}


//!Put bracket item into list
siml::CmFormula & siml::CmFormula::pushBackBrackets()
{
    CommandPtr item( new BracketPairCmd());
    m_commands.push_back(item);
    return *this;
}


/*!
Iterate through the equation and add the prefix at all variable and
parameter names

@note The function makes a deep copy of each path object.
(More efficient were making a deep copy only if the use count is >1.)

@param inPrefix Partial path that is put in front of all of the formula's paths.
*/
void siml::CmFormula::prependPaths(CmPath const & inPrefix)
{
    CommandContainer::iterator it;

    for( it = m_commands.begin(); it != m_commands.end(); ++it)
    {
        //try if current item is a path
        MemAccessCmd * oldItem = dynamic_cast<MemAccessCmd *>((*it).get());
        if( !oldItem ) { continue; }

        //put prefix in front of old path
        CmMemAccess access = oldItem->access;
        access.prependPath( inPrefix);
        //replace with new item that has extended path
        CommandPtr newItem( new MemAccessCmd( access));
        *it = newItem;
    }
}


/*!
Replace some paths by new paths. The replacements are given in the map inReplacements.

@note The function makes a deep copy of each changed path object.

@param inReplacements Map that contains the replacements.
*/
void siml::CmFormula::replacePaths( CmPath::ReplaceMap const & inReplacements)
{
    CommandContainer::iterator it;

    for( it = m_commands.begin(); it != m_commands.end(); ++it)
    {
        //try if current item is a path
        MemAccessCmd * oldItem = dynamic_cast<MemAccessCmd *>((*it).get());
        if( !oldItem ) { continue; }

        //get path and replace it
        CmMemAccess access = oldItem->access;
        access.replacePath( inReplacements);
        //replace with new item
        CommandPtr newItem( new MemAccessCmd( access));
        *it = newItem;
    }
}


/*!Put items into string from left to right for debuging.*/
std::string siml::CmFormula::toString() const
{
    string resSting;
    CommandContainer::const_iterator it;

    for( it = m_commands.begin(); it != m_commands.end(); ++it)
    {
        resSting += ((*it)->toString() + " ");
    }

    return resSting;
}


/*!For printing: convert the object to a string (using "." as cmponent separator), then put
the string into the stream.*/
std::ostream& siml::operator<<(std::ostream& out, siml::CmFormula const & formula)
{
    string strFormula = formula.toString();
    out << strFormula;
    return out;
}


