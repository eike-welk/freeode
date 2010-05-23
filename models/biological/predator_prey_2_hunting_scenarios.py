#!/usr/bin/env python
#    Copyright (C) 2009 by Eike Welk
#    eike.welk@gmx.net                                                     




#A modified predator prey model.
#
#                   --- Do parameter variations ---
#
#



from __future__ import division
#import library functions
from pylab import plot, show, figure, xlabel, ylabel, legend, title, autumn,\
                  hot, cm
from numpy import array, linspace, logspace, hstack
#import the compiled simulation objects
from predator_prey_2 import EnhancedModel


#Szenario: hunting is introduced and then abandoned ----------------------------------------------


def compute_scenario(hunting_rate_x, hunting_rate_y, duration):
    '''
    Compute multiple simulations with parameters taken from the arguments.
    Create graph that shows the simulation results one after the other.

    ARGUMENTS
    ---------
    hunting_rate_x:  list of hunting rates for species 1 (small fish)
    hunting_rate_y:  list of hunting rates for species 2 (predatory fish)
    duration:        list of duration for each simulation
    '''
    model = EnhancedModel() #create a simulation object instance
    figure() #create new figure window
    max_i = len(duration)-1

    x, y = 1, 0.1
    cum_duration = 0
    #do simulations with the different parameter values, plot results
    for i in range(len(duration)):
        model.init_hunting(hunting_rate_x[i], hunting_rate_y[i], x, y, duration[i])
        model.simulateDynamic()   #solve ODE
        res = model.getResults()  #get results as a storage.DictStore object
        color_tuple = cm.jet(i/max_i)
        #label_str = 'r1=%g' % r1 #create descriptive string
        label_str = 'hx: %g, hy: %g' % (hunting_rate_x[i], hunting_rate_y[i])
        plot(res['time'] + cum_duration, res['x'],
            label='x:     '+label_str, color=color_tuple, linestyle=':')
        plot(res['time'] + cum_duration, res['y'],
            label='y: ', color=color_tuple, linestyle='--')
        plot(res['time'] + cum_duration, res['hunting_yield'],
            label='yield: ', color=color_tuple, linestyle='-')
        #start next simulation with state values from previous simulation
        x = res['x'][-1]
        y = res['y'][-1]
        #cumulative duration to put the simulation's plots after each other
        cum_duration += duration[i]


    #finishing touches on plot
    xlabel('time')
    ylabel('x: prey, y: predators')
    legend()
    title('Predator prey with hunting')


#Strong hunting on prey. Predator numbers become really low, system takes
#long time to recover after hunting stops.
#Yield optimum around hunting_rate_x = 4 ... 4.7
hunting_rate_x = [0,   4.5,   0]
hunting_rate_y = [0,   0,   0]
duration       = [22, 100, 20]
compute_scenario(hunting_rate_x, hunting_rate_y, duration)

#Moderate hunting on both species. Number of both species relatively high
#while hunting. System recovers in a short time after hunting stops.
#Hunting yield is nearly as high as in strong hunting scenario.
hunting_rate_x = [0,   2,   0]
hunting_rate_y = [0,   0.2,   0]
duration       = [22, 100, 20]
compute_scenario(hunting_rate_x, hunting_rate_y, duration)

#must always be the last statement
show()

