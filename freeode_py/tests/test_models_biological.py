# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2010 - 2010 by Eike Welk                                *
#    eike.welk@gmx.net                                                     *
#                                                                          *
#    License: GPL                                                          *
#                                                                          *
#    This program is free software; you can redistribute it and/or modify  *
#    it under the terms of the GNU General Public License as published by  *
#    the Free Software Foundation; either version 2 of the License, or     *
#    (at your option) any later version.                                   *
#                                                                          *
#    This program is distributed in the hope that it will be useful,       *
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#    GNU General Public License for more details.                          *
#                                                                          *
#    You should have received a copy of the GNU General Public License     *
#    along with this program; if not, write to the                         *
#    Free Software Foundation, Inc.,                                       *
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#***************************************************************************

"""
Compile and run all example models as tests.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

from py.test import skip as skip_test # pylint:disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint:disable-msg=F0401,E0611,W0611

from freeode.util import compile_run, search_result_lines



def test_bioreactor_simple(): #IGNORE:C01111
    msg = '''Test model: bioreactor_simple.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'bioreactor_simple'
    test_suffix = 'testprog_1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix)
    #Search for the test lines
    search_result_lines(res_txt, ['initial-values: 0.1 20.0', 
                                  'final-values:  10.1  0.0',
                                  ])

      

def test_bioreactor(): #IGNORE:C01111
    msg = '''Test model: bioreactor.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'bioreactor'
    test_suffix = 'testprog_2'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix)
    #Search for the test lines
    search_result_lines(res_txt, ['initial-values-batch: 0.1    20.0  ', 
                                  'final-values-batch:   9.795  -3.065', 
                                  'initial-values-conti: 0.1    20.0  ', 
                                  'final-values-conti:   0.181  19.626', 
                                  'initial-values-smart: 0.1    20.0  ', 
                                  'final-values-smart:   9.606  0.149 '
                                  ])

      

def test_competition(): #IGNORE:C01111
    msg = '''Test model: competition.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'competition'
    test_suffix = 'testprog_3'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix)
    #Search for the test lines
    search_result_lines(res_txt, ['case1-final: 4e-7   10.0 ', 
                                  'case2-final: 9.999  4e-7 ', 
                                  'case3-final: 9.614  0.047', 
                                  'case4-final: 6.678  6.654'
                                  ])



def test_predator_prey_2(): #IGNORE:C01111
    msg = '''Test model: predator_prey_2.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'predator_prey_2'
    test_suffix = 'testprog_4'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix)
    #Search for the test lines
    search_result_lines(res_txt, ['initial_state: 2.0    2.0      0.0 ', 
                                  'final_state:   0.130  1.350   30.0 '
                                  ])



def test_predator_prey(): #IGNORE:C01111
    msg = '''Test model: predator_prey.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'predator_prey'
    test_suffix = 'testprog_5'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix)
    #Search for the test lines
    search_result_lines(res_txt, ['classic_final:  1.906 0.427 30.0', 
                                  'logistic_final: 4.987 0.780 30.0', 
                                  'enhanced_final: 0.130 1.350 30.0'
                                  ])



if __name__ == '__main__':
    # Debugging code may go here.
    test_predator_prey()
    pass #pylint:disable-msg=W0107

