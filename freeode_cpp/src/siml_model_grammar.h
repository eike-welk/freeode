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
#ifndef SIML_MODEL_GRAMMAR_HPP
#define SIML_MODEL_GRAMMAR_HPP

#include "siml_code_model.h"
#include "siml_name_grammar.h"

#include <boost/spirit/core.hpp>
#include <boost/spirit/symbols/symbols.hpp>
// #include <boost/shared_ptr.hpp>

#include <string>
// #include <vector>
#include <iostream>

//!Intermediate storage for data aquired while parsing a model.
/*!Created a new namespace to avoid name clashes since these are all global symbols.
The namespace is named for easier access in KDevelop. */
namespace temp_store_model {
using namespace siml;
using namespace std;
// using boost::shared_ptr;

//!The data gathered while parsing the model is stored here
CmModelDescriptor model;

//!error string
string possible_error;

//!Clear the whole temorary model
void start_model(char const *, char const *)
{
    model = CmModelDescriptor();
    possible_error = "Error at start of MODEL definition";
}

//parameter----------------------------------------------------------------
//!temporary storage while a parameter definition is parsed
CmParameterDescriptor p_temp;
//!Clear the temporary storage for parsing parameters
void start_parameter(char const *, char const *) { p_temp = CmParameterDescriptor(); }
//!Add a parameter definition to the model.
/*!The function takes "p_temp" and puts it into "model.parameter"; the container for
parsed parameters. The chunk of text that led to the new parameter desciptor
is stored too*/
void add_parameter(char const * first, char const * const last)
{
    p_temp.definition_text = string(first, last);
    model.parameter.push_back(p_temp);
}

//variable----------------------------------------------------------------
//!temporary storage while a variable definition is parsed
CmVariableDescriptor v_temp;
//!Clear the temporary storage for the CmVariableDescriptor objects
void start_variable(char const *, char const *) { v_temp = CmVariableDescriptor(); }
//!Add a variable definition to the model.
/*!See add_parameter*/
void add_variable(char const * first, char const * const last)
{
    v_temp.definition_text = string(first, last);
    model.variable.push_back(v_temp);
}
//!Mark one variable inside model as a state variable.
/*!If the variable does not exist nothing will happen. @todo Should this become an internal compiler eror?*/
void set_variable_integrated(char const * first, char const * const last)
{
    string stateVarName(first, last);

    //loop over all variables to find the variable that will be marked
    CmVariableTable::iterator it;
    for( it = model.variable.begin(); it != model.variable.end(); ++it )
    {
        CmVariableDescriptor& varD = *it;
        if( varD.name == stateVarName )
        {
            varD.is_state_variable = true;
            break;
        }
    }
}

//equation----------------------------------------------------------------
//!temporary storage while a variable definition is parsed
CmEquationDescriptor e_temp;
//!Clear the temporary storage for the CmEquationDescriptor objects
void start_equation(char const *, char const *) { e_temp = CmEquationDescriptor(); }
//!Add an assignment to a algebraic variable to the model. (a:=p2*c)
void add_algebraic_assignment(char const * first, char const * const last)
{
    e_temp.definition_text = string(first, last);
    e_temp.is_assignment = true;
    e_temp.is_ode_assignment = false; //this is algebraic
    model.equation.push_back(e_temp);
}
//!Add an assignment to the derivative of an integrated variable to the model. ($c:=p1*c)
void add_assignment_time_derivative(char const * first, char const * const last)
{
    e_temp.definition_text = string(first, last);
    e_temp.is_assignment = true;
    e_temp.is_ode_assignment = true; //this is an ODE
    model.equation.push_back(e_temp);
}

//!pointer to the central storage of parse results
CmCodeRepository* parse_result_storage;

//!return the correctly parsed model.
void return_model(char const * /*first*/, char const * const /*last*/)
{
    cout << "Parsing model " << model.name << " finished correctly." << endl;
    parse_result_storage->model.push_back(model);
//     parse_result_storage.reset(); //decrease refference count
}

//!return the error (the partial model is returned too).
void return_error(char const * /*first*/, char const * const /*last*/)
{
    cout << "Parsing model " << model.name << " failled!" << endl;
    cout << possible_error << endl;

    CmErrorDescriptor ed;
    ed.message_from_parser = possible_error;
    parse_result_storage->error.push_back(ed);
    parse_result_storage->model.push_back(model);
//     parse_result_storage.reset(); //decrease refference count
}

} //namespace temp_store_model



namespace siml {

namespace spirit = boost::spirit;


/*!
@short Grammar of a "MODEL".

The model uses global variables to store temporary
information, during a parsing run.

@todo review this comment: Therefore the models can't be nested.
To get around this limitation struct definition cold use functor members. For an
example see: /usr/include/boost/spirit/symbols/symbols.hpp

The temporary varibles and the semantic actions reside in the namespace
"temp_store_model".
*/
struct model_grammar : public spirit::grammar<model_grammar>
{
    //!Construct the grammar
    /*!Before using the grammar it must have a pointer to the global result storage.
    Therefore the function set_result_storage (...) must be called. (once for all
    model_grammar instances)*/
    model_grammar() {}

    //!Give the grammar a pointer to the global storage for parse results.
    static void set_result_storage(CmCodeRepository* result_storage)
    {
        temp_store_model::parse_result_storage = result_storage;
    }

