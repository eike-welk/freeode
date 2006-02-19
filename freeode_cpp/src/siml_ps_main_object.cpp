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
#define PHOENIX_LIMIT 10
#define BOOST_SPIRIT_CLOSURE_LIMIT 10

#include "siml_globaldef.h"

#include "siml_ps_main_object.h"
#include "siml_ps_skip.h"
// #include "siml_ps_name.h"
// #include "siml_ps_model.h"
#include "siml_ps_toplevel.h"
// #include "siml_pygenmain.h"
// #include "siml_cmerror.h"

#include <boost/spirit.hpp>
// #include <boost/spirit/core.hpp>
//#include <boost/spirit/actor/push_back_actor.hpp>
//#include <boost/spirit/phoenix.hpp>
//#include <boost/spirit/symbols/symbols.hpp>
// #include <boost/spirit/iterator.hpp>

#include <iostream>
// #include <vector>
// #include <string>
// #include <streambuf>
// #include <fstream>


using namespace std;
using namespace boost::spirit;
using namespace siml;
using boost::shared_ptr;


siml::ps_main_object::ps_main_object()
{
}


siml::ps_main_object::~ps_main_object()
{
}


/*!
This is the parsing action
*/
void siml::ps_main_object::doParse( BufferIterator bufBegin, BufferIterator bufEnd)
{
    //create instance of the toplevel grammar.
    ps_toplevel toplevel_grammar;
    //this parser recognizes whitespace and comments
    ps_skip skip;
    //this object caries the result of parsing.
    parse_info<BufferIterator> info;

    //do the parsing. The results are stored in the global struct
    //CmCodeRepository::repository which is accessible by the non member function
    //repository()
    info = boost::spirit::parse(bufBegin, bufEnd, toplevel_grammar, skip);

    ///@todo this is debug output. (-m)
//     if     (info.full){ cout << "parser consumed all input.\n"; }
//     else if(info.hit) { cout << "parser consumed input partially.\n"; }
//     else              { cout << "parser consumed no input.\n"; }
    ///@todo this is debug output. (-mmm)
//     repository()->display();

    return;
}


