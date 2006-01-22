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

#include <iostream>
#include <boost/format.hpp>

using std::cout;
using std::endl;
using std::string;
using boost::shared_ptr;
using boost::format;


/*!Add the descriptor if it has a unique name.

@return pointer to error if an error happened, or null pointer otherwise.
*/
shared_ptr<siml::CmErrorDescriptor>
siml::CmModelDescriptor::addParameter(CmMemoryDescriptor inPar)
{
    //check if name is unique
    if( !isIdentifierUnique(inPar.name) )
    {
        string msg =
                (format("The name %1% does already exist! \n"
                        "The names of sub-models, variables and parameters must be unique "
                        "within a model.") % inPar.name
                ).str();
        shared_ptr<CmErrorDescriptor> err(new CmErrorDescriptor(msg));
        return err;
    }

    //add the parameter
    parameter.push_back(inPar);
    //return no error
    return shared_ptr<CmErrorDescriptor> ();
}


/*!
Add the descriptor and see if name is unique.

@return pointer to error if an error happened, or null pointer otherwise.
*/
boost::shared_ptr<siml::CmErrorDescriptor>
siml::CmModelDescriptor::addSubModel(CmSubModelLink inSub)
{
    ///@todo check if type exists

    //check if name is unique
    if( !isIdentifierUnique(inSub.name) )
    {
        string msg =
                (format("The name %1% does already exist! \n"
                "The names of sub-models, variables and parameters must be unique "
                "within a model.") % inSub.name
                ).str();
        shared_ptr<CmErrorDescriptor> err(new CmErrorDescriptor(msg));
        return err;
    }

    //add the parameter
    subModel.push_back(inSub);
    //return no error
    return shared_ptr<CmErrorDescriptor> ();
}


/*!Add the descriptor and see if name is unique.

@return pointer to error if an error happened, or null pointer otherwise.
*/
shared_ptr<siml::CmErrorDescriptor>
siml::CmModelDescriptor::addVariable(CmMemoryDescriptor inVar)
{
    //check if name is unique
    if( !isIdentifierUnique(inVar.name) )
    {
        string msg =
                (format("The name %1% does already exist! \n"
                "The names of sub-models, variables and parameters must be unique "
                "within a model.") % inVar.name
                ).str();
        shared_ptr<CmErrorDescriptor> err(new CmErrorDescriptor(msg));
        return err;
    }

     //add the variable
    variable.push_back(inVar);
    //return no error
    return shared_ptr<CmErrorDescriptor> ();
}

/*!

@return pointer to error if an error happened, or null pointer otherwise.
*/
boost::shared_ptr<siml::CmErrorDescriptor>
siml::CmModelDescriptor::setVariableIntegrated(std::string stateVarName)
{
    //loop over all variables to find the variable that will be marked
    CmMemoryTable::iterator it;
    for( it = variable.begin(); it != variable.end(); ++it )
    {
        CmMemoryDescriptor& varD = *it;
        if( varD.name == stateVarName )
        {
            varD.is_state_variable = true;
            break;
        }
    }
    //variable does not exist: generate error
    if( it == variable.end())
    {
        string msg =
                (format("No variable with name %1% exists! "
                        "You used the symbol %1% as a state variable.") % stateVarName
                ).str();
        shared_ptr<CmErrorDescriptor> err(new CmErrorDescriptor(msg));
        return err;
    }

    //return no error
    return shared_ptr<CmErrorDescriptor> ();
}


/*!
Loop over all sub model, all parameters, and all variables, and see if the name
already exists.

If the name already exists return false, otherwise return true.

@param name the name that is checked for uniqueness.
*/
bool
siml::CmModelDescriptor::isIdentifierUnique(CmPath const & name) const
{
    //loop over all unit names
    CmSubModelTable::const_iterator itSub;
    for( itSub = subModel.begin(); itSub != subModel.end(); ++itSub )
    {
        CmSubModelLink const& subD = *itSub;
        if( subD.name == name )
        {
            return false;
        }
    }

    //loop over all parameters to see if the name already exists
    CmMemoryTable::const_iterator itM;
    for( itM = parameter.begin(); itM != parameter.end(); ++itM )
    {
        CmMemoryDescriptor const& memD = *itM;
        if( memD.name == name )
        {
            return false;
        }
    }

    //loop over all variables to see if the name already exists
    for( itM = variable.begin(); itM != variable.end(); ++itM )
    {
        CmMemoryDescriptor const& varD = *itM;
        if( varD.name == name )
        {
            return false;
        }
    }

    //OK the name is unique
    return true;
}


/*!
The name of the descriptor for a variable or a parameter is checked for uniqueness.
If the name already exists return false, otherwise return true.

@param varOrPar the descriptor that is checked for uniqueness of the name.
 */
// bool
// siml::CmModelDescriptor::isIdentifierUnique(CmMemoryDescriptor const & varOrPar) const
// {
//     return isIdentifierUnique( varOrPar.name );
// }


/*!Iterate through all lists and display their contents.*/
void
siml::CmModelDescriptor::display() const
{
    if( isProcess ) { cout << "PROCESS -------------" << endl; }
    else            { cout << "MODEL -------------" << endl; }

    cout << "name: " << name << endl;

    cout << "parameters:" << endl;
    for(uint i=0; i<parameter.size(); ++i) {
        cout << "|  " << parameter[i].name << ", " << parameter[i].type << ", " << parameter[i].default_expr << endl;
    }

    cout << "sub models:" << endl;
    for(uint i=0; i<subModel.size(); ++i) {
        cout << "|  " << subModel[i].name << ", " << subModel[i].type << endl;
    }

    cout << "variables:" << endl;
    for(uint i=0; i<variable.size(); ++i) {
        cout << "|  " << variable[i].name << ", " << variable[i].type << endl;
    }

    cout << "parameter assignments:" << endl;
    for(uint i=0; i<parameterAssignment.size(); ++i) {
//         cout << equation[i].definition_text << endl;
        cout << "|  "    << parameterAssignment[i].lhs;
        cout << "  :=  " << parameterAssignment[i].rhs << endl;
    }

    cout << "initial expressions:" << endl;
    for(uint i=0; i<initialExpression.size(); ++i) {
        cout << "|  "    << initialExpression[i].lhs;
        cout << "  :=  " << initialExpression[i].rhs << endl;
    }

    cout << "equations:" << endl;
//     uint es=equation.size();
    for(uint i=0; i<equation.size(); ++i) {
//         cout << equation[i].definition_text << endl;
        cout << "|  "    << equation[i].lhs;
        cout << "  :=  " << equation[i].rhs;
        if( equation[i].is_ode_assignment ) { cout << "  - ODE" << endl; }
        else                                { cout << "  - algebraic" << endl; }
    }

    if( errorsDetected ) { cout << "Errors detected!" << endl; }
    else                 { cout << "No Errors." << endl; }
}


// /*!Iterate through all lists and display their contents.*/
// void
// siml::CmProcessDescriptor::display() const
// {
//     cout << "process ";
//     CmModelDescriptor::display();
//
// }


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

    cout << "errors -----------------------------" << endl;
    for( uint i=0; i < error.size(); ++i )
    {
        cout << error[i].error_message << endl;
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
