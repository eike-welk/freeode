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

#ifndef SIML_PS_PROCESS_H
#define SIML_PS_PROCESS_H

#include "siml_code_model.h"
#include "siml_ps_name.h"
#include "siml_error_generator.h"

#include <boost/spirit/core.hpp>
#include <boost/spirit/symbols/symbols.hpp>
// #include <boost/shared_ptr.hpp>

#include <string>
// #include <vector>
#include <iostream>

//!Intermediate storage for data aquired while parsing a model.
/*!Created a new namespace to avoid name clashes since these are all global symbols.
The namespace is named for easier access in KDevelop. */
namespace temp_store_process {
using namespace siml;
using namespace std;
// using boost::shared_ptr;

//!The data gathered while parsing the process is stored here
CmProcessDescriptor process;

//!error that is maybe detected.
CmErrorDescriptor err_temp;

//!Clear the whole temorary process
void start_process(char const *, char const *)
{
    process = CmProcessDescriptor();
    err_temp = CmErrorDescriptor();
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
    ///@todo check if name is unique
    process.parameter.push_back(p_temp);
}

//unit (sub-model)----------------------------------------------------------
//!temporary storage while a unit definition is parsed
CmSubModelDescriptor submod_temp;
//!Clear the temporary storage for parsing parameters
void start_sub_model(char const *, char const *) { submod_temp = CmSubModelDescriptor(); }
//!Add a parameter definition to the model.
void add_sub_model(char const * first, char const * const last)
{
    string definition_text(first, last);
    ///@todo check if name is unique, if model type exists
    process.subModel.push_back(submod_temp);
}

//parameter assignment (SET)----------------------------------------------------------------
//!temporary storage while a variable definition is parsed
CmEquationDescriptor param_assign_temp;
//!Clear the temporary storage for the CmEquationDescriptor objects
void start_param_assign(char const *, char const *) { param_assign_temp = CmEquationDescriptor(); }
//!Add an assignment to a algebraic variable to the model. (a:=p2*c)
void add_param_assign(char const * first, char const * const last)
{
    param_assign_temp.definition_text = string(first, last);
    param_assign_temp.is_assignment = true;
    param_assign_temp.is_ode_assignment = false;
    process.parameterAssignment.push_back(param_assign_temp);
}

//initial value assignment (INITIAL)----------------------------------------------------------------
//!temporary storage while a variable definition is parsed
CmEquationDescriptor init_expr_temp;
//!Clear the temporary storage for the CmEquationDescriptor objects
void start_init_expr(char const *, char const *) { init_expr_temp = CmEquationDescriptor(); }
//!Add an assignment to a algebraic variable to the model. (a:=p2*c)
void add_init_expr(char const * first, char const * const last)
{
    init_expr_temp.definition_text = string(first, last);
    init_expr_temp.is_assignment = true;
    init_expr_temp.is_ode_assignment = false;
    process.initialExpression.push_back(init_expr_temp);
}

//SOLUTIONPARAMETERS----------------------------------------------------------------
//!temporary storage while a variable definition is parsed
CmSolutionParameterDescriptor sol_parms_temp;
//!Clear the temporary storage for the CmEquationDescriptor objects
void start_sol_parms(char const *, char const *) { sol_parms_temp = CmSolutionParameterDescriptor(); }
//!Add an assignment to a algebraic variable to the model. (a:=p2*c)
void add_sol_parms(char const * /*first*/, char const * const /*last*/)
{
    process.solutionParameters = sol_parms_temp;
}

//equation----------------------------------------------------------------
//!temporary storage while a variable definition is parsed
// CmEquationDescriptor e_temp;
//!Clear the temporary storage for the CmEquationDescriptor objects
// void start_equation(char const *, char const *) { e_temp = CmEquationDescriptor(); }
//!Add an assignment to a algebraic variable to the model. (a:=p2*c)
// void add_algebraic_assignment(char const * first, char const * const last)
// {
//     e_temp.definition_text = string(first, last);
//     e_temp.is_assignment = true;
//     e_temp.is_ode_assignment = false; //this is algebraic
//     model.equation.push_back(e_temp);
// }
//!Add an assignment to the derivative of an integrated variable to the model. ($c:=p1*c)
// void add_assignment_time_derivative(char const * first, char const * const last)
// {
//     e_temp.definition_text = string(first, last);
//     e_temp.is_assignment = true;
//     e_temp.is_ode_assignment = true; //this is an ODE
//     model.equation.push_back(e_temp);
// }

//!pointer to the central storage of parse results
CmCodeRepository* parse_result_storage;

//!return the correctly parsed model.
void return_process(char const * /*first*/, char const * const /*last*/)
{
    cout << "Parsing process " << process.name << " finished correctly." << endl;
    parse_result_storage->process.push_back(process);
}

//!return the error (the partial process is returned too).
void return_error(char const * /*first*/, char const * const /*last*/)
{
    cout << "Parsing process " << process.name << " failled!" << endl;

    process.errorsDetected = true;

    parse_result_storage->error.push_back(err_temp);
    parse_result_storage->process.push_back(process);
}

} //namespace temp_store_process



namespace siml {

    namespace spirit = boost::spirit;


    /*!
    @short Parser for "PROCESS".

    @todo combine model and process parser into one universal model parser.

    The parser uses global variables to store temporary
    information, during a parsing run.

    The temporary varibles and the semantic actions reside in the namespace
    "temp_store_process".
    */
    struct ps_process : public spirit::grammar<ps_process>
    {
        //!Construct the grammar and give it a refference to the code model
        /*!Before using the grammar it must have a pointer to the global result storage.
        Therefore the function set_result_storage (...) must be called. (once for all
        ps_process instances)*/
        ps_process() {}

