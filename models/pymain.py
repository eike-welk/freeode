#!/usr/bin/python

#Main program for the simulator scripts

from testprogram import *
#from bioreactor1 import *

# execfile('testprogram.py')

simBatch = Batch()
simBatch.simulate()
simBatch.graph('r.X r.S')
simBatch.graph('r.mu')

simConti = Conti()
simConti.simulate()
simConti.graph('r.X r.S')
simConti.graph('r.mu')

##sim.simulate()
##sim.graph('r.X r.S')
