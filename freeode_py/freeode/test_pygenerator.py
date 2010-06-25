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
Test code for the "interpreter.py" module
    Test basic functionality.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises



def test_ExpressionGenerator_1(): #IGNORE:C01111
    msg = 'Test creation of expression strings. Check all operators'
    #skip_test(msg)
    print msg
    from numpy import float64
    from freeode.pygenerator import ExpressionGenerator, func
    from freeode.interpreter import IFloat
    from freeode.ast import RoleConstant, NodeFuncCall, NodeParentheses

    e_gen = ExpressionGenerator()
    #create some variables and numbers
    a = IFloat()
    a.target_name = 'a'
    b = IFloat()
    b.target_name = 'b'
    c = IFloat(2)
    c.role = RoleConstant
    
    #Get some functions that are converted into Python operators
    add = func(IFloat.__add__)
    sub = func(IFloat.__sub__)
    mul = func(IFloat.__mul__)
    div = func(IFloat.__div__)
    pow = func(IFloat.__pow__)
    mod = func(IFloat.__mod__)
    neg = func(IFloat.__neg__)
    
    #expression a + b * 2
    expr = NodeFuncCall(add, (a, NodeFuncCall(mul, (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2, 'float64':float64}) == 1 + 2 * 2 #5

    #expression a - b / 2
    expr = NodeFuncCall(sub, (a, NodeFuncCall(div, (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2, 'float64':float64}) == 1 - 2 / 2 #0

    #expression a ** b % 2
    expr = NodeFuncCall(pow, (a, NodeFuncCall(mod, (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':2, 'b':3, 'float64':float64}) == 2 ** 3 % 2 #0

    #expression - 2
    expr = NodeFuncCall(neg, (c,))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'float64':float64}) == -2

    #expression (a + b) * 2
    expr = NodeFuncCall(mul, (NodeParentheses((NodeFuncCall(add, (a, b)),)
                                              ), 
                              c)
                        )
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2, 'float64':float64}) == (1 + 2) * 2 #6



def test_ExpressionGenerator_2(): #IGNORE:C01111
    msg = 'Test creation of expression strings. Check function call.'
    #skip_test(msg)
    print msg
    
    import math 
    from freeode.pygenerator import ExpressionGenerator
    from freeode.interpreter import IFloat, BUILTIN_LIB
    from freeode.ast import NodeFuncCall

    e_gen = ExpressionGenerator()
    #create a variable
    a = IFloat()
    a.target_name = 'a'

    #get the "sin" function
    sin = BUILTIN_LIB.sin
    
    #create expression "sin(a)" and create Python code for it
    expr = NodeFuncCall(sin, (a,))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    
    #Execute the generated Python code
    assert eval(expr_str, {'a':0, 'sin':math.sin}) == 0



def test_SimulationClassGenerator__create_sim_class_1():
    msg = ''' Test SimulationClassGenerator.create_sim_class: 
    Just see if function does not crash.
    '''
    #skip_test(msg)
    print msg
    
    import cStringIO
    from freeode.pygenerator import SimulationClassGenerator
    from freeode.interpreter import Interpreter
    #from freeode.simulatorbase import SimulatorBase
    
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
    #skip_test(msg)
    print msg
    from freeode.pygenerator import ProgramGenerator
    
    pg = ProgramGenerator()
    pg.write_program_start()
    print pg.get_buffer()
    


def test_ProgramGenerator__write_program_end():
    msg = ''' Test ProgramGenerator.write_program_end: 
    Just see if function does not crash.
    '''
    #skip_test(msg)
    print msg
    from freeode.pygenerator import ProgramGenerator
    
    pg = ProgramGenerator()
    pg.simulation_class_names = ['Foo', 'Bar']
    pg.write_program_end()
    print pg.get_buffer()
    


def test_ProgramGenerator__create_program_1():
    msg = \
    ''' 
    Test ProgramGenerator.create_program: 
    Test basic functions of the compiler. Loads generated program as module.
    '''
    #skip_test(msg)
    print msg
    
    import os
    from freeode.pygenerator import ProgramGenerator
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
class A:
    data x: Float
    data b: Float param
    
    func initialize(this):
        x = 0
        b = 1
        solution_parameters(duration = 30, reporting_interval = 0.1)
    
    func dynamic(this):
        $x = b
    
compile A
'''
    
    #interpret the compile time code
    intp = Interpreter()
    intp.interpret_module_string(prog_text, 'foo.siml', '__main__')
    #create the output text
    pg = ProgramGenerator()
    pg.create_program('foo.siml', intp.get_compiled_objects())
    #print pg.get_buffer()
    
    #write the buffer into a file, import the file as a module
    progname = 'testprog_ProgramGenerator__create_program_1'
    prog_text_file = open(progname + '.py','w')
    prog_text_file.write(pg.get_buffer())
    prog_text_file.close()
    module = __import__(progname)
    
    #test the generated module
    A = module.A
    a = A()
    #call generated initialize(...) function
    a.initialize()
    assert a.param.b == 1
    #solve (trivial) ODE and test solution
    a.simulateDynamic()
    x_vals = a.getResults()['x']
    assert x_vals[-1] - 30 < 1e-6
    
    #clean up
    os.remove(progname + '.py')



def test_ProgramGenerator__create_program_2():
    msg = \
    ''' 
    Test ProgramGenerator.create_program: 
    Test program with additional initialization function.
    Load program as module and test init_*** function.
    '''
    #skip_test(msg)
    print msg
    
    import os
    from freeode.pygenerator import ProgramGenerator
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
class A:
    data x: Float 
    data b: Float param
    
    #This is the additional initialization function.
    func init_b(this, in_b):
        b = in_b #set parameter
        x = 0    #set initial value
                                                       #10     
    func initialize(this):
        b = 0.1 #set parameter
        x = 0   #set initial value
        
    func dynamic(this):
        $x = b
        
compile A
'''
    
    #interpret the compile time code
    intp = Interpreter()
    intp.interpret_module_string(prog_text, 'foo.siml', '__main__')
    #create the output text
    pg = ProgramGenerator()
    pg.create_program('foo.siml', intp.get_compiled_objects())
    #print pg.get_buffer()
    
    #write the buffer into a file, import the file as a module
    progname = 'testprog_ProgramGenerator__create_program_2'
    prog_text_file = open(progname + '.py','w')
    prog_text_file.write(pg.get_buffer())
    prog_text_file.close()
    module = __import__(progname)
    
    #test the generated module
    A = module.A
    a = A()
    #call generated init_b(...) function
    a.init_b(42)
    assert a.param.b == 42
    
    #clean up
    os.remove(progname + '.py')
    


def test_ProgramGenerator__create_program_3():
    msg = \
    ''' 
    Test ProgramGenerator.create_program: 
    Test most common language features.
    '''
    #skip_test(msg)
    print msg
    
    import os
    from freeode.pygenerator import ProgramGenerator
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
class A:
    data x: Float 
    data a, b, c, d, e: Float param

    func initialize(this):
        a = 2 * (3 + 4)               # = 14, test brackets
        b = a**0 / 0.1 % 9 - -a/a  # = 2, arithmetic operators
        
        #if statement should reduce to single assignment
        if -2**-3 == -(2 ** (-3)):    # tricky operator precedence
            c = 1                     # c = 1
        else:
            c = 0
        
        #if statement, comparison and logical operators
        if (a != 1 and not a == 1 or a == 1) and (a < 1 or a > 1):
            d = 1                     # d = 1
            e = sin(d * 3.1415)       # close to 0 #test function call
        else:
            d = 0
            e = sin(d * 3.1415)       # = 0  #test function call
            
        x = 0   #set initial value
        
    func dynamic(this):
        $x = b
        
compile A
'''
    
    #interpret the compile time code
    intp = Interpreter()
    intp.interpret_module_string(prog_text, 'foo.siml', '__main__')
    #create the output text
    pg = ProgramGenerator()
    pg.create_program('foo.siml', intp.get_compiled_objects())
    #print pg.get_buffer()
    
    #write the buffer into a file, import the file as a module
    #progname must be unique! otherwise race condition!
    progname = 'testprog_ProgramGenerator__create_program_3'
    prog_text_file = open(progname + '.py','w')
    prog_text_file.write(pg.get_buffer())
    prog_text_file.close()
    module = __import__(progname)
    
    #test the generated module
    A = module.A
    a = A()
    #call generated init_b(...) function
    a.initialize()
    assert a.param.a == 14
    assert a.param.b == 2
    assert a.param.c == 1
    assert a.param.d == 1
    assert abs(a.param.e) < 0.001 #close to 0 
    
    #clean up
    os.remove(progname + '.py')
    


if __name__ == '__main__':
    # Debugging code may go here.
    test_ExpressionGenerator_1()
    #test_ProgramGenerator__create_program_3()
    pass
