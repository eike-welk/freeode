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
except ImportError:
    print 'No py library, many tests may fail!'



def test_data_statement_simple_1(): #IGNORE:C01111
    #py.test.skip('Test data statement: create attributes')
    print 'Test data statement: create attributes'
    from freeode.interpreter import Interpreter, IFloat, IString
    from freeode.ast import DotName
    
    prog_text = \
'''
data a: Float const
data b: String const
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    mod = intp.modules['test']
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print mod
    
    a = mod.get_attribute(DotName('a'))
    assert isinstance(a, IFloat)
    b = mod.get_attribute(DotName('b'))
    assert isinstance(b, IString)
  
  

def test_data_statement_roles_1(): #IGNORE:C01111
    #py.test.skip('Test data statement: create attributes with different roles')
    print 'Test data statement: create attributes with different roles'
    from freeode.interpreter import Interpreter
    from freeode.ast import (DotName, RoleConstant, RoleParameter, 
                             RoleVariable)
    
    prog_text = \
'''
data a: Float const
data b: Float param
data c: Float variable
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    mod = intp.modules['test']
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print mod
    
    a = mod.get_attribute(DotName('a'))
    assert a.role is RoleConstant
    b = mod.get_attribute(DotName('b'))
    assert b.role is RoleParameter
    c = mod.get_attribute(DotName('c'))
    assert c.role is RoleVariable
    
  

def test_data_statement_roles_2(): #IGNORE:C01111
    '''
    In user defined classes the role should be propagated recursively to the 
    child attributes.
    However, the child attributes' roles are not simply replaced, but only 
    changed if they are more variable than the new role. 
    
    These are the main roles, the variable character increases from left to 
    right:
    RoleConstant, RoleParameter, RoleVariable, RoleUnkown
    const,        param,         variable,     role_unknown
    '''
    msg = 'Test data statement: roles should be propagated to child attributes.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.ast import (DotName, RoleConstant, RoleParameter, 
                             RoleVariable)
    
    prog_text = \
'''
class A:
    data c: Float const
    data p: Float param
    data v: Float variable
    
data ac: A const
data ap: A param
data av: A variable
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    mod = intp.modules['test']
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print mod
    
    #all attributes should be const
    a_curr = mod.get_attribute(DotName('ac'))
    c = a_curr.get_attribute(DotName('c'))
    p = a_curr.get_attribute(DotName('p'))
    v = a_curr.get_attribute(DotName('v'))
    assert c.role is RoleConstant
    assert p.role is RoleConstant
    assert v.role is RoleConstant
  
    #Roles: c: const; p,v: param
    a_curr = mod.get_attribute(DotName('ap'))
    c = a_curr.get_attribute(DotName('c'))
    p = a_curr.get_attribute(DotName('p'))
    v = a_curr.get_attribute(DotName('v'))
    assert c.role is RoleConstant
    assert p.role is RoleParameter
    assert v.role is RoleParameter
  
    #Roles: c: const; p: param; v: variable
    a_curr = mod.get_attribute(DotName('av'))
    c = a_curr.get_attribute(DotName('c'))
    p = a_curr.get_attribute(DotName('p'))
    v = a_curr.get_attribute(DotName('v'))
    assert c.role is RoleConstant
    assert p.role is RoleParameter
    assert v.role is RoleVariable
  
  

def test_builtin_function_call_1(): #IGNORE:C01111
    #py.test.skip('Test disabled')
    print 'Test interpreter object: call built in function sqrt...............................................................'
    from freeode.interpreter import Interpreter
    from freeode.ast import DotName
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
  
  

def test_builtin_function_call_2(): #IGNORE:C01111
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
  
  

def test_function_definition_1(): #IGNORE:C01111
    msg = '''Test all legal styles of function definitions.'''
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter

    prog_text = \
'''
func foo1(a, b):
    return a + b
    
func foo2(a=1, b=2):
    return a + b
    
