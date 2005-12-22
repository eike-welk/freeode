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
#include "siml_skip_grammar.h"
#include "siml_name_grammar.h"
#include "siml_model_grammar.h"
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

    //The keywords. TODO put this into the definition of name_grammar
    char const * const keywords[] = {
        "MODEL","PARAMETER", "VARIABLE", "SET", "EQUATION", "AS", "DEFAULT",
        "ASSIGN", "IF", "ELSE",
        "TYPICAL", "ANY"
        "END"
    };
    std::size_t const keywords_size = sizeof(keywords) / sizeof(keywords[0]);

    for (std::size_t i = 0; i < keywords_size; ++i) {
            name_grammar::reserved_keywords.add(keywords[i]);
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

    std::ifstream inputStream("/home/eike/sim_lang/src/test.siml");
    std::istreambuf_iterator<char> itBegin(inputStream);
    std::istreambuf_iterator<char> itEnd;
    std::string<char> inputStr(itBegin, itEnd);
    char const * inputCStr = inputStr.c_str();

    cout << "The input: \n";
    cout << inputCStr;
    cout << "\n\n";

    shared_ptr<CmCodeRepository> parse_result(new CmCodeRepository);
    model_grammar model(parse_result);
    skip_grammar skip;
    parse_info<> info;
    info = boost::spirit::parse(inputCStr, model, skip);

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

    show_CmCodeRepository(parse_result);

    //generate python program from CmCodeRepository
    std::ofstream pyOutputStream("/home/eike/sim_lang/src/testproc.py");
    PyGenerator pyGen(parse_result, pyOutputStream, cerr);

    pyGen.generate_all();

    pyOutputStream.close();

    return;
}


/*!
@todo fuction should add on member variables or be static
@todo make function const
*/
void Parser::show_CmCodeRepository(shared_ptr<CmCodeRepository> parse_result)
{
    cout << "error messages: " << endl;
    for( uint i=0; i < parse_result->error.size(); ++i )
    {
        cout << parse_result->error[i].message_from_parser << endl;
    }
    cout << endl;

    cout << "models parsed: " << endl;
    for( uint i=0; i < parse_result->model.size(); ++i )
    {
        CmModelDescriptor model;
        model = parse_result->model[i];

        cout << "model: " << model.name << endl;
        cout << "parameters:" << endl;
        for(uint i=0; i<model.parameter.size(); ++i) {
            cout << model.parameter[i].name << ",\t" << model.parameter[i].type << ",\t" << model.parameter[i].default_expr << endl;
        }
        cout << "variables:" << endl;
        for(uint i=0; i<model.variable.size(); ++i) {
            cout << model.variable[i].name << ",\t" << model.variable[i].type << endl;
        }
        cout << "equations:" << endl;
//     uint es=model.equation.size();
        for(uint i=0; i<model.equation.size(); ++i) {
//         cout << model.equation[i].definition_text << endl;
            cout << "lhs: "  << model.equation[i].lhs;
            cout << "  rhs: " << model.equation[i].rhs;
            if( model.equation[i].is_ode_assignment ) {
                cout << "  - ODE" << endl;
            } else {
                cout << "  - algebraic" << endl;
            }
        }
    }
}
