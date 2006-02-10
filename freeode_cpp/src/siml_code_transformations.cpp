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


#include "siml_code_transformations.h"
#include "siml_cmerror.h"
// #include "siml_cmpath.h"

#include <boost/format.hpp>

#include <set>
#include <map>
// #include <vector>
#include <list>


using namespace siml;
using boost::shared_ptr;
using boost::format;
using std::string;
using std::set;
using std::map;
// using std::vector;
using std::list;


/*!
Transform a model with sub-models into an equivalent model without sub-models.
This can also be seen as allocating memory for the (sub-)models.

All parameters, variables and equations of the submodels are (recursively)
copied to the flat model. Parmeters and variables get unique long names.

This is the first step in generating code for a procedure.

@param  compositeProcess the model that will be converted.
@return The generated equivalent model without submodels.
 */
CmModelDescriptor
siml::createFlatModel( CmModelDescriptor const & compositeProcess )
{
    CmModelDescriptor flatModel; //the result

    //copy the features that are not copied recursively
    flatModel.name = compositeProcess.name;
    flatModel.isProcess = compositeProcess.isProcess;
    flatModel.initialEquation = compositeProcess.initialEquation;
    flatModel.solutionParameters = compositeProcess.solutionParameters;

    //copy the recursive features
    int recursionLevel = 0;
    CmPath variablePrefix;
    flattenModelRecursive(&compositeProcess, variablePrefix, recursionLevel, &flatModel);

    return flatModel;
}

/*!
Copy parameters, variables and equations for createFlatModel(...).

@param  inCompositeModel the model that will be converted.
@param  inPathPrefix this is put in front of all variable and parameter names.
@param  inRecursionLevel depth of recursion to avoid enless loops
@param  outFlatModel the result. The converted entities are put here.
@internal
*/
void
siml::flattenModelRecursive(    CmModelDescriptor const * inCompositeModel,
                                siml::CmPath const inPathPrefix,
                                uint const inRecursionLevel,
                                CmModelDescriptor * outFlatModel )
{
    //protect against circular dependencies ------------------------------
    uint const recursionLevelMax =10;
    if( inRecursionLevel > 10 )
    {
        string msg = ( format(
                "The maximum recursion level (%1%) has been reached!\n"
                "Procedure: %2%; Submodel where the error happened: %3%.\n"
                "(Maybe there are circular dependencies.)"
                ) % recursionLevelMax % outFlatModel->name % inCompositeModel->name ).str();
        CmError::addError( msg, (char const *)0); ///@todo add iterator
        outFlatModel->errorsDetected = true;
        return;
    }

    //copy the recursive entities -------------------------------------
    //copy parameters
    CmMemoryTable::const_iterator itM;
    for(    itM = inCompositeModel->parameter.begin();
            itM != inCompositeModel->parameter.end();
            ++itM )
    {
        CmMemoryDescriptor mem = *itM;
        mem.name.prepend(inPathPrefix); //put prefix in front of parameter name
        outFlatModel->addParameter(mem);// add to model
    }

    //copy variables
    for(    itM = inCompositeModel->variable.begin();
            itM != inCompositeModel->variable.end();
            ++itM )
    {
        CmMemoryDescriptor mem = *itM;
        mem.name.prepend(inPathPrefix); //put prefix in front of variable name
        outFlatModel->addVariable(mem); // add to model
    }

    //copy parameter assignments (SET)
    CmEquationTable::const_iterator itE;
    for(    itE = inCompositeModel->parameterAssignment.begin();
            itE != inCompositeModel->parameterAssignment.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //go through the equation and add the prefix at all variable names
        equ.lhs.prependPath( inPathPrefix);
        equ.rhs.prependPaths( inPathPrefix);
        //add updated equation to the model
        outFlatModel->addParameterAssignment(equ);
    }

    //copy equations
    for(    itE = inCompositeModel->equation.begin();
            itE != inCompositeModel->equation.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //go through the equation and add the prefix at all variable names
        equ.lhs.prependPath( inPathPrefix);
        equ.rhs.prependPaths( inPathPrefix);
        //add updated equation to the model
        outFlatModel->addEquation(equ);
    }
    //special handling for the error flag - errors were maybe detected. don't stop, we want to find more
    if( inCompositeModel->errorsDetected )
    {
        outFlatModel->errorsDetected = true;
    }

    //recursively call this function for each submodel----------------------------
    //increase recursion level
    uint newRecursionLevel = inRecursionLevel+1;

    CmSubModelTable::const_iterator itS;
    for(    itS = inCompositeModel->subModel.begin();
            itS != inCompositeModel->subModel.end();
            ++itS )
    {
        //Search model definition in repository.
        CmModelDescriptor * submodel = repository()->findModel(itS->type);
        //Error: Null pointer - model does not exist!
        if( !submodel )
        {
            string msg = ( format(
                    "The model %1% does not exist!" ) % itS->type ).str();
            CmError::addError( msg, (char const *)0); ///@todo add iterator
            outFlatModel->errorsDetected = true;
            continue;
        }

        //add the submodel's name to the prefix.
        CmPath newPrefix = inPathPrefix;
        newPrefix.append(itS->name);
        //copy entities of submodel
        flattenModelRecursive( submodel, newPrefix, newRecursionLevel, outFlatModel );
    }
}

