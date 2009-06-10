# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2009 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
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
Test code for the "simlcompiler.py" module.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#The py library is not standard. Preserve ability to use some test functions
# for debugging when the py library, and the py.test testing framework, are 
# not installed. 
try:                      
    import py
except ImportError:
    print 'No py library, many tests may fail!'


def test_do_compile(): #IGNORE:C01111
    msg = 'Test do_compile: Compile and execute a program. (Bypasses program argument handling.)'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlcompiler import SimlCompilerMain
    import os
    
    prog_text = \
'''
data g: Float const
g = 9.81


class BarrelWithHole:
    data V, h: Float
    data A_bott, A_o, mu, q: Float param

    func dynamic(this):                            #line 10
        h = V/A_bott
        $V = q - mu*A_o*sqrt(2*g*h)

    func initialize(this, q_in):
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
        q = q_in #0.05
 
                               
class RunTest:                                     #line 20
    data system: BarrelWithHole

    func dynamic(this):
        system.dynamic()

    func initialize(this):
        system.initialize(0.03)
#        solutionParameters.simulationTime = 100
#        solutionParameters.reportingInterval = 1
                                                   #line 30
#    func final(this):
#        graph(system.V)
        

compile RunTest
'''

    prog_text_file = open('ttest_1.siml','w')
    prog_text_file.write(prog_text)
    prog_text_file.close()
    
    main = SimlCompilerMain()
    main.input_file_name = 'ttest_1.siml'
    main.output_file_name = 'ttest_1.py'
    main.do_compile()
    
    exit_val = os.system('./ttest_1.py')
    assert exit_val == 0
    
    os.remove('ttest_1.siml')
    os.remove('ttest_1.py')
    
  
#TODO: try to compile all example models as test


if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_do_compile()
    pass
