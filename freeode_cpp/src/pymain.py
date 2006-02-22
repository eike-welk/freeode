#!/usr/bin/python
# Main program for development of the Python part of
# the Siml compiler. The common base class is written 
# with the Eric IDE and then converted into a C++ string
# with "py2c_string.py".
# The generated Python Programs are tested with this script.
#
# This Program MUST be run in the "src" directory.  

import sys
sys.path.insert(0, '../models/')

from testprogram import *

# execfile('testprogram.py')

##simBatch = Batch()
##simBatch.simulateDynamic()
##simBatch.graph('r.X r.S')
##simBatch.graph('r.mu')

#Perform dynamic simulation.
simConti = Conti()
simConti.simulateDynamic()
simConti.graph('r.X r.S')
simConti.graph('r.mu')

#Perform steady state simulation (clumsy)
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


