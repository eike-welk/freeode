#!/usr/bin/python

#Main program for the simulator scripts

from testproc import *
# execfile('testproc.py')

sim = SimBio()
sim.simulate()
sim.graph('r.X r.S')

##sim.simulate()
##sim.graph('r.X r.S')
