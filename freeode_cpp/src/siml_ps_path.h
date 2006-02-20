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


namespace siml {

namespace spirit = boost::spirit;

/**
@short parse paths
Parser for a variable or a parameter path e.g: "mo1.X"
The parsed path (the result) is in the member path.
A refference or pointer to it can be passed to a functor's constructor
in semantic action. e.g.:
@code
//The functor
struct my_functor{
    my_functor(CmPath const & inPath) : m_InPath(inPath) {}
    template <typename IteratorT>
    void operator()(IteratorT first, IteratorT last) const {...do someting...}
}
//use the functor
ps_path p1;
my_rule=p1[my_functor(p1.path);
@endcode

With functor_parser it is possible to pass the path directly to the semantic action.
The existing grammar could be mostly reused.
An other alternative are closures.

See functor_parser in the docs. It does just that. Below is an example whose
result_t is a std::string.
@code
struct QS
{
   typedef std::string result_t;

   template< typename ScannerT >
   int operator()
   ( ScannerT const& scan, result_t& result )const
   {
      match<> m = ( lexeme_d[( '"'
                    >> !( (*(c_escape_ch_p-'"'))[assign(result)] ) >> '"' )]
                  ).parse( scan );

      return m? m.length() : -1;
   }
};

const functor_parser<QS> QS_p;
@endcode

@todo integrate subscripts: "film.X(0:20)"

@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
struct ps_path : public spirit::grammar<ps_path>
{
    ps_path(){}

    ~ps_path(){}

    //!The parsed path.
    CmPath path;

    /*! Functor that makes the path to be a time derivative.*/
    struct set_time_derivative_true
    {
        CmPath & m_path;

        set_time_derivative_true(CmPath & path) : m_path( path) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
            m_path.setTimeDerivative( true);
        }
    };

    /*! Functor that deletes all components and sets derivative to false.*/
    struct clear_path
    {
        CmPath & m_path;

        clear_path(CmPath & path) : m_path( path) {}

        template <typename IteratorT>
        void operator()(IteratorT, IteratorT) const
        {
            m_path.clear();
        }
    };

    /*! Functor that adds a string to the end of a path.*/
    struct append_str
    {
        CmPath & m_path;

        append_str(CmPath & path) : m_path( path) {}

        template <typename IteratorT>
        void operator()(IteratorT first, IteratorT last) const
        {
            m_path.append(std::string(first, last));
        }
    };

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!Current iterator type
        /*!
        The scanner contains the type of the iterator which is used in the parse function
        (among other things). So if you start parsing (in the toplevel cpp file) with:
        @code
        char const * inputCStr = ....;
        ....
        info = boost::spirit::parse(inputCStr, toplevel_grammar, skip);
        @endcode
        Then IteratorT will be:  @code char const * @endcode
        */
        typedef typename ScannerT::iterator_t IteratorT;

        //!The grammar's rules.
        definition(ps_path const& self)
        {
//             using spirit::str_p; using spirit::ch_p; using spirit::alnum_p;
//             using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
//             using spirit::assign_a;
            using spirit::str_p; using spirit::eps_p;
            using spirit::lexeme_d;

            //we need a mutable self for the semantic actions
            ps_path & selfm = const_cast<ps_path &>(self);

            path = lexeme_d
                    [
                        eps_p               [clear_path(selfm.path)]
//                         >> !(str_p("$")     [set_time_derivative_true(selfm.path)] )
                        >> name             [append_str(selfm.path)]
                        >> *("." >> name    [append_str(selfm.path)] )
                    ];
            //             path = lexeme_d[name >> *("." >> name) >> eps_p-(alnum_p | '_')]; //maybe better because then we know when the rule is finished
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
