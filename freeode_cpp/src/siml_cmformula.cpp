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


siml::CmFormula::~CmFormula()
{
}


/*!Put formula item at end of list list*/
siml::CmFormula & siml::CmFormula::append(ItemPtr inItem)
{
    m_items.push_back(inItem);
    return *this;
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



