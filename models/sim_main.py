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

#import the commands for starting programs and such.
import os
#manipulate the current directory because Eric does not set it up propperly
os.getcwd() 
##os.chdir('/home/eike/codedir/freeode/trunk/models') #put your model directory here

#run the compiler
(inp, msg) = os.popen4('/home/eike/codedir/freeode/trunk/freeode_cpp/debug/src/siml bioreactor.siml')
print msg.read(); inp.close(); msg.close();
#import the generated simulation script(s) - no typing of bioreactor.Conti required
from bioreactor import *

#Perform dynamic simulation. Batch reactor.
if 0:
    simBatch = Batch()
    simBatch = Batch()
    simBatch.simulateDynamic()
    simBatch.graph('r.X r.S')
    simBatch.graph('r.mu')

#Perform dynamic simulation. Continuous reactor.
if 1:
    simConti = Conti()
    simConti.simulateDynamic()
    simConti.graph('r.X r.S')
    simConti.graph('r.mu')

#Perform steady state simulation (clumsy). Continuous reactor.
if 1:
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
