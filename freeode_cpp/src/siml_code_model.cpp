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


#include "siml_code_model.h"
#include "siml_cmerror.h"

#include <iostream>
#include <boost/format.hpp>


using std::cout;
using std::endl;
using std::string;
using boost::shared_ptr;
using boost::format;


/*!
@return True if the lhs is the time differential of a variable: $v1 := a*b*v1 + v2; otherwise false
*/
bool siml::CmEquationDescriptor::isOdeAssignment() const
{
    return lhs.timeDerivative();
}


/*!Add the descriptor if it has a unique name.

@return true if no error happened, false otherwise.
*/
void siml::CmModelDescriptor::addParameter(CmMemoryDescriptor inPar)
{
    //check if name is unique
    if( isIdentifierExisting(inPar.name) )
    {
        string msg =
                (format("The name '%1%' does already exist! \n"
                        "The names of sub-models, variables and parameters must be unique "
                        "within a model.") % inPar.name
                ).str();
        CmError::addError( msg, inPar.defBegin);
        errorsDetected = true;
        return /*false*/;
    }

    //add the parameter
    parameter.push_back(inPar);
    //return no error
    return /*true*/;
}


/*!
Add the descriptor and see if name is unique.

@return true if no error happened, false otherwise.
*/
void siml::CmModelDescriptor::addSubModel(CmSubModelLink inSub)
{
    // check if type exists
    CmModelDescriptor const * theType = repository()->findModel( inSub.type);
    if( theType == 0 )
    {
        string msg = ( format( "The model '%1%' does not exist!") % inSub.type ).str();
        CmError::addError( msg, inSub.defBegin);
        errorsDetected = true;
        return/* false*/;
    }

    //check if name is unique
    if( isIdentifierExisting(inSub.name) )
    {
        string msg = ( format(  "The name '%1%' does already exist! \n"
                                "The names of sub-models, variables and parameters must be unique "
                                "within a model.") % inSub.name ).str();
        CmError::addError( msg, inSub.defBegin);
        errorsDetected = true;
        return;
    }

    //add the parameter
    subModel.push_back(inSub);
    //return no error
    return/* true*/;
}


/*!Add the descriptor and see if name is unique.

@return true if no error happened, false otherwise.
*/
void siml::CmModelDescriptor::addVariable(CmMemoryDescriptor inVar)
{
    //check if name is unique
    if( isIdentifierExisting(inVar.name) )
    {
        string msg =
                (format("The name '%1%' does already exist! \n"
                "The names of sub-models, variables and parameters must be unique "
                "within a model.") % inVar.name
                ).str();
        CmError::addError( msg, inVar.defBegin);
        errorsDetected = true;
        return /*false*/;
    }

     //add the variable
    variable.push_back(inVar);
    //return no error
    return /*true*/;
}


/*!Add an expression to set a value to a parameter.
Also sets the right options.
*/
void siml::CmModelDescriptor::addParameterAssignment( CmEquationDescriptor inEqu)
{
    //set the right options
//     inEqu.is_assignment = true;
//     inEqu.is_ode_assignment = false;
    //add to model
    parameterAssignment.push_back( inEqu);
}


/*!Add an equation. Options must be set before calling this function!*/
void siml::CmModelDescriptor::addEquation( CmEquationDescriptor inEqu)
{
    //add to model
    equation.push_back( inEqu);
}


/*!Add an equation to set the initial value to a parameter.*/
void siml::CmModelDescriptor::addInitialEquation( CmEquationDescriptor inEqu)
{
    initialEquation.push_back( inEqu);
}


/*!
Set flag so variable is treated as an integrated variable

@return true if no error happened, false otherwise.
*/
// void siml::CmModelDescriptor::setVariableIntegrated(CmPath const & stateVarName)
// {
//     CmMemoryTable::iterator itV = findVariable( stateVarName);
//
//     //variable does not exist: generate error
//     if( itV != variable.end() )
//     {
//         itV->is_state_variable = true;
//     }
//     else
//     {
//         string msg = ( format( "Compiler internal Error! No variable with name %1% exists! "
//                                "You use the symbol %1% as a state variable.") % stateVarName ).str();
//         CmError::addError( msg, (char const *)0);
//         errorsDetected = true;
//     }
// }


