#!/usr/bin/python
#-------------------------------------------------------------------------------
# Example: simulation main script
#
# This is the main script for development of a simulation program with the Siml 
# compiler. This script calls the compiler and also executes the generated 
# simulation program. 
# For the script to work, the Siml compiler has to be installed.
#-------------------------------------------------------------------------------
#export PATH=$PATH:"codedir/freeode/trunk/freeode_cpp/debug/src"
#os.popen3()
#os.system()

#import the commands for starting programs and manipulating directories.
import os
#manipulate the current directory if necessary
##print os.getcwd() #see in what directory you are
##os.chdir('/home/eike/codedir/freeode/trunk/models') #put your model directory here

#run the compiler 
(inp, msg) = os.popen4('/home/eike/codedir/freeode/trunk/freeode_cpp/debug/src/siml bioreactor.siml')
print msg.read(); inp.close(); msg.close(); #print compiler's output

#import the generated simulation script(s) - no typing of bioreactor.Conti required this way
from bioreactor import *


if 0: 
    #Perform dynamic simulation. Batch reactor.
    simBatch = Batch()
    simBatch = Batch()
    simBatch.simulateDynamic()
    simBatch.graph('r.X r.S')
    simBatch.graph('r.mu')

    
if 1:
    #Perform dynamic simulation. Continuous reactor.
    simConti = Conti()
    simConti.simulateDynamic()
    simConti.graph('r.X r.S')
    simConti.graph('r.mu')


if 1:
    #Perform steady state simulation (clumsy). Continuous reactor.
    simConti = Conti()
    #Define range of dilution rates that will be tried
    D_start = 0.02
    D_end   = 0.4
    D_num   = 40
    #Put initial guess into the simulation object (only used for 
    #the first computation)
    simConti.setParameters( X_init=10, S_init=0)
    simConti.clear()
    #Compute series of steady state solutions
    dVals = linspace(D_start, D_end, D_num)
    for newD in dVals:
        simConti.setParameters( D=newD)
        simConti.simulateSteadyState()
    #Display results of steady state simulation
    simConti.time = dVals
    simConti.graph('r.X r.S')
    simConti.graph('r.STY')
