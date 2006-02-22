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
// #include "siml_globaldef.h"
#include "siml_pyprocessgenerator.h"

#include "siml_cmmodelintermediate.h"
#include "siml_cmerror.h"
// #include "siml_pyformulaconverter.h"

#include <iostream>
#include <set>

#include <boost/format.hpp>
#include <boost/tuple/tuple.hpp>


using std::string;
using std::endl;
using std::map;
using std::vector;
using std::cout;
using std::set;

using boost::format;
using boost::tie;
using boost::shared_ptr;


/*!Construct and initialize the object, but do not generate codee.*/
siml::PyProcessGenerator::PyProcessGenerator( std::ostream& inPyFile ) :
        m_PyFile(inPyFile),
        m_StateVectorSize(0),
        m_ResultArrayColls(0)
{

}


siml::PyProcessGenerator::~PyProcessGenerator()
{
}


/*!
Create a single process
 */
void siml::PyProcessGenerator::genProcessObject( CmModelDescriptor const & inProcess)
{
    //create the intermediate model
    m_FlatProcess.createIntermediateModel( inProcess);

    //Don't generate code when there are errors.
    if( m_FlatProcess.errorsDetected )
    {
        format msg = format("Process %1%: No Python object generated due to Errors.") % m_FlatProcess.name;
        CmError::addError( msg.str(), m_FlatProcess.defBegin);
        return;
    }

    //allocate space for the state variables in the state vector. Alocate space for all variables in the output array.
    layoutArrays();
    //create Python variable names for all paths
    createPyVarNames();
    //put the map between paths and python names into the formula conversion object
    m_toPy.setPythonName( m_PythonName);

    //generate the start of the simulation object's definition
    m_PyFile << format("class %1%(SimulatorBase):\n") % m_FlatProcess.name;
    m_PyFile << format("%|4t|\"\"\"\n");
    m_PyFile << format("%|4t|Object to simulate process %1%\n") % m_FlatProcess.name;
    string fileName = m_FlatProcess.defBegin.get_position().file;
    int line = m_FlatProcess.defBegin.get_position().line;
    m_PyFile << format("%|4t|Definition in file: '%1%' line: %2%\n") % fileName % line;
    m_PyFile << format("%|4t|\"\"\"\n");
    m_PyFile << '\n';

    //Generate Constuctor which creates the maps for later access to variables (and some day parameters)
    genConstructor();

    //generate the SET function where parameter values are assigned (as member variables).
    genSetParameters();

    //Generate function to Set INITIAL values of the state variables.
    geSetInitialValues();

    //Generate the function that contains the equations.
    genOdeFunction();

    //Function to compute the algebraic variables after the simulation.
    genOutputEquations();
}


/*!
Generate the __init__ function.
Generate Constuctor which creates the parameters as member variables
 */
void siml::PyProcessGenerator::genConstructor()
{
    m_PyFile << format("%|4t|def __init__(self):") << '\n';

    //call base class' constructor
    m_PyFile << format("%|8t|#call base class' constructor.\n");
    m_PyFile << format("%|8t|SimulatorBase.__init__(self)\n\n");

    //Map for converting variable names to indices or slices
    //necessary for convenient access to the simulation results from Python.
    //used by Python functions: get(...), graph(...)
    //loop produces: self._resultArrayMap = { 'reactor.S':1, 'reactor.X':0, 'reactor.mu':2,  }
    m_PyFile << format("%|8t|#Map for converting variable names to indices or slices.\n");
    m_PyFile << format("%|8t|self._resultArrayMap = {");
    map<CmPath, string>::const_iterator itMa;
    for( itMa = m_ResultArrayMap.begin(); itMa != m_ResultArrayMap.end(); ++itMa )
    {
        CmPath path;
        string simlName, index;
        tie(path, index) = *itMa;
        simlName = path.toString(); //the Python access function uses the Siml name
        m_PyFile << format(" '%1%':%2%,") % simlName % index; ///@todo the algo writes one comma too much (after the last element)
    }
    m_PyFile << " }\n\n";

    //Set the solution parameters
    m_PyFile << format("%|8t|#Set the solution parameters.\n");
    m_PyFile << format("%|8t|self.reportingInterval = float(%1%)\n") % m_FlatProcess.solutionParameters.reportingInterval;
    m_PyFile << format("%|8t|self.simulationTime    = float(%1%)\n\n") % m_FlatProcess.solutionParameters.simulationTime;

    //Compute parameter values
    m_PyFile << format("%|8t|#Compute parameter values.\n");
    m_PyFile << format("%|8t|self.setParameters()\n\n");

//     //Compute the initial values
//     m_PyFile << format("%|8t|#Compute the initial values.\n");
//     m_PyFile << format("%|8t|self.setInitialValues()\n");

    //Easy access to number of state variables and total number of variables
    m_PyFile << format("%|8t|#Number of state variables and total number of variables.\n");
    m_PyFile << format("%|8t|self._numStates    = %1%\n") % m_StateVectorSize;
    m_PyFile << format("%|8t|self._numVariables = %1%\n") % m_ResultArrayColls;

    m_PyFile << '\n';

    ///@todo initialize _resultArray with the right dimensions. Now get() dfails prior to a simulation run.
}


