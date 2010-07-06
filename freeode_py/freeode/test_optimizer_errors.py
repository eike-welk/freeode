# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
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
Test code for the "optimizer.py" module
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises



def test_VariableUsageChecker_1(): #IGNORE:C01111
    msg = '''Test checking of variable usage. Provoke all errors at least once.'''
    #skip_test(msg)
    print msg
    
    from freeode.optimizer import MakeDataFlowDecorations, VariableUsageChecker
    from freeode.interpreter import Interpreter
    from freeode.util import DotName, UserException#, aa_make_tree

    prog_text = \
'''
class A:
    data p1,p2: Float param
    data a,b,c: Float
    
    #illegal read of parameter p1
    func init_1(this):
        p2 = p1
        a = 0
        
    #illegal write to differential $a
    func init_2(this):
        $a = 1
        p1 = 1
        p2 = 1
        a = 0
    
    #Missing assignment to parameter p1
    func init_3(this):
        p2 = 1
        a = 0
        
    #illegal write to state variable a
    func dynamic(this): 
        a = 2
        $a = p1
        b = a - p2
        c = p1
        
    #illegal write to state variable a
    func final(this):
        a = 2
        b = 1
        print(a, b, p1)
        
        
compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    #mod = intp.modules['test']
    #print mod
    
    #get the flattened version of the A class
    sim = intp.get_compiled_objects()[0]
    #aa_make_tree(sim)
    
    #create the input and output decorations on each statement of the 
    #function
    dd = MakeDataFlowDecorations()
    dd.decorate_simulation_object(sim)

    #Find all input and output variables
    vu = VariableUsageChecker()
    vu.set_annotated_sim_object(sim) 
    
    #illegal read of parameter p1
    initialize = vu.main_funcs[DotName('init_1')]
    #vu.check_initialize_function(initialize) 
    assert_raises(UserException, 4500100, 
                  vu.check_initialize_function, (initialize,))
    
    #illegal write to differential $a
    initialize = vu.main_funcs[DotName('init_2')]
    #vu.check_initialize_function(initialize) 
    assert_raises(UserException, 4500200, 
                  vu.check_initialize_function, (initialize,))
    
    #Missing assignment to parameter p1
    initialize = vu.main_funcs[DotName('init_3')]
    #vu.check_initialize_function(initialize) 
    assert_raises(UserException, 4500300, 
                  vu.check_initialize_function, (initialize,))
    
    #illegal write to state variable a
    dynamic = vu.main_funcs[DotName('dynamic')]
    #vu.check_dynamic_function(dynamic) 
    assert_raises(UserException, 4500200, 
                  vu.check_dynamic_function, (dynamic,))
    
    #illegal write to state variable a
    final = vu.main_funcs[DotName('final')]
    #vu.check_final_function(final) 
    assert_raises(UserException, 4500200, 
                  vu.check_final_function, (final,))



if __name__ == '__main__':
    # Debugging code may go here.
    test_VariableUsageChecker_1()
    #test_unknown_const_1()
    #test_MultiDict_1()
    #test_unknown_const_1()
    pass  #pylint:disable-msg=W0107 
