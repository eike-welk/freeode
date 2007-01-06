############################################################################
#    Copyright (C) 2006 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################
__doc__ = \
'''
Basic infrastructure for the generated simulator classes.

This file is imported by the generated simulation programs,
and not by the Siml compiler.
'''


#from numpy import *
from pylab import *

import scipy.integrate.ode as odeInt
import scipy.optimize.minpack as minpack

#from scipy import integrate
import Gnuplot, Gnuplot.funcutils # @todo switch to a more well known graphics library

class SimulatorBase(object):
    """ Base class for the generated simulator classes """
    #TODO: think about separate data storage object.

    def __init__(self):
        self.variableNameMap = {}
        '''Maping between variable (siml) name and index in the result array'''
        self.parameterNameMap = {}
        '''Maping between parameter (siml) name and (data member, python name)???'''
        self.p_solutionParameters_simulationTime = 100.0
        '''Duration of the simulation. Built in parameter.'''
        self.p_solutionParameters_reportingInterval = 1.0
        '''Interval at which the simulation results are recorded.
           Built in parameter.'''
        self.time = None
        '''Array with times at which the solution was computed.'''
        self.resultArray = None
        '''Array with the simulation results'''
        self.initialValues = None
        '''Array with the initial values of the state variables.'''
        self.stateVectorLen = None
        '''Length of the state vector'''
        self.algVectorLen = None
        '''Length of vector that contains the algebraic variables'''


    def help(self):
        """Show the simulation object's documentation."""
        help(self.__class__)

    #TODO: change to: helpAttributes(self), also help about parameter names
    def helpVariables(self):
        """Show list of all variables."""
        for i in self.variableNameMap:
            print "'%s', " % i,
        print


    def clear(self):
        """
        Delete the results. Use prior to simulateSteadyState().
        """
        if hasattr(self, 'time'):
            del self.time
        if hasattr(self, 'resultArray'):
            del self.resultArray

    #TODO: change to: attribute(self, attrName), also return parameters
    def variable(self, varName):
        """
        Get a variable by name.

        The funcion returns a vector with the variable's values at all
        simulated points in time. Parameter values can not be accessed by
        this function.
        Parameter:
        varName:    Text string with the variable name as it would appear in
                    the Siml language.
                    There are special variable names:
                        'time': vector of simulated points in time
                        'all': array of all variables
        Example:
            >>> mySimulationObject.variable('r.X')
        """
        if varName == 'time':
            return self.time
        elif varName == 'all':
            return self.resultArray
        index = self.variableNameMap[varName]
        return self.resultArray[:,index]


    def graph(self, varNames):
        """
        Show one or several variables in a graph.

        The X-axis is always the time, the specified variables appear on the
        Y-Axis.
        Arguments:
            varNames :  Text string with a list of variables to be plotted.
                        (Space or comma separated.) e.g.: 'r.X r.mu'
        """
        #self._graphGnuplot(varNames)
        self._graphMatPlotLib(varNames)


    def _graphGnuplot(self, varNames):
        '''Create plots with gnuplot. Called by graph()'''
        diagram=Gnuplot.Gnuplot(debug=0, persist=1)
        diagram('set data style lines')
        diagram.title(varNames)
        diagram.xlabel('Time')

        varList = varNames.replace(',', ' ').split(' ')
        for varName1 in varList:
            if len(varName1) == 0:
                continue
            if not (varName1 in self.variableNameMap):
                print('Error unknown variable name: %s') % varName1
                continue
            curve=Gnuplot.Data(self.variable('time'), self.variable(varName1))
            diagram.replot(curve)


    def _graphMatPlotLib(self, varNames):
        '''Create plots with matplotlib. Called by graph()'''
        figure() #create new figure window

        timeVect = self.variable('time')
        varList = varNames.replace(',', ' ').split(' ')
        for varName1 in varList:
            if len(varName1) == 0:
                continue
            if not (varName1 in self.variableNameMap):
                print('Error unknown variable name: %s') % varName1
                continue
            varVect = self.variable(varName1)
            plot(timeVect, varVect, label=varName1)

        xlabel('time')
        #ylabel(varNames)
        legend()


    def initialize(self):
        '''
        Compute the initial values.
        Dummy function; must be reimplemented in derived classes!
        '''
        pass


    def dynamic(self, t, y, returnAlgVars=False):
        '''
        Compute time derivative of state variables.
        This function will be called by the solver repeatedly.
        Dummy function; must be reimplemented in derived classes!
        '''
        pass


    def final(self): 
        ''' 
        Display and save simulation results. 
        This function will be called once; after the simulation results 
        have been computed. 
        Dummy function; must be reimplemented in derived classes!
        ''' 
        pass
    
    
