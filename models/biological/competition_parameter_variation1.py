#!/usr/bin/env python

#Lotka and Volterra's model of competition of two species.
#Do parameter variations

#import library functions
from pylab import plot, show, figure, xlabel, ylabel, legend, title, autumn,\
                  hot, cm
from numpy import array, linspace, logspace, hstack
#import the compiled simulation objects
from competition import Case1, Case2, Case3, Case4

lsp = linspace

#Case 3 ----------------------------------------------
#vary the growt rate of organism 1
mo = Case3() #create a simulaton object instance
figure() #create new figure window
hot()
#create a couple of initial values for x and y
r1Vals = linspace(0.5, 3, 10)
col =    linspace(0, 1, 10)

#do simulations with the different parameter values, and put the results into a
#phase-plane plot
for i in range(len(r1Vals)):
    #initialize the simulation object, override some of the parameter values
    mo.initialize('m.r1', r1Vals[i],
                  'N1_init', 1,
                  'N2_init', 2,
                  'solutionParameters.simulationTime', 20,
                  'showGraph', 0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    colorStr = cm.jet(col[i])
    labelStr = 'r1=%g' % (r1Vals[i]) #create descriptive string
    plot(res['time'], res['m.N1'], label='N1: '+labelStr, color=colorStr, linestyle='-')
    plot(res['time'], res['m.N2'], label='N2: '+labelStr, color=colorStr, linestyle='--')

#finishing touches on plot
xlabel('time')
ylabel('N1, N2')
legend()
title('Competition of two species; case 3.')



#Case 4 ----------------------------------------------
#vary the growt rate of organism 1
mo = Case4() #create a simulaton object instance
figure() #create new figure window
hot()
#create a couple of initial values for x and y
r1Vals = linspace(0.3, 5, 10)
col =    linspace(0, 1, 10)

#do simulations with the different parameter values, and put the results into a
#phase-plane plot
for i in range(len(r1Vals)):
    #initialize the simulation object, override some of the parameter values
    mo.initialize('m.r1', r1Vals[i],
                  'N1_init', 1,
                  'N2_init', 2,
                  'solutionParameters.simulationTime', 20,
                  'showGraph', 0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    colorStr = cm.jet(col[i])
    labelStr = 'r1=%g' % (r1Vals[i]) #create descriptive string
    plot(res['time'], res['m.N1'], label='N1: '+labelStr, color=colorStr, linestyle='-')
    plot(res['time'], res['m.N2'], label='N2: '+labelStr, color=colorStr, linestyle='--')

#finishing touches on plot
xlabel('time')
ylabel('N1, N2')
legend()
title('Competition of two species; case 4.')

show()
