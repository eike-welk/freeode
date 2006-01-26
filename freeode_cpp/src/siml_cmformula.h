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
#ifndef SIMLCMFORMULA_H
#define SIMLCMFORMULA_H


#include <string>
#include <list>
#include <boost/shared_ptr.hpp>

#include "siml_cmpath.h"


namespace siml {

/**
@short A parsed formula

This is a list of commands that represents the formula in RPN.
The commands for a hirarchy with abstract base class.

	@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class CmFormula{
public:
    //!Base class of formula commands
    struct FormulaItem {
        //!number of operands
        uint const ops;
        FormulaItem(uint inOps): ops(inOps) {}
        virtual ~FormulaItem() {}
        virtual std::string toString() const =0;
    };
    //!Operator: + - * / ^
    struct MathOperator: public FormulaItem {
        std::string const symbol;
        //!Specify formula symbol e.g. "+" and number of operands. inOps==1 means prefix (sign) e.g.- 2
        MathOperator(std::string const & inSymbol, uint inOps): FormulaItem(inOps), symbol(inSymbol) {};
        std::string toString() const { return symbol; }
    };
    //!A number in the formula
    struct Number: public FormulaItem {
        std::string const number;
        //!Specify number as string
        Number(std::string const & inNumber): FormulaItem(0), number(inNumber) {};
        std::string toString() const { return number; }
    };
    //!A path; refference to a variable in the formula
    struct Path: public FormulaItem {
        CmPath const path;
        //!Specify parsed path
        Path(std::string const & inPath): FormulaItem(0), path(inPath) {};
        std::string toString() const { return path.toString(); }
    };
    typedef boost::shared_ptr<FormulaItem> ItemPtr;
    typedef std::list<ItemPtr> ItemContainer;

    CmFormula();

    ~CmFormula();

    //!Put formula item into list
    CmFormula & append(ItemPtr inItem);

    //!Simplistic string conversion
    std::string toString() const;

private:
    ItemContainer m_items;
};

}

#endif
