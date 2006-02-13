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
#ifndef SIML_PYPROCESSGENERATOR_H
#define SIML_PYPROCESSGENERATOR_H


#include "siml_code_model.h"
// #include "siml_cmpath.h"
#include "siml_pyformulaconverter.h"

#include <boost/shared_ptr.hpp>

#include <iostream>
// #include <vector>
#include <string>
// #include <fstream>
#include <map>


namespace siml {

/**
@short Generate a process


@author Eike Welk
*/
class PyProcessGenerator{
public:
    //!Constructor
    PyProcessGenerator( std::ostream & inPyFile );
    //!Destuctor
    ~PyProcessGenerator();

    //!generate python code for one process
    void genProcessObject(int iProcess);

private:
    //text generating functions
    //!generate the processe's constructor
    void genConstructor();
    //!generate the function that conains the equations
    void genOdeFunction();
    //!create the function that compotes the algebraic variables for output
    void genOutputEquations();
    //!generate the simulation's main function @todo put into file's header?
    void genSimulateFunction();
    //!generate function that returns a single variable from the array of simulation results
    void genAccessFunction();
    //!create the function that shows results graphically
    void genGraphFunction();

    //creation of internal data structures
    //!Define which variable is at what index in various arrays
    void layoutArrays();
    //!create maping between path and Python variable name
    void createPyVarNames();

    //!The generated python program is stored here
    std::ostream& m_PyFile;

    //!The process - special format
    /*!This object contains all memory and all equations that are used in the simulation.
    The entities from all sub-models were copied into this object, and given unique names.*/
    CmModelDescriptor m_FlatProcess;

    //!All parameters of the process
//     CmMemoryTable m_Parameter;
    //!All variables of the process
//     CmMemoryTable m_Variable;
    //!All equations of the process
//     CmEquationTable m_Equation;

    //!Mapping between variable name and index in state vector.
    /*!The variable name is the key. So the contents are pairs: var_name, index) e.g: ("S", "1")
    @todo make map into CmPath --> string */
    std::map<CmPath, std::string> m_StateVectorMap;
    //!State variable names in order of ascending index
    /*!Only needed to produce good looking code since state_vector_map is ordered alphabeticaly*/
//     std::vector<std::string> state_vector_ordering;
    //!The state vector's number of rows.
    uint m_StateVectorSize; ///@todo remove; use m_StateVectorMap.size() instead.

    //!Mapping between variable name and index in result array.
    /*!The variable name is the key. So the contents are pairs: var_name, index) e.g: ("mu", "5")
     *
     * The result array keeps the time series of all variables (state and algebraic) after the simulation
     * is finished for easy retrieval. The first index is the time axis, the collumns (second index) are
     * different variables.
     * @todo make map into CmPath --> string */
    std::map<CmPath, std::string> m_ResultArrayMap;
    //!All variable names in order of ascending collumn index in result array.
    /*!Only needed to produce good looking code since result_vector_map is ordered alphabeticaly*/
//     std::vector<std::string> result_array_ordering;
    //!Number of collumns (2nd index) of the result array.
    uint m_ResultArrayColls; ///@todo remove; use m_ResultArrayMap.size() instead.

    //!Python names for all variables and parameters.
    /*! Mapping between siml path ("a.b.c") and Python expression to access this object ("self.a_b_c") */
    std::map<CmPath, std::string> m_PythonName;

    //!create Python expressions from CmFormula objects.
    PyFormulaConverter m_toPy;
};

}

#endif //SIML_PYPROCESSGENERATOR_H
