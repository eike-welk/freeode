/*******************************************************************************
 *   Copyright (C) 2004 Angus Leeming
 *   Copyright (C) 2005 by Eike Welk
 *   eike.welk@post.rwth-aachen.de
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

#ifndef SIML_SKIP_GRAMMAR_HPP
#define SIML_SKIP_GRAMMAR_HPP

#include <boost/spirit/core.hpp>
#include <boost/spirit/utility.hpp>

namespace siml {

namespace spirit = boost::spirit;

/*!
@short Definition of whitespace and comments

This grammar specifies what part of the text are thrown away because they are
whitespace or comments.
Comments start with "#" and go to the end of the line.
Comment can be between curly brackets "{" .... "}". These comments can be nested.
*/
struct ps_skip : spirit::grammar<ps_skip>
{
    //!When the grammar is used the framework creates this struct.
    template <typename ScannerT>
    struct definition {
        definition(ps_skip const &)
        {
            using spirit::space_p;
            using spirit::anychar_p;
            using spirit::comment_nest_p;

            skip
                    = space_p
//                     | '#'  >> *(anychar_p - '\n')
                    | comment_p("#")
                    | comment_nest_p('{', '}');
//             whitespace
//                 = space_p - '\n';
        }

        spirit::rule<ScannerT> const &
        start() const { return skip; }

        private:
        spirit::rule<ScannerT> skip/*, whitespace*/;
    };
};

} // namespace siml

#endif // SIML_SKIP_GRAMMAR_HPP
