# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
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
Test code for the "optimizer.py" module
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



def test_MakeDataFlowDecorations_1(): #IGNORE:C01111
    msg = '''Test the creation of data flow annotations.'''
    #py.test.skip(msg)
    print msg
    
    from freeode.optimizer import MakeDataFlowDecorations
    from freeode.interpreter import (Interpreter, IFloat) 
    from freeode.ast import DotName, NodeAssignment

    prog_text = \
'''
class A:
    data p1,p2: Float param
    data a,b,c,d: Float
    
    func dynamic(this):       
        a = p1
        b = a - p2
        if a > p1:
            c = p1
            d = p1
        else:
            c = p2 
            d = p2

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
    #print sim
    #get attributes
    a = sim.get_attribute(DotName('a'))
    b = sim.get_attribute(DotName('b'))
    c = sim.get_attribute(DotName('c'))
    d = sim.get_attribute(DotName('d'))
    p1 = sim.get_attribute(DotName('p1'))
    p2 = sim.get_attribute(DotName('p2'))
    #get generated main function
    dyn = sim.get_attribute(DotName('dynamic'))    
    #print object ids in hex (for easier manual testing)
    hexid = lambda x: hex(id(x))
    print 'a:', hexid(a), ' b:', hexid(b),  ' c:', hexid(c),  ' d:', hexid(d), \
          ' p1:', hexid(p1),  ' p2:', hexid(p2) 

    #------- the test -------------------
    #create the input and output decorations on each statement of the 
    #function
    dd = MakeDataFlowDecorations()
    dd.decorate_simulation_object(sim)
    #dd.decorate_main_function(dyn)

    #see if the inputs and outputs were detected correctly
    # a = p1   
    stmt = dyn.statements[0]
    assert stmt.inputs == set([p1])
    assert stmt.outputs == set([a])
    #  b = a - p2
    stmt = dyn.statements[1]
    assert stmt.inputs == set([a, p2])
    assert stmt.outputs == set([b])
    
    #'if' statement
    stmt = dyn.statements[2]
    #look at inputs
    assert stmt.inputs.issuperset(set([a, p1, p2])) 
    #there is an additional constant IFloat(1) in the condition of the else
    one_set = stmt.inputs - set([a, p1, p2])
    assert len(one_set) == 1
    one_obj = one_set.pop()
    assert one_obj == IFloat(1)
    #look at outputs
    assert stmt.outputs == set([c, d])
    
    #the dynamic function
    assert dyn.inputs == set([p1, p2, one_obj])
    assert dyn.outputs == set([a, b, c, d])



def test_unknown_const_1(): #IGNORE:C01111
    msg = '''Test correct treatment of unknown constants.'''
    py.test.skip(msg)
    print msg
    
    from freeode.optimizer import MakeDataFlowDecorations, DataFlowChecker
    from freeode.interpreter import (Interpreter, IFloat) 
    from freeode.ast import DotName, NodeAssignment

    prog_text = \
'''
data c1: Float const

class A:
    data a, b: Float
    data c2: Float const
    
    func dynamic(this):       
        a = c1
        b = c2

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
    #print sim
    #get attributes
    a = sim.get_attribute(DotName('a'))
    b = sim.get_attribute(DotName('b'))
#    c = sim.get_attribute(DotName('c1'))
#    c = sim.get_attribute(DotName('c2'))
    #get generated main function
    dyn = sim.get_attribute(DotName('dynamic'))
    hexid = lambda x: hex(id(x))
    print 'a:', hexid(a), ' b:', hexid(b)#,  ' c2:', hexid(c)
    
    #create the input and output decorations on each statement of the 
    #function
    dd = MakeDataFlowDecorations()
    dd.decorate_simulation_object(sim)
    #check data flow of all functions
    fc = DataFlowChecker()
    fc.set_sim_object(sim)
    
    
    assert False, 'This program should raise an exceptions because unknown const attributes were used'


if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_unknown_const_1()
    pass


