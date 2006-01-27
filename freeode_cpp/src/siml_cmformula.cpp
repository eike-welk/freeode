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
siml::CmFormula::CmFormula( CmFormula const & inFormula)
{
    m_items = inFormula.m_items;
}


siml::CmFormula::~CmFormula()
{
}


/*!Do a shallow copy. Only the list of pointers is copied, not the formula items.*/
siml::CmFormula & siml::CmFormula::operator= ( CmFormula const & inFormula)
{
    if( this != &inFormula ) {
        m_items = inFormula.m_items;
    }
    return *this;
}


/*!Remove all elements from the list*/
siml::CmFormula & siml::CmFormula::clear()
{
    //the smart pointers will delete the stored objects if necessary.
    m_items.clear();
    return *this;
}


/*!Put formula item at end of list list*/
// siml::CmFormula & siml::CmFormula::append( ItemPtr inItem)
// {
//     m_items.push_back( inItem);
//     return *this;
// }


//!Put operator item into list
siml::CmFormula & siml::CmFormula::appendMathOperator( std::string const & inSymbol, uint inOps)
{
    ItemPtr item( new MathOperatorItem(inSymbol, inOps));
    m_items.push_back( item);
    return *this;
}


//!Put number item into list
siml::CmFormula & siml::CmFormula::appendNumber( std::string const & inString)
{
    ItemPtr item( new NumberItem( inString));
    m_items.push_back( item);
    return *this;
}


//!Put path item into list
siml::CmFormula & siml::CmFormula::appendPath(CmPath const & inPath)
{
    ItemPtr item( new PathItem( inPath));
    m_items.push_back( item);
    return *this;
}


//!Put bracket item into list
siml::CmFormula & siml::CmFormula::appendBrackets()
{
    ItemPtr item( new BracketPairItem());
    m_items.push_back(item);
    return *this;
}


/*!Iterate through the equation and add the prefix at all variable and
parameter names*/
void siml::CmFormula::prependPaths(CmPath const & inPrefix)
{
    ItemContainer::iterator itI;

    for( itI = m_items.begin(); itI != m_items.end(); ++itI)
    {
        //try it current item is a path
        PathItem * oldItem = dynamic_cast<PathItem *>((*itI).get());
        if( !oldItem ) { continue; }

        //put prefix in front of old path
        CmPath path = oldItem->path;
        path.prepend( inPrefix);
        //replace with new item that has extended path
        ItemPtr newItem( new PathItem(path));
        *itI = newItem;
    }

}


/*!Put items into string from left to right for debuging.*/
std::string siml::CmFormula::toString() const
{
    string resSting;
    ItemContainer::const_iterator itI;

    for( itI = m_items.begin(); itI != m_items.end(); ++itI)
    {
        resSting += ((*itI)->toString() + " ");
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


