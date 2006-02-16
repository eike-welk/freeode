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


#include "siml_cmmodelintermediate.h"
#include "siml_cmerror.h"
// #include "siml_cmpath.h"

#include <boost/format.hpp>

#include <set>
#include <map>
// #include <vector>
#include <list>
#include <sstream>


// using namespace siml;
using boost::shared_ptr;
using boost::format;
using std::string;
using std::set;
using std::map;
// using std::vector;
using std::list;
using std::ostringstream;


/*!
Transform a model with sub-models into an equivalent model without sub-models.

This can also be seen as allocating memory for the (sub-)models.

All parameters, variables and equations of the submodels are recursively
copied into *this, the flat model. Parmeters and variables get unique long names,
by prefixing their names with the sub-model's name.

This is the first step in generating code for a procedure.

@param  compositeProcess the model that will be converted.
 */
void
siml::CmModelIntermediate::createFlatModel( CmModelDescriptor const & compositeProcess )
{
    //copy the features that are not copied recursively
    name                = compositeProcess.name;
    isProcess           = compositeProcess.isProcess;
    initialEquation     = compositeProcess.initialEquation;
    solutionParameters  = compositeProcess.solutionParameters;
    defBegin            = compositeProcess.defBegin;

    //copy the recursive features
    int recursionLevel = 0;
    CmPath variablePrefix;
    flattenModelRecursive( compositeProcess, variablePrefix, recursionLevel);
}


/*!
Copy parameters, variables and equations for createFlatModel(...).
The objects are recursively copied into *this. All identifiers get a prefix
(the sub-model's name) to stay unique.

@internal
@param  inCompositeModel the model that will be converted.
@param  inPathPrefix this is put in front of all variable and parameter names.
@param  inRecursionLevel depth of recursion to avoid enless loops
@internal
*/
void
siml::CmModelIntermediate::flattenModelRecursive(
                                    CmModelDescriptor const & inCompositeModel,
                                    siml::CmPath const inPathPrefix,
                                    uint const inRecursionLevel )
{
    //protect against circular dependencies ------------------------------
    uint const recursionLevelMax =10;
    if( inRecursionLevel > 10 )
    {
        string msg = ( format(
                "The maximum recursion level (%1%) has been reached!\n"
                "Procedure: %2%; Submodel where the error happened: %3%.\n"
                "(Maybe there are circular dependencies.)"
                ) % recursionLevelMax % name % inCompositeModel.name ).str();
        CmError::addError( msg, (char const *)0); ///@todo add iterator
        errorsDetected = true;
        return;
    }

    //copy the recursive entities -------------------------------------
    //copy parameters
    CmMemoryTable::const_iterator itM;
    for(    itM = inCompositeModel.parameter.begin();
            itM != inCompositeModel.parameter.end();
            ++itM )
    {
        CmMemoryDescriptor mem = *itM;
        mem.name.prepend(inPathPrefix); //put prefix in front of parameter name
        addParameter(mem);// add to model
    }

    //copy variables
    for(    itM = inCompositeModel.variable.begin();
            itM != inCompositeModel.variable.end();
            ++itM )
    {
        CmMemoryDescriptor mem = *itM;
        mem.name.prepend(inPathPrefix); //put prefix in front of variable name
        addVariable(mem); // add to model
    }

    //copy parameter assignments (SET)
    CmEquationTable::const_iterator itE;
    for(    itE = inCompositeModel.parameterAssignment.begin();
            itE != inCompositeModel.parameterAssignment.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //go through the equation and add the prefix at all variable names
        equ.lhs.prependPath( inPathPrefix);
        equ.rhs.prependPaths( inPathPrefix);
        //add updated equation to the model
        addParameterAssignment(equ);
    }

    //copy equations
    for(    itE = inCompositeModel.equation.begin();
            itE != inCompositeModel.equation.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //go through the equation and add the prefix at all variable names
        equ.lhs.prependPath( inPathPrefix);
        equ.rhs.prependPaths( inPathPrefix);
        //add updated equation to the model
        addEquation(equ);
    }
    //special handling for the error flag - errors were maybe detected. don't stop, we want to find more
    if( inCompositeModel.errorsDetected )
    {
        errorsDetected = true;
    }

    //recursively call this function for each submodel----------------------------
    //increase recursion level
    uint newRecursionLevel = inRecursionLevel+1;

    CmSubModelTable::const_iterator itS;
    for(    itS = inCompositeModel.subModel.begin();
            itS != inCompositeModel.subModel.end();
            ++itS )
    {
        //Search model definition in repository.
        CmModelDescriptor * submodel = repository()->findModel(itS->type);
        //Error: Null pointer - model does not exist!
        if( !submodel )
        {
            string msg = ( format(
                    "The model %1% does not exist!" ) % itS->type ).str();
            CmError::addError( msg, itS->defBegin);
            errorsDetected = true;
            continue;
        }

        //add the submodel's name to the prefix.
        CmPath newPrefix = inPathPrefix;
        newPrefix.append(itS->name);
        //copy entities of submodel
        flattenModelRecursive( *submodel, newPrefix, newRecursionLevel);
    }
}