/*!
Look through the list of equations.
Find all time derivatives (uses of '$'), mark the variables in the list of variables.

Currently time derivatives can only occour on the lhs.

@todo move to special class for code generation
 */
void siml::CmModelDescriptor::markStateVariables()
{
    //loop over all equations
    CmEquationTable::const_iterator itE;
    for( itE = equation.begin(); itE != equation.end(); ++itE )
    {
        CmEquationDescriptor const & equn = *itE;
        //See if lhs is time derivative (no time derivatives are legal on rhs)
        if( !equn.lhs.timeDerivative() ) { continue; }

        //try to find the variable's definition
        CmMemoryTable::iterator itVar = findVariable( equn.lhs.path());
        if( itVar != variable.end() )
        {   //mark variable as state variable
            itVar->is_state_variable = true;
        }
        else
        {   //error
            string msg = ( format(  "No variable with name '%1%' exists! "
                                    "You use the symbol '%1%' as a state variable.")
                                    % equn.lhs.path().toString() ).str();
            CmError::addError( msg, equn.defBegin);
            errorsDetected = true;
        }
    }
}


/*!Find parmeter by name, return the definition.
@return Iteratetor that points to the parameter's CmMemoryDescriptor if the parameter exists, or parameter.end() otherwise
*/
siml::CmMemoryTable::const_iterator siml::CmModelDescriptor::findParameter( CmPath const & name) const
{
    ///@note An 'iterator' can be converted to a 'const_iterator', but not viceversa.
    CmModelDescriptor * self = const_cast<CmModelDescriptor *>(this);
    return self->findParameter( name);
}
/*!Find parmeter by name, return the definition.
@return Iteratetor that points to the parameter's CmMemoryDescriptor if the parameter exists, or parameter.end() otherwise
*/
siml::CmMemoryTable::iterator siml::CmModelDescriptor::findParameter( CmPath const & name)
{
    //loop over all parameters and compare the names
    CmMemoryTable::iterator itM;
    for( itM = parameter.begin(); itM != parameter.end(); ++itM )
    {
        if( itM->name == name ) { return itM; }
    }
    //no parameter with that name exists.
    return parameter.end();
}


/*!Find submodel by name, return the definition.
@return Iteratetor that points to the parameter's CmMemoryDescriptor if the parameter exists, or subModel.end() otherwise
 */
siml::CmSubModelTable::const_iterator siml::CmModelDescriptor::findSubModel(CmPath const & name) const
{
    ///@note An 'iterator' can be converted to a 'const_iterator', but not viceversa.
    CmModelDescriptor * self = const_cast<CmModelDescriptor *>(this);
    return self->findSubModel( name);
}
/*!Find submodel by name, return the definition.
@return Iteratetor that points to the parameter's CmMemoryDescriptor if the parameter exists, or subModel.end() otherwise
 */
siml::CmSubModelTable::iterator siml::CmModelDescriptor::findSubModel(CmPath const & name)
{
    //loop over all parameters and compare the names
    CmSubModelTable::iterator itS;
    for( itS = subModel.begin(); itS != subModel.end(); ++itS )
    {
        if( itS->name == name ) { return itS; }
    }
    //no parameter with that name exists.
    return subModel.end();
}


/*!Find variable by name, return the definition.
@return Iteratetor that points to the parameter's CmMemoryDescriptor if the parameter exists, or variable.end() otherwise
 */
siml::CmMemoryTable::const_iterator siml::CmModelDescriptor::findVariable(CmPath const & name) const
{
    ///@note An 'iterator' can be converted to a 'const_iterator', but not viceversa.
    CmModelDescriptor * self = const_cast<CmModelDescriptor *>(this);
    return self->findVariable( name);
}
/*!Find variable by name, return the definition.
@return Iteratetor that points to the parameter's CmMemoryDescriptor if the parameter exists, or variable.end() otherwise
 */
siml::CmMemoryTable::iterator siml::CmModelDescriptor::findVariable(CmPath const & name)
{
    //loop over all parameters and compare the names
    CmMemoryTable::iterator itM;
    for( itM = variable.begin(); itM != variable.end(); ++itM )
    {
        if( itM->name == name ) { return itM; }
    }
    //no parameter with that name exists.
    return variable.end();
}


