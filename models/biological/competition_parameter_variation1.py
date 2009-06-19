#!/usr/bin/env python

#Lotka and Volterra's model of competition of two species. (Not Predator-Prey)
#
#                   --- Do parameter variations ---
#
#
# This is a simple model of competition of two species in a biological system.
# The species compete for some common resource, which is not explicitly
# mentioned in the equations.
# The differential equations were proposed by Alfred J. Lotka and Vito Volterra.
#
#See:
#   http://en.wikipedia.org/wiki/Lotka-Volterra_inter-specific_competition_equations
#   Leah Edelstein-Keshet; Mathematical Models in Biology; 1988.
#       (republished by SIAM 2005) pp. 224.
#

from __future__ import division
#import library functions
from pylab import plot, show, figure, xlabel, ylabel, legend, title, autumn,\
                  hot, cm
from numpy import array, linspace, logspace, hstack
#import the compiled simulation objects
from competition import Case3, Case4


#Case 3 ----------------------------------------------
#vary the growth rate of organism 1
model = Case3() #create a simulation object instance
figure() #create new figure window
#create some values for the growth rate of organism 1
r1_vals = linspace(0.5, 3, 10)
max_i = len(r1_vals)-1

#do simulations with the different parameter values, plot results
for i, r1 in enumerate(r1_vals):
    model.init_r1(r1)         #Use alternative initialization function to supply parameter
    model.simulateDynamic()   #solve ODE
    res = model.getResults()  #get results as a storage.DictStore object
    color_tuple = cm.jet(i/max_i)
    label_str = 'r1=%g' % r1 #create descriptive string
    plot(res['time'], res['m.N1'], label='N1: '+label_str, color=color_tuple, linestyle='-')
    plot(res['time'], res['m.N2'], label='N2: '+label_str, color=color_tuple, linestyle='--')

#finishing touches on plot
xlabel('time')
ylabel('N1, N2')
legend()
title('Competition of two species; case 3.')



#Case 4 ----------------------------------------------
#vary the growth rate of organism 1
model = Case4() #create a simulation object instance
figure() #create new figure window
#create some values for the growth rate of organism 1
r1_vals = linspace(0.3, 5, 10)
max_i = len(r1_vals)-1

#do simulations with the different parameter values, plot results
for i, r1 in enumerate(r1_vals):
    model.init_r1(r1)         #Use alternative initialization function to supply parameter
    model.simulateDynamic()   #solve ODE
    res = model.getResults()  #get results as a storage.DictStore object
    color_tuple = cm.jet(i/max_i)
    label_str = 'r1=%g' % r1 #create descriptive string
    plot(res['time'], res['m.N1'], label='N1: '+label_str, color=color_tuple, linestyle='-')
    plot(res['time'], res['m.N2'], label='N2: '+label_str, color=color_tuple, linestyle='--')

#finishing touches on plot
xlabel('time')
ylabel('N1, N2')
legend()
title('Competition of two species; case 4.')

#show the graph (enter display loop)
show()
