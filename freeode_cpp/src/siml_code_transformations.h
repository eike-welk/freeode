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
#ifndef SIML_CODE_TRANSFORMATIONS_H
#define SIML_CODE_TRANSFORMATIONS_H


#include "siml_code_model.h"
#include "siml_cmpath.h"

#include <boost/shared_ptr.hpp>

// #include <iostream>
// #include <vector>
// #include <string>
// #include <fstream>
// #include <map>


namespace siml {

//!create model without sub-models
CmModelDescriptor createFlatModel( CmModelDescriptor const & compositeProcess);

//!copy parameters, variables and equations for createFlatModel
void
flattenModelRecursive(  CmModelDescriptor const * inCompositeModel,
                        CmPath const inPathPrefix,
                        uint const inRecursionLevel,
                        CmModelDescriptor * outFlatModel );

//!Apply the parameter propagation rules
void propagateParameters( CmModelDescriptor & process);

//!Test for semantic errors
void checkErrors( CmModelDescriptor & process);
}

#endif //SIML_CODE_TRANSFORMATIONS_H
