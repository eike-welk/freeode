# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2011 - 2011 by Eike Welk                                #
#    eike.welk@gmx.net                                                     #
#                                                                          #
#    License: GPL                                                          #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################
'''
Compute the critical height difference between two vessels, so that turbulent 
flow develops in their connecting pipe.

If the height difference is small the velocity in the connecting pipe is low,
so that the flow in the connecting pipe is laminar. 
'''

from numpy import array, mgrid, ogrid
from matplotlib.pyplot import (show, imshow, contourf, plot, colorbar, 
                               xlabel, ylabel)



#---------------------
#    Constants
#---------------------
# Reynolds Number that marks the transition to turbulent flow.
#Re_crit = 2300 # Lower limit
Re_crit = 4000 # Upper limit
g = 9.81 # {m / s**2}
rho = 1000 # {kg / m**3} density water
mu = 1e-3 # {N * s / m**2} viskosity water


def critical_height(pipe_length, pipe_diameter):
    '''
    Compute critical height difference between two vessels, so that turbulent 
    flow develops in their connecting pipe.
    
    Parameter
    ---------
    pipe_length: array[float]
        Length of pipe that connects the vessels
        
    pipe_diameter: array[float]
        Hydaulic diameter of pipe that connects the vessels
        
    Returns
    -------
    h_crit: array[float]
        Height difference for critical flow
    '''
    h_crit = 32 * Re_crit * mu**2 * pipe_length      \
            / (rho**2 * g * pipe_diameter**3)
            
    return h_crit


def make_graph():
    l_min, l_max = 0.05, 0.2 # {m}
    length, diameter = mgrid[l_min:l_max:100j, 0.005:0.020:100j]
    h_crit = critical_height(length, diameter)
    
    l_10 = length[:, 0]
    d_10 = l_10 / 10
    
    #print h_crit
    #imshow(h_crit)
    contourf(length, diameter, h_crit)
    plot(l_10, d_10, color='black')
    
    xlabel('Length')
    ylabel('Diameter')
    colorbar()
    
    show()


if __name__ == '__main__':
    make_graph()
