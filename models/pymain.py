#!/usr/bin/python

#Main program for the simulator scripts

from testprogram import *
#from bioreactor1 import *

# execfile('testprogram.py')

##simBatch = Batch()
##simBatch.simulateDynamic()
##simBatch.graph('r.X r.S')
##simBatch.graph('r.mu')

simConti = Conti()
simConti.simulateDynamic()
simConti.graph('r.X r.S')
simConti.graph('r.mu')


