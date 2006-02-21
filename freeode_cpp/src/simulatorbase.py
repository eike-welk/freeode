

from scipy import * # Also includes Numeric.
import Gnuplot, Gnuplot.funcutils # @todo switch to a more well known graphics library


class SimulatorBase:
    """ Base class for the generated simulator classes """

    def __init__(self):
         #Show if initial values have been computed
##        self._initialValuesDirty = True
        pass

    def clear(self):
        """
        Delete the time and the result array.
        """
        if hasattr(self, 'time'):
            del self.time
        if hasattr(self, '_resultArray'):
            del self._resultArray

    def get(self, varName):
        """
        Get a variable by name.

        @todo add returning multiple variables at once

        There are special variable names:
           'time': vector of times
           'all': array of all variables
        """
        if varName == 'time':
            return self.time
        elif varName == 'all':
            return self._resultArray
        index = self._resultArrayMap[varName]
        return self._resultArray[:,index]

    def graph(self, varNames):
        """
        Show one or several variables in a graph.

        Parameters:
           varNames: String with a list of variables to be plotted. (Space or comma seperated.)
                     e.g.: 'X mu'
            
        @todo there must be an error when the variable name is wrong.
        """

        diagram=Gnuplot.Gnuplot(debug=0, persist=1)
        diagram('set data style lines')
        diagram.title(varNames)
        diagram.xlabel('Time')

        varList = varNames.replace(',', ' ').split(' ')
        for varName1 in varList:
            if not (varName1 in self._resultArrayMap): 
                print('Error unknown variable name: %s') % varName1
                continue
                
            curve=Gnuplot.Data(self.get('time'), self.get(varName1))
            diagram.replot(curve)

    def simulateDynamic(self):
        """
        This function performs the simulation.
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
        self._outputEquations(y)

    def simulateSteadyState(self):
        """
        This function computes a steady state solution. And appends it to the 
        array of results. 
        Initial guess: When there are no prior results the initial valuse are
        (ab)used as a initial guess; otherwise the latest results are used as 
        the initial guess.
        In the time array the count of current simulation is stored. This way the 
        graph function still gives useful results with steady state simulations.
        """
        
        pass

        

