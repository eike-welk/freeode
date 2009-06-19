#!/usr/bin/env python
#    Copyright (C) 2009 by Eike Welk
#    eike.welk@post.rwth-aachen.de



##############################################################################
#                           CURENTLY NOT PORTED                              #
#                                                                            #
#       THE NECESSARY SIML PROGRAM WOULD BE TOO COMPLEX FOR THE PARSER       #
##############################################################################



#Lotka and Volterra's model of competition of two species. (Not Predator-Prey)
#
#                   --- Create phase plane diagrams ---
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



#import library functions
from pylab import plot, show, figure, xlabel, ylabel, legend, title
from numpy import array, linspace, hstack, r_
#import the compiled simulation objects
from competition import Case1, Case2, Case3, Case4

lsp = linspace

#Case 1 ----------------------------------------------
#Create phase plane plot.
#TODO: quiver plot
mo = Case1() #create a simulaton object instance
figure() #create new figure window
#create a couple of initial values for x and y
initN1 = hstack((lsp(0.2, 4, 4),  lsp(0.1, 0.1, 4),lsp(0.1, 12, 6),lsp(12, 12, 6)  ))
initN2 = hstack((lsp(0.1, 0.1, 4),lsp(0.1, 1, 4), lsp(12, 12, 6),  lsp(0.1, 12, 6) ))

#do simulations with the different initial values, and put the results into a
#phase-plane plot
for i in range(len(initN1)):
    #initialize the simulation object, with new initial values
    mo.initialize(N1_init=initN1[i], N2_init=initN2[i], showGraph=0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    labelStr = 'N1=%g, N2=%g' % (initN1[i], initN2[i]) #create descriptive string
    plot(res['m.N1'], res['m.N2'], label=labelStr)       #plot the solution

#finishing touches on plot
xlabel('N1 (species 1)')
ylabel('N2 (species 2)')
#legend()
title('Competition of two species; case 1.')


#Case 2 ----------------------------------------------
#Create phase plane plot.
mo = Case2() #create a simulaton object instance
figure() #create new figure window
#create a couple of initial values for x and y
initN1 = hstack((lsp(0.1, 1, 3),  lsp(0.1, 0.1, 6),lsp(0.1, 12, 6),lsp(12, 12, 6)  ))
initN2 = hstack((lsp(0.1, 0.1, 3),lsp(0.2, 12, 6), lsp(12, 12, 6), lsp(0.1, 12, 6) ))

#do simulations with the different initial values, and put the results into a
#phase-plane plot
for i in range(len(initN1)):
    #initialize the simulation object, with new initial values
    mo.initialize(N1_init=initN1[i], N2_init=initN2[i], showGraph=0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    labelStr = 'N1=%g, N2=%g' % (initN1[i], initN2[i]) #create descriptive string
    plot(res['m.N1'], res['m.N2'], label=labelStr)       #plot the solution

#finishing touches on plot
xlabel('N1 (species 1)')
ylabel('N2 (species 2)')
#legend()
title('Competition of two species; case 2.')


#Case 3 ----------------------------------------------
#Create phase plane plot.
mo = Case3() #create a simulaton object instance
figure() #create new figure window
#create a couple of initial values for x and y
initN1 = hstack((array([0.1, 12]),lsp(0.11, 0.5, 4),lsp(0.1, 0.1, 4), lsp(0.1, 11.1, 6),lsp(12, 12, 6)  ))
initN2 = hstack((array([0.1, 12]),lsp(0.1, 0.1, 4), lsp(0.11, 0.5, 4),lsp(12, 12, 6),   lsp(0.1, 11.1, 6) ))

#do simulations with the different initial values, and put the results into a
#phase-plane plot
for i in range(len(initN1)):
    #initialize the simulation object, with new initial values
    mo.initialize(N1_init=initN1[i], N2_init=initN2[i], showGraph=0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    labelStr = 'N1=%g, N2=%g' % (initN1[i], initN2[i]) #create descriptive string
    plot(res['m.N1'], res['m.N2'], label=labelStr)       #plot the solution

#finishing touches on plot
xlabel('N1 (species 1)')
ylabel('N2 (species 2)')
#legend()
title('Competition of two species; case 3.')


#Case 4 ----------------------------------------------
#Create phase plane plot.
mo = Case4() #create a simulaton object instance
figure() #create new figure window
#create a couple of initial values for x and y
initN1 = hstack((array([0.1, 12]),lsp(0.2, 4, 6),  lsp(0.1, 0.1, 6),lsp(0.1, 11, 6),lsp(12, 12, 6)  ))
initN2 = hstack((array([0.1, 12]),lsp(0.1, 0.1, 6),lsp(0.2, 4, 6),  lsp(12, 12, 6), lsp(0.1, 11, 6) ))

#do simulations with the different initial values, and put the results into a
#phase-plane plot
for i in range(len(initN1)):
    #initialize the simulation object, with new initial values
    mo.initialize(N1_init=initN1[i], N2_init=initN2[i], showGraph=0)
    mo.simulateDynamic()   #solve ODE
    res = mo.getResults()  #get results as a storage.DictStore object
    labelStr = 'N1=%g, N2=%g' % (initN1[i], initN2[i]) #create descriptive string
    plot(res['m.N1'], res['m.N2'], label=labelStr)       #plot the solution

#finishing touches on plot
xlabel('N1 (species 1)')
ylabel('N2 (species 2)')
#legend()
title('Competition of two species; case 4.')





#show all graphs and wait until they have been clicked away
show()