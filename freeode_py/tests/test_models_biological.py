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

from freeode.util import compile_run, search_result_lines, Line



def test_exponential_growth(): #IGNORE:C01111
    msg = '''Test model: exponential_growth.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'exponential_growth'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['final-values:', 40.343, 20])
                                  ])


      
def test_bioreactor_simple(): #IGNORE:C01111
    msg = '''Test model: bioreactor_simple.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'bioreactor_simple'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['final-values:',   10.1, 0, 20])
                                  ])



def test_bioreactor(): #IGNORE:C01111
    msg = '''Test model: bioreactor.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'bioreactor'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['initial-values-batch:', 0.1,  20   ], 0.01), 
                                  Line(['final-values-batch:',   9.79, -3.06], 0.01), 
                                  Line(['initial-values-conti:', 0.1,  20   ], 0.01), 
                                  Line(['final-values-conti:',   0.18, 19.62], 0.01), 
                                  Line(['initial-values-smart:', 0.1,  20   ], 0.01), 
                                  Line(['final-values-smart:',   9.60,  0.14], 0.01)
                                  ])

      

def test_competition(): #IGNORE:C01111
    msg = '''Test model: competition.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'competition'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['case1-final:', 4e-7,  10.0 ]), 
                                  Line(['case2-final:', 9.999, 4e-7 ]), 
                                  Line(['case3-final:', 9.614, 0.047]), 
                                  Line(['case4-final:', 6.678, 6.654])
                                  ])



def test_predator_prey_2(): #IGNORE:C01111
    msg = '''Test model: predator_prey_2.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'predator_prey_2'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['initial_state', 2.0,   2.0,    0.0 ]), 
                                  Line(['final_state'  , 0.130, 1.350, 30.0 ])
                                  ])



def test_predator_prey(): #IGNORE:C01111
    msg = '''Test model: predator_prey.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/biological/'
    base_name = 'predator_prey'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line('classic_final  1.906 0.427 30.0'), 
                                  Line('logistic_final 4.987 0.780 30.0'), 
                                  Line('enhanced_final 0.130 1.350 30.0')
                                  ])



if __name__ == '__main__':
    # Debugging code may go here.
    test_exponential_growth()
    pass #pylint:disable-msg=W0107

