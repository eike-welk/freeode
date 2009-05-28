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
    High level tests involving program text in Siml.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#The py library is not standard. Preserve ability to use some test functions
# for debugging when the py library, and the py.test testing framework, are 
# not installed. 
try:                      
    import py
except:
    print 'No py library, many tests may fail!'



def test_interpreter_object_builtin_function_call_1():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: call built in function sqrt...............................................................'
    from freeode.interpreter import Interpreter, DotName
    import math
    
    prog_text = \
'''
data a: Float const
a = sqrt(2)
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print 'module after interpreter run: ---------------------------------'
    print intp.modules['test']
    
    assert intp.modules['test'].get_attribute(DotName('a')).value == math.sqrt(2)
  
  

def test_interpreter_object_builtin_function_call_2():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: call built in function print...............................................................'
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
print('test')
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print 'module after interpreter run: ---------------------------------'
    print intp.modules['test']
  
  

def test_interpreter_function_definition_and_call_1():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: function definition and function call ...............................................................'
    from freeode.interpreter import Interpreter, DotName

    prog_text = \
'''
print('start')

func foo(b):
    print('in foo. b = ', b)
    return b*b
    print('after return')

data a: Float const
a = 2*2 + foo(3*4) + foo(2)
print('a = ', a)

print('end')
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print 'module after interpreter run: ---------------------------------'
    print intp.modules['test']
    
    assert intp.modules['test'].get_attribute(DotName('a')).value == 2*2 + (3*4)**2 + 2**2
  
  

def test_print_function_1():
    #py.test.skip('Test the print function. - actual printing, built in objects.')
    print 'Test the print function. - actual printing: Float, String, expression.'
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
#print known constants
print(23)
print('hello ',2, ' the world!')

#print unknown value
data foo: Float
data bar: String
print(foo)
print(bar)

#print unevaluated expression
data a,b: Float
print(a+b)
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
#TODO: assertions



def test_print_function_2():
    #py.test.skip('Test the print function. - actual printing, user defined class.')
    print 'Test the print function. - actual printing, user defined class.'
    from freeode.interpreter import Interpreter
    
    prog_text = \
'''
#print user defined class
class C:
    data a: Float const
    data b: String const
    
    func __str__(this):
        return a.__str__() + ' and ' + b.__str__()
    
data c: C
c.a = 5
c.b = 'hello'
print(c)
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
#TODO: assertions
  
  

def test_print_function_3():
    #py.test.skip('Test the print function. - code generation for: Float, String')
    print 'Test the print function. - code generation for: Float, String'
    from freeode.interpreter import Interpreter
    from freeode.ast import DotName
    
    prog_text = \
'''
class A:
    data a,b,foo: Float
    data bar: String
    
    func dynamic(this):
        #print known constants
        print(23)
        print('hello ',2, ' the world!')
        
        #print unknown value
        print(foo)
        print(bar)
        
        #print unevaluated expression
        print(a+b)
        
compile A
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']

    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    #print sim
    #get the dynamic function with the generated code
    dynamic = sim.get_attribute(DotName('dynamic'))
    assert len(dynamic.statements) == 5



def test_print_function_4():
    #py.test.skip('Test the print function. - code generation for: user defined class.')
    print 'Test the print function. - code generation for: user defined class.'
    from freeode.interpreter import Interpreter
    from freeode.ast import DotName
    
    prog_text = \
'''
#print user defined class
class C:
    data a: Float 
    data b: String
    
    func __str__(this):
        return a.__str__() + ' and ' + b.__str__()
        #return ' and ' + b.__str__()


class A:
    data c: C
    
    func dynamic(this):
        print(c)
        
compile A
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']

    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    print sim
    #get the dynamic function with the generated code
    dynamic = sim.get_attribute(DotName('dynamic'))
    assert len(dynamic.statements) == 1
  
  

def test_interpreter_class_definition_1():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: class definition ...............................................................'
    from freeode.interpreter import Interpreter, DotName

    prog_text = \
'''
print('start')