func foo3(a:Float, b:Float):
    return a + b

func foo4(a:Float=1, b:Float=2):
    return a + b
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
  
  

def test_function_call_1(): #IGNORE:C01111
    msg = '''Test all legal styles of function calls.'''
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.ast import DotName

    prog_text = \
'''
func foo(a:Float=1, b:Float=2):
    return a + b

data a,b,c,d,e,f,g,h: Float const

a = foo()           # a == 3       - line 7
b = foo(5)          # b = 7
c = foo(5, 6)       # c = 11
d = foo(a=10)       # d = 12       - line 10
e = foo(b=20)       # e = 21
f = foo(5, b=20)    # f = 25
g = foo(a=10, b=20) # g = 30
h = foo(b=20, a=10) # h = 30       - line 14
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
    
    #get the interpreted module
    mod = intp.modules['test']
#    print
#    print 'module after interpreter run: ---------------------------------'
#    print mod
    
    #test the results
    a = mod.get_attribute(DotName('a'))
    b = mod.get_attribute(DotName('b'))
    c = mod.get_attribute(DotName('c'))
    d = mod.get_attribute(DotName('d'))
    e = mod.get_attribute(DotName('e'))
    f = mod.get_attribute(DotName('f'))
    g = mod.get_attribute(DotName('g'))
    h = mod.get_attribute(DotName('h'))
    assert a.value == 3
    assert b.value == 7
    assert c.value == 11
    assert d.value == 12
    assert e.value == 21
    assert f.value == 25
    assert g.value == 30
    assert h.value == 30
 
  

def test_function_definition_and_call_1(): #IGNORE:C01111
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
  
  

def test_print_function_1(): #IGNORE:C01111
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
    #TODO: assertions



def test_print_function_2(): #IGNORE:C01111
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
    #TODO: assertions
  
  

def test_print_function_3(): #IGNORE:C01111
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



def test_print_function_4(): #IGNORE:C01111
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
    #print sim
    
    #get the dynamic function with the generated code
    dynamic = sim.get_attribute(DotName('dynamic'))
    assert len(dynamic.statements) == 1
  
  

def test_graph_function_1(): #IGNORE:C01111
    #py.test.skip('Test the print function. - code generation for: user defined class.')
    print 'Test the print function. - code generation for: user defined class.'
    from freeode.interpreter import Interpreter
    from freeode.ast import DotName
    
    prog_text = \
'''
class A:
    data c: Float
    
    func final(this):
        graph(c)
        
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
    
    #get the final function with the generated code
    final = sim.get_attribute(DotName('final'))
    assert len(final.statements) == 1
  
  

def test_interpreter_class_definition_1(): #IGNORE:C01111
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
  
  
  
def test_interpreter_class_definition_2(): #IGNORE:C01111
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



def test_interpreter_method_call(): #IGNORE:C01111
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



def test_method_call_this_namespace_1(): #IGNORE:C01111
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

      
      
def test_method_call_this_namespace_2(): #IGNORE:C01111
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

      
      
def test_StatementVisitor_assign_const_1(): #IGNORE:C01111
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
def test_StatementVisitor_assign_emit_code_1(): #IGNORE:C01111
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
      


def test_StatementVisitor_assign_emit_code_2(): #IGNORE:C01111
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
      


def test_StatementVisitor__visit_NodeCompileStmt__code_generation_1(): #IGNORE:C01111
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
    
    
    
    
def test_interpreter_user_defined_operators_1(): #IGNORE:C01111
    '''
    User defined operators must be converted into multiple statements,
    that contain only operations on fundamental types. Intermediate results
    are kept in function local variables, that are stored by the compile 
    statement.
    
    The used Siml class simulates a geometric vector class.
    '''
    #py.test.skip('Test user defined operators - code generation.')
    print 'Test user defined operators - code generation.'
    from freeode.interpreter import Interpreter, IFloat, CallableObject
    from freeode.ast import DotName

    prog_text = \
