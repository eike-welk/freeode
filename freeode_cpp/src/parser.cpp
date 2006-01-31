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

#include "parser.h"
#include "siml_ps_skip.h"
// #include "siml_ps_name.h"
// #include "siml_ps_model.h"
#include "siml_ps_toplevel.h"
#include "siml_pyprocessgenerator.h"
#include "siml_cmerror.h"

//#include <boost/spirit.hpp>
#include <boost/spirit/core.hpp>
//#include <boost/spirit/actor/push_back_actor.hpp>
//#include <boost/spirit/phoenix.hpp>
//#include <boost/spirit/symbols/symbols.hpp>
#include <boost/spirit/iterator.hpp>

#include <iostream>
#include <vector>
#include <string>
#include <streambuf>
#include <fstream>


using namespace std;
using namespace boost::spirit;
using namespace siml;
using boost::shared_ptr;


Parser::Parser()
{

    ///The keywords. @todo put this into the definition of ps_name
    char const * const keywords[] = {
        "MODEL","PARAMETER", "VARIABLE", "SET", "EQUATION", "AS", "DEFAULT",
        "ASSIGN", "IF", "ELSE",
        "TYPICAL",
        "END"
    };
    std::size_t const keywords_size = sizeof(keywords) / sizeof(keywords[0]);

    for (std::size_t i = 0; i < keywords_size; ++i) {
            ps_name::reserved_keywords.add(keywords[i]);
    }
}


Parser::~Parser()
{
}


/*!
This is the parsing action
*/
void Parser::doParse()
{
    std::ifstream inputStream("/home/eike/codedir/freeode/trunk/freeode_cpp/src/test.siml");
    std::istreambuf_iterator<char> itBegin(inputStream);
    std::istreambuf_iterator<char> itEnd;
    std::string<char> inputStr="\n\n\n"+std::string(itBegin, itEnd)+"\n\n\n"; //protect against iterating beyond begin or end of the string by the error generation function.
    char const * inputCStr = inputStr.c_str();

    ///@todo using different iterators than "char const *" does not work.
    ///@todo make sure BufferIterator ("siml_code_model.h") is equal to iterator_t
//     typedef position_iterator<char const *> iterator_t;
//     iterator_t begin(inputCStr, inputCStr+strlen(inputCStr), "test.file");
//     iterator_t end;
    typedef char const * iterator_t;
    iterator_t begin = inputCStr;
    iterator_t end = inputCStr+strlen(inputCStr);

    cout << "The input: \n";
    cout << inputStr;
    cout << "-----------------------------------------------------\n\n";

    shared_ptr<CmCodeRepository> parse_result(new CmCodeRepository);
    ps_toplevel toplevel_grammar(parse_result.get());
    ps_skip skip;
    parse_info<> info;
//     info = ps_toplevel.parse(begin, end, skip);
    info = boost::spirit::parse(begin, end, toplevel_grammar, skip);

    if     (info.full){ cout << "parser consumed all input.\n"; }
    else if(info.hit) { cout << "parser consumed input partially.\n"; }
    else              { cout << "parsing failed.\n"; }

    parse_result->display();

    //generate python program from CmCodeRepository
    std::ofstream pyOutputStream("/home/eike/codedir/freeode/trunk/freeode_cpp/src/testproc.py");
    PyProcessGenerator pyGen(parse_result, pyOutputStream, cerr);
    pyGen.generateAll();
    pyOutputStream.close();

    CmError::printStorageToCerr();
    return;
}


