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
 ***************************************************************************
 *   This file is based on the calculator/v_machine example from the       *
 *   spirit documentation. Published under the Boost Software License.     *
 *   Copyright (c) 1998-2003 Joel de Guzman                                *
 *   Thank you for this usefull example!                                   *
 *   URL:                                                                  *
 *   http://www.boost.org/libs/spirit/example/fundamental/\                *
 *   more_calculators/vmachine_calc.cpp                                    *
 ***************************************************************************/
#ifndef SIML_PS_FORMULA_H
#define SIML_PS_FORMULA_H


// #include "siml_cmpath.h"
// #include "siml_ps_path.h"
#include "siml_ps_mem_access.h"
#include "siml_cmformula.h"
// #include "siml_error_generator.h"

#include <boost/spirit.hpp>
// #include <boost/spirit/symbols/symbols.hpp>
// #include <boost/spirit/actor/actors.hpp>
// #include <boost/shared_ptr.hpp>

// #include <string>
// #include <vector>
#include <iostream>


namespace siml {

namespace spirit = boost::spirit;

/**
@short parse formulas
Parser for mathematical expressions.
The parsed formula (the result) is in the member formula.
A refference or pointer to the member formula can be passed to a functor's
constructor in a semantic action.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
struct ps_formula : public spirit::grammar<ps_formula>
{
    ps_formula(){}

    ~ps_formula(){}

    CmFormula formula;

    /*!Functor to delete the formula's contents*/
    struct clear_formula
    {
        CmFormula & m_OutFormula;

        clear_formula(CmFormula & outFormula): m_OutFormula( outFormula) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
//             std::cout << "clear_formula" << std::endl;
            m_OutFormula.clear();
        }
    };

    /*!Functor to add a path to the end of the formula.*/
    struct append_mem_access
    {
        CmMemAccess const & m_access;
        CmFormula & m_OutFormula;

        append_mem_access( CmMemAccess const & inAccess, CmFormula & outFormula):
                m_access( inAccess), m_OutFormula( outFormula) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
//             std::cout << "append_mem_access: m_InPath: " << m_InPath.toString(".") << std::endl;
            m_OutFormula.pushBackMemAccess(m_access);
        }
    };

    /*!Functor to add a number to the end of the formula.*/
    struct append_number
    {
        CmFormula & m_OutFormula;

        append_number( CmFormula & outFormula): m_OutFormula( outFormula) {}

        template <typename IteratorT>
        void operator()( IteratorT begin, IteratorT end) const
        {
//             std::cout << "append_number: " << std::string( begin, end) << std::endl;
            m_OutFormula.pushBackNumber( std::string( begin, end));
        }
    };

    /*!Functor to add a mathematical operator to the end of the formula.*/
    struct append_operator
    {
        std::string m_Symbol;
        uint m_Ops;
        CmFormula & m_OutFormula;

        /*!@param inSymbol   Formula symbbol for operator e.g. "+".
           @param inOps      Number of operands (2, 1 possible for "-").
           @param outFormula Reference to the formula object where the operator will be stored.
        */
        append_operator( std::string inSymbol, uint inOps, CmFormula & outFormula):
                m_Symbol(inSymbol), m_Ops(inOps), m_OutFormula( outFormula) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
//             std::cout << "append_operator: m_Symbol: " << m_Symbol << ", m_Ops: " << m_Ops << std::endl;
            m_OutFormula.pushBackMathOperator( m_Symbol, m_Ops);
        }
    };

    /*!Functor to add a pair of brackets to the end of the formula.*/
    struct append_brackets
    {
        CmFormula & m_OutFormula;

        append_brackets( CmFormula & outFormula): m_OutFormula(outFormula) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
//             std::cout << "append_brackets" << std::endl;
            m_OutFormula.pushBackBrackets();
        }
    };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!The grammar's rules.
        definition(ps_formula const& self)
        {
//             using spirit::str_p; using spirit::ch_p; using spirit::alnum_p;
//             using spirit::nothing_p; using spirit::anychar_p;
//             using spirit::assign_a;
//             using spirit::lexeme_d;
            using spirit::real_p; using spirit::eps_p;

            //we need a mutable self for the semantic actions
            ps_formula & selfm = const_cast<ps_formula &>(self);

            formula =
                eps_p                       [clear_formula( selfm.formula)]
                >> expression
                ;

            expression
                    =  term
                    >> *(   ('+' >> term)   [append_operator( "+", 2, selfm.formula)]
                        |   ('-' >> term)   [append_operator( "-", 2, selfm.formula)]
                        )
                    ;

            term
                    =  factor
                    >> *(   ('*' >> factor) [append_operator( "*", 2, selfm.formula)]
                        |   ('/' >> factor) [append_operator( "/", 2, selfm.formula)]
                        )
                    ;

            ///@todo add exponential rule (binding stronger than sign)
            factor
                    =   identifier                  [append_mem_access( identifier.mem_access, selfm.formula)]
                    |   (real_p >> eps_p)           [append_number( selfm.formula)]
                    |   ('(' >> expression >> ')')  [append_brackets( selfm.formula)]
                    |   ('-' >> factor)             [append_operator( "-", 1, selfm.formula)]
                    |   ('+' >> factor)
                    ;
        }

        //!The start rule of the grammar. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return formula; }

        //!Rules that are defined here
        spirit::rule<ScannerT> formula, expression, term, factor, number;
        //!Grammar that recognizes access to variables and parameters
        ps_mem_access identifier;
    };
};

}

#endif