'''
class Vec1D:
    data x: Float role_unknown

    func __add__(this, other):
        data res: Vec1D
        res.x = x + other.x
        return res
        
    func __assign__(this, other):
        x = other.x


class A:
    data a,b,c: Vec1D
    
    func dynamic(this):
        #--- invoke the operators ----
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
    #first statement (res.x = x + other.x) assigns to function local variable
    assert stmt0.target is not a_x 
    assert stmt0.target is not b_x 
    assert stmt0.target is not c_x
    assert stmt0.expression.operator == '+'
    #second statement (c=a+b) assigns to c.x
    assert stmt1.target is c_x
    #second statement assigns temporary result of previous computation to attribute c.x
    assert stmt0.target is stmt1.expression
    #assert False



def test_interpreter_user_defined_operators_2(): #IGNORE:C01111
    '''
    User defined operators must also work with constant data. 
    Same class as in previous test, but all variables are constant.
    
    The used Siml class simulates a geometric vector class.
    '''
    #py.test.skip('Test user defined operators - code generation.')
    print 'Test user defined operators - code generation.'
    from freeode.interpreter import Interpreter 
    from freeode.ast import DotName, RoleConstant

    prog_text = \
'''
class Vec1D:
    data x: Float role_unknown

    func __add__(this, other):
        data res: Vec1D
        res.x = x + other.x
        return res
        
    func __assign__(this, other):
        x = other.x


data a,b,c: Vec1D const
a.x = 2
b.x = 3


#--- invoke the operators ----
c=a+b
'''

    #create the interpreter and interpret the mini-program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    
    mod = intp.modules['test']
    #print
    #print 'Interpreted module: -----------------------------------------------------'
    #print mod
    
    #get the attributes that we have defined
    a = mod.get_attribute(DotName('a'))
    a_x = a.get_attribute(DotName('x'))
    assert a_x.role == RoleConstant
    assert a_x.value == 2
    b = mod.get_attribute(DotName('b'))
    b_x = b.get_attribute(DotName('x'))
    assert b_x.role == RoleConstant
    assert b_x.value == 3
    c = mod.get_attribute(DotName('c'))
    c_x = c.get_attribute(DotName('x'))
    assert c_x.role == RoleConstant
    assert c_x.value == 5
    


def test_interpreter_expression_statement_1(): #IGNORE:C01111
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



def test_user_defined_class_roles_1(): #IGNORE:C01111
    '''
    The role keywords (const, param, variable, ...) should work with user 
    defined classes too.
    '''
    #py.test.skip('Test user defined classes with different roles.')
    print 'Test user defined classes with different roles.'
    from freeode.interpreter import Interpreter
    from freeode.ast import (DotName, RoleConstant, RoleAlgebraicVariable)
    
    prog_text = \
'''
class A:
    data a: Float

#use the class as a constant
data ac: A const
ac.a = 2

class B:
    #use the class as a variable
    data av: A 
    data v: Float
    
    func dynamic(this):
        av.a = v
        
compile B
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
#    print
    mod = intp.modules['test']
#    print 'module after interpreter run: ---------------------------------'
#    print mod
    ac = mod.get_attribute(DotName('ac'))
    a = ac.get_attribute(DotName('a'))
    assert a.role == RoleConstant

#    #get flattened object
    sim = intp.get_compiled_objects()[0] 
#    print 'Flattened object: ---------------------------------'
#    print sim
    av_a = sim.get_attribute(DotName('av.a'))
    assert av_a.role == RoleAlgebraicVariable
  
  

def test_function_return_value_roles_1(): #IGNORE:C01111
    '''
    User defined functions can be called from constant and from variable 
    environments. Test the roles of their return values.
    This test only involves fundamental types.
    '''
    #py.test.skip('Test roles of return values of user defined functions.')
    print 'Test roles of return values of user defined functions.'
    from freeode.interpreter import Interpreter
    from freeode.ast import (DotName, RoleConstant, RoleAlgebraicVariable)
    
    prog_text = \