/*!
Generate the (SET) function where values are assigned to the parameters.
The parameters are data members of the simulation object.

All parameter that are assigne only numbers are (named) function arguments.
The function looks like this:
@code
    def setParameters(self, mu_max=0.32, Ks=0.1, Yxs=0.5, Sf=20, D=0.1):
        self.p_mu_max    = float(mu_max) # = mu_max
        ....
        self.p_dummy1    = self.p_Sf * self.p_D # = dummy1
@endcode
*/
void siml::PyProcessGenerator::genSetParameters()
{
    CmEquationTable::const_iterator it;
    //Determine the parameters with simple assignments in the SET section. e.g.:"Ks := 0.1;"
    //These parameters can be easyly changed, and then the computations for the
    //other parameters are carried out.
    //The easy parameters become named arguments of the setParameters(self, ...) function
    set<CmPath> functionArgs;
    for( it = m_FlatProcess.parameterAssignment.begin(); it != m_FlatProcess.parameterAssignment.end(); ++it )
    {
        CmEquationDescriptor equnD = *it;
        //A formula of size 1 is a simple assignment
        if( equnD.rhs.size() != 1 ) { continue; }
        //And the only element must also be a number.
        CmFormula::NumberCmd * numPtr = dynamic_cast<CmFormula::NumberCmd*>( equnD.rhs.commands().front().get());
        if( !numPtr ) { continue; }
        //finally put the parmeter name into the set
        functionArgs.insert(equnD.lhs.path());
    }

    //write first line of function definition
    m_PyFile << format("%|4t|def setParameters(self");
    //write parmeter list with default values.
    for( it = m_FlatProcess.parameterAssignment.begin(); it != m_FlatProcess.parameterAssignment.end(); ++it )
    {
        CmEquationDescriptor equnD = *it;
        if( functionArgs.find( equnD.lhs.path()) == functionArgs.end() ) { continue; }
        string argName    = m_funcArgName[equnD.lhs.path()];
        string defaultVal = m_toPy.convert( equnD.rhs);
        m_PyFile << format(", %1%=%2%") % argName % defaultVal;
    }
    m_PyFile << "):\n";

    m_PyFile <<
            "        \"\"\"\n"
            "        Assign values to the parmeters. The function represents the SET section.\n"
            "        All parameters that have numbers assigned to them can be given new values\n"
            "        by passing them as named arguments of this function.\n"
            "        e.g. mySimulation.setParameters( Ks=0.5, Sf=5)\n"
            "        The parameters are data members of the simulation object.\n"
            "        \"\"\"\n"
            "        \n"
            ;

    //Assign values to the parameters that have function arguments.
    m_PyFile << format("%|8t|#Assign values to the parameters with function arguments") << '\n';
    for( it = m_FlatProcess.parameterAssignment.begin(); it != m_FlatProcess.parameterAssignment.end(); ++it )
    {
        CmEquationDescriptor equnD = *it;
        if( functionArgs.find( equnD.lhs.path()) == functionArgs.end() ) { continue; }

        string simlName = equnD.lhs.toString();
        string pyName = m_PythonName[ equnD.lhs.path()];
        string pyFuncArg  = m_funcArgName[equnD.lhs.path()];
        m_PyFile << format("%|8t|%1% %|25t|= float(%2%) # = %3%") % pyName % pyFuncArg % simlName << '\n';
    }

    //Assign values to the parameters that have computations.
    m_PyFile << format("%|8t|#Assign values to the parameters with computations") << '\n';
    for( it = m_FlatProcess.parameterAssignment.begin(); it != m_FlatProcess.parameterAssignment.end(); ++it )
    {
        CmEquationDescriptor equnD = *it;
        if( functionArgs.find( equnD.lhs.path()) != functionArgs.end() ) { continue; }

        string simlName = equnD.lhs.toString();
        string pyName = m_PythonName[ equnD.lhs.path()];
        string pyMathExpr  = m_toPy.convert( equnD.rhs);
        m_PyFile << format("%|8t|%1% %|25t|= %2% # = %3%") % pyName % pyMathExpr % simlName << '\n';
    }
    m_PyFile << '\n';
}


