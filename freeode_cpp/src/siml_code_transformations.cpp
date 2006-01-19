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

using namespace siml;
using boost::shared_ptr;
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
    string variablePrefix;
    flattenModelRecursive(compositeModel, variablePrefix, recursionLevel, repo, flatModel);

    return sFlatModel;
}

/*!
copy parameters, variables and equations for createFlatModel
@internal
*/
void
siml::flattenModelRecursive(    CmModelDescriptor const * inCompositeModel,
                                std::string const inVariablePrefix,
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
//         mem.name.addPrefix(inVariablePrefix);
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
//         mem.name.addPrefix(inVariablePrefix);
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

    //recursively call this function for each submodel
    uint newRecursionLevel = inRecursionLevel+1;
    CmSubModelTable::const_iterator itS;
    for(    itS = inCompositeModel->subModel.begin();
            itS != inCompositeModel->subModel.end();
            ++itS )
    {
        CmModelDescriptor * submodel = 0;
        ///@todo implement CmCodeRepository::findModel
        submodel = inRepo->findModel(itS->type);
        string newPrefix;
//         newPrefix.addSuffix(itS->name );
        flattenModelRecursive(    submodel, newPrefix, newRecursionLevel,
                                  inRepo, outFlatModel );
    }
}