'''
func plus2(x):
    data r: Float
    r = x + 2
    return r

data ac,bc: Float const
ac = 3
bc = plus2(ac)


class B:
    data av,bv: Float
    
    func dynamic(this):
        bv = plus2(av)
        
compile B
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
#    print
    mod = intp.modules['test']
#    print 'module after interpreter run: ---------------------------------'
#    print mod
    ac = mod.get_attribute(DotName('ac'))
    bc = mod.get_attribute(DotName('bc'))
    assert ac.role == RoleConstant
    assert bc.role == RoleConstant
    assert ac.value == 3
    assert bc.value == 5

#    #get flattened object
    sim = intp.get_compiled_objects()[0] 
#    print 'Flattened object: ---------------------------------'
#    print sim
    av = sim.get_attribute(DotName('av'))
    bv = sim.get_attribute(DotName('bv'))
    assert av.role == RoleAlgebraicVariable
    assert bv.role == RoleAlgebraicVariable
  
  

def test_interpreter_dollar_operator_1(): #IGNORE:C01111
    msg = 'Test "$" operator. Basic capabililities.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter, IFloat, CallableObject
    from freeode.ast import DotName, RoleStateVariable, RoleTimeDifferential

    prog_text = \
'''
class A:
    data a1: Float 

    func dynamic(this):
        $a1 = a1

compile A
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0] 
    
    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    #get the attributes that we have defined
    a1 = sim.get_attribute(DotName('a1'))
    a1_dt = sim.get_attribute(DotName('a1$time'))   #implicitly defined by $ operator
    dynamic = sim.get_attribute(DotName('dynamic'))
    
    #test some facts about the attributes
    assert isinstance(a1, IFloat)        #a1 is state variable, because it 
    assert a1.role == RoleStateVariable  #has derivative
    assert isinstance(a1_dt, IFloat)     
    assert a1_dt.role == RoleTimeDifferential # $a1 is a time differential
    assert isinstance(dynamic, CallableObject)
    
    #test if assignment really is 'a1$time' = 'a1'
    assign = dynamic.statements[0]
    assert assign.target is a1_dt
    assert assign.expression is a1
    #assert False



def test_interpreter_dollar_operator_2(): #IGNORE:C01111
    msg = '''
    Test "$" operator. 
    Bug: $ operator did not work with attributes of user defined classes.
    Background: Class instantiation did not get parent refferences right.
    '''
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter, CallableObject, IFloat
    from freeode.ast import DotName, RoleStateVariable, RoleTimeDifferential

    prog_text = \
'''
class A:
    data z: Float
    
    func dynamic(this):
        $z = z

class B:
    data a: A

    func dynamic(this):
        a.dynamic()

compile B
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0]
    #TODO: Assertions

    #get flattened object
    sim = intp.get_compiled_objects()[0] 
    #get the attributes that we have defined
    az = sim.get_attribute(DotName('a.z'))
    az_dt = sim.get_attribute(DotName('a.z$time'))   #implicitly defined by $ operator
    dynamic = sim.get_attribute(DotName('dynamic'))
    #test some facts about the attributes
    assert isinstance(az, IFloat)        #a1 is state variable, because it 
    assert az.role == RoleStateVariable  #has derivative
    assert isinstance(az_dt, IFloat)     
    assert az_dt.role == RoleTimeDifferential # $a1 is time differential
    assert isinstance(dynamic, CallableObject)
    
    #test if assignment really is 'a1$time' = 'a1'
    assign = dynamic.statements[0]
    assert assign.target is az_dt
    assert assign.expression is az
    #assert False

  
  
def test_compile_statement__small_simulation_program(): #IGNORE:C01111
    msg = 'Test compile statement: see if small simulation program can be compiled.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter

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
#        print('h: ', h)

    func initialize(this, q_in):
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
        q = q_in #0.05
 
                                                   #line 20
class RunTest:
    data system: BarrelWithHole

    func dynamic(this):
        system.dynamic()

    func initialize(this):
        system.initialize(0.55)
#        solutionParameters.simulationTime = 100
#        solutionParameters.reportingInterval = 1  #line 30

    func final(this):
#        graph(system.V, system.h)
        print('Simulation finished successfully.')
        

compile RunTest
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0] 
    
  
  
def test_compile_statement_1(): #IGNORE:C01111
    msg = '''
    Test the compile statement 
    - Flattening and storage of functions' local variables'''
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter, IFloat, CallableObject
    from freeode.ast import DotName

    prog_text = \
