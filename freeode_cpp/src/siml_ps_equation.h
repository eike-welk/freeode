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
#ifndef SIML_PS_EQUATION_H
#define SIML_PS_EQUATION_H


#include "siml_code_model.h"
#include "siml_cmpath.h"
#include "siml_cmformula.h"
#include "siml_ps_path.h"
#include "siml_ps_formula.h"
#include "siml_error_generator.h"

#include <boost/spirit.hpp>

#include <iostream>


namespace siml {

namespace spirit = boost::spirit;

/**
@short parse equations
Parser for an equation e.g: "mu := mu_max*S/(S+Ks);"
The parsed equation (the result) is in the member equation.
A refference or pointer to this member can be passed to a functor
in a semantic action.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
struct ps_equation : public spirit::grammar<ps_equation>
{
    ps_equation(){}

    ~ps_equation(){}

    //!The parsed equation.
    CmEquationDescriptor equation;

    /*!Functor that clears all members of the equation*/
    struct clear_equation
    {
        CmEquationDescriptor & m_equation;

        clear_equation( CmEquationDescriptor & equation):
                m_equation( equation) {}

        template <typename IteratorT>
        void operator()( IteratorT, IteratorT) const
        {
            m_equation=CmEquationDescriptor();
        }
    };

    /*!Functor that sets some options that are not set by the parsers.*/
//     struct finish_equation
//     {
//         CmEquationDescriptor & m_equation;
//
//         finish_equation( CmEquationDescriptor & equation): m_equation( equation) {}
//
//         template <typename IteratorT>
//         void operator()( IteratorT, IteratorT) const
//         {
//             /*[assign_a( e_temp.is_ode_assignment, true)]*/
//         }
//     };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!The grammar's rules.
        definition(ps_equation const& self):
                true_val(true), false_val(false)
        {
            using spirit::str_p; using spirit::ch_p; using spirit::alnum_p;
            using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
//             using spirit::assign_a;
            using spirit::lexeme_d;

            //we need a mutable self for the semantic actions
            ps_equation & selfm = const_cast<ps_equation &>(self);

            equation_rule
                =  path         [clear_equation(selfm.equation)]
                                [assign_a(selfm.equation.lhs, path.path)]
                >> str_p(":=")  /*[assign_a( selfm.equation.is_assignment, true_val)]*/
                >> formula      [assign_a( selfm.equation.rhs, formula.formula)]
                >> (+ch_p(';')) /*[finish_equation(selfm.equation)]*/
                ;
        }

        //!The start rule of the grammar. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return equation_rule; }

        //!Rules that are defined here
        spirit::rule<ScannerT> equation_rule;
        //!Grammar that describes a formula
        ps_formula formula;
        //!Grammar that describes a path
        ps_path path;
        //!Constants because assign_a needs references
        bool const true_val, false_val;
    };
};

}

#endif