/*!
Generate function to Set INITIAL values of the state variables.

@todo A function to change the initial values from Python ia needed: Generate a setInitialValues(self, ...) how to really do this needs to be elaporated.
*/
void siml::PyProcessGenerator::geSetInitialValues()
{
    m_PyFile <<
            "    def setInitialValues(self):\n"
            "        \"\"\"\n"
            "        Copute the initial values of the state variables.\n"
            "        The function represents the SET section.\n"
            "        The inital values are stored together as a state vector in a data member.\n"
            "        \"\"\"\n"
            "        \n"
            ;

    //Assign initial values to the state variables
    m_PyFile << format("%|8t|#Assign initial values to the state variables and store them in a vector.\n");
    m_PyFile << format("%|8t|initialValues = zeros(%1%, Float)\n") % m_StateVectorSize;
    CmEquationTable::const_iterator it;
    for( it = m_FlatProcess.initialEquation.begin(); it != m_FlatProcess.initialEquation.end(); ++it )
    {
        CmEquationDescriptor equnD = *it;
        string simlName = equnD.lhs.toString();
        string index = m_StateVectorMap[equnD.lhs.path()]; //look up m_Variable's index in the state vector.
        string pyMathExpr  = m_toPy.convert( equnD.rhs);
        m_PyFile << format("%|8t|initialValues[%1%] = %2% # = %3%\n") % index % pyMathExpr % simlName;
    }
    m_PyFile << '\n';
    m_PyFile << format("%|8t|return initialValues\n");
    m_PyFile << '\n';
}


/*!
Generate the function that computes the time derivatives.
This function contains all equations. The function will be called repeatedly by
the simulation library routine.
@todo write member function genEquation( CmEquationDescriptor const &) .
@todo concept for TIME special variable needed.
 */
void siml::PyProcessGenerator::genOdeFunction()
{
    m_PyFile <<
            "    def _diffStateT(self, y, time):\n"
            "        \"\"\"\n"
            "        Compute the time derivatives of the state variables.\n"
            "        This function will be called repeatedly by the integration algorithm.\n"
            "        y: state vector,  time: current time\n"
            "        \"\"\"\n"
            "        \n";

//     //Create local variables for the parameters.
//     m_PyFile << format("%|8t|#Create local variables for the parameters.") << '\n';
//     CmMemoryTable::const_iterator itP;
//     for( itP = m_Parameter.begin(); itP != m_Parameter.end(); ++itP )
//     {
//         CmMemoryDescriptor paramD = *itP;
//         m_PyFile << format("%|8t|%1% = self.%1%") % paramD.name << '\n';
//     }
//     m_PyFile << '\n';

    //Dissect the state vector into individual, local state variables.
    m_PyFile << format("%|8t|#Dissect the state vector into individual, local state variables.") << '\n';
    CmMemoryTable::const_iterator itV;
    for( itV = m_FlatProcess.variable.begin(); itV != m_FlatProcess.variable.end(); ++itV )
    {
        CmMemoryDescriptor varD = *itV;
        if( varD.isStateVariable == false ) { continue; }

        string varName = m_PythonName[varD.name];
        string index = m_StateVectorMap[varD.name]; //look up variable's index in the state vector.
        m_PyFile << format("%|8t|%1% = y[%2%]") % varName % index << '\n';
    }
    m_PyFile << '\n';

    //Create the return vector
    m_PyFile << format("%|8t|#Create the return vector (the time derivatives dy/dt).") << '\n';
    m_PyFile << format("%|8t|y_t = zeros(%1%, Float)") % m_StateVectorSize << '\n';
    m_PyFile << '\n';

    //write a line to compute each algebraic variable
    m_PyFile << format("%|8t|#Compute the algebraic variables.") << '\n';
    CmEquationTable::const_iterator itE;
    for( itE = m_FlatProcess.equation.begin(); itE != m_FlatProcess.equation.end(); ++itE )
    {
        CmEquationDescriptor equnD = *itE;
        if( equnD.isOdeAssignment() ) { continue; } //only algebraic variables
        string algebVar = m_PythonName[equnD.lhs.path()];
        string mathExpr = m_toPy.convert( equnD.rhs);
        m_PyFile << format("%|8t|%1% = %2%") % algebVar % mathExpr << '\n';
    }

    //write a line to compute the time derivative of each integrated variable
    m_PyFile << format("%|8t|#Compute the state variables. (Really the time derivatives.)") << '\n';
    for( itE = m_FlatProcess.equation.begin(); itE != m_FlatProcess.equation.end(); ++itE )
    {
        CmEquationDescriptor equnD = *itE;
        if( !equnD.isOdeAssignment() ) { continue; } //only state variables
        string simlVarName = equnD.lhs.path().toString();
        string mathExpr = m_toPy.convert( equnD.rhs);
        string index = m_StateVectorMap[equnD.lhs.path()]; //look up variable's index in state vector
        m_PyFile << format("%|8t|y_t[%1%] = %2% # = d %3% /dt ") % index % mathExpr % simlVarName << '\n';
    }
    m_PyFile << '\n';

    //return the result
    m_PyFile << format("%|8t|return y_t") << '\n';
    m_PyFile << '\n';
}


