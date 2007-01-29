############################################################################
#    Copyright (C) 2007 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
#                                                                          #
#    License: LGPL                                                         #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU Library General Public License as       #
#    published by the Free Software Foundation; either version 2 of the    #
#    License, or (at your option) any later version.                       #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU Library General Public     #
#    License along with this program; if not, write to the                 #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

'''
Basic infrastructure for the generated simulator classes.

This file is imported by the generated simulation programs,
and not by the Siml compiler.
'''



from numpy import array, linspace, zeros, shape, ones, resize
from pylab import figure, xlabel, plot, legend, title, show
import scipy.integrate.ode as odeInt
import scipy.optimize.minpack as minpack

from freeode.storage import DictStore

##try to import the gnuplot lib 
#try:
#    import Gnuplot, Gnuplot.funcutils 
#    exist_gnuplot_lib = True
#except:
#    exist_gnuplot_lib = False



class SimulatorBase(object):
    """ Base class for the generated simulator classes """
    #TODO: think about separate data storage object.

    def __init__(self):
        self.variableNameMap = {}
        '''Maping between variable (siml) name and index in the result array'''
        self.parameterNameMap = {} #TODO: attribute is currently unused
        '''Maping between parameter (siml) name and (data member, python name)???'''
        self.p_solutionParameters_simulationTime = 100.0
        '''Duration of the simulation. Built in parameter.'''
        self.p_solutionParameters_reportingInterval = 1.0
        '''Interval at which the simulation results are recorded.
           Built in parameter.'''
        self.defaultFileName = 'error-no-file-name-given.csv'
        '''Default file name for storing simulation results. 
           Set by generated simulator class'''
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

    def info(self):
        """Show list of all variables."""
        print 'Variables:'
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

    def getAttribute(self, attrName):
        """
        Get an attribute by name.

        The funcion returns a vector with the attribute's values at all
        simulated points in time. Parameter values can not be accessed by
        this function.
        Arguments:
        varName:    Text string with the attribute name as it would appear in
                    the Siml language.
                    There are special attribute names:
                        'time': vector of simulated points in time
                        'all': array of all attributes
        Example:
            >>> mySimulationObject.getAttribute('r.X')
        """
        #TODO: also return parameters
        if attrName == 'time':
            return self.time
#        elif attrName == 'all':
#            return self.resultArray
        index = self.variableNameMap[attrName]
        return self.resultArray[:,index]

    def save(self, fileName=None):
        '''
        Save the simulation results to disk.
        If no filename is given, self.defaultFileName is used
        '''
        if fileName == None:
            fileName = self.defaultFileName
        result = self.getResults()
        result.save(fileName)
        
    def getResults(self):
        '''Return the simulation results in a DictStore object'''
        result = DictStore()
        #put Variables into DictStore
        for name in self.variableNameMap.keys():
            result[name] = self.getAttribute(name)
        #TODO: also include parameters
        return result
            
    def graph(self, varNames, titleStr=None):
        """
        Show one or several attributes in a graph.

        The X-axis is always the time, the specified attributes appear on the
        Y-Axis.
        Arguments:
            varNames :  list of strings of the attributes to be plotted.
                        example: ['r.X', 'r.mu']
        """
        #self._graphGnuplot(varNames)
        self._graphMatPlotLib(varNames, titleStr)

