#!/usr/bin/env python
#    Copyright (C) 2009 by Eike Welk
#    eike.welk@gmx.net                                                     



#Python script that uses "predator_prey.siml"
#
#                   --- Predator-Prey Models - Plot Phase Diagrams ---
#
#



#import library functions
from pylab import plot, show, figure, xlabel, ylabel, legend, title, quiver
from numpy import amax, amin, mgrid, zeros
#import the compiled simulation objects
from predator_prey import ClassicModel, LogisticPrey, EnhancedModel



def compute_phase_diagram(model, start_x, start_y, duration, title_str='Phase plot'):
    '''
    Compute multiple simulations with parameters taken from the arguments.
    Create graph that shows the simulation results one after the other.

    ARGUMENTS
    ---------
    model:           one of the predator-prey models
    duration:        list of duration for each simulation
    start_x:         list of start values for species 1
    start_y          list of start values for species 2
    '''
    figure() #create new figure window

    #max_i = len(duration)-1
    xmax, ymax = -1e100, -1e100
    xmin, ymin = 1e100, 1e100
    #do simulations with the different parameter values,
    #plot results into phase plane
    for i in range(len(duration)):
        model.init_phase_plot(start_x[i], start_y[i], duration[i])
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
    title(title_str)




#Classic Predator - Prey Model ----------------------------------------------
model = ClassicModel() #create a simulaton object instance
#create a couple of initial values for x and y
init_x =   [0.5, 1.5, 2.7,  4]
init_y =   [0.5, 0.5, 0.7,  1]
duration = [ 10,  10,  10, 10]
#Do several simulations and create phase plot from results
compute_phase_diagram(model, init_x, init_y, duration,
                      'Classic Predator - Prey Model')


#Predator Prey Model; Logistic Growth of Prey --------------------------------
model = LogisticPrey() #create a simulaton object instance
#create a couple of initial values for x and y
init_x =   [0.5,    25]
init_y =   [3,   0.01]
duration = [100,   100]
#Do several simulations and create phase plot from results
compute_phase_diagram(model, init_x, init_y, duration,
                      'Predator Prey Model; Logistic Growth of Prey')


#Complicated homegrown model; ------------------------------------------------
#Logistic Growth of prey, predators have upper limit for growth speed.
model = EnhancedModel() #create a simulation object instance
#create a couple of initial values for x and y
init_x =   [0.1,   3,  25]
init_y =   [0.2, 2.2, 0.2]
duration = [100, 100, 100]
#Do several simulations and create phase plot from results
compute_phase_diagram(model, init_x, init_y, duration,
                      'Homegrown Predator-Prey Model')


#show all graphs and wait until they have been clicked away
show()