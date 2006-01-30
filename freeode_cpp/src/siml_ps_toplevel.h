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
#ifndef SIML_PS_TOPLEVEL_H
#define SIML_PS_TOPLEVEL_H


#include "siml_code_model.h"
// #include "siml_ps_name.h"
#include "siml_ps_model.h"
// #include "siml_ps_process.h"
#include "siml_error_generator.h"

#include <boost/spirit/core.hpp>
#include <boost/spirit/symbols/symbols.hpp>
// #include <boost/shared_ptr.hpp>

#include <string>
// #include <vector>
#include <iostream>


namespace siml {
namespace spirit = boost::spirit;

/*!
@short Top level parser.

The parser uses global variables to store temporary
information, during a parsing run.

The temporary varibles and the semantic actions reside in the namespace
"temp_store_toplevel".
 */
struct ps_toplevel : public spirit::grammar<ps_toplevel>
{
    //!pointer to the central storage of parse results
    CmCodeRepository* parse_result_storage;
    //!temporary storage for errors
    CmErrorDescriptor err_temp;

    //!Construct the grammar and give it a pointer to the code model
    ps_toplevel(CmCodeRepository* parse_storage): parse_result_storage( parse_storage) {}

    /*!Functor that adds an error to the error list.*/
    struct add_error
    {
        ps_toplevel & m_grammar;

        add_error( ps_toplevel & grammar): m_grammar( grammar) {}

        template <typename IteratorT>
        void operator()( IteratorT, IteratorT) const
        {
            cout << "Error at toplevel!" << endl;
            m_grammar.parse_result_storage->error.push_back(m_grammar.err_temp);
        }
    };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT> struct definition
    {
        //!The grammar's rules.
        definition(ps_toplevel const& self):
            model( self.parse_result_storage)
        {
            using spirit::str_p; using spirit::ch_p;
            using spirit::eps_p; using spirit::nothing_p;
            using spirit::print_p; using spirit::anychar_p;
            using spirit::assign_a;

            //we need a mutable self for the semantic actions
            ps_toplevel & selfm = const_cast<ps_toplevel &>(self);

            //The start rule. Parses a complete file.
            toplevel_definition
                = *( model
//                   |   parameter_estimation
                    | ( ( print_p - "MODEL" - "PROCESS" )   [make_error("Expecting MODEL or PROCESS definition.", selfm.err_temp)]
                                                            [add_error( selfm)] >>
                          nothing_p
                      )
                    )
                ;
        }

        //!The start rule of the model grammar.
        spirit::rule<ScannerT> const &
        start() const { return toplevel_definition; }

        private:
        //!Rules that are defined here
        spirit::rule<ScannerT> toplevel_definition;
        //!Grammar that describes a model
        ps_model model;
        //!Grammar that describes a process
//             ps_process process;
    };
};

} // namespace siml

#endif // SIML_PS_TOPLEVEL_H
