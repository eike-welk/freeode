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
Test code for the "interpreter.py" module
    Test basic functionality.
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



def test_ExpressionGenerator_1(): #IGNORE:C01111
    msg = 'Test creation of expression strings. Check all operators'
    #py.test.skip(msg)
    print msg
    from freeode.pygenerator import ExpressionGenerator, IFloat
    from freeode.ast import (RoleConstant,
                             NodeOpInfix2, NodeOpPrefix1, NodeParentheses)

    e_gen = ExpressionGenerator()
    #create some variables and numbers
    a = IFloat()
    a.target_name = 'a'
    b = IFloat()
    b.target_name = 'b'
    c = IFloat(2)
    c.role = RoleConstant
    
    #expression a + b * 2
    expr = NodeOpInfix2('+', (a, NodeOpInfix2('*', (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2}) == 5

    #expression a - b / 2
    expr = NodeOpInfix2('-', (a, NodeOpInfix2('/', (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2}) == 0

    #expression a ** b % 2
    expr = NodeOpInfix2('**', (a, NodeOpInfix2('%', (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':2, 'b':3}) == 0

    #expression - 2
    expr = NodeOpPrefix1('-', (c,))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {}) == -2

    #expression (a + b) * 2
    expr = NodeOpInfix2('*', (NodeParentheses((NodeOpInfix2('+', (a, b)),)
                                              ), 
                              c)
                        )
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2}) == 6



def test_ExpressionGenerator_2(): #IGNORE:C01111
    msg = 'Test creation of expression strings. Check function call.'
    #py.test.skip(msg)
    print msg
    from math import sin
    from freeode.pygenerator import ExpressionGenerator
    from freeode.interpreter import IFloat, CallableObject
    from freeode.ast import NodeFuncCall

    e_gen = ExpressionGenerator()
    #create a variable
    a = IFloat()
    a.target_name = 'a'
    #create a function
    fsin = CallableObject(None)
    fsin.codegen_name = 'sin'
    
    #expression: sin(a)
    expr = NodeFuncCall(fsin, (a,))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':0, 'sin':sin}) == 0



def test_SimulationClassGenerator__create_sim_class_1():
    msg = ''' Test SimulationClassGenerator.create_sim_class: 
    Just see if function does not crash.
    '''
    #py.test.skip(msg)
    print msg
    
    import cStringIO
    from freeode.pygenerator import SimulationClassGenerator
    from freeode.interpreter import Interpreter
    from freeode.simulatorbase import SimulatorBase
    
    prog_text = \
'''
class A:
    data a:Float
    data b: Float 
    data c: Float param
    
    func initialize(this):
        a = 1
        c = 2
        print(a)
    
    func dynamic(this):
        b = c
        $a = b * sin(a)
        
    func final(this):
        graph(a)
    
compile A
'''
    
    #interpret the compile time code
    intp = Interpreter()
    intp.interpret_module_string(prog_text, 'foo.siml', '__main__')
    flat_o = intp.get_compiled_objects()[0]
    #create the Python class definition as text
    buf = cStringIO.StringIO()
    cg = SimulationClassGenerator(buf)
    cg.create_sim_class('A', flat_o)
    cls_txt = buf.getvalue()
    print cls_txt

#    exec cls_txt
#    a = A()


def test_ProgramGenerator__write_program_start():
    msg = ''' Test ProgramGenerator.write_program_start: 
    Just see if function does not crash.
    '''
    #py.test.skip(msg)
    print msg
    from freeode.pygenerator import ProgramGenerator
    
    pg = ProgramGenerator()
    pg.write_program_start()
    print pg.get_buffer()
    


def test_ProgramGenerator__write_program_end():
    msg = ''' Test ProgramGenerator.write_program_end: 
    Just see if function does not crash.
    '''
    #py.test.skip(msg)
    print msg
    from freeode.pygenerator import ProgramGenerator
    
    pg = ProgramGenerator()
    pg.simulation_class_names = ['Foo', 'Bar']
    pg.write_program_end()
    print pg.get_buffer()
    


def test_ProgramGenerator__create_program():
    msg = ''' Test ProgramGenerator.create_program: 
    Just see if function does not crash.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.pygenerator import ProgramGenerator
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
class A:
    data a: Float
    data b: Float param
    
    func dynamic(this):
        $a = 1
    
compile A
'''
    
    #interpret the compile time code
    intp = Interpreter()
    intp.interpret_module_string(prog_text, 'foo.siml', '__main__')
    #create the output text
    pg = ProgramGenerator()
    pg.create_program('foo.siml', intp.get_compiled_objects())
    print pg.get_buffer()
    


if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_SimulationClassGenerator__create_sim_class_1()
    pass
