#!/usr/bin/python

#Main program for the simulator scripts

from testproc import *
# execfile('testproc.py')

simConti = Conti()
simConti.simulate()
simConti.graph('r.X r.S')

simBatch = Batch()
simBatch.simulate()
simBatch.graph('r.X r.S')

##sim.simulate()
##sim.graph('r.X r.S')
