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
#include <boost/format.hpp>


using namespace siml;
using boost::shared_ptr;
using boost::format;
using std::string;


/*!
Transform a model with sub-models into an equivalent model without sub-models.
This can also be seen as allocating memory for the (sub-)models.

All parameters, variables and equations of the submodels are (recursively)
copied to the flat model. Parmeters and variables get unique long names.

This is the first step in generating code for a procedure.

@param  compositeModel the model that will be converted.
@param  repo the place where we search for the sub-models
@return The generated equivalent model without submodels.
 */
shared_ptr<CmModelDescriptor>
siml::createFlatModel(    CmModelDescriptor const * compositeModel,
                          CmCodeRepository * repo )
{
    shared_ptr<CmModelDescriptor> sFlatModel( new CmModelDescriptor); //the result

    //less typing + KDevelop's code completion sucks!
    CmModelDescriptor * flatModel = sFlatModel.get();

    //copy the features that are not copied recursively
    flatModel->name = compositeModel->name;
    flatModel->isProcess = compositeModel->isProcess;
    flatModel->initialExpression = compositeModel->initialExpression;
    flatModel->solutionParameters = compositeModel->solutionParameters;

    //copy the recursive features
    int recursionLevel = 0;
    CmPath variablePrefix;
    flattenModelRecursive(compositeModel, variablePrefix, recursionLevel, repo, flatModel);

    return sFlatModel;
}

/*!
Copy parameters, variables and equations for createFlatModel(...).

@param  inCompositeModel the model that will be converted.
@param  inPathPrefix this is put in front of all variable and parameter names.
@param  inRecursionLevel depth of recursion to avoid enless loops
@param  inRepo the place where we search for the sub-models
@param  outFlatModel the result. The converted entities are put here.
@internal
*/
void
siml::flattenModelRecursive(    CmModelDescriptor const * inCompositeModel,
                                siml::CmPath const inPathPrefix,
                                uint const inRecursionLevel,
                                CmCodeRepository * inRepo,
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
        inRepo->error.push_back(CmErrorDescriptor(msg) );
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
        mem.name.prepend(inPathPrefix);//put prefix in front of parameter name
        shared_ptr<CmErrorDescriptor> err;
        err = outFlatModel->addParameter(mem);// add to model
        if( err )
        {
            inRepo->error.push_back(*err);
            outFlatModel->errorsDetected = true;
        }
    }

    //copy variables
    for(    itM = inCompositeModel->variable.begin();
            itM != inCompositeModel->variable.end();
            ++itM )
    {
        CmMemoryDescriptor mem = *itM;
        mem.name.prepend(inPathPrefix); //put prefix in front of variable name
        shared_ptr<CmErrorDescriptor> err;
        err = outFlatModel->addVariable(mem); // add to model
        if( err )
        {
            inRepo->error.push_back(*err);
            outFlatModel->errorsDetected = true;
        }
    }

    //copy parameter assignments (SET)
    CmEquationTable::const_iterator itE;
    for(    itE = inCompositeModel->parameterAssignment.begin();
            itE != inCompositeModel->parameterAssignment.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //go through the equation and add the prefix at all variable names
        equ.lhs.prepend( inPathPrefix);
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
        equ.lhs.prepend( inPathPrefix);
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
        CmModelDescriptor * submodel = inRepo->findModel(itS->type);
        //Error: Null pointer - model does not exist!
        if( !submodel )
        {
            string msg = ( format(
                    "The model %1% does not exist!" ) % itS->type ).str();
            inRepo->error.push_back(CmErrorDescriptor(msg) );
            outFlatModel->errorsDetected = true;
            continue;
        }

        //add the submodel's name to the prefix.
        CmPath newPrefix = inPathPrefix;
        newPrefix.append(itS->name);
        //copy entities of submodel
        flattenModelRecursive(    submodel, newPrefix, newRecursionLevel,
                                  inRepo, outFlatModel );
    }
}
