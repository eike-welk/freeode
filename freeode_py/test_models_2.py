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



def test_tank(): #IGNORE:C01111
    msg = '''Test model: tank.siml'''
#    skip_test(msg)
    print msg
 
    directory = '../models/mechanical/'
    base_name = 'tank'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line('initial-values: 0.0     0.0'), 
                                  Line('final-values:   0.030 600.0')
                                  ])



def test_tuned_abs_damper(): #IGNORE:C01111
    msg = '''Test model: tuned_abs_damper.siml'''
#    skip_test(msg)
    print msg
 
    directory = '../models/mechanical/'
    base_name = 'tuned_abs_damper'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #No testing; I don't understand any of it
    #TODO: do some testing



def test_fibonacci_compile_time(): #IGNORE:C01111
    msg = '''Test model: fibonacci_compile_time.siml'''
#    skip_test(msg)
    print msg
 
    directory = '../models/other/'
    base_name = 'fibonacci_compile_time'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['Recursive algorithm:', 55.0 ]), 
                                  Line(['Closed solution:',     55.0 ]),
                                  Line(['15.0 :', 610.0 ])
                                  ])



def test_sum_compile_time(): #IGNORE:C01111
    msg = '''Test model: sum_compile_time.siml'''
#    skip_test(msg)
    print msg
 
    directory = '../models/other/'
    base_name = 'sum_compile_time'
    output_suffix = '_test1'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    out_name = directory + base_name + output_suffix + '.py'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, out_name, '--no-graphs')
    #Search for the test lines
    search_result_lines(res_txt, [Line(['Recursive sum:' , 55.0 ]), 
                                  Line(['Closed formula:', 55.0 ])
                                  ])



if __name__ == '__main__':
    # Debugging code may go here.
    test_fibonacci_compile_time()
    pass #pylint:disable-msg=W0107