data pi: Float const
pi = 3.1415

class A:
    print('in A definition')
    data a1: Float const
    data a2: Float const

class B:
    data b1: Float const
    b1 = pi
    data b2: Float const

data a: A const
data b: B const

a.a1 = 1
a.a2 = 2 * b.b1
print('a.a1: ', a.a1, ', a.a2: ', a.a2)

print('end')
'''

    #create the interpreter
    intp = Interpreter()
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print 'module after interpreter run: ---------------------------------'
    print intp.modules['test']
  
    assert (intp.modules['test'].get_attribute(DotName('pi')).value == 3.1415)
    assert (intp.modules['test'].get_attribute(DotName('a'))
                                .get_attribute(DotName('a1')).value == 1)
    assert (intp.modules['test'].get_attribute(DotName('a'))
                                .get_attribute(DotName('a2')).value == 2 * 3.1415)
    assert (intp.modules['test'].get_attribute(DotName('b'))
                                .get_attribute(DotName('b1')).value == 3.1415)
  
  
  
def test_interpreter_class_definition_2():
    '''
    Test user defined classes - correctness of parent attribute.
    
    Data attributes are copied when a class is instantiated. (All attributes
    are constructed when the class is defined.) The parent pointers, which 
    point back to the object that contains each object, must be updated 
    by the copy algorithm.  Otherwise they point to the old parents before the 
    copy.
    
    Interpreter Object has a __deepcopy__ function that takes care of this.
    '''
    #py.test.skip('Test user defined classes - correctness of parent attribute.')
    print 'Test user defined classes - correctness of parent attribute.'
    from freeode.interpreter import (Interpreter, IFloat)
    from freeode.ast import (DotName)

    prog_text = \
'''
class A:
    data z: Float const

class B:
    data a: A const


data b:B const
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
    
    #get the instance objects defined in this program
    mod = intp.modules['test']
    b = mod.get_attribute(DotName('b'))
    a = b.get_attribute(DotName('a'))
    z = a.get_attribute(DotName('z'))
    
    #check the correctness of the parent attributes
    assert b.parent() is mod
    assert a.parent() is b
    assert z.parent() is a



def test_interpreter_method_call():
    #py.test.skip('Method calls do not work! Implement method wrappers!')
    print 'Test interpreter: method call ...............................................................'
    from freeode.interpreter import Interpreter, DotName

    prog_text = \
'''
print('start')

class A:
    data a1: Float const
    data a2: Float const
    
    func compute(this, x):
        print('in compute_a2 x=', x)
        return x + 2
        
data a: A const
a.a1 = a.compute(3)

#print('a.a1 = ', a.a1)

print('end')
'''

    #create the interpreter
    intp = Interpreter()
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
  
    assert (intp.modules['test'].get_attribute(DotName('a'))
                                .get_attribute(DotName('a1')).value == 5)
#    assert False, 'Test'



def test_method_call_this_namespace_1():
    #py.test.skip('Method calls do not work! Implement method wrappers!')
    print 'Test interpreter: method call, this namespace ...............................................................'
    from freeode.interpreter import Interpreter, DotName

    prog_text = \
'''
print('start')

class A:
    data a1: Float const
    data a2: Float const
    
    func compute(this, x):
        print('in compute_a2 x=', x)
        a1 = x
        a2 = a1 + 2
        
data a: A const
a.compute(3)
print('a.a1 = ', a.a1)
print('a.a2 = ', a.a2)

print('end')
'''

    #create the interpreter
    intp = Interpreter()
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
  
    assert (intp.modules['test'].get_attribute(DotName('a'))
                                .get_attribute(DotName('a1')).value == 3)
    assert (intp.modules['test'].get_attribute(DotName('a'))
                                .get_attribute(DotName('a2')).value == 5)
#    assert False, 'Test'

      
      
def test_method_call_this_namespace_2():
    #py.test.skip('Test interpreter: method call, this namespace')
    print 'Test interpreter: method call, this namespace'
    from freeode.interpreter import Interpreter, DotName

    prog_text = \
