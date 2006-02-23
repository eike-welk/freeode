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
(inp, msg) = os.popen4('/home/eike/codedir/freeode/trunk/freeode_cpp/debug/src/siml spring_simple.siml')
print msg.read(); inp.close(); msg.close(); #print compiler's output

#import the generated simulation script(s) - no typing of bioreactor.Conti required this way
from spring_simple import *


if 1: 
    #Perform dynamic simulation. Batch reactor.
    simMech = Step()
    simMech.simulateDynamic()
    simMech.graph('s.x s.v')


    

