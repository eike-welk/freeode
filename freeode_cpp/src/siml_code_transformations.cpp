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
                          CmCodeRepository  const * repo )
{
    shared_ptr<CmModelDescriptor> sFlatModel( new CmModelDescriptor); //the result

    //less typing + KDevelop's code completion sucks!
    CmModelDescriptor * flatModel = sFlatModel.get();

    //copy the features that are not copied recursively
    flatModel->name = compositeModel->name;
    flatModel->isProcess = compositeModel->isProcess;
    flatModel->solutionParameters = compositeModel->solutionParameters;

    //copy the recursive features
    string recursionLevel;
    flattenModelRecursive(compositeModel, recursionLevel, repo, flatModel);

    return sFlatModel;
}

/*!
copy parameters, variables and equations for createFlatModel
@internal
*/
void
siml::flattenModelRecursive(    CmModelDescriptor const * inCompositeModel,
                                std::string const inRecursionLevel,
                                CmCodeRepository  const * inRepo,
                                CmModelDescriptor * outFlatModel)
{
}