/*!
Look through the list of equations.
Find all time derivatives (uses of '$'), mark the variables in the list of variables.

Currently time derivatives can only appear on the LHS of an equation.
 */
void siml::CmModelIntermediate::markStateVariables()
{
    //loop over all equations
    CmEquationTable::const_iterator itE;
    for( itE = equation.begin(); itE != equation.end(); ++itE )
    {
        CmEquationDescriptor const & equn = *itE;
        //See if lhs is time derivative (no time derivatives are legal on rhs)
        if( !equn.lhs.isTimeDerivative() ) { continue; }

        //try to find the variable's definition
        CmMemoryTable::iterator itVar = findVariable( equn.lhs.path());
        if( itVar != variable.end() )
        {   //mark variable as state variable
            itVar->is_state_variable = true;
        }
        else
        {   //error
            string msg = ( format(
                    "Undefined Variable: %1%\nYou use the symbol %1% as a state variable."
                                 ) % equn.lhs.path()).str();
            CmError::addError( msg, equn.defBegin);
            errorsDetected = true;
        }
    }
}


/*!
The parameter propagation rules say:

Parameters declared high in the hierarchy replace parameters declared lower in the hierarchy,
that have the same name. (Same name means: last component of the path is the same.)

Example Ks replaces r.Ks, a.b.Ks .

@note This algorithm assumes that parameters with short names come first.
*/
void siml::CmModelIntermediate::propagateParameters()
{
//     list<CmMemoryTable::iterator> deletedParams;
//     map<CmPath, CmPath> replaceParams;
    CmPath::ReplaceMap replaceParams;

    //find pameters (paths) that should be replaced (by parameters with shorter names)--------------------------
    CmMemoryTable::iterator itM1, itM2;
    //loop over all parameters. Take *itM1 and try to find parameters that will be replaced by *itM1.
    for( itM1 = parameter.begin(); itM1 != parameter.end(); ++itM1 )
    {
        CmMemoryDescriptor const & m1 = *itM1; //Kdevelop's completion is bad

        //see if the parameter is already subject to replaceing. If yes go to next parameter.
        if( replaceParams.find( m1.name ) != replaceParams.end() ) { continue; }

        //loop over the parameters below *itM1 and see if they can be replaced.
        itM2 = itM1; ++itM2;
        for( ; itM2 != parameter.end(); ++itM2 )
        {
            CmMemoryDescriptor const & m2 = *itM2; //Kdevelop's completion is bad
            if( m1.name.isTailOf( m2.name ) )
            {
//                 deletedParams.insert( itM2 );
                replaceParams[m2.name] = m1.name;
            }
        }
    }

    //delete replaced parameters from the list of parameters. ---------------------------------------------
    CmMemoryTable::iterator itPar;
    for( itPar = parameter.begin(); itPar != parameter.end(); )
    {
        //see if the parameter is subject to replaceing. If yes delete the parameter.
        if( replaceParams.find( itPar->name ) != replaceParams.end() )
        {
            CmMemoryTable::iterator itDel = itPar;
            ++itPar; //increment iterator, deletiong will invalidate it
            parameter.erase( itDel );
        }
        else //only increment iterator
        {
            ++itPar;
        }
    }

     //rename all references to parameters in the set section---------------------------------------
    CmEquationTable::iterator itE;
    for( itE = parameterAssignment.begin(); itE != parameterAssignment.end(); ++itE)
    {
        itE->lhs.replacePath(replaceParams);  //this should never do anything
        itE->rhs.replacePaths(replaceParams);
    }

    //rename all references to parameters in the initial equations---------------------------------------
    for( itE = initialEquation.begin(); itE != initialEquation.end(); ++itE)
    {
        itE->lhs.replacePath(replaceParams);  //this should never do anything
        itE->rhs.replacePaths(replaceParams);
    }

    //rename all references to parameters in the equations---------------------------------------
    for( itE = equation.begin(); itE != equation.end(); ++itE)
    {
        itE->lhs.replacePath(replaceParams);  //this should never do anything
        itE->rhs.replacePaths(replaceParams);
    }
}


