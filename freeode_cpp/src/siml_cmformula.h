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

// #include "siml_cmpath.h"
#include "siml_cmmemaccess.h"


namespace siml {

/**
@short A parsed formula

This is a list of commands that represents the formula in RPN.
The commands are a hirarchy of classes with a common (abstract) base class.
The commands are held by smart, shared pointers (the polymorphic class in a container problem).

The copy constructor and operator=() performe only shallow copies in the sense that
they copy only the pointers but not the commands, they are shared among all copies of
the formula. So care must be taken to implement mutating member functions.

The commands however are immutable. So to change a command (e.g. to change a varible
name @see prependPaths ), it must be replaced by a new command object,
instead of modifying the command. The formula will then have an
own version of this single command, instead of sharing it with the other copies.

There are no memory management problems because of the shared pointers.

@note replace commans instead of modify commands in all mutating member functions.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class CmFormula{
public:
    //!Base class of formula commands
    /*!Important: all data members of derived classes should be const to make the objects immutable!*/
    struct FormulaCmd {
        //!number of operands
        uint const numOps;
        FormulaCmd(uint inOps): numOps(inOps) {}
        virtual ~FormulaCmd() {}
        virtual std::string toString() const =0;
    };
    //!Operator: + - * / ^
    struct MathOperatorCmd: public FormulaCmd {
        std::string const symbol;
        //!Specify formula symbol and number of operands.
        /*! @param inSymbol   Formula symbbol for operator e.g. "+".
            @param inOps      Number of operands (2: infix "+"; 1: only sensible for "-", prefix, sign). */
        MathOperatorCmd(std::string const & inSymbol, uint inOps): FormulaCmd(inOps), symbol(inSymbol) {};
        std::string toString() const { return symbol; }
    };
    //!A number
    struct NumberCmd: public FormulaCmd {
        std::string const number;
        //!Specify number as string
        NumberCmd(std::string const & inNumber): FormulaCmd(0), number(inNumber) {};
        std::string toString() const { return number; }
    };
    //!A path; refference to a variable
    struct MemAccessCmd: public FormulaCmd {
        CmMemAccess const access;
        //!Specify parsed path
        MemAccessCmd(CmMemAccess const & inAccess): FormulaCmd(0), access(inAccess) {};
        std::string toString() const { return access.toString(); }
    };
    //! Pair of brackets
    struct BracketPairCmd: public FormulaCmd {
        CmPath const path;
        //!Specify parsed path
        BracketPairCmd(): FormulaCmd(1) {};
        std::string toString() const { return std::string("()"); }
    };
    typedef boost::shared_ptr<FormulaCmd> ItemPtr;
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
//     CmFormula & append(ItemPtr inItem);
    //!Put operator item into list
    CmFormula & pushBackMathOperator(std::string const & inSymbol, uint inOps);
    //!Put number item into list
    CmFormula & pushBackNumber(std::string const & inString);
    //!Put path item into list
    CmFormula & pushBackMemAccess(CmMemAccess const & inAccess);
    //!Put bracket item into list
    CmFormula & pushBackBrackets();

    //!Put prefix in front of all paths
    void prependPaths( CmPath const & inPrefix);
    //!Change some paths
    void replacePaths( CmPath::ReplaceMap const & inReplacements);

    //!Simplistic string conversion
    std::string toString() const;

private:
    ItemContainer m_items;
};


//!printing
std::ostream& operator<<(std::ostream& out, siml::CmFormula const & formula);

}

#endif
