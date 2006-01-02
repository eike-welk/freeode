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

#ifndef SIML_CODE_MODEL_HPP
#define SIML_CODE_MODEL_HPP

#include <string>
#include <vector>

namespace siml {

/*!
@short Descripion of an error.

This object contains data about an error. It is used to generate nicely
formated error message.
*/
struct CmErrorDescriptor
{
    //!Error message that was generated by the parser. (If any)
    std::string error_message;
    //!Start of the sequence that contains the error.
//     char const * where_first;
    //!End of the sequence that contains the error.
//     char const * where_last;

    CmErrorDescriptor() /*: where_first(0), where_last(0)*/ {};
};
//!container for Errors. See: @see CmErrorDescriptor
typedef std::vector<CmErrorDescriptor> CmErrorTable;


/*!
@short All data of a single parameter

This is the parsing result for one line of the PARAMETER section. The code
generator will later use this information.
@todo A pair of pointers: char const * where_first, where_last; instead of std::string definition_text would be a good idea, to aid the generation of code generator errors.
@todo merge CmParameterDescriptor and CmVariableDescriptor into CmValueStore.
*/
struct CmMemoryDescriptor
{
    //!parameter name
    std::string name;
    //!identifier name in generated program
    std::string name_program;
    //!REAL or INT
    std::string type;
    //!the default value, relevant if no value is set. (parameter)
    std::string default_expr;
    //!mathematical expression from the set section. (parameter)
    std::string set_expr;
    //!expression for assignment of an initial value. (variable)
    std::string initial_expr;
    //!text that was parsed to gather the information in this object.
    std::string definition_text;

    //!true if variable is an integrated variable
    bool is_state_variable;

    CmMemoryDescriptor() : type("ANY"), default_expr(""), is_state_variable(false) {};

};
//!container for the parameter descriptors of a model. See: @see CmParameterDescriptor
typedef std::vector<CmMemoryDescriptor> CmMemoryTable;


/*!
@short Descripion of one equation or assignment.
*/
struct CmEquationDescriptor
{
    //!the equation's left hand side
    std::string lhs;
    //!the equation's right hand side
    std::string rhs;
    //!if true the equation is really an assignment ":=" otherwise it's a true equation "="
    bool is_assignment;
    //!if true the lhs is the time differential of a variable: $v1 := a*b*v1 + v2;
    bool is_ode_assignment;
    //!text that was parsed to gather the information in this object.
    std::string definition_text;

    CmEquationDescriptor() : is_assignment(false), is_ode_assignment(false) {};
};
//!container for the equation descriptors of a model. See: @see CmEquationDescriptor
typedef std::vector<CmEquationDescriptor> CmEquationTable;


/*!
@short Descripion of sub-models

Represents one line of the "UNIT" section
*/
struct CmSubModelDescriptor
{
    //!The sub-model's name in the parent model.
    std::string name;
    //!The sub-model's type.
    std::string type;
};
//!container for model references.
typedef std::vector<CmSubModelDescriptor> CmSubModelTable;


/*!
@short Storage for "SOLUTIONPARAMETERS"
*/
struct CmSolutionParameterDescriptor
{
    std::string reportingInterval;
    std::string simulationTime;
};


/*!
@short Descripion of a "MODEL"
This is the parsing result of a model: "MODEL ... END"
*/
struct CmModelDescriptor
{
    //!The model's name
    std::string name;

    //!Container for parameters. ("PARAMETER") See: @see CmParameterDescriptor
    CmMemoryTable parameter;
    //!Container for the sub models ("UNIT") @see CmSubModelDescriptor
    CmSubModelTable subModel;
    //!Container for variables. See: @see CmVariableDescriptor
    CmMemoryTable variable;
    //!Container for parameter initializations. ("SET section") See: @see CmEquationDescriptor
    CmEquationTable parameterAssignment;
    //!Container for the eqations. See: @see CmEquationDescriptor
    CmEquationTable equation;
    //!Container for initializations of integrated variables. ("INITIAL" section) See: @see CmEquationDescriptor
    CmEquationTable initialExpression;
    //!Some simulation options
    CmSolutionParameterDescriptor solutionParameters;

    //!If true: the model is really a "PROCESS"; else: it is a "MODEL"
    bool isProcess;
    //!There are errors
    bool errorsDetected;

    //!Constructor
    CmModelDescriptor(): isProcess(false), errorsDetected(false) {};
    //!Display the model's contents (for debuging)
    void display() const;
};
struct CmModelDescriptor;
//!container for models.
typedef std::vector<CmModelDescriptor> CmModelTable;


/*!
@short Binary representation of the input files.

The parser stores all results here, and intermediate results (what symbols do
currently exist) are taken from here.

The code generator gets this object and it generates a computer program from it.
Additonally errors and warnings from the parser and the code generator are
collected here too.
*/
struct CmCodeRepository
{
    //!List of models
    CmModelTable model;
    //!List of processes
    CmModelTable process;
    //!list of recognized errors
    CmErrorTable error;

    //!Display the repositorie's contents (for debuging)
    void display() const;
};

} //namespace siml

#endif // SIML_CODE_MODEL_HPP
