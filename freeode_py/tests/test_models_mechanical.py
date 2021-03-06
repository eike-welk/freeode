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



def test_tank(): #IGNORE:C01111
    msg = '''Test model: tank.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/mechanical/'
    base_name = 'tank'
    test_suffix = '_testprog6'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    res_txt = compile_run(in_name, test_suffix)#, clean_up=False)
    #Search for the test lines
    search_result_lines(res_txt, ['initial-values: 0.0     0.0', 
                                  'final-values:   0.030 600.0'
                                  ])



def test_tuned_abs_damper(): #IGNORE:C01111
    msg = '''Test model: tuned_abs_damper.siml'''
#    skip_test(msg)
    print msg
 
    directory = 'models/mechanical/'
    base_name = 'tuned_abs_damper'
    test_suffix = '_testprog7'
    
    #Special name for output, to avoid race condition if input  file is used 
    #by other test too
    in_name = directory + base_name + '.siml'
    
    #Run compiler and simulation(s); catch the output
    _res_txt = compile_run(in_name, test_suffix)#, clean_up=False)
    #No testing; I don't understand any of it
    #TODO: do some testing



if __name__ == '__main__':
    # Debugging code may go here.
    test_tank()
    pass #pylint:disable-msg=W0107

