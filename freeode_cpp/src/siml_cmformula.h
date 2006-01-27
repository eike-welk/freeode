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
#ifndef SIML_CMFORMULA_H
#define SIML_CMFORMULA_H


#include <string>
#include <list>
#include <iostream>

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
        uint const numOps;
        FormulaItem(uint inOps): numOps(inOps) {}
        virtual ~FormulaItem() {}
        virtual std::string toString() const =0;
    };
    //!Operator: + - * / ^
    struct MathOperator: public FormulaItem {
        std::string const symbol;
        //!Specify formula symbol and number of operands.
        /*! @param inSymbol   Formula symbbol for operator e.g. "+".
            @param inOps      Number of operands (2: infix "+"; 1: only sensible for "-", prefix, sign). */
        MathOperator(std::string const & inSymbol, uint inOps): FormulaItem(inOps), symbol(inSymbol) {};
        std::string toString() const { return symbol; }
    };
    //!A number
    struct Number: public FormulaItem {
        std::string const number;
        //!Specify number as string
        Number(std::string const & inNumber): FormulaItem(0), number(inNumber) {};
        std::string toString() const { return number; }
    };
    //!A path; refference to a variable
    struct Path: public FormulaItem {
        CmPath const path;
        //!Specify parsed path
        Path(CmPath const & inPath): FormulaItem(0), path(inPath) {};
        std::string toString() const { return path.toString(); }
    };
    //! Pair of brackets
    struct BracketPair: public FormulaItem {
        CmPath const path;
        //!Specify parsed path
        BracketPair(): FormulaItem(1) {};
        std::string toString() const { return std::string("()"); }
    };
    typedef boost::shared_ptr<FormulaItem> ItemPtr;
    typedef std::list<ItemPtr> ItemContainer;

    //!Default constructor
    CmFormula();
    //!Copy constructor
    CmFormula( CmFormula const & inFormula);

    ~CmFormula();

    //!Assignment operator
    CmFormula & operator= ( CmFormula const & inFormula);

    //!Remove all elements from the list
    CmFormula & clear();

    //!Put any formula item into list
    CmFormula & append(ItemPtr inItem);
    //!Put operator item into list
    CmFormula & appendMathOperator(std::string const & inSymbol, uint inOps);
    //!Put number item into list
    CmFormula & appendNumber(std::string const & inString);
    //!Put path item into list
    CmFormula & appendPath(CmPath const & inPath);
    //!Put bracket item into list
    CmFormula & appendBrackets();

    //!Simplistic string conversion
    std::string toString() const;

private:
    ItemContainer m_items;
};


//!printing
std::ostream& operator<<(std::ostream& out, siml::CmFormula const & formula);

}

#endif
