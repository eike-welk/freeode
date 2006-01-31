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

#ifndef SIML_PS_NAME_HPP
#define SIML_PS_NAME_HPP

#include <boost/spirit/core.hpp>
#include <boost/spirit/symbols/symbols.hpp>

namespace siml {

namespace spirit = boost::spirit;

/*!
@short This grammar specifies what a name is.

A Name must start with a letter or "_" and inside it can contain letters,
numbers and "_". A name can not be equal to a keyword.

The keyword rejection can be turned on and off in the constructor.

For rejection of keywords the ps_name contains a static member
reserved_keywords (a symbol table), where keywords should be added at the start
of the program.

@todo implement the correct template arguments for the position_iterator.
@todo see: http://www.boost.org/libs/spirit/doc/symbols.html
@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
class ps_name : public spirit::grammar<ps_name>
{
    public:
    //The coice of the <char> template agument is arbitrary. We won't look at it.
    typedef spirit::symbols<char> symbol_table_t;

    private:
    //!empty symbol table
    static symbol_table_t empty_table;
    //!symbol table that contains the keywords
    static symbol_table_t reserved_keywords;
    //!pointer to one of the static symbol tables
    symbol_table_t const * keywords;

    //!initialize the symbol table "reserved_keywords" with the language's keywords
    static symbol_table_t init_reserved_keywords();

    public:
    //!construct the grammar
    /*! @param check_reserved_keywords if true keywords are rejected, otherwise keywords are accepted too.
    */
    ps_name(bool check_reserved_keywords = true)
    {
        if( check_reserved_keywords )   { keywords = &reserved_keywords; }
        else                            { keywords = &empty_table; }
    }

    //!When the grammar is used the framework creates this struct.
    template <typename ScannerT>
    struct definition
    {
        definition(ps_name const & self)
        {
            using spirit::alpha_p;
            using spirit::alnum_p;
            using spirit::lexeme_d;
            //convert the pointer into a refference (the scanner syntax looks better this way)
            symbol_table_t const & keywords = *self.keywords;

            name =
                lexeme_d[ ((alpha_p | '_') >> *(alnum_p | '_')) ] - keywords;
        }

        //!Returns the start symbol. Called by spirit's internal magic.
        spirit::rule<ScannerT> const &
        start() const { return name; }

        private:
        spirit::rule<ScannerT> name;
    };
};

//Initialize the static symbol table
/*ps_name::symbol_table_t ps_name::reserved_keywords;
ps_name::symbol_table_t ps_name::empty_table;*/
//     ps_name::reserved_keywords = "MODEL","PARAMETER", "VARIABLE", "SET", "EQUATION", "AS", "DEFAULT",
//     "ASSIGN", "IF", "ELSE",
//     "TYPICAL",
//     "END";

} // namespace siml

#endif // SIML_PS_NAME_HPP
