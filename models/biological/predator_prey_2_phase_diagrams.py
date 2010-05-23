#!/usr/bin/env python
#    Copyright (C) 2009 by Eike Welk
#    eike.welk@gmx.net                                                     




#A modified predator prey model.
#
#   --- Create phase diagrams at different hunting rates ---
#
#



from __future__ import division
#import library functions
from pylab import (plot, show, figure, xlabel, ylabel, legend, title, autumn,
                  hot, cm, quiver)
from numpy import array, linspace, r_, mgrid, zeros, amax, amin
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

    #max_i = len(duration)-1
    xmax, ymax = -1e100, -1e100
    xmin, ymin = 1e100, 1e100
    #do simulations with the different parameter values,
    #plot results into phase plane
    for i in range(len(duration)):
        model.init_hunting(hunting_rate_x, hunting_rate_y,
                           start_x[i], start_y[i], duration[i])
        model.simulateDynamic()   #solve ODE
        res = model.getResults()  #get results as a storage.DictStore object
        #color_tuple = cm.jet(i/max_i)
        plot(res['x'], res['y'], color='black', linestyle='-')

        #find maximum figure dimensions for quiver plot
        xmax = max(xmax, amax(res['x']))
        ymax = max(ymax, amax(res['y']))
        xmin = min(xmin, amin(res['x']))
        ymin = min(ymin, amin(res['y']))

    #Sample differentials at different points in phase plane,
    #plot field of arrows
    X, Y = mgrid[xmin:xmax:20j,ymin:ymax:20j]
    U, V = zeros(X.shape), zeros(X.shape)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            s_dt = model.dynamic(0, [X[i,j], Y[i,j]])
            U[i,j],V[i,j] = s_dt[0], s_dt[1]
    #The axes don't have the same scale, therefore scale the arrows
    #TODO: this is a bad hack; future keyword 'angles' should do the trick
    scale_xy = (ymin-ymax)/(xmin-xmax) * 1.3
    quiver(X, Y, scale_xy*U, V, pivot='center', units='inches', color='red',zorder=0)

    #finishing touches on plot
    xlabel('x - prey')
    ylabel('y - predators')
    legend()
    title('Predator prey with hunting - hx = %g, hy = %g' % (hunting_rate_x, hunting_rate_y))


#create phase diagram with no hunting
hunting_rate_x = 0
hunting_rate_y = 0
duration       = [100, 100, 100, 100]
start_x        = [0.1,   3,  25,  25]
start_y        = [0.1, 2.5, 0.1,   3]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#create phase diagram with little hunting on both species
hunting_rate_x = 1
hunting_rate_y = 0.1
duration       = [100, 100, 100, 100, 100]
start_x        = [0.1,   3,  19,  20,  20]
start_y        = [0.1, 2.5,   2,   4, 0.1]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#create phase diagram with moderate hunting on predators
hunting_rate_x = 0
hunting_rate_y = 0.3
duration       = [100, 100, 100, 100]
start_x        = [0.1,   3,  20,  20]
start_y        = [0.1, 2.5,   2,   4]
#compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)


#------------------------------------------------------------------------------------
#The parameters of the last two simulations
#are the same as in 'predator_prey_2_hunting_scenarios'

#Create phase diagram with moderate hunting on both species.
#Stable system. (Hunting yield is nearly as high as in strong hunting scenario)
hunting_rate_x = 2
hunting_rate_y = 0.2
duration       = [ 100, 100, 100,   100]
start_x        = [  15,  15,  15,    15]
start_y        = [0.12, 1.3,   2,     4]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#Create phase diagram with strong hunting on prey. The system is stable.
#yield optimum around hunting_rate_x = 4 .. 4.3 .. 4.7
hunting_rate_x = 4.5
hunting_rate_y = 0
duration       = [  100, 100, 100,  100]
start_x        = [    3,   3,   3,    1]
start_y        = [ 0.01, 0.1, 0.2, 0.01]
compute_phase_diagram(hunting_rate_x, hunting_rate_y, duration, start_x, start_y)



#must always be the last statement
show()

