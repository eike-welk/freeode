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
#ifndef SIML_PYFORMULACONVERTER_H
#define SIML_PYFORMULACONVERTER_H


#include "siml_cmformula.h"

// #include <iostream>
// #include <vector>
#include <string>
// #include <fstream>
#include <map>


namespace siml {

/**
@short convert CmFormula to Python code

Create a Python expression from a Formula.

@todo research is conversion into visitor pattern a good idea? The function dispatch() would be gone.
@todo can the visitor pattern be employed with abstract syntax trees?

@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class PyFormulaConverter{
public:
//     typedef CmFormula::CommandContainer CommandContainer;
    typedef CmFormula::CommandContainer::const_reverse_iterator CommandIterator;

    PyFormulaConverter();
    PyFormulaConverter( std::map<CmPath, std::string> mapPathToPyName);

    ~PyFormulaConverter();

    //!Change the mapping between paths and Python names.
    void setPythonName( std::map<CmPath, std::string> mapPathToPyName) { m_PythonName = mapPathToPyName; }

    //!Create Python expression
    std::string convert( CmFormula const & formula);

private:
    //!decide which execute function should be called.
    std::string dispatch();

    //!Execute +, -, *, /, ^.
    std::string execute( CmFormula::MathOperatorCmd const * cmd);
    //!return number
    std::string execute( CmFormula::NumberCmd const * cmd);
    //!return variable or parameter name
    std::string execute( CmFormula::MemAccessCmd const * cmd);
    //!Create bracket pair
    std::string execute( CmFormula::BracketPairCmd const * cmd);

    //!Python names for all variables and parameters.
    /*! Mapping between siml path ("a.b.c") and Python expression to access this object ("self.a_b_c") */
    std::map<CmPath, std::string> m_PythonName;

    //!Pointer to current command
    /*!Iterator into the command container. The methods that are specialized on
    each command increase the counter appropriately.*/
    CommandIterator m_ProgramCounter;
    //!End of the formula continer (only for error protection)
    CommandIterator m_ProgramEnd;
};

}

#endif