        //!Give the grammar a pointer to the global storage for parse results.
        static void set_result_storage(CmCodeRepository* result_storage)
        {
            temp_store_process::parse_result_storage = result_storage;
        }

        //!When the grammar is used the framework creates this struct. All rules are defined here.
        template <typename ScannerT> struct definition
        {
            //!The grammar's rules.
            definition(ps_process const& self)
            {
                using namespace temp_store_process;
                using spirit::str_p; using spirit::ch_p;
                using spirit::eps_p; using spirit::nothing_p; using spirit::anychar_p;
                using spirit::assign_a;

                //The start rule. Parses the complete process: PROCESS ... END
                process_definition
                    = str_p("PROCESS")            [&start_process] >> //clear all temporary storage
                      ( (   name                  [assign_a(process.name)] >>
                            !parameter_section >> !unit_section >> !set_section >>
                            !initial_section >> !solutionparameters_section >>
                            str_p("END")          [&return_process]
                        )
                      | ( eps_p                   [&return_error] >>
                          nothing_p
                        )
                      );

                //parse block of parameter definitions: PARAMETER p1 AS REAL; p2 AS REAL; ...
                parameter_section
                    =   str_p("PARAMETER") >>
                        *(    parameter_definition
                            | (eps_p[make_error("Error in PARAMETER definition!", err_temp)] >> nothing_p)
                         );
                parameter_definition ///@TODO units
                    = ( eps_p                                [&start_parameter] >> //clear temporary storage
                        (name /*- param_name*/)                  /*[param_name.add]*/ //store in symbol table + check if name is already taken
                                                             [assign_a(p_temp.name)] >>  //store name in temporary storage
                        !("AS" >> str_p("REAL")              [assign_a(p_temp.type)]) >> //store parameter type
                        !("DEFAULT" >> rough_math_expression [assign_a(p_temp.default_expr)]) >> //store default value
                        +(ch_p('\n') | ';')
                      )                                      [&add_parameter]; //add parameter definition to model

                //parse block of sub-model definitions: UNIT u1 AS Model1; ...
                unit_section
                    =   str_p("UNIT") >>
                        *(    unit_definition
                            | (eps_p[make_error("Error in UNIT (sub-model) definition!", err_temp)] >> nothing_p)
                         );
                unit_definition
                    = ( eps_p                                [&start_sub_model] >> //clear temporary storage
                        name                                 [assign_a(submod_temp.name)] >>  //store name in temporary storage
                        !("AS" >> name                       [assign_a(submod_temp.type)]) >> //store sub model type
                        +(ch_p('\n') | ';')
                      )                                      [&add_sub_model]; //add sub-model definition to model

                //parse the SET section where values are assigned to the parameters: SET p1=2.5; p2:=3.1;
                set_section
                    = str_p("SET") >>
                    *(    parameter_assignment
                        | (eps_p[make_error("Error in SET section!", err_temp)] >> nothing_p)
                     );
                parameter_assignment
                    = ( name                                [&start_param_assign]
                                                            [assign_a(param_assign_temp.lhs)] >>
                        ":=" >> rough_math_expression       [assign_a(param_assign_temp.rhs)] >>
                        +(ch_p('\n') | ';')
                      )                                     [&add_param_assign];

                //parse the INITIAL section where start values are assigned to the integrated variables: INITAIL v1=2.5; v2:=3.1;
                initial_section
                    = str_p("INITIAL") >>
                      *(    initial_assignment
                        |   (eps_p[make_error("Error in INITIAL section!", err_temp)] >> nothing_p)
                       );
                initial_assignment
                    = ( name                                [&start_init_expr]
                                                            [assign_a(init_expr_temp.lhs)] >>
                        ":=" >> rough_math_expression       [assign_a(init_expr_temp.rhs)] >>
                        +(ch_p('\n') | ';')
                      )                                     [&add_init_expr];

                //parse the SOLUTIONPARAMETERS section
                solutionparameters_section
                    = str_p("SOLUTIONPARAMETERS")           [&start_sol_parms] >>
                      *(    solutionparameters_assignment   [&add_sol_parms]
                        |   (eps_p[make_error("Error in SOLUTIONPARAMETERS section!", err_temp)] >> nothing_p)
                       );
                solutionparameters_assignment
                    = ( str_p("ReportingInterval") >> ":=" >>
                        (real_p >> eps_p)                   [assign_a(sol_parms_temp.reportingInterval)] >>
                        +ch_p(';')
                      )
                    | ( str_p("SimulationTime") >> ":=" >>
                        (real_p  >> eps_p)                  [assign_a(sol_parms_temp.simulationTime)] >>
                        +ch_p(';')
                      );

                //very bad parser for mathematical expressions
                rough_math_expression
                        = +(name | real_p | '+' | '-' | '*' | '/' | '(' | ')');
            }

            //!The start rule of the model grammar.
            spirit::rule<ScannerT> const &
            start() const { return process_definition; }

            private:
            //!Rules that are defined here
            spirit::rule<ScannerT>
            process_definition,
            parameter_section, parameter_definition,
            unit_section, unit_definition,
            set_section, parameter_assignment,
//             equation_section, assignment_variable, assignment_time_derivative,
            initial_section, initial_assignment,
            solutionparameters_section, solutionparameters_assignment,
            rough_math_expression;
            //!Grammar that describes all names (model, parameter, variable)
            ps_name name;
            //!symbol table for the known parmeter names.
//             spirit::symbols<> param_name;
            //!symbol table for the known variable names.
//             spirit::symbols<> var_name;
        };
    };

} // namespace siml

#endif // SIML_PS_PROCESS_H
