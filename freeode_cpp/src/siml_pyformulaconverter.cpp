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


#include "siml_pyformulaconverter.h"

#include <boost/format.hpp>


using std::string;
using boost::format;


siml::PyFormulaConverter::PyFormulaConverter()
{
}


siml::PyFormulaConverter::PyFormulaConverter( std::map<CmPath, std::string> mapPathToPyName):
    m_PythonName( mapPathToPyName)
{
}


siml::PyFormulaConverter::~PyFormulaConverter()
{
}


/*!
Create Python expression
@return Python expression that computes the formula.
*/
std::string siml::PyFormulaConverter::convert( CmFormula const & formula)
{
    m_ProgramCounter = formula.commands().rbegin(); //program counter
    m_ProgramEnd     = formula.commands().rend();

    return dispatch();
}


/*!Look at m_ProgramCounter and decide which execute function should be called.*/
std::string siml::PyFormulaConverter::dispatch()
{
    if( m_ProgramCounter == m_ProgramEnd )
    {
        ///@todo generate internal compiler error
        return "(error: end of formula reached)";
    }

//     cast shared pointers:
//     template<class T, class U>
//     shared_ptr<T> dynamic_pointer_cast(shared_ptr<U> const & r);
    CmFormula::FormulaCmd const * cmdGeneric = m_ProgramCounter->get();

    CmFormula::MathOperatorCmd const * cmdMath    = dynamic_cast<CmFormula::MathOperatorCmd const *>(cmdGeneric);
    CmFormula::NumberCmd       const * cmdNum     = dynamic_cast<CmFormula::NumberCmd const *>(cmdGeneric);
    CmFormula::MemAccessCmd    const * cmdMem     = dynamic_cast<CmFormula::MemAccessCmd const *>(cmdGeneric);
    CmFormula::BracketPairCmd  const * cmdBracket = dynamic_cast<CmFormula::BracketPairCmd const *>(cmdGeneric);

    if      ( cmdMath )    { return execute(cmdMath); }
    else if ( cmdNum  )    { return execute(cmdNum); }
    else if ( cmdMem )     { return execute(cmdMem); }
    else if ( cmdBracket ) { return execute(cmdBracket); }
    else
    {
        ///@todo generate internal compiler error
        return " (error: unknown command: " + cmdGeneric->toString() + " ) ";
    }
}


/*!Create string that represents the Mathematical operation in Python syntax.
Increments the program counter and calles dispatch.*/
std::string siml::PyFormulaConverter::execute( CmFormula::MathOperatorCmd const * cmd)
{
    if      ( cmd->numOps == 1 )
    {
        ++m_ProgramCounter;
        return cmd->symbol + dispatch();
    }
    else if ( cmd->numOps == 2 )
    {
        string op1, op2;
        ++m_ProgramCounter; op2 = dispatch();
        ++m_ProgramCounter; op1 = dispatch();
        return (format("%1% %2% %3%") % op1 % cmd->symbol % op2).str();
    }
    else
    {
        ///@todo generate internal compiler error
        return (format(" (error: math operator: unknown number of operands: %1%) ") % cmd->numOps).str();
    }
}


/*!Create string that represents theNumber stored in cmd.*/
std::string siml::PyFormulaConverter::execute( CmFormula::NumberCmd const * cmd)
{
    return cmd->number;
}


/*!Create string that accesses the variable or parameter in the Python program.*/
std::string siml::PyFormulaConverter::execute( CmFormula::MemAccessCmd const * cmd)
{
    return m_PythonName[cmd->access.path()];
}


/*!Create pair of brackets around the result of the following command.
Increments the program counter and calles dispatch.*/
std::string siml::PyFormulaConverter::execute( CmFormula::BracketPairCmd const * /*cmd*/)
{
    string op;
    ++m_ProgramCounter; op  = dispatch();
    return "(" + op + ")";
}