/*!
Functor's action function.
Determine the validity of the identifiers in the SET section (parameterAssignment).
Current checks:
    - All operands must be (defined) parameters;
    - No $ allowed.*/
void siml::CmModelIntermediate::CheckSetSectionIdentifier::operator() ( CmMemAccess const & mem) const
{
    if( process.findParameter( mem.path()) == process.parameter.end() )
    {   //all operands must be parameters
        format msg = format( "Undefined parameter: %1%" ) % mem.path();
        CmError::addError( msg.str(), equation.defBegin);
        process.errorsDetected = true;
    }
    else if( mem.isTimeDerivative() )
    {   //no $ allowed.
        format msg = format( "Parameters can not be differentiated! See: %1%" ) % mem;
        CmError::addError( msg.str(), equation.defBegin);
        process.errorsDetected = true;
    }
}


/*!
Functor's action function.
Determine the validity of the identifiers in the RHS in the EQUATION section.
Current checks:
        - RHS: no $ allowed.
        - RHS: Memory access must go to defined parameters or variables.
*/
void siml::CmModelIntermediate::CheckEquationRhsIdentifier::operator() ( CmMemAccess const & mem) const
{
    if( !process.isIdentifierExisting( mem.path()) )//note: intermediate models have no sub-models.
    {   //all operands must be defined
        format msg = format( "Undefined identifier: %1%\nExpecting variable or parameter here." ) % mem.path();
        CmError::addError( msg.str(), equation.defBegin);
        process.errorsDetected = true;
    }
    else if( mem.isTimeDerivative() )
    {   //no $ allowed.
        format msg = format( "Illegal time derivation: %1%\nTime derivation is only legal on the LHS." ) % mem;
        CmError::addError( msg.str(), equation.defBegin);
        process.errorsDetected = true;
    }
}