'''
class A:
    data a1: Float 
    
    func foo(this, x):
        return x
        
    func dynamic(this):
        data b,c: Float
        b = foo(a1)
        c = foo(a1 + b)
        $a1 = b

compile A
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    #print intp.modules['test']
    #print intp.get_compiled_objects()[0] 
    
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

    #check number of attributes, most are automatically generated
    #attributes:           initialize, dynamic, final, 
    #instance variables:   a1, $a1, 
    #local variables:      A.dynamic.b, A.dynamic.c, 
    #intermediate result:  A.foo.x, (2nd call)
    assert len(sim.attributes) == 8
    


def test_pass_statement_1(): #IGNORE:C01111
    msg = '''
    Test the pass statement. Try the normal use case.
    - The pass statement does nothing it is necessary to create empty 
    functions and classes. 
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isinstance, 
                                     CallableObject, TypeObject, IFloat)
    from freeode.ast import DotName

    prog_text = \
'''
#empty class body
class Dummy:
    pass

data d: Dummy const


#empty function body
func f_dummy():
    pass
    
f_dummy()
    
    
#call class with pass statement in compiled code
class A:
    data x: Float 
    data d: Dummy
    
    func foo(this):
        pass
        
    func dynamic(this):
        foo()
        $x = 1

compile A
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    
    #test the module a bit
    mod = intp.modules['test']
    #print mod
    class_Dummy = mod.get_attribute(DotName('Dummy'))
    d = mod.get_attribute(DotName('d'))
    f_dummy = mod.get_attribute(DotName('f_dummy'))
    class_A = mod.get_attribute(DotName('A'))
    assert siml_isinstance(d, class_Dummy)
    assert isinstance(f_dummy, CallableObject)
    assert isinstance(class_A, TypeObject)

    #Test the compiled object
    flat_A = intp.get_compiled_objects()[0] 
    #print flat_A
    x = flat_A.get_attribute(DotName('x'))
    x_time = flat_A.get_attribute(DotName('x$time'))
    assert isinstance(x, IFloat)
    assert isinstance(x_time, IFloat)
    assert len(flat_A.attributes) == 5
    


def test_pass_statement_2(): #IGNORE:C01111
    msg = '''
    Test the pass statement. Try stupid but legal cases.
    - The pass statement should just do nothing. 
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isinstance, 
                                     CallableObject, TypeObject, IFloat)
    from freeode.ast import DotName

    prog_text = \
'''
#class with definition after pass statement
class A:
    pass
    data x: Float role_unknown

data a:A
a.x = 2

#function with statement after pass statement
func add2(x):
    pass
    return x + 2
    
data four: Float const
four = add2(2)
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    
    #test the module a bit
    mod = intp.modules['test']
    #print mod
    class_A = mod.get_attribute(DotName('A'))
    a = mod.get_attribute(DotName('a'))
    a_x = a.get_attribute(DotName('x'))
    add2 = mod.get_attribute(DotName('add2'))
    four = mod.get_attribute(DotName('four'))
    assert isinstance(class_A, TypeObject)
    assert siml_isinstance(a, class_A)
    assert isinstance(a_x, IFloat)
    assert a_x.value == 2
    assert isinstance(add2, CallableObject)
    assert isinstance(four, IFloat)
    assert four.value == 4



def test_if_statement_1(): #IGNORE:C01111
    msg = '''
    Test the if statement. Just constant code, no code creation.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isinstance, 
                                     CallableObject, TypeObject, IFloat)
    from freeode.ast import DotName

    prog_text = \
