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
#ifndef SIML_PS_PATH_H
#define SIML_PS_PATH_H


#include "siml_cmpath.h"
#include "siml_ps_name.h"
#include "siml_error_generator.h"

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
@short parse paths

Usage ? Hmm.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class ps_path : public spirit::grammar<ps_path>
{
public:
    ps_path(){};

    ~ps_path(){};

private:
    //!The parsed path.
    CmPath m_path;

public:
    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!Current iterator type
        /*!
        The scanner contains the type of the iterator which is used in the parse function
        (among other things). So if we write:
        @code
        char const * inputCStr = ....;
        ....
        info = boost::spirit::parse(inputCStr, toplevel_grammar, skip);
        @endcode
        Then IteratorT will be:  @code char const * @endcode
        */
        typedef typename ScannerT::iterator_t IteratorT;

        ///@todo Implement the functors

        //!The grammar's rules.
        definition(ps_path const& self)
        {
            using spirit::str_p; using spirit::ch_p;
            using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
            using spirit::assign_a;

//             CmPath test=self.m_path; //access to the grammars private members is possible.

            path = (name >> *("." >> name));
        }

        //!The start rule of the grammar. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return path; }

        private:
        //!Rules that are defined here
        spirit::rule<ScannerT> path;
        //!Grammar that describes all names (model, parameter, variable)
        ps_name name;
    };
};

}

#endif
