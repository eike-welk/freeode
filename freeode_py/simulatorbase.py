

from scipy import * # Also includes Numeric.
import Gnuplot, Gnuplot.funcutils # @todo switch to a more well known graphics library


class SimulatorBase(object):
    """ Base class for the generated simulator classes """

    def __init__(self):
##        #Store if initial values have been computed
##        self._initialValuesDirty = True
        self._variableNameMap = {}
        '''Maping between variable (siml) name and index in the result array'''
        self._parameterNameMap = {}
        '''Maping between parameter (siml) name and (data member, python name)???'''
        self.simulationTime = 0.0
        self.reportingInterval = 0.0
        self.time = None
        self._resultArray = None
        
    def help(self):
        """Show the simulation objects documentation string."""
        help(self.__class__)

    def helpVariables(self):
        """Show list of all variables."""
        for i in self._variableNameMap: 
            print "'%s', " % i,
        print
    #TODO: add helpParameters, helpAttributes
    
    def clear(self):
        """
        Delete the results. Use prior to simulateSteadyState().
        """
        if hasattr(self, 'time'):
            del self.time
        if hasattr(self, '_resultArray'):
            del self._resultArray

    #TODO: write parameter, Attribute
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
            return self._resultArray
        index = self._variableNameMap[varName]
        return self._resultArray[:,index]

    def graph(self, varNames):
        """
        Show one or several variables in a graph.

        The X-axis is always the time, the specified variables appear on the 
        Y-Axis.
        Parameter:
        varNames:   Text string with a list of variables to be plotted. (Space or 
                    comma seperated.) e.g.: 'r.X r.mu'
        Example:
            >>> mySimulationObject.graph('r.X r.mu')
        """

        diagram=Gnuplot.Gnuplot(debug=0, persist=1)
        diagram('set data style lines')
        diagram.title(varNames)
        diagram.xlabel('Time')

        varList = varNames.replace(',', ' ').split(' ')
        for varName1 in varList:
            if not (varName1 in self._variableNameMap): 
                print('Error unknown variable name: %s') % varName1
                continue
                
            curve=Gnuplot.Data(self.variable('time'), self.variable(varName1))
            diagram.replot(curve)

    def setInitialValues(self):
        '''
        Compute the initial values. 
        Dummy function; must be reimplemented in derived classes!
        '''
        pass
    
    def _outputEquations(self, y):
        '''
        Compute the algebraic variable from the state variables.
        Dummy function; must be reimplemented in derived classes!
        '''
        pass
    
    def simulateDynamic(self):
        """
        Perform a dynamic simulation.
        
        The results can be displayed with the graph(...) function.
        The funcion variable(...) returns the simulation result of a speciffic
        variable as a vector.
        """

##        #The numerical integration changes the initial values, but the user maybe 
##        #wants to compute them in advance
##        if self._initialValuesDirty :
##            #Compute the initial values. (They are overwritten by integrate.odeint)
##            self._initialValues = self.setInitialValues()
##        self._initialValuesDirty = True;
        
        #Compute the initial values. (They are overwritten by integrate.odeint)
        initialValues = self.setInitialValues()
        #create the array of output time points
        self.time = linspace(0.0, self.simulationTime, self.simulationTime/self.reportingInterval + 1) #note: no rounding is better, linspace is quite smart.
        #compute the numerical solution
        y = integrate.odeint(self._diffStateT, initialValues, self.time)
        #compute the algebraic variables for a second time, so they can be shown in graphs.
        self._resultArray = self._outputEquations(y)

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
        
        #TODO: Use flag self._isSteadyStateStart instead of self.time
        if not hasattr(self, 'time'):
            #this is the first call in a row of steady state simulations - setup everything
            lastResult = -1
            self._resultArray = array([[0]], Float)
            self.time = array([0], Float)
            x0 = self.setInitialValues()    #initial guess for root finder: initial values abused
            t0 = -1
        else:
            lastResult = shape(self._resultArray)[0]-1
            x0 = self._resultArray[lastResult, 0:self._numStates] #initial guess for root finder: last result
            t0 = self.time[lastResult] 
        
        #compute the state variables of the steady state solution
        (xmin, msg) = optimize.leastsq(self._diffStateT, x0, (0)) #funcion will also report local minima that are no roots. Caution!
##        xmin = optimize.fsolve(self._diffStateT, x0, (0)) #function is always stuck in one (the trivial) minimum 
        #also compute the algebraic variables
        currRes = self._outputEquations(xmin)
        #expand the storage and save the results
        self._resultArray = resize(self._resultArray, (lastResult+2, self._numVariables))
        self._resultArray[lastResult+1,:] = currRes[0,:]
        self.time = resize(self.time, (lastResult+2,))
        self.time[lastResult+1] = t0 + 1


