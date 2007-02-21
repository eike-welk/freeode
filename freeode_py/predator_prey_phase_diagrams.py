#!/usr/bin/env python
#Create phase plane diagrams of the predator-prey models.

#import library functions
from pylab import plot, show, figure, xlabel, ylabel, legend, title
from numpy import linspace
#import the compiled simulation objects
from predator_prey import ClassicModel, LogisticPrey


#Classic Predator - Prey Model ----------------------------------------------
#Create phase plane plot.
mo = ClassicModel() #create a simulaton object instance
figure() #create new figure window
#create a couple of initial values for x and y
initX = linspace(0.5, 4.9, 6)
initY = linspace(0.5, 0.9, 6)

#do simulations with the different initial values, and put the results into a
#phase-plane plot
for i in range(len(initX)):
    #initialize the simulation object, with new initial values
    mo.initialize(x0=initX[i], y0=initY[i], showGraph=0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    labelStr = 'x=%g, y=%g' % (initX[i], initY[i]) #create descriptive string
    plot(res['x'], res['y'], label=labelStr)       #plot the solution

#finishing touches on plot
xlabel('x (prey)')
ylabel('y (predator)')
legend()
title('Classic Predator - Prey Model')


#Predator Prey Model; Logistic Growth of Prey --------------------------------
#Create phase plane plot.
mo = LogisticPrey() #create a simulaton object instance
figure() #create new figure window
#create a couple of initial values for x and y
initX = linspace(0.1, 3, 6)
initY = linspace(0.01, 0.3, 6)

#do simulations with the different initial values, and put the results into a
#phase-plane plot
for i in range(len(initX)):
    #initialize the simulation object, with new initial values
    mo.initialize(x0=initX[i], y0=initY[i], showGraph=0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    labelStr = 'x=%g, y=%g' % (initX[i], initY[i]) #create descriptive string
    plot(res['x'], res['y'], label=labelStr)       #plot the solution

#finishing touches on plot
xlabel('x (prey)')
ylabel('y (predator)')
legend()
title('Predator Prey Model; Logistic Growth of Prey')


#show all graphs and wait until they have been clicked away
show()