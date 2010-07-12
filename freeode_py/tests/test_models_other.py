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



def test_fibonacci_compile_time(): #IGNORE:C01111
    msg = '''Test model: fibonacci_compile_time.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/other/'
    base_name = 'fibonacci_compile_time'
    test_suffix = '_testprog8'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix, '--debug-areas=perf')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['Recursive algorithm:', 55.0 ]), 
                                  Line(['Closed solution:',     55.0 ]),
                                  Line(['15.0 :', 610.0 ])
                                  ])



def test_sum_compile_time(): #IGNORE:C01111
    msg = '''Test model: sum_compile_time.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/other/'
    base_name = 'sum_compile_time'
    test_suffix = '_testprog9'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix, '--debug-areas=perf')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['Recursive sum:' , 55.0 ]), 
                                  Line(['Closed formula:', 55.0 ])
                                  ])



def test_debug_areas(): #IGNORE:C01111
    msg = '''Test model: debug_areas.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/other/'
    base_name = 'debug_areas'
    test_suffix = '_testprog10'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation with standard debug areas. All special output 
    #should be disabled
    res_txt = compile_run(in_name, test_suffix)
    #Search for the test lines
    search_result_lines(res_txt, [Line('print-always: 1'), 
                                  Line('init-x: 0.0'), 
                                  Line('final-x: 100.0')
                                  ])

    #Run compiler and simulation with debug area "debug-compile-time" (and "perf")
    #enabled. All additional output with this debug area should be displayed.
    res_txt = compile_run(in_name, test_suffix, '--debug-areas=debug-compile-time,perf')
    #Search for the test lines
    search_result_lines(res_txt, [Line('print-always: 1'), 
                                  Line('init-x: 0.0'), 
                                  Line('final-x: 100.0'), 
                                  Line('debug-compile-time1: 1'), 
                                  Line('debug-compile-time2: 2'), 
                                  Line('debug-compile-time3: 3'), 
                                  Line('debug-compile-time4: 4')
                                  ])

    #Run compiler and simulation with debug area "debug-run-time" (and "perf")
    #enabled. All additional output with this debug area should be displayed.
    res_txt = compile_run(in_name, test_suffix, '--debug-areas=debug-run-time,perf')
    #Search for the test lines
    search_result_lines(res_txt, [Line('print-always: 1'), 
                                  Line('init-x: 0.0'), 
                                  Line('final-x: 100.0'), 
                                  Line('debug-run-time2: 2'), 
                                  Line('debug-run-time3: 3'), 
                                  Line('debug-run-time4: 4')
                                  ])



if __name__ == '__main__':
    # Debugging code may go here.
    test_debug_areas()
    pass #pylint:disable-msg=W0107