/*!
The parametre propagation rules say:

Parameters declared high in the hierarchy replace parameters declared lower in the hierarchy,
that have the same name. (Same name means: last component of the path is the same.)

@note This algorithm assumes that parameters with short names come first.
*/
void siml::propagateParameters( CmModelDescriptor & process)
{
//     list<CmMemoryTable::iterator> deletedParams;
//     map<CmPath, CmPath> replaceParams;
    CmPath::ReplaceMap replaceParams;

    //find pameters (paths) that should be replaced (by parameters with shorter names)--------------------------------------------------
    CmMemoryTable::iterator itM1, itM2;
    //loop over all parameters. Take *itM1 and try to find parameters that will be replaced by *itM1.
    for( itM1 = process.parameter.begin(); itM1 != process.parameter.end(); ++itM1 )
    {
        CmMemoryDescriptor const & m1 = *itM1; //Kdevelop's completion is bad

        //see if the parameter is already subject to replaceing. If yes go to next parameter.
        if( replaceParams.find( m1.name ) != replaceParams.end() ) { continue; }

        //loop over the parameters below *itM1 and see if they can be replaced.
        itM2 = itM1; ++itM2;
        for( ; itM2 != process.parameter.end(); ++itM2 )
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
    for( itPar = process.parameter.begin(); itPar != process.parameter.end(); )
    {
        //see if the parameter is subject to replaceing. If yes delete the parameter.
        if( replaceParams.find( itPar->name ) != replaceParams.end() )
        {
            CmMemoryTable::iterator itDel = itPar;
            ++itPar; //increment iterator, deletiong will invalidate it
            process.parameter.erase( itDel );
        }
        else //only increment iterator
        {
            ++itPar;
        }
    }

     //rename all references to parameters in the set section---------------------------------------
    CmEquationTable::iterator itE;
    for( itE = process.parameterAssignment.begin(); itE != process.parameterAssignment.end(); ++itE)
    {
        itE->lhs.replacePath(replaceParams);  //this should never do anything
        itE->rhs.replacePaths(replaceParams);
    }

    //rename all references to parameters in the initial equations---------------------------------------
    for( itE = process.initialEquation.begin(); itE != process.initialEquation.end(); ++itE)
    {
        itE->lhs.replacePath(replaceParams);  //this should never do anything
        itE->rhs.replacePaths(replaceParams);
    }

    //rename all references to parameters in the equations---------------------------------------
    for( itE = process.equation.begin(); itE != process.equation.end(); ++itE)
    {
        itE->lhs.replacePath(replaceParams);  //this should never do anything
        itE->rhs.replacePaths(replaceParams);
    }
}




/*!
Test for semantic errors

set:
-All operands (paths) must be parameters.
- no $ allowed.
-All parameters must be initialized.

Equation:
-lhs must be variable not parameter.
-rhs: no $ allowed.
-All memory access must go to declared parameters and variables.
-No assignment to state variables.
-No assignment to parameters.
-All state variables must have '$x =' assignments.
-All algebraic variables must have assignments.

@note The result will be (or-ed into) process.errorsDetected;
*/
void siml::checkErrors( CmModelDescriptor & process)
{
    //SET section ----------------------------------------------
    //all operands must be parameters
    return;
}



