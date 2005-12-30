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

#define BOOST_SPIRIT_DEBUG

#include "siml_code_model.h"
// #include "siml_ps_name.h"
#include "siml_ps_model.h"
#include "siml_ps_process.h"

#include <boost/spirit/core.hpp>
#include <boost/spirit/symbols/symbols.hpp>
// #include <boost/shared_ptr.hpp>

#include <string>
// #include <vector>
#include <iostream>

//!Intermediate storage for data aquired while parsing a model.
/*!Created a new namespace to avoid name clashes since these are all global symbols.
The namespace is named for easier access in KDevelop. */
namespace temp_store_toplevel {
using namespace siml;
using namespace std;
// using boost::shared_ptr;


//!pointer to the central storage of parse results
CmCodeRepository* parse_result_storage;


} //namespace temp_store_toplevel



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
        //!Construct the grammar and give it a pointer to the code model
        /*!Initializes the result storage pointers for all other grammars too.*/
        ps_toplevel(CmCodeRepository* parse_storage)
        {
            temp_store_toplevel::parse_result_storage = parse_storage;
            //initialize the result storage pointers for all other grammars
            ps_model::set_result_storage(parse_storage);
            ps_process::set_result_storage(parse_storage);
        }

        //!When the grammar is used the framework creates this struct. All rules are defined here.
        template <typename ScannerT> struct definition
        {
            //!The grammar's rules.
            definition(ps_toplevel const& self)
            {
                using namespace temp_store_toplevel;
                using spirit::str_p; using spirit::ch_p;
                using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
                using spirit::assign_a;

                //The start rule. Parses a complete file.
                toplevel_definition
                        = *(
                                model
                            |   process
                           );
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
            ps_process process;
        };
    };

} // namespace siml

#endif // SIML_PS_TOPLEVEL_H
