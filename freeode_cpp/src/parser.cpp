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
#include "siml_python_generator.h"

//#include <boost/spirit.hpp>
#include <boost/spirit/core.hpp>
//#include <boost/spirit/actor/push_back_actor.hpp>
//#include <boost/spirit/phoenix.hpp>
//#include <boost/spirit/symbols/symbols.hpp>

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

    //The keywords. TODO put this into the definition of ps_name
    char const * const keywords[] = {
        "MODEL","PARAMETER", "VARIABLE", "SET", "EQUATION", "AS", "DEFAULT",
        "ASSIGN", "IF", "ELSE",
        "TYPICAL", "ANY"
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

@todo File IO:


*/
void Parser::doParse()
{
//     char const * inputCStr =
//             "MODEL mo1\n"
//             "PARAMETER\n max_mu DEFAULT 0.32; Ks DEFAULT 0.1; Yxs DEFAULT 0.5; \n"
//             "VARIABLE\n  mu; X INITIAL 0.2; S INITIAL 10;\n"
// //             "SET\n p1:=5; p2:=6;\n"
//             "EQUATION\n mu := max_mu*S/(S+Ks); $X := mu*X; $S := 1/Yxs*mu*X;\n"
//             "END";

    std::ifstream inputStream("/home/eike/codedir/freeode/trunk/freeode_cpp/src/test.siml");
    std::istreambuf_iterator<char> itBegin(inputStream);
    std::istreambuf_iterator<char> itEnd;
    std::string<char> inputStr(itBegin, itEnd);
    char const * inputCStr = inputStr.c_str();

    cout << "The input: \n";
    cout << inputCStr;
    cout << "-----------------------------------------------------\n\n";

    shared_ptr<CmCodeRepository> parse_result(new CmCodeRepository);
//     CmCodeRepository* parse_result_ptr = parse_result;
//     ps_model model(parse_result.get());
    ps_toplevel toplevel_grammar(parse_result.get());
    ps_skip skip;
    parse_info<> info;
    info = boost::spirit::parse(inputCStr, toplevel_grammar, skip);

    if(info.full) {
        cout << "parser consumed all input.\n";
    }
    else if(info.hit) {
        cout << "parser consumed input partially.\n";
    }
    else
    {
        cout << "parsing failed.\n";
    }

//     cout << "possible error at:" << info.stop << endl;

//     show_CmCodeRepository(parse_result);
    parse_result->display();

    //generate python program from CmCodeRepository
    std::ofstream pyOutputStream("/home/eike/codedir/freeode/trunk/freeode_cpp/src/testproc.py");
    PyGenerator pyGen(parse_result, pyOutputStream, cerr);

    pyGen.generate_all();

    pyOutputStream.close();

    return;
}