'''
data a,b: Float const
a = 2 

if a == 1:
    b = 1
elif a == 2:
    b = 2
else:
    b = 3
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    
    #test the module a bit
    mod = intp.modules['test']
    #print mod
    a = mod.get_attribute(DotName('a'))
    b = mod.get_attribute(DotName('b'))
    print 'b = ', b.value
    assert a.value == 2
    assert b.value == 2



def test_if_statement_2(): #IGNORE:C01111
    msg = '''
    Test the if statement. Code is generated and condition involves variables.
    All branches of the statement must be visited.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isrole, IFloat, IBool)
    from freeode.ast import DotName, NodeIfStmt, NodeAssignment, RoleConstant

    prog_text = \
'''
class A:
    data a,b: Float
    
    func dynamic(this):       
        if a == 1:
            b = 1
        elif a == 2:
            b = 2
        else:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    mod = intp.modules['test']
    #print mod
    
    sim = intp.get_compiled_objects()[0]
    #print sim
    #look at variables
    a = sim.get_attribute(DotName('a'))
    assert a.is_assigned == False
    b = sim.get_attribute(DotName('b'))
    assert b.is_assigned == True
    #look at generated function and if statement
    dynamic = sim.get_attribute(DotName('dynamic'))
    assert len(dynamic.statements) == 1 #function has one statement
    if_stmt = dynamic.statements[0]
    assert isinstance(if_stmt, NodeIfStmt)
    assert len(if_stmt.clauses) == 3  #if statement has 3 clauses
    clause_a_1 = if_stmt.clauses[0]
    clause_a_2 = if_stmt.clauses[1]
    clause_a_3 = if_stmt.clauses[2]
    #each clause contains one assignment
    assert len(clause_a_1.statements) == 1
    assert isinstance(clause_a_1.statements[0], NodeAssignment)
    assert len(clause_a_2.statements) == 1
    assert isinstance(clause_a_2.statements[0], NodeAssignment)
    assert len(clause_a_3.statements) == 1
    assert isinstance(clause_a_3.statements[0], NodeAssignment)
    #the last clause is an else statement: condition equivalent to True, constant 
    assert isinstance(clause_a_3.condition, (IFloat, IBool))
    assert siml_isrole(clause_a_3.condition.role, RoleConstant)
    assert bool(clause_a_3.condition.value) is True



def test_if_statement_3(): #IGNORE:C01111
    msg = '''
    Test the if statement. Code is generated but all conditions evaluate 
    to false. No if statement is generated.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isrole, IFloat, IBool)
    from freeode.ast import DotName, NodeIfStmt, NodeAssignment, RoleConstant

    prog_text = \
'''
class A:
    data a,b: Float
    
    func dynamic(this):       
        if 0 == 1:
            b = 1
        elif 0 == 2:
            b = 2
        elif 0 == 3:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    mod = intp.modules['test']
    #print mod
    
    sim = intp.get_compiled_objects()[0]
    #print sim
    #look at variables
    a = sim.get_attribute(DotName('a'))
    assert a.is_assigned == False
    b = sim.get_attribute(DotName('b'))
    assert b.is_assigned == False
    #look at generated function and if statement
    dynamic = sim.get_attribute(DotName('dynamic'))
    assert len(dynamic.statements) == 0 #function has no statement



def test_if_statement_4_1(): #IGNORE:C01111
    msg = '''
    Test the if statement. Code is generated and condition involves variables.
    There is no catch all (else) statement. The interpreter must complain about it.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isrole, IFloat, IBool, UserException)
    from freeode.ast import DotName, NodeIfStmt, NodeAssignment, RoleConstant

    prog_text = \