#    def _graphGnuplot(self, varNames):
#        '''Create plots with gnuplot. Called by graph()'''
#        diagram=Gnuplot.Gnuplot(debug=0, persist=1)
#        diagram('set data style lines')
#        diagram.title(varNames)
#        diagram.xlabel('Time')
#
#        #varList = varNames.replace(',', ' ').split(' ')
#        for varName1 in varList:
#            if len(varName1) == 0:
#                continue
#            if not (varName1 in self.variableNameMap):
#                print('Error unknown variable name: %s') % varName1
#                continue
#            curve=Gnuplot.Data(self.variable('time'), self.variable(varName1))
#            diagram.replot(curve)


    def _graphMatPlotLib(self, varList, titleStr=None):
        '''Create plots with matplotlib. Called by graph()'''
        figure() #create new figure window

        timeVect = self.getAttribute('time')
        #varList = varNames.replace(',', ' ').split(' ')
        for varName1 in varList:
            if len(varName1) == 0:
                continue
            if not (varName1 in self.variableNameMap):
                print('Error unknown attribute name: %s') % varName1
                continue
            varVect = self.getAttribute(varName1)
            plot(timeVect, varVect, label=varName1)

        xlabel('time')
        #ylabel(varNames)
        if titleStr != None:
            title(titleStr)
        legend()


    def _createParamOverrideDict(self, argList, kwArgDict):
        '''
        Create a dict of parameter-name, value pairs; that are used by init
        to override the values from the SIML program.
        The method is called by self.initialize(...)
        arguments:
            argList   : list from *args of initialize() function
            kwArgDict : dict from **args of initialize() function
        returns:
            dict looking like this: {'g':10.81, 'm1.p1':23.23}
        '''
        #kwArgDict: every parameter name without dot is permissible        
        ovrDict = kwArgDict
        #care for argList
        i = 0
        while i < len(argList):
            arg = argList[i]
            #argument is a dict. Put values into override dict
            if isinstance(arg, dict):
                ovrDict.update(arg)
            #suppose that argument is a string and next argument a float number
            else:
                num = float(argList[i+1])
                ovrDict[str(arg)] = num
                i += 1
            i += 1
        return ovrDict
    
    
    def _overrideParam(self, paramName, overrideDict, originalValue):
        '''
        Replace the original parameter value from the SIML program
        with an other value; that is given when the program runs.
        arguments:
            paramName     : string, SIML name of parameter
            overrideDict  : dict with the new values: <name>: <value> pairs
            originalValue : float number, original value from SIML program
        returns:
            float number, either original value or value from overrideDict
        '''
        if paramName in overrideDict:
            return overrideDict[paramName]
        else:
            return originalValue
    
   
    def initialize(self, *args, **kwArgs):
        '''
        Compute the initial values.
        Dummy function; must be reimplemented in derived classes!
        arguments:
            *args    : two ways to specify parameter values are possible:
                       dict: initialize({'g':10.81})
                       parameter name followed by value: 
                       initialize('g', 10.81)
            **kwargs : parameter names without dot can be specified as 
                       keyword arguments: initialize(g=10.81)
        '''
        pass
        #ovd = self._createParamOverrideDict(args, kwArgs)
        #p_fnord = self._overrideParam('fnord', ovd, 23)


    def dynamic(self, t, y, returnAlgVars=False):
        '''
        Compute time derivative of state attributes.
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

        The results can be displayed with the graph(...) function and stored 
        with the store function. The funcion getAttributes(...) returns the 
        simulation result of a speciffic attribute.
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
        solver = (odeInt(self.dynamic).set_integrator('vode', nsteps = 5000) #IGNORE:E1102
                                     .set_initial_value(self.initialValues,  
                                                        self.time[0]))
        #compute the numerical solution
        i=1
        while solver.successful() and i < len(self.time):
            #do time step
            solver.integrate(self.time[i])
            #save state vars (and time)
            self.time[i] = solver.t #in case solver does not hit end time
            self.resultArray[i,0:self.stateVectorLen] = solver.y
            #compute algebraic variables (again)
            self.resultArray[i,self.stateVectorLen:] = (                   #IGNORE:E1111
                    self.dynamic(solver.t, solver.y, returnAlgVars=True))
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

        The results can be displayed with the graph(...) function and stored 
        with the store function. The funcion getAttributes(...) returns the 
        simulation result of a speciffic attribute.
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
        currRes = ones(4) #dummy to make pydev show no error
        #currRes = self.outputEquations(xmin)
        #expand the storage and save the results
        self.resultArray = resize(self.resultArray,
                                  (lastResult+2,
                                   self.stateVectorLen + self.algVectorLen))
        self.resultArray[lastResult+1,:] = currRes[0,:]
        self.time = resize(self.time, (lastResult+2,))
        self.time[lastResult+1] = t0 + 1



#---- simulator main function -------------------------------------------------
#The followin functions are for running the simulator as a standalone program

def secureShow():
    '''Show the graphs; but don't crash if no graphs exist.'''
    from matplotlib._pylab_helpers import Gcf
    if len(Gcf.get_all_fig_managers()) == 0:
        return
    show()
    
    
