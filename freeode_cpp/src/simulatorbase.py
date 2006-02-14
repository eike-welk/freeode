

from scipy import * # Also includes Numeric.
import Gnuplot, Gnuplot.funcutils # @todo switch to a more well known graphics library


class SimulatorBase:
    """ Base class for the generated simulator classes """

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
            return self.resultArray
        index = self.resultArrayMap[varName]
        return self.resultArray[:,index]

    def graph(self, varNames):
        """
        Show one or several variables in a graph.

        Parameters:
           varNames: String with a list of variables to be plotted. (Space or comma seperated.)
                     e.g.: 'X mu'
        """

        diagram=Gnuplot.Gnuplot(debug=0, persist=1)
        diagram('set data style lines')
        diagram.title(varNames)
        diagram.xlabel('Time')

        varList = varNames.replace(',', ' ').split(' ')
        for varName1 in varList:
            if not (varName1 in self.resultArrayMap): continue
            curve=Gnuplot.Data(self.get('time'), self.get(varName1))
            diagram.replot(curve)

    def simulate(self):
        """
        This function performs the simulation.
        """

        self.time = linspace(0.0, self.simulationTime, self.simulationTime/self.reportingInterval + 1) #note: no rounding is better, linspace is quite smart.
        y = integrate.odeint(self._diffStateT, self.initialValues, self.time)
        self._outputEquations(y)


