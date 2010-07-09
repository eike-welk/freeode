# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 - 2010 by Eike Welk                                *
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
Test code for the "simlcompiler.py" module.
"""

from __future__ import division
from __future__ import absolute_import              

from py.test import skip as skip_test  #pylint:disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test  #pylint:disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises #pylint:disable-msg=W0611



def test_do_compile(): #IGNORE:C01111
    msg = '''Test do_compile: Compile and execute a program. 
    Bypasses program argument handling. 
    Checks if the simulation is computing the right value too.'''
#    skip_test(msg)
    print msg
    
    import os
    from subprocess import Popen, PIPE
    from freeode.simlcompiler import SimlCompilerMain
    
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
        solution_parameters(200, 1)
                     
    func final(this):                              #line 30
        #graph(system.V)
        print("final-values: ", system.V, time)
        

compile RunTest
'''

    base_name = 'testprog_SimlCompilerMain_do_compile'
    prog_text_file = open(base_name + '.siml','w')
    prog_text_file.write(prog_text)
    prog_text_file.close()
    
    main = SimlCompilerMain()
    main.input_file_name =  base_name + '.siml'
    main.output_file_name = base_name + '.py'
    main.do_compile()
    
    sim = Popen('./' + base_name + '.py', shell=True, stdout=PIPE)
    res_txt, _ = sim.communicate()
    print 'Program output: ', res_txt
    print  'Return code: ', sim.returncode
    
    #Program must say that it terminated successfully 
    assert sim.returncode == 0

    #Scan the program's output to check if it's working.
    final_vals = []
    for line in res_txt.split('\n'): #pylint:disable-msg=E1103 
        if line.startswith('final-values:'):
            vals = line.split()[1:]
            final_vals = map(float, vals)
        
    #Test if the values that the program returns are correct
    v, time = final_vals
    assert abs(v - 0.379) < 0.001 and time == 200
    
    #clean up
    os.remove(base_name + '.siml')
    os.remove(base_name + '.py')
    
  

if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_do_compile()
    pass #pylint:disable-msg=W0107