/*!
Allocate space for each state variable in the state vector and result array.
The state variable have the same indices in both arrays.

The function changes:
m_StateVectorMap, state_vector_ordering??, m_StateVectorSize,
m_ResultArrayMap, result_array_ordering??, m_ResultArrayColls.
*/
void siml::PyProcessGenerator::layoutArrays()
{
    m_StateVectorMap.clear(); /*state_vector_ordering.clear();*/ m_StateVectorSize=0;
    m_ResultArrayMap.clear(); /*result_array_ordering.clear();*/ m_ResultArrayColls=0;

    //loop over all variables and assign indices for the _state_ variables
    //each state variable gets a unique index in both arrays: state vector, result array.
    CmMemoryTable::const_iterator itV;
    uint currIndex=0;
    for( itV = m_FlatProcess.variable.begin(); itV != m_FlatProcess.variable.end(); ++itV )
    {
        CmMemoryDescriptor varD = *itV;
        if( varD.isStateVariable == false ) { continue; }

        string currIndexStr = (format("%1%") % currIndex).str(); //convert currIndex to currIndexStr
//         string varNameStr = varD.name.toString();
        m_StateVectorMap[varD.name] = currIndexStr;
        m_ResultArrayMap[varD.name] = currIndexStr;
/*        state_vector_ordering.push_back(varD.name);
        result_array_ordering.push_back(varD.name);*/
        ++currIndex;
    }
    m_StateVectorSize = currIndex;

    //Loop over all variables again and assign indices for the _algebraic_ variables.
    //Each algebraic variable gets a unique index in the result array.
    //The algebraic variables come after the state variables in the result array
    for( itV = m_FlatProcess.variable.begin(); itV != m_FlatProcess.variable.end(); ++itV )
    {
        CmMemoryDescriptor varD = *itV;
        if( varD.isStateVariable == true ) { continue; }

        string currIndexStr = (format("%1%") % currIndex).str(); //convert currIndex to currIndexStr
        string varNameStr = varD.name.toString();
        m_ResultArrayMap[varD.name] = currIndexStr;
/*        result_array_ordering.push_back(varD.name);*/
        ++currIndex;
    }
    m_ResultArrayColls = currIndex;
}


/*!
Create maping between Siml path and Python variable name.
@todo check if names are duplicate and alter them
*/
void siml::PyProcessGenerator::createPyVarNames()
{
    CmMemoryTable::const_iterator itMem;
    //loop over all parameters and create Python expressions to access them
    for( itMem = m_FlatProcess.parameter.begin(); itMem != m_FlatProcess.parameter.end(); ++itMem )
    {
        CmMemoryDescriptor const & mem = *itMem;
        //expressions for access in function bodies
        string pyName = "self.p_" + mem.name.toString( "_"); //eg.: "self.p_r1_d" - member variable
        m_PythonName[mem.name] = pyName;
        //names as parameters of a set* function (for gegenSetParameters())
        string setParamName = mem.name.toString( "_"); //eg.: "r1_d" - exchange "." with "_"
        m_funcArgName[mem.name] = setParamName;
    }

    //loop over all variables and create Python expressions to access them
    for( itMem = m_FlatProcess.variable.begin(); itMem != m_FlatProcess.variable.end(); ++itMem )
    {
        CmMemoryDescriptor const & mem = *itMem;
        //expressions for access in function bodies
        string pyName = "v_" + mem.name.toString( "_"); //eg.: "v_r1_d" - local variable
        m_PythonName[mem.name] = pyName;
//         //names as parameters of a set* function
//         string setParamName = mem.name.toString( "_"); //eg.: "r1_d" - exchange "." with "_"
//         m_funcArgName[mem.name] = setParamName;
    }
}


