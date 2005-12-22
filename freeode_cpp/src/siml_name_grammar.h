/***************************************************************************
 *   Copyright (C) 2005 by Eike Welk   *
 *   eike.welk@post.rwth-aachen.de   *
 *   Copyright (C) 2004 Angus Leeming
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
 *
 *
 *   The file was originally taken from "YAC"
 *   (http://www.lyx.org/~leeming/yac/), where it was distributed
 *   under the Boost Software License, Version 1.0.
 ******************************************************************************/

#ifndef SIML_NAME_GRAMMAR_HPP
#define SIML_NAME_GRAMMAR_HPP

#include <boost/spirit/core.hpp>
#include <boost/spirit/symbols/symbols.hpp>

namespace siml {

namespace spirit = boost::spirit;

/*!
@short This grammar specifies what a name is.

A Name must start with a letter or "_" and inside it can contain letters,
numbers and "_". A name can not be equal to a keyword.

The keyword rejection can be turned on and off in the constructor.

For rejection of keywords the name_grammar contains a static member
reserved_keywords (a symbol table), where keywords should be added at the start
of the program.
*/
class name_grammar : public spirit::grammar<name_grammar>
{
    spirit::symbols<char> dummy_reserved_keywords;

public:
    // We are only interested in the names themselves.
    // char is just the smallest space waster available.
    static spirit::symbols<char> reserved_keywords;
    spirit::symbols<char> const & keywords;

    //!construct the name_grammar
    /*! @param check_reserved_keywords if true keywords are rejected, otherwise keywords are accepted too.
    */
    name_grammar(bool check_reserved_keywords = true)
        : keywords(check_reserved_keywords ?
                   reserved_keywords :
                   dummy_reserved_keywords)
    {}

    //!When the grammar is used the framework creates this struct.
    template <typename ScannerT>
    struct definition {
        definition(name_grammar const & self)
        {
            using spirit::alpha_p;
            using spirit::alnum_p;
            using spirit::lexeme_d;

            name
                = lexeme_d[ ((alpha_p | '_') >> *(alnum_p | '_')) ]
                  - self.keywords;
        }

        spirit::rule<ScannerT> const &
        start() const { return name; }

        private:
        spirit::rule<ScannerT> name;
    };
};

//Initialize the static symbol table
spirit::symbols<char> name_grammar::reserved_keywords;

} // namespace siml

#endif // SIML_NAME_GRAMMAR_HPP