'''
class A:
    data a1: Float const
    data a2: Float const
    
    func compute(this, x):
        print('in compute_a2 x=', x)
        a1 = x
        a2 = a1 + 2
        
class B:
    data a: A
    
    func compute(this, x):
        a.compute(x)
    
data b: B const
b.compute(3)
print('b.a.a1 = ', b.a.a1)
print('b.a.a2 = ', b.a.a2)
'''

    #create the interpreter
    intp = Interpreter()
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
  
    assert (intp.modules['test'].get_attribute(DotName('b'))
                                .get_attribute(DotName('a'))
                                .get_attribute(DotName('a1')).value == 3)
    assert (intp.modules['test'].get_attribute(DotName('b'))
                                .get_attribute(DotName('a'))
                                .get_attribute(DotName('a2')).value == 5)
#    assert False, 'Test'

      
      
def test_StatementVisitor_assign_const_1():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: assignment. needs working data statement and number ...............................................................'
    from freeode.interpreter import Interpreter, DotName
    
    prog_text = \
'''
data a: Float const
a = 2
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print 'module after interpreter run: ---------------------------------'
    print intp.modules['test']
    
    assert intp.modules['test'].get_attribute(DotName('a')).value == 2
  
  

# -------- Test interpreter object - emit code ----------------------------------------
def test_StatementVisitor_assign_emit_code_1():
    #py.test.skip('Test disabled')
    print 'Test StatementVisitor.assign: emit code without the usual infrastructure.'
    from freeode.interpreter import (Interpreter, IFloat)
    from freeode.ast import (Node, NodeAssignment, NodeOpInfix2)

    prog_text = \
'''
data a: Float variable
data b: Float variable
b = 2*a #emit this statement
'''

    #create the interpreter
    intp = Interpreter()
    #enable collection of statements for compilation
    intp.start_collect_code()
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
    #get the results of the collection process
    stmts, func_locals = intp.stop_collect_code()
  
    print
    print '--------------- main module ----------------------------------'
    #print intp.modules['test']
    #put collected statements into Node for pretty printing
    n = Node(statements=stmts)
    print
    print '--------------- collected statements ----------------------------------'
    #print n
        
    #one statement: b = 2*a    
    assert len(stmts) == 1
    assert isinstance(stmts[0], NodeAssignment)                #  b = 2 * a
    assert isinstance(stmts[0].target, IFloat)           #  b
    assert stmts[0].target.value is None
    assert isinstance(stmts[0].expression, NodeOpInfix2)       #  2*a
    assert isinstance(stmts[0].expression.arguments[0], IFloat)#  2
    assert stmts[0].expression.arguments[0].value == 2
    assert isinstance(stmts[0].expression.arguments[1], IFloat)#  a
    assert stmts[0].expression.arguments[1].value is None
      


def test_StatementVisitor_assign_emit_code_2():
    #py.test.skip('Test interpreter object: emit code without the usual infrastructure.')
    print 'Test StatementVisitor.assign: emit code without the usual infrastructure.'
    from freeode.interpreter import (Interpreter, IFloat)
    from freeode.ast import (Node, NodeAssignment, NodeOpInfix2)

    prog_text = \
'''
data a: Float const
data b: Float variable
data c: Float variable
a = 2*2 #constant no statement emitted
b = 2*a #emit b = 8; compute 2*a at compile time
c = 2*b #emit everything
#print('a = ', a)
#print('b = ', b)
#print('c = ', c)
'''

    #create the interpreter
    intp = Interpreter()
    #enable collection of statements for compilation
    intp.start_collect_code()
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
    #get the results of the collection process
    stmts, func_locals = intp.stop_collect_code()
 
    print
    print '--------------- main module ----------------------------------'
    #print intp.modules['test']
    #put collected statements into Node for pretty printing
    n = Node(statements=stmts)
    print
    print '--------------- collected statements ----------------------------------'
    #print n
        
    assert len(stmts) == 2
    # b = 4
    assert isinstance(stmts[0], NodeAssignment)
    assert isinstance(stmts[0].expression, IFloat) # 8
    assert stmts[0].expression.value == 8
    # c = 2*b
    assert isinstance(stmts[1], NodeAssignment)
    assert isinstance(stmts[1].expression, NodeOpInfix2)        # 2 * b
    assert isinstance(stmts[1].expression.arguments[0], IFloat) # 2
    assert stmts[1].expression.arguments[0].value == 2
    assert isinstance(stmts[1].expression.arguments[1], IFloat) # b
    assert stmts[1].expression.arguments[1].value is None      
      


def test_StatementVisitor__visit_NodeCompileStmt__code_generation_1():
    #py.test.skip('Test StatementVisitor.visit_NodeCompileStmt')
    print 'Test StatementVisitor.visit_NodeCompileStmt:'
    from freeode.interpreter import (Interpreter, IFloat, SimlFunction)
    from freeode.ast import (DotName)

    prog_text = \
'''
class A:
    data b: Float
     
    func dynamic(this):
        b = 2

