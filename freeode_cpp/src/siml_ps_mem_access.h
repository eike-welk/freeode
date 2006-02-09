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
#ifndef SIML_PS_MEM_ACCESS_H
#define SIML_PS_MEM_ACCESS_H


// #include "siml_code_model.h"
// #include "siml_cmpath.h"
// #include "siml_cmformula.h"
#include "siml_ps_path.h"
// #include "siml_ps_formula.h"
#include "siml_cmmemaccess.h"
#include "siml_error_generator.h"

#include <boost/spirit.hpp>

#include <iostream>


namespace siml {

namespace spirit = boost::spirit;

/**
@short parse equations
Parser for a memory access e.g: "$r001.X" or "r001.X"
The parsed memory access opject (the result) is a public member variable "access".
A refference or pointer to this member can be passed to a functor
in a semantic action.

ps_mem_access should one day be able to parse all of the following, and sensible combinations:
- r001.v001.X                       : simple path
- $r001.v001.X                      : time derivation
-       -------------   not implemented from here on     -------------
- r001.v001.X[0:50.2]               : partial access, possibly multi dimensional
- PARTIAL(r001.v001.X, h1)          : space derivation
- PARTIAL(r001.v001.X[0:50.2], h1)  : space derivation of a part
- DIFF(r001.v001.X, h1)             : alternative syntax for space derivation
- DIFF(r001.v001.X, Time)           : derivation in time direction, without integration of variable

@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
struct ps_mem_access : public spirit::grammar<ps_mem_access>
{
    ps_mem_access(){}

    ~ps_mem_access(){}

    //!The parsed memory access object.
    CmMemAccess mem_access;

    /*!Functor that initializes all members of the memory access object.*/
    struct clear_access
    {
        CmMemAccess & m_access;

        clear_access( CmMemAccess & access):
                m_access( access) {}

        template <typename IteratorT>
        void operator()( IteratorT /*begin*/, IteratorT) const
        {
            m_access = CmMemAccess();
        }
    };

//     set_time_derivative_true(selfm.path)
    /*!Functor that changes the time derivative propperty of the memory access object.*/
    struct set_time_derivative_true
    {
        CmMemAccess & m_access;

        set_time_derivative_true( CmMemAccess & access):
                m_access( access) {}

        template <typename IteratorT>
        void operator()( IteratorT /*begin*/, IteratorT) const
        {
            m_access.setTimeDerivative( true);
        }
    };

    /*!Functor that changes the path propperty of the memory access object.*/
    struct set_path
    {
        CmMemAccess & m_access;
        CmPath & m_path;

        set_path( CmMemAccess & access, CmPath & path):
                m_access( access), m_path( path) {}

        template <typename IteratorT>
        void operator()( IteratorT /*begin*/, IteratorT) const
        {
            m_access.setPath( m_path);
        }
    };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!The grammar's rules.
        definition(ps_mem_access const& self)/*:
                true_val(true), false_val(false)*/
        {
            using spirit::str_p; using spirit::ch_p; using spirit::alnum_p;
            using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
//             using spirit::assign_a;
            using spirit::lexeme_d;

            //we need a mutable self for the semantic actions
            ps_mem_access & selfm = const_cast<ps_mem_access &>(self);

            memory_access_rule
                    =   eps_p               [clear_access(selfm.mem_access)]
                    >>  !(str_p("$")        [set_time_derivative_true(selfm.mem_access)] )
                    >>  path                [set_path(selfm.mem_access, path.path)]
                    ;
        }

        //!The start rule of the grammar. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return memory_access_rule; }

        //!Rules that are defined here
        spirit::rule<ScannerT> memory_access_rule;
        //!Grammar that recognizes a path
        ps_path path;
        //!Constants because assign_a needs references
//         bool const true_val, false_val;
    };
};

}

#endif