/*!
Loop over all sub model, all parameters, and all variables, and see if the name
already exists.

@param name the name that is checked for uniqueness.

@return false if the name already exists, otherwise return true.
*/
bool
siml::CmModelDescriptor::isIdentifierExisting(CmPath const & name) const
{
    if( findParameter( name ) != parameter.end() ) { return true; }
    if( findSubModel( name )  != subModel.end() )  { return true; }
    if( findVariable( name )  != variable.end() )  { return true; }

    //OK the name is unique
    return false;
}


/*!Iterate through all lists and display their contents.*/
void
siml::CmModelDescriptor::display() const
{
    if( isProcess ) { cout << "PROCESS -------------" << endl; }
    else            { cout << "MODEL -------------" << endl; }

    cout << "name: " << name << endl;

    CmMemoryTable::const_iterator itM;

    cout << "parameters:" << endl;
    for( itM = parameter.begin(); itM != parameter.end(); ++ itM) {
        CmMemoryDescriptor const & par = *itM; //Kdevelop's completion is bad
        cout << "|  " << par.name << ", " << par.type << "\n";
    }

    cout << "sub models:" << endl;
    for(uint i=0; i<subModel.size(); ++i) {
        cout << "|  " << subModel[i].name << ", " << subModel[i].type << endl;
    }

    cout << "variables:" << endl;
    for( itM = variable.begin(); itM != variable.end(); ++ itM) {
        CmMemoryDescriptor const & var = *itM; //Kdevelop's completion is bad
        cout << "|  " << var.name << ", " << var.type << endl;
    }

    cout << "parameter assignments:" << endl;
    for(uint i=0; i<parameterAssignment.size(); ++i) {
//         cout << equation[i].definition_text << endl;
        cout << "|  "    << parameterAssignment[i].lhs;
        cout << "  :=  " << parameterAssignment[i].rhs << endl;
    }

    cout << "initial equations:" << endl;
    for(uint i=0; i<initialEquation.size(); ++i) {
        cout << "|  "    << initialEquation[i].lhs;
        cout << "  :=  " << initialEquation[i].rhs << endl;
    }

    cout << "equations:" << endl;
//     uint es=equation.size();
    for(uint i=0; i<equation.size(); ++i) {
//         cout << equation[i].definition_text << endl;
        cout << "|  "    << equation[i].lhs;
        cout << "  :=  " << equation[i].rhs;
        if( equation[i].isOdeAssignment() ) { cout << "  - ODE" << endl; }
        else                                { cout << "  - algebraic" << endl; }
    }

    if( errorsDetected ) { cout << "Errors detected!" << endl; }
    else                 { cout << "No Errors." << endl; }
}


/*!Static pointer to the one and only code model*/
siml::CmCodeRepository * siml::CmCodeRepository::repository = new CmCodeRepository();


/*!Iterate through all lists and display their contents.*/
void
siml::CmCodeRepository::display() const
{
    cout << "models ----------------------------------" << endl;
    for( uint i=0; i < model.size(); ++i )
    {
        model[i].display();
        cout<<endl;
    }

    cout << "processes ----------------------------------" << endl;
    for( uint i=0; i < process.size(); ++i )
    {
        process[i].display();
        cout<<endl;
    }
    cout << "------------------------------------" << endl;
}

/*!
Search for a model declaration with this name in the repository.

@param name Name of the model declaration.
@return     Pointer to the declaration or 0 if no declaration with this name exists.
 */
siml::CmModelDescriptor *
siml::CmCodeRepository::findModel(std::string const & name)
{
    //copy parameter assignments
    CmModelTable::iterator itM;
    for(    itM = model.begin();
            itM != model.end();
            ++itM )
    {
        if( itM->name == name ) { return &(*itM); }
    }

    return 0;
}

/*!
Search for a model declaration with this name in the repository.
Version where the object can be manipulated

@param name Name of the model declaration.
@return     Pointer to the declaration or 0 if no declaration with this name exists.
 */
// siml::CmModelDescriptor const *
//         siml::CmCodeRepository::findModel(std::string const & name) const
// {
//     CmModelDescriptor const * mc = findModel(name);
//     return mc;
// }