def runSimulations(simulationClassList):
    '''Instantiate simulation objects and run dynamic simulations'''
    if not isinstance(simulationClassList, list):
        simulationClassList = [simulationClassList]
    for simClass in simulationClassList:
        simObj = simClass()
        simObj.simulateDynamic()
        

def parseCommandLineOptions(simulationClassList):
    '''
    Parse the command line, and find out what the user wants from us.
    Argument:
        simulationClassList: list of (generated) simulation classes    
    '''
    import optparse
    import sys
    import freeode.ast as ast #for version string
        
    #set up parser for the command line aruments
    optPars = optparse.OptionParser(
                usage='%prog [<option>]',
                description='Simulation program. Run the contained simulations.', 
                version='%prog ' + ast.progVersion)
    
    optPars.add_option('-l', '--list', dest='list', 
                       action="store_true", default=False,
                       help='list the available simulations and exit', 
                       )
    optPars.add_option('-r', '--run', dest='run',
                       help='run the specified simulation. (number counts ' 
                          + 'from top of file; or special value "all" which ' 
                          + 'is equivalent to giving no options)',
                       metavar='<number>')
    optPars.add_option('-i', '--interactive', dest='interactive',
                       action="store_true", default=False,
                       help='go to interactive mode (defunct)')
    optPars.add_option('--prepend-newline', dest='prepend_newline',
                       action="store_true", default=False,
                       help='prepend output with one newline ' 
                          + '(usefull when started from the compiler)')
    #do the parsing
    (options, args) = optPars.parse_args()
    
    #print start message
    if options.prepend_newline:
        print
    print 'Freeode simulator, main function ...' 

    #test list option
    if options.list:
        print 'available simulations:'
        for i, sim in enumerate(simulationClassList):
            #get some usefull simulation name
            simStr = str(sim) #looks like: <class '__main__.Experiment1'>
            nameStart = simStr.find('.') + 1
            simName = simStr[nameStart:-2]
            #print number and simulation name
            print i, ': ', simName
        sys.exit(0) #exit successfully
        
    #user has said which simulation procedure should be run
    if options.run == 'all': #special argument 'all': -r all
        runSimulations(simulationClassList)
        show()
        sys.exit(0)
    elif options.run: #argument is int number: -r 2
        #test if argument is a number
        try: int(options.run)
        except: 
            optPars.error('option "-r": invalid number of simulation object: %s'
                          % options.run)
        #test if object with this number exists
        num = int(options.run)
        if num < 0 or num >= len(simulationClassList):
            optPars.error('option "-r": invalid number of simulation object: %d' 
                          % num)
        #run simulation
        runSimulations(simulationClassList[num])
        secureShow()
        sys.exit(0)
        
    #user wants to go into interactive mode
    if options.interactive:
        print 'interactive mode is not implemented yet'
        sys.exit(0)
        
    #default action: run all simulations
    #print 'Freeode (%s) main function ...' % ast.progVersion
    runSimulations(simulationClassList)
    secureShow()
    sys.exit(0)
    

def simulatorMainFunc(simulationClassList):
    '''
    Main function to run the simulation(s) as a stanalone program
    This function is called from the generated file's main routine
    Argument:
        simulationClassList: list of (generated) simulation classes
    '''
    #print 'Hello world; main function ...' 
    parseCommandLineOptions(simulationClassList)
    return



if __name__ == '__main__':
    # Self-testing code goes here.
    pass