'''
class A:
    data a,b: Float
    data c: Float const
    
    func dynamic(this):       
        if a == 1:
            b = 1
        elif a == 2:
            b = 2
        elif a == 3:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    try:
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print 'Exception is OK'
        print e
    else:
        assert False, 'No exception is raised.'



def test_if_statement_4_2(): #IGNORE:C01111
    msg = '''
    Test the if statement. Code is generated and condition involves variables.
    There is no else statement, but one statement is always True.
    The interpreter must accept this case. The statement which is always true 
    becomes the 'else' clause.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isrole, IFloat, IBool, UserException)
    from freeode.ast import DotName, NodeIfStmt, NodeAssignment, RoleConstant

    prog_text = \
'''
class A:
    data a,b: Float
    data c: Float const
    
    func dynamic(this):       
        if a == 1:
            b = 1
        elif 2 == 2:
            b = 2
        elif a == 3:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    mod = intp.modules['test']
    #print mod
    
    sim = intp.get_compiled_objects()[0]
    #print sim
    #look at variables
    a = sim.get_attribute(DotName('a'))
    assert a.is_assigned == False
    b = sim.get_attribute(DotName('b'))
    assert b.is_assigned == True
    #look at generated function and if statement
    dynamic = sim.get_attribute(DotName('dynamic'))
    assert len(dynamic.statements) == 1 #function has one statement
    if_stmt = dynamic.statements[0]
    assert isinstance(if_stmt, NodeIfStmt)
    #if statement has 2 clauses, although the original if has 3 clauses:
    # - clause 2 has become the else clause
    assert len(if_stmt.clauses) == 2  
    clause_a_1 = if_stmt.clauses[0]
    clause_2_2 = if_stmt.clauses[1]
    #each clause contains one assignment
    assert len(clause_a_1.statements) == 1
    assert isinstance(clause_a_1.statements[0], NodeAssignment)
    assert len(clause_2_2.statements) == 1
    assert isinstance(clause_2_2.statements[0], NodeAssignment)
    #the last clause is an else statement: condition equivalent to True, constant 
    assert isinstance(clause_2_2.condition, (IFloat, IBool))
    assert siml_isrole(clause_2_2.condition.role, RoleConstant)
    assert bool(clause_2_2.condition.value) is True



def test_if_statement_5(): #IGNORE:C01111
    msg = '''
    Test the if statement. Code is generated but condition involves only constants.
    Only one clause is visited, and the if statement is converted to linear code.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, siml_isrole, IFloat, IBool)
    from freeode.ast import DotName, NodeIfStmt, NodeAssignment, RoleConstant

    prog_text = \
'''
class A:
    data a,b: Float
    
    func dynamic(this):       
        if 2 == 1:
            b = 1
        elif 2 == 2:
            b = 2
        else:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    mod = intp.modules['test']
    #print mod
    
    sim = intp.get_compiled_objects()[0]
    #print sim
    #look at variables
    a = sim.get_attribute(DotName('a'))
    assert a.is_assigned == False
    b = sim.get_attribute(DotName('b'))
    assert b.is_assigned == True
    #look at generated function and if statement
    dynamic = sim.get_attribute(DotName('dynamic'))
    #function has one statement
    assert len(dynamic.statements) == 1 
    #But this statement is an assignment, NOT an if statement
    assign_stmt = dynamic.statements[0]
    assert isinstance(assign_stmt, NodeAssignment)
    #This assignment must be from clause 2:
    #    b = 2
    target = assign_stmt.target
    expr = assign_stmt.expression
    assert target is b
    assert isinstance(expr, IFloat)
    assert expr.value == 2



if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_if_statement_5()
    pass