/*!
Test for semantic errors (the syntax was already checked by the parser).

SET:
        - All: Operands (paths) must be parameters.
        - All: No $ allowed.
        - LHS: All parameters must be initialized.
        - LHS: No duplicate assignments.

EQUATION:
        - LHS must be (defined) variable not parameter.
        - LHS: All variables must have assignments.
        - LHS: No duplicate assignments. - catches: No assignment to state variables.
        - RHS: no $ allowed.
        - RHS: Memory access must go to defined parameters or variables.

INITIAL:
        - LHS must be state variable.
        - LHS: All state variables must have assignments.
        - LHS: No duplicate assignments.
        - LHS: no $ allowed.
        - RHS: no $ allowed.
        - RHS: Memory access must go to defined parameters or variables.

Function Result:
        - Errors will be generated and put imto the global storage.
        - The variable process.errorsDetected will be set to true, if errors are detected.
*/
void siml::CmModelIntermediate::checkErrors()
{
    typedef set<CmPath> PathMap;
    PathMap noAssignmentYet; //set for rule: one and only one assignment for each identifier.
    CmMemoryTable::const_iterator itMem;
    CmEquationTable::const_iterator itEqu;

    //SET section ------------------------------------------------------------------------------------------
    //put all parameters into the set. When one is assigned it will be taken out again.
    for( itMem = parameter.begin(); itMem != parameter.end(); ++itMem){ noAssignmentYet.insert( itMem->name); }

    //Look at the entire SET section and see if no rules were violated.
    for( itEqu = parameterAssignment.begin(); itEqu != parameterAssignment.end(); ++itEqu)
    {
        CmEquationDescriptor const & equ = *itEqu;
        CheckSetSectionIdentifier inspectMem( *this, equ);// all operands must be parameters;  no $ allowed.
        //RHS inspect all identifiers
        equ.rhs.applyToMemAccessConst( inspectMem);
        //LHS: inspect the identifier
        inspectMem( equ.lhs);
        //LHS: no duplicate assignment.
        if( findParameter( equ.lhs.path()) == parameter.end() ) { continue; } //was already checked, but information was forgotten.
        if( noAssignmentYet.find( equ.lhs.path()) != noAssignmentYet.end() )
        {   //OK the identifier has not been assigned already.
            //Take identifier out of set, because assignement has happened.
            noAssignmentYet.erase( equ.lhs.path());
        }
        else
        {
            format msg = format( "Duplicate assignment to parameter: %1%\n") % equ.lhs;
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
        }
    }

    //Test if there are still uassigned parameters
    if( noAssignmentYet.size() > 0 )
    {
        ostringstream msg;
        msg << "Process: " << name << ". The following parameters are unassigned: ";
        PathMap::const_iterator it;
        for( it = noAssignmentYet.begin(); it != noAssignmentYet.end(); ++it ) { msg << *it << ", "; }
        CmError::addError( msg.str(), defBegin);
        errorsDetected = true;
    }

    //EQUATION section ----------------------------------------------------------------------------------
    //put all variables into the set. When one is assigned it will be taken out again.
    noAssignmentYet.clear();
    for( itMem = variable.begin(); itMem != variable.end(); ++itMem){ noAssignmentYet.insert( itMem->name); }

    //Look at the entire EQUATION section and see if no rules were violated.
    for( itEqu = equation.begin(); itEqu != equation.end(); ++itEqu)
    {
        CmEquationDescriptor const & equ = *itEqu;
        //RHS: no $ allowed; Memory access must go to defined parameters or variables.
        CheckEquationRhsIdentifier inspector( *this, equ);
        equ.rhs.applyToMemAccessConst( inspector);
        //LHS: must not be parameter.
        if( findParameter( equ.lhs.path()) != parameter.end() )
        {
            format msg = format( "Illegal assignment to parameter: %1%\n"
                                 "Parameters can only be assigned once in the SET section." ) % equ.lhs;
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
            continue;
        }
        //LHS: must be variable
        if( findVariable( equ.lhs.path()) == variable.end() )
        {
            format msg = format( "Undefined variable: %1%" ) % equ.lhs;
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
            continue;
        }
        //LHS: no duplicate assignment
        if( noAssignmentYet.find( equ.lhs.path()) != noAssignmentYet.end() )
        {   //OK the identifier has not been assigned already.
            //Take identifier out of set, because assignement has happened.
            noAssignmentYet.erase( equ.lhs.path());
        }
        else
        {
            format msg = format( "Duplicate assignment to variable: %1%\n") % equ.lhs.path();
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
        }
    }

    //Test if there are still uassigned variables
    if( !noAssignmentYet.empty() )
    {
        ostringstream msg;
        msg << "Process: " << name << ". The following variables are unassigned: ";
        PathMap::const_iterator it;
        for( it = noAssignmentYet.begin(); it != noAssignmentYet.end(); ++it ) { msg << *it << ", "; }
        CmError::addError( msg.str(), defBegin);
        errorsDetected = true;
    }

    //Check initial section --------------------------------------------------------------------------
    //put the state variables into the set. When one is assigned it will be taken out again.
    noAssignmentYet.clear();
    for( itMem = variable.begin(); itMem != variable.end(); ++itMem)
    {
        if( itMem->is_state_variable ) { noAssignmentYet.insert( itMem->name); }
    }

    //Look at the entire INITIAL section and see if no rules were violated.
    for( itEqu = initialEquation.begin(); itEqu != initialEquation.end(); ++itEqu)
    {
        CmEquationDescriptor const & equ = *itEqu;
        //RHS: no $ allowed; Memory access must go to defined parameters or variables.
        CheckSetSectionIdentifier inspector( *this, equ);///@todo make special functor with better error messages.
        equ.rhs.applyToMemAccessConst( inspector);
        //LHS: must be defined variable.
        CmMemoryTable::const_iterator lhsVar = findVariable( equ.lhs.path());
        if(  lhsVar == variable.end() )
        {
            format msg = format( "Undefined variable: %1%" ) % equ.lhs.path();
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
            continue;
        }
        //LHS: must be state variable.
        if( !lhsVar->is_state_variable )
        {
            format msg = format( "State variable required! Variable %1% is algebraic.\n"
                                 "Only state Variables can be initalied." ) % equ.lhs.path();
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
            continue;
        }
        //LHS: no $ allowed.
        if( equ.lhs.isTimeDerivative() )
        {
            format msg = format( "Illegal time derivative in initial section: %1%" ) % equ.lhs;
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
        }
        //LHS: no duplicate initilization
        if( noAssignmentYet.find( equ.lhs.path()) != noAssignmentYet.end() )
        {   //OK the identifier has not been assigned already.
            //Take identifier out of set, because assignement has happened.
            noAssignmentYet.erase( equ.lhs.path());
        }
        else
        {
            format msg = format( "Duplicate initialization of state variable: %1%\n") % equ.lhs.path();
            CmError::addError( msg.str(), equ.defBegin);
            errorsDetected = true;
        }
    }

    //Test if there are still uninitialized state variables
    if( !noAssignmentYet.empty() )
    {
        ostringstream msg;
        msg << "Process: " << name << ". The following state variables are not initialized: ";
        PathMap::const_iterator it;
        for( it = noAssignmentYet.begin(); it != noAssignmentYet.end(); ++it ) { msg << *it << ", "; }
        CmError::addError( msg.str(), defBegin);
        errorsDetected = true;
    }

}



