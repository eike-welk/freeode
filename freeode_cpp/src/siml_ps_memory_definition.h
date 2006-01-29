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
#ifndef SIML_PS_MEMORY_DEFINITION_H
#define SIML_PS_MEMORY_DEFINITION_H


#include "siml_code_model.h"
// #include "siml_cmformula.h"
#include "siml_ps_name.h"
// #include "siml_ps_formula.h"
// #include "siml_error_generator.h"

#include <boost/spirit.hpp>

#include <iostream>


namespace siml {
namespace spirit = boost::spirit;

/**
@short parse definition of variable or parameter

This grammar parses one line of the PARAMETER or VARIABLE section.

The parsed definition (the result) is in the member memory_descriptor.
A refference or pointer to this member can be passed to a functor
in a semantic action.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
struct ps_memory_definition : public spirit::grammar<ps_memory_definition>
{
    //!The parsed memory definition.
    CmMemoryDescriptor memory;

    ps_memory_definition(){}

    ~ps_memory_definition(){}

    /*!Functor that clears all members of the memory definition*/
    struct clear_mem_descriptor
    {
        CmMemoryDescriptor & m_memory;

        clear_mem_descriptor( CmMemoryDescriptor & mem):
                m_memory( mem) {}

        template <typename IteratorT>
        void operator()( IteratorT, IteratorT) const
        {
            m_memory=CmMemoryDescriptor();
        }
    };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
            struct definition
    {
        //!The grammar's rules.
        definition(ps_memory_definition const& self)
//             :true_val(true), false_val(false)
        {
//            using spirit::str_p; using spirit::ch_p; using spirit::alnum_p;
//            using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
//            using spirit::lexeme_d;
            using spirit::assign_a; using spirit::ch_p;


            //we need a mutable self for the semantic actions
            ps_memory_definition & selfm = const_cast<ps_memory_definition &>(self);

            memory_definition_rule
                =  name                                 [clear_mem_descriptor( selfm.memory)]  //clear temporary storage
                                                        [assign_a(selfm.memory.name)]   //store the name
                >> !("AS" >> ( name | "REAL" )          [assign_a(selfm.memory.type)])  //store the type
                >> +ch_p(';')
                ;
            ///@TODO add upper and lower bounds; units; and:
            //TODO  !("INITIAL" >> formula              [assign_a( v_temp.initial_expr, formula.formula)]) >> //store initial value
            //TODO  !("DEFAULT" >> formula              [assign_a( p_temp.default_expr, formula.formula)]) >> //store default value
        }

        //!The start rule of the grammar. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return memory_definition_rule; }

        //!Rules that are defined here
        spirit::rule<ScannerT> memory_definition_rule;
        //!Grammar that parses a name
        ps_name name;
        //!Constants because assign_a needs references
//         bool const true_val, false_val;
    };
};

}

#endif
