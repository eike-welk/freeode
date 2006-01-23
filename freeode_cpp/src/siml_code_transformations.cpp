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
Transfor a model with sub-models into an equivalent model without sub-models.

All parameters, variables and equations of the submodels are (recursively)
copied to the flat model. Parmeters and variables get unique long names.

This is the first step in generating code for a procedure.
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
copy parameters, variables and equations for createFlatModel

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
    //copy the recursive entities -------------------------------------
    //copy parameters
    CmMemoryTable::const_iterator itM;
    for(    itM = inCompositeModel->parameter.begin();
            itM != inCompositeModel->parameter.end();
            ++itM )
    {
        CmMemoryDescriptor mem = *itM;
        mem.name.prepend(inPathPrefix);
        shared_ptr<CmErrorDescriptor> err;
        err = outFlatModel->addParameter(mem);
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
        mem.name.prepend(inPathPrefix);
        shared_ptr<CmErrorDescriptor> err;
        err = outFlatModel->addVariable(mem);
        if( err )
        {
            inRepo->error.push_back(*err);
            outFlatModel->errorsDetected = true;
        }
    }

    //copy parameter assignments
    CmEquationTable::const_iterator itE;
    for(    itE = inCompositeModel->parameterAssignment.begin();
            itE != inCompositeModel->parameterAssignment.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //TODO go through the equation and add the prefix at all variable names
        shared_ptr<CmErrorDescriptor> err;
//         err = outFlatModel->addParameterAssignment(mem);
        if( err )
        {
            inRepo->error.push_back(*err);
            outFlatModel->errorsDetected = true;
        }
    }

    //copy equations
    for(    itE = inCompositeModel->equation.begin();
            itE != inCompositeModel->equation.end();
            ++itE )
    {
        CmEquationDescriptor equ = *itE;
        //TODO go through the equation and add the prefix at all variable names
        shared_ptr<CmErrorDescriptor> err;
//         err = outFlatModel->addEquation(mem);
        if( err )
        {
            inRepo->error.push_back(*err);
            outFlatModel->errorsDetected = true;
        }
    }
    //special handling for the error flag
    if( inCompositeModel->errorsDetected )
    {
        outFlatModel->errorsDetected = true;
    }

    //recursively call this function for each submodel----------------------------
    //increase recursion level
    uint newRecursionLevel = inRecursionLevel+1;
    //add the current model's name to the prefix.
    CmPath newPrefix = inPathPrefix;
    newPrefix.append(inCompositeModel->name);

    CmSubModelTable::const_iterator itS;
    for(    itS = inCompositeModel->subModel.begin();
            itS != inCompositeModel->subModel.end();
            ++itS )
    {
        CmModelDescriptor * submodel = inRepo->findModel(itS->type);
        if( !submodel )
        {
            string msg = ( format(
                    "The model %1% does not exist!" ) % itS->type ).str();
            inRepo->error.push_back(CmErrorDescriptor(msg) );
            outFlatModel->errorsDetected = true;
        }

        flattenModelRecursive(    submodel, newPrefix, newRecursionLevel,
                                  inRepo, outFlatModel );
    }
}