/*!
Generate a function that computes the algebraic variables again after the simulation,
so they can be examined too. Only state variables are stored doring ODE simulation.
*/
void siml::PyProcessGenerator::genOutputEquations()
{
    m_PyFile <<
            "    def _outputEquations(self, stateResult):\n"
            "        \"\"\"\n"
            "        Compute (again) the algebraic variables as functions of the state \n"
            "        variables. All variables are then stored together in a 2D array.\n"
            "        \"\"\"\n"
            "        \n";

    //compute size of result array
    m_PyFile << format("%|8t|#compute size of result array\n");
    m_PyFile << format("%|8t|#assert shape(stateResult)[0] == size(self.time) #not true for steady state\n");
    m_PyFile << format("%|8t|dimRes = size(shape(stateResult))\n");
    m_PyFile << format("%|8t|if dimRes == 1:       \n");
    m_PyFile << format("%|8t|    sizeTime = 1\n");
    m_PyFile << format("%|8t|else:\n");
    m_PyFile << format("%|8t|    sizeTime = shape(stateResult)[0]\n\n");

    //create the result array
    m_PyFile << format("%|8t|#create the result array\n");
    m_PyFile << format("%|8t|resultArray = zeros((sizeTime, %1%), Float)\n") % m_ResultArrayColls;
    //copy the state variables into the result array
    m_PyFile << format("%|8t|#copy the state variables into the result array\n");
//     m_PyFile << format("%|8t|numStates = shape(stateResult)[1]") << '\n';
    m_PyFile << format("%|8t|resultArray[:,0:self._numStates] = stateResult;\n");
    m_PyFile << '\n';

//     //Create local variables for the parameters.
//     m_PyFile << format("%|8t|#Create local variables for the parameters.") << '\n';
//     CmMemoryTable::const_iterator itP;
//     for( itP = m_Parameter.begin(); itP != m_Parameter.end(); ++itP )
//     {
//         CmMemoryDescriptor paramD = *itP;
//         m_PyFile << format("%|8t|%1% = self.%1%") % paramD.name << '\n';
//     }
//     m_PyFile << '\n';

    //Create local state variables - take them from the result array.
    m_PyFile << format("%|8t|#Create local state variables - take them from the result array.") << '\n';
    CmMemoryTable::const_iterator itV;
    for( itV = m_FlatProcess.variable.begin(); itV != m_FlatProcess.variable.end(); ++itV )
    {
        CmMemoryDescriptor varD = *itV;
        if( varD.isStateVariable == false ) { continue; } //only state variables

        string pyName = m_PythonName[ varD.name];    //look up variable's Python name
        string index = m_ResultArrayMap[ varD.name]; //look up variable's index
        m_PyFile << format( "%|8t|%1% = resultArray[:,%2%]") % pyName % index << '\n';
    }
    m_PyFile << '\n';

    //compute the algebraic variables from the state variables.
    m_PyFile << format( "%|8t|#Compute the algebraic variables from the state variables.") << '\n';
    CmEquationTable::const_iterator itE;
    for( itE = m_FlatProcess.equation.begin(); itE != m_FlatProcess.equation.end(); ++itE )
    {
        CmEquationDescriptor equnD = *itE;
        if( equnD.isOdeAssignment() ) { continue; }

        string algebVar = equnD.lhs.toString();
        string index = m_ResultArrayMap[ equnD.lhs.path()];
        string mathExpr = m_toPy.convert( equnD.rhs);
        m_PyFile << format( "%|8t|resultArray[:,%1%] = %2% # = %3%") % index % mathExpr % algebVar << '\n';
    }
    m_PyFile << '\n';

    m_PyFile << format( "%|8t|return resultArray\n\n");
}