compile A
'''

    #create the interpreter
    intp = Interpreter()
    #run program
    intp.interpret_module_string(prog_text, None, 'test')
  
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0] 

    #there must be one compiled object present
    assert len(intp.get_compiled_objects()) == 1
    
    comp_obj = intp.get_compiled_objects()[0]
    #the attributes b and dynamic must exist
    assert isinstance(comp_obj.get_attribute(DotName('b')), IFloat)
    assert isinstance(comp_obj.get_attribute(DotName('dynamic')), SimlFunction)
    assert len(comp_obj.get_attribute(DotName('dynamic')).statements) == 1
    
    
    
    
def test_interpreter_user_defined_operators_1():
    '''
    User defined operators must be converted into multiple statements,
    that contain only operations on fundamental types. Intermediate results
    are kept in function local variables, that are stored by the compile 
    statement.
    '''
    #py.test.skip('Test user defined operators - code generation.')
    print 'Test user defined operators - code generation.'
    from freeode.interpreter import Interpreter, IFloat, CallableObject
    from freeode.ast import DotName

    prog_text = \
'''
class Time2:
    data x: Float 

    func __add__(this, other):
        data res: Time2
        res.x = 2*(x + other.x)
        return res
        
    func __assign__(this, other):
        x = other.x


class A:
    data a,b,c: Time2
    
    func dynamic(this):
        c=a+b

compile A
'''

    #create the interpreter and interpret the mini-program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0] 
    
    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    #get the attributes that we have defined
    a_x = sim.get_attribute(DotName('a.x'))
    b_x = sim.get_attribute(DotName('b.x'))
    c_x = sim.get_attribute(DotName('c.x'))
    dynamic = sim.get_attribute(DotName('dynamic'))
    #test some facts about the attributes
    assert isinstance(a_x, IFloat)
    assert isinstance(b_x, IFloat)
    assert isinstance(c_x, IFloat)
    assert isinstance(dynamic, CallableObject)
    
    assert len(dynamic.statements) == 2
    stmt0 = dynamic.statements[0]
    stmt1 = dynamic.statements[1]
    #first statement (res.x = 2*(x + other.x)) assigns to function local variable
    assert stmt0.target not in [a_x, b_x, c_x]
    assert stmt0.expression.operator == '*'
    #second statement (c=a+b) assigns to c.x
    assert stmt1.target is c_x
    #second statement assigns temporary result of previous computation to attribute c.x
    assert stmt0.target is stmt1.expression
    #assert False



def test_interpreter_expression_statement_1():
    '''
    Unevaluated expressions also generate code.
    '''
    #py.test.skip('Test expression statement - code generation.')
    print 'Test expression statement - code generation.'
    from freeode.interpreter import Interpreter, IFloat, CallableObject
    from freeode.ast import DotName, NodeExpressionStmt

    prog_text = \
'''
class A:
    data a,b: Float
    
    func dynamic(this):
        1+2
        a+b

