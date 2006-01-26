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
#include "siml_ps_path.h"
#include "siml_cmformula.h"
// #include "siml_error_generator.h"

#include <boost/spirit.hpp>
// #include <boost/spirit/symbols/symbols.hpp>
// #include <boost/spirit/actor/actors.hpp>
// #include <boost/shared_ptr.hpp>

// #include <string>
// #include <vector>
#include <iostream>


///use these definitions?
// typedef char                    char_t;
// typedef file_iterator <char_t>  iterator_t;
// typedef scanner<iterator_t>     scanner_t;
// typedef rule <scanner_t>        rule_t;


namespace siml {

namespace spirit = boost::spirit;

/**
@short parse formulas
Parser for mathematical expressions.

Usage ? Hmm.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
struct ps_formula : public spirit::grammar<ps_formula>
{
    ps_formula(){}

    ~ps_formula(){}

    CmFormula m_formula;

    struct push_path
    {
        CmPath const & m_InPath;
        CmFormula & m_OutFormula;

        push_path(CmPath const & inPath, CmFormula const & outFormula):
            m_InPath(inPath), m_OutFormula(const_cast<CmFormula&>(outFormula)) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
            std::cout   << "push_path: m_InPath: " << m_InPath.toString(".") << std::endl;
//             m_OutFormula.appendPath(m_InPath);
        }
    };
//
//     struct append_str
//     {
//         CmPath & m_path;
//
//         append_str(CmPath const & path) : m_path(const_cast<CmPath &>(path)) {}
//
//         template <typename IteratorT>
//                 void operator()(IteratorT first, IteratorT last) const
//         {
//             m_path.append(std::string(first, last));
//         }
//     };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!The grammar's rules.
        definition(ps_formula const& self)
        {
            using spirit::str_p; using spirit::ch_p; using spirit::alnum_p; using spirit::real_p;
            using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
//             using spirit::assign_a;
//             using spirit::lexeme_d;

//             number =
//                     (real_p >> eps_p)/*[push_int(self.code)]*/
//                     ;

            factor =
                    path[push_path(path.m_path, self.m_formula)]
                    |   (real_p >> eps_p)/*[push_number(self.code)]*/
                    |   ('(' >> expression >> ')')/*[push_bracket(self.code)]*/
                    |   ('-' >> factor)/*[push_op("-", 1, self.code)]*/
                    |   ('+' >> factor)
                    ;

            term =
                    factor
                    >> *(   ('*' >> factor)/*[push_op("*", 2, self.code)]*/
                        |   ('/' >> factor)/*[push_op(OP_DIV, self.code)]*/
                        )
                    ;

            expression =
                    term
                    >> *(   ('+' >> term)/*[push_op(OP_ADD, self.code)]*/
                        |   ('-' >> term)/*[push_op(OP_SUB, self.code)]*/
                        )
                    ;

            formula =
                eps_p/*[clear_formula(self.m_formula)]*/
                >> expression
                ;
        }

        //!The start rule of the grammar. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return formula; }

        //!Rules that are defined here
        spirit::rule<ScannerT> formula, expression, term, factor, number;
        //!Grammar that describes all names (model, parameter, variable)
        ps_path path;
    };
};

}

#endif