    //!When the grammar is used the framework creates this struct. All rules are defined here.
    template <typename ScannerT>
    struct definition
    {
        //!The grammar's rules.
        definition(model_grammar const& self)
        {
            using namespace temp_store_model;
            using spirit::str_p; using spirit::ch_p;
            using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
            using spirit::assign_a;

            //The start rule. Parses the complete model: MODEL ... END
            model_definition
                = ( eps_p                   [&start_model] >> //clear all temorary storage
                    "MODEL" >> name         [assign_a(model.name)] >>
                    !parameter_section >> !variable_section >> !set_section >> !equation_section >>
                    "END"
                  )                         [&return_model]
                | ( eps_p                   [&return_error] >>
                    nothing_p
                  );

            //parse block of parameter definitions: PARAMETER p1 AS REAL DEFAULT 1; p2 AS REAL DEFAULT 10; ...
            parameter_section
                =   str_p("PARAMETER") >>
                    *(    parameter_definition
                        | (eps_p[assign_a(possible_error, "Error in parameter definition!")] >> nothing_p)
                     );
            parameter_definition //@TODO allow math expression in DEFAULT; units
                = ( eps_p                                [&start_parameter] >> //clear temporary storage
                    (name - param_name)                  [param_name.add] //store in symbol table + check if name is already taken
                                                         [assign_a(p_temp.name)] >>  //store name in temporary storage
                    !("AS" >> str_p("REAL")              [assign_a(p_temp.type)]) >> //store parameter type
                    !("DEFAULT" >> rough_math_expression [assign_a(p_temp.default_expr)]) >> //store default value
                    +(ch_p('\n') | ';')
                  )                                      [&add_parameter]; //add parameter definition to model

            //parse block of variable definitions: VARIABLE v1 AS ANY; v2 AS ANY; ...
            variable_section
                = str_p("VARIABLE") >>
                *(    variable_definition
                    | (eps_p[assign_a(possible_error, "Error in variable definition!")] >> nothing_p)
                 );
            variable_definition //@TODO add upper and lower bounds; units; INITIAL values for integrated variables
                = ( eps_p                                [&start_variable] >> //clear temporary storage
                    (name - param_name - var_name)       [var_name.add]       //store in symbol table + check if name is already taken
                                                         [assign_a(v_temp.name)] >>
                    !("AS" >> str_p("ANY")               [assign_a(v_temp.type)]) >>
                    !("INITIAL" >> rough_math_expression [assign_a(v_temp.initial_expr)]) >> //store initial value
                    +(ch_p('\n') | ';')
                  )                                      [&add_variable]; //add variable definition to model

//             //parse the SET section where values are assigned to the parameters: SET p1=2.5; p2:=3.1;
//             set_section
//                 = str_p("SET") >>
//                 *(    parameter_assignment
//                     | (eps_p[assign_a(possible_error, "Error in SET section!")] >> nothing_p)
//                  );
//             parameter_assignment
//                 = name >> ":=" >> rough_math_expression >> +(ch_p('\n') | ';');

            //Parse the EQUATION section: EQUATION v1 := 2*v2 + v3; $v2 := v2/v1;
            equation_section
                = str_p("EQUATION") >>
                *(    assignment_variable
                    | assignment_time_derivative
                    //TODO | equation
                    | (eps_p[assign_a(possible_error, "Error in EQUATION section!")] >> nothing_p)
                 );
            assignment_variable
                = ( eps_p                           [&start_equation] >>
                    (var_name >> eps_p)             [assign_a(e_temp.lhs)] >>
                    ":=" >> rough_math_expression   [assign_a(e_temp.rhs)] >>
                    +(ch_p('\n') | ';')
                  )                                 [&add_algebraic_assignment];
            assignment_time_derivative
                = ( eps_p                           [&start_equation] >>
                    '$' >> (var_name >> eps_p)      [assign_a(e_temp.lhs)] [&set_variable_integrated]>>
                    ":=" >> rough_math_expression   [assign_a(e_temp.rhs)] >>
                    +(ch_p('\n') | ';')
                  )                                 [&add_assignment_time_derivative];
//             equation
//                 = rough_math_expression >> "=" >> rough_math_expression;

//             time_derivative
//                 = '$' >> (var_name >> eps_p)        [&set_variable_integrated];

            //very bad parser for mathematical expressions
            rough_math_expression
                    = +(longest_d[var_name | param_name] | real_p | '+' | '-' | '*' | '/' | '(' | ')');
        }

        //!The start rule of the model grammar.
        spirit::rule<ScannerT> const &
        start() const { return model_definition; }

        private:
//         std::vector<std::string> parameter_name;
//         std::vector<std::string> variable_name;

        //!Rules that are defined here
        spirit::rule<ScannerT>
            model_definition, parameter_section, parameter_definition,
            variable_section, variable_definition,
            set_section, parameter_assignment,
            equation_section, assignment_variable, assignment_time_derivative,
            /*time_derivative,*/ rough_math_expression;
        //!Grammar that describes all names (model, parameter, variable)
        name_grammar name;
        //!symbol table for the known parmeter names.
        spirit::symbols<> param_name;
        //!symbol table for the known variable names.
        spirit::symbols<> var_name;
    };
};

} // namespace siml

#endif // SIML_MODEL_GRAMMAR_HPP