#    def outputEquations(self, y):
#        '''
#        Compute the algebraic variable from the state variables.
#        Dummy function; must be reimplemented in derived classes!
#        '''
#        pass


    def simulateDynamic(self):
        """
        Perform a dynamic simulation.

        The results can be displayed with the graph(...) function.
        The funcion variable(...) returns the simulation result of a speciffic
        variable as a vector.
        """
        #Compute the initial values if necessary.
        if not self.initialValues:
            self.initialize()
        #create the array of output time points. Note: no rounding is better
        self.time = linspace(0.0, self.p_solutionParameters_simulationTime,
                             self.p_solutionParameters_simulationTime/
                             self.p_solutionParameters_reportingInterval + 1)
        #Create space for storing simulation results
        #dim 1: time; dim 2: the different variables
        #-> vector of variables (state and algebraic) lies horizontally
        self.resultArray = zeros((len(self.time),
                                  self.stateVectorLen + self.algVectorLen),
                                 'float64')
        self.resultArray[0,0:self.stateVectorLen] = self.initialValues
        #create integrator object and care for intitial values
        solver = odeInt(self.dynamic).set_integrator('vode') \
                                     .set_initial_value(self.initialValues,
                                                        self.time[0])
        #compute the numerical solution
        i=1
        while solver.successful() and i < len(self.time):
            #do time step
            solver.integrate(self.time[i])
            #save state vars (and time)
            self.time[i] = solver.t #in case solver does not hit end time
            self.resultArray[i,0:self.stateVectorLen] = solver.y
            #compute algebraic variables (again)
            self.resultArray[i,self.stateVectorLen:] = \
                    self.dynamic(solver.t, solver.y, returnAlgVars=True)
            i += 1
        #generate run time error
        if not solver.successful():
            print 'error: simulation was terminated'
            #return
        #run final function
        self.final()


    def simulateSteadyState(self):
        """
        Perform a stady state simulation.

        Call self.clear() before using this method!

        This function computes one steady state solution, of the system of
        differential equations. Which solution of the potentially many solutions
        is found, depends on the initial guess. A steady state solution is a
        vector of all variables. This vector is appended to the array of results.
        Usually one will compute a series of stady state solutions, each with
        slightly different parameters.

        Initial guess: When there are no prior results, the initial values are
        (ab)used as an initial guess; otherwise the latest results are used as
        the initial guess.
        In the time array the count of current simulation is stored. This way the
        graph function still produces useful graphs with steady state simulations.

        The final results can be displayed with the graph(...) function.
        The funcion variable(...) returns the simulation result of a speciffic
        variable as a vector.
        """

        raise Exception('This method is currently broken!')

        #TODO: Use flag self._isSteadyStateStart instead of self.time
        if not hasattr(self, 'time'):
            #this is the first call in a row of steady state simulations - setup everything
            lastResult = -1
            self.resultArray = array([[0]], 'float64')
            self.time = array([0], 'float64')
            self.initialize()    #initial guess for root finder: initial values abused
            x0 = self.initialValues
            t0 = -1
        else:
            lastResult = shape(self.resultArray)[0]-1
            x0 = self.resultArray[lastResult, 0:self.stateVectorLen] #initial guess for root finder: last result
            t0 = self.time[lastResult]

        #compute the state variables of the steady state solution
        (xmin, msg) = minpack.leastsq(self.dynamic, x0, (t0)) #funcion will also report local minima that are no roots. Caution!
##        xmin = optimize.fsolve(self.dynamic, x0, (0)) #function is always stuck in one (the trivial) minimum
        #also compute the algebraic variables
        currRes = self.outputEquations(xmin)
        #expand the storage and save the results
        self.resultArray = resize(self.resultArray,
                                  (lastResult+2,
                                   self.stateVectorLen + self.algVectorLen))
        self.resultArray[lastResult+1,:] = currRes[0,:]
        self.time = resize(self.time, (lastResult+2,))
        self.time[lastResult+1] = t0 + 1