compile A
'''

    #create the interpreter and interpret the mini-program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0] 
    
    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    #get the attributes that we have defined
    a = sim.get_attribute(DotName('a'))
    b = sim.get_attribute(DotName('b'))
    dynamic = sim.get_attribute(DotName('dynamic'))
    #test some facts about the attributes
    assert isinstance(a, IFloat)
    assert isinstance(b, IFloat)
    assert isinstance(dynamic, CallableObject)
    #only one statement is collected (a+b)
    assert len(dynamic.statements) == 1
    stmt0 = dynamic.statements[0]
    assert isinstance(stmt0, NodeExpressionStmt)
    assert stmt0.expression.operator == '+'
    #assert False



def test_interpreter_object_compile_statement():
    py.test.skip('Test interpreter object: compile statement!!!')
    print 'Test interpreter object: compile statement'
    from freeode.interpreter import Interpreter

    prog_text = \
'''
print('start')

class B:
    data b1: Float variable
    
    func foo(this, x):
        b1 = b1 * x
    
class A:
    data a1: Float param
    data b: B variable
    
    func init(this):
        a1 = 1
        b.b1 = 11
        
    func dynamic(this):
        a1 = a1 + 2
        b.foo(a1)

compile A

print('end')
'''

    #create the interpreter
    intp = Interpreter()
    #run program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
    print intp.get_compiled_objects() 

    #TODO: Assertions
    #assert False
      
      

def test_interpreter_dollar_operator_1():
    #py.test.skip('Test interpreter: "$" operator.')
    print 'Test interpreter: "$" operator.'
    from freeode.interpreter import Interpreter, IFloat, CallableObject
    from freeode.ast import DotName

    prog_text = \
'''
class A:
    data a1: Float 

    func dynamic(this):
        $a1 = 2

compile A
'''


    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    print intp.get_compiled_objects()[0] 
    
    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    #get the attributes that we have defined
    a1 = sim.get_attribute(DotName('a1'))
    a1_dt = sim.get_attribute(DotName('a1$time'))
    dynamic = sim.get_attribute(DotName('dynamic'))
    #test some facts about the attributes
    assert isinstance(a1, IFloat)
    assert isinstance(a1_dt, IFloat)
    assert isinstance(dynamic, CallableObject)
    #assert False



def test_interpreter_dollar_operator_2():
    #py.test.skip('Test interpreter: "$" operator. - Problem with user defined classes.')
    print 'Test interpreter: "$" operator. - Problem with user defined classes.'
    from freeode.interpreter import Interpreter

    prog_text = \
'''
class A:
    data z: Float
    
    func dynamic(this):
        $z = 2

class B:
    data a: A

    func dynamic(this):
        a.dynamic()

compile B #this crashes
#compile A #this works
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    print intp.get_compiled_objects()[0] 
  
    #TODO: Assertions

  
def test_interpreter_small_simulation_program():
    #py.test.skip('Test interpreter: small simulation program.!!!')
    print 'Test interpreter: small simulation program.'
    from freeode.interpreter import Interpreter

    prog_text = \
'''
data g: Float const
g = 9.81


class BarrelWithHole:
    data V, h: Float
    data A_bott, A_o, mu, q, g: Float param

    func dynamic(this):
        h = V/A_bott
        $V = q - mu*A_o*sqrt(2*g*h)
#        print('h: ', h)

    func init(this, q_in):
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
        q = q_in #0.05
 
 
class RunTest:
    data system: BarrelWithHole

    func dynamic(this):
        system.dynamic()

    func init(this):
        system.init(0.55)
#        solutionParameters.simulationTime = 100
#        solutionParameters.reportingInterval = 1

    func final(this):
#        graph system.V, system.h
        print('Simulation finished successfully.')
        

compile RunTest
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
    print intp.get_compiled_objects() 
  
    #TODO: Assertions

  
if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_print_function_4()
    pass

