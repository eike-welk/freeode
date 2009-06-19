#!/usr/bin/env python
#    Copyright (C) 2009 by Eike Welk
#    eike.welk@post.rwth-aachen.de




#A modified predator prey model.
#
#                   --- Create phase diagrams at different hunting rates ---
#
#



from __future__ import division
#import library functions
from pylab import (plot, show, figure, xlabel, ylabel, legend, title, autumn,
                  hot, cm)
from numpy import array, linspace, logspace, r_
#import the compiled simulation objects
from predator_prey_2 import EnhancedModel




def compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y):
    '''
    Compute multiple simulations with parameters taken from the arguments.
    Create graph that shows the simulation results one after the other.

    ARGUMENTS
    ---------
    hunting_rate_x:  hunting rate for species 1 (small fish)
    hunting_rate_y:  hunting rate for species 2 (predatory fish)
    duration:        list of duration for each simulation
    start_x:         list of start values for species 1
    start_y          list of start values for species 2
    '''
    model = EnhancedModel() #create a simulation object instance
    figure() #create new figure window

    max_i = len(duration)-1
    #do simulations with the different parameter values, plot results
    for i in range(len(duration)):
        model.init_hunting(hunting_rate_x, hunting_rate_y,
                           start_x[i], start_y[i], duration[i])
        model.simulateDynamic()   #solve ODE
        res = model.getResults()  #get results as a storage.DictStore object
        color_tuple = cm.jet(i/max_i)
        plot(res['x'], res['y'], color=color_tuple, linestyle='--')

    #TODO: plot field of arrows
    #quiver(X, Y, U, V, **kw)

    #finishing touches on plot
    xlabel('x - prey')
    ylabel('y - predators')
    legend()
    title('Predator prey with hunting - hx = %g, hy = %g' % (hunting_rate_x, hunting_rate_y))


#create phase diagram with no hunting
hunting_rate_x = 0
hunting_rate_y = 0
duration       = [100, 100, 100, 100]
start_x        = [0.1,   3,  19,  19]
start_y        = [0.1, 2.5,   2,   4]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#create phase diagram with moderate hunting
hunting_rate_x = 2
hunting_rate_y = 0.2
duration       = [ 100, 100, 100,   100]
start_x        = [  15,  15,  15,    15]
start_y        = [ 0.5, 1.3,   2,     4]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#create phase diagram with strong hunting
#yield optimum around hunting_rate_x = 4 .. 4.3 .. 4.7
hunting_rate_x = 4.5
hunting_rate_y = 0
duration       = [  100, 100, 100,  100]
start_x        = [    3,   3,   3,    1]
start_y        = [ 0.01, 0.1, 0.2, 0.01]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#must always be the last statement
show()

