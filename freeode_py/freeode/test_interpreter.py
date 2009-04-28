# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
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
Test code for the interpreter module
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



#TODO: Convert to unit test framework
#-------- Test expression evaluation (only immediate values) ------------------------------------------------------------------------
def test_expression_evaluation_1():
    #py.test.skip('Test expression evaluation (only immediate values)')
    print 'Test expression evaluation (only immediate values)'
    from freeode.interpreter import *
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('0+1*2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #interpret the expression
    exv = ExpressionVisitor(None)
    res = exv.dispatch(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == 2.0
    
    
#----------- Test expression evaluation (access to variables) ---------------------------------------------------------------
def test_expression_evaluation_2():
    #py.test.skip('Test expression evaluation (access to variables)')
    print 'Test expression evaluation (access to variables)'
    from freeode.interpreter import *
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('1 + a * 2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #create module where name lives
    mod = InstModule()
    val_2 = CLASS_FLOAT.construct_instance()
    val_2.value = 2.0
    val_2.role = RoleConstant
    mod.create_attribute(DotName('a'), val_2)
    print
    print 'Module where variable is located: --------------------------------------------'
    print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    
    #interpret the expression
    exv = ExpressionVisitor(None)
    exv.environment = env
    res = exv.dispatch(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == 5.0
    
    
#Test expression evaluation (returning of partially evaluated expression when accessing variables)-------------------
def test_expression_evaluation_3():
    #py.test.skip('Test disabled')
    print 'Test expression evaluation (returning of partially evaluated expression when accessing variables)'
    from freeode.interpreter import *
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('a + 2*2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #create module where name lives
    mod = InstModule()
    #create attribute 'a' with no value
    val_2 = CLASS_FLOAT.construct_instance()
    val_2.value = None
    val_2.role = RoleVariable
    mod.create_attribute(DotName('a'), val_2)
    print
    print 'Module where variable is located: --------------------------------------------'
    print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    
    #interpret the expression
    exv = ExpressionVisitor(None)
    exv.environment = env
    res = exv.dispatch(ex)
    print
    print 'Result object - should be an unevaluated expression: --------------------------------------------------------------'
    print res 
    assert isinstance(res, NodeOpInfix2)
    assert res.operator == '+'

#--------- Test basic execution of statements (no interpreter object) ----------------------------------------------------------------
def test_basic_execution_of_statements():
    #py.test.skip('Test disabled')
    print 'Test basic execution of statements (no interpreter object) .................................'
    from freeode.interpreter import *
    
    prog_text = \
'''
print 'start'

data a:Float const 
data b:Float const 
a = 2*2 + 3*4
b = 2 * a
print 'a = ', a, 'b = ', b

data c:String const
c = 'Hello ' + 'world!'
print 'c = ', c

print 'end'
'''

    #create the built in library
    mod = CLASS_MODULE.construct_instance()
    mod.create_attribute(DotName('Float'), CLASS_FLOAT)
    mod.create_attribute(DotName('String'), CLASS_STRING)
    print
    print 'global namespace - before interpreting statements - built in library: ---------------'
    print mod
           
    #init the interpreter
    env = ExecutionEnvironment()
    exv = ExpressionVisitor(None)
    exv.environment = env
    stv = StatementVisitor(None)
    stv.environment = env
    stv.expression_visitor = exv
    #set up parsing the main module
    stv.environment.global_scope = mod
    stv.environment.local_scope = mod

    #parse the program text
    ps = simlparser.Parser()
    module_code = ps.parseModuleStr(prog_text)
    
    #interpreter main loop
    for stmt in module_code.statements:
        stv.dispatch(stmt)
        
    print
    print 'global namespace - after interpreting statements: -----------------------------------'
    print mod
    
    assert mod.get_attribute(DotName('a')).value == 16
    assert mod.get_attribute(DotName('b')).value == 2*16
  
  
#---------- Test interpreter object: function call ------------------------------------------------
def test_interpreter_object_function_call():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: function call ...............................................................'
    from freeode.interpreter import *

    prog_text = \
'''
print 'start'

func foo(b):
    print 'in foo. b = ', b
    return b*b
    print 'after return'

data a:Float const
a = 2*2 + foo(3*4) + foo(2)
print 'a = ', a
print 'end'
'''
    #create the interpreter
    intp = Interpreter()
    #run mini program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print 'module after interpreter run: ---------------------------------'
    print intp.modules['test']
    
    assert intp.modules['test'].get_attribute(DotName('a')).value == 2*2 + (3*4)**2 + 2**2
  
  
#-------- Test interpreter object: class definition --------------------------------------------------------
def test_interpreter_object_class_definition():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: class definition ...............................................................'
    from freeode.interpreter import *

    prog_text = \
'''
print 'start'

data pi: Float const
pi = 3.1415

class A:
    print 'in A definition'
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
print 'a.a1: ', a.a1, ', a.a2: ', a.a2

print 'end'
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

  
#--------- Test interpreter object: method call ---------------------------------------
def test_interpreter_object_method_call():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: method call ...............................................................'
    from freeode.interpreter import *

    prog_text = \
'''
print 'start'

func times_3(x):
    print 'times_2: x=', x
    return 2*x
    
class A:
    data a1: Float const
    data a2: Float const
    
    func compute(x):
        print 'in compute_a2 x=', x
        a1 = x
        a2 = x + times_3(a1)
        return a2
        
data a: A const
a.compute(3)
print 'a.a1 = ', a.a1
print 'a.a2 = ', a.a2

#compile test: A

print 'end'
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
                                .get_attribute(DotName('a2')).value == 9)

      
#---------------- Test interpreter object: emit code simple ----------------------------------------
def test_interpreter_object_emit_code_simple():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: emit code simple ...............................................................'
    from freeode.interpreter import *

    prog_text = \
'''
print 'start'


data a: Float const
data b: Float variable
data c: Float variable
a = 2*2 #constant no statement emitted
b = 2*a #compute 2*a at compile time
c = 2*b #emit everything
print 'a = ', a
print 'end'
'''

    #create the interpreter
    intp = Interpreter()
    #enable collection of statements for compilation
    intp.compile_stmt_collect = []
    #interpret the program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print '--------------- main module ----------------------------------'
    print intp.modules['test']
    #put collected statements into Node for pretty printing
    n = Node(stmts=intp.compile_stmt_collect)
    print
    print '--------------- collected statements ----------------------------------'
    print n
        
    #TODO: Assertions
      
    #------------- Test interpreter object: compile statement ...............................................................
def test_interpreter_object_compile_statement():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: compile statement ...............................................................'
    from freeode.interpreter import *

    prog_text = \
'''
print 'start'

class B:
    data b1: Float variable
    
    func foo(x):
        b1 = b1 * x
    
class A:
    data a1: Float param
    data b: B variable
    
    func init():
        a1 = 1
        b.b1 = 11
        
    func dynamic():
        a1 = a1 + 2
        b.foo(a1)

compile A

print 'end'
'''

    #create the interpreter
    intp = Interpreter()
    #run program
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
    print intp.compile_module

    #TODO: Assertions
      
      
    #------------------------- Test interpreter object: "$" operator ...............................................
def test_interpreter_object_dollar_operator():
    #py.test.skip('Test disabled')
    print 'Test interpreter object: "$" operator ...............................................................'
    from freeode.interpreter import *

    prog_text = \
'''
print 'start'

class B:
    data b1: Float variable
    
    func foo(x):
        $b1 = b1 * x
    
class A:
    data a1: Float param
    data b: B variable
    
    func init():
        a1 = 1
        b.b1 = 11
        
    func dynamic():
        a1 = a1 + 2
        b.foo(a1)

compile A

print 'end'
'''

    #create the interpreter
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
    print intp.compile_module
  
    #TODO: Assertions

  
if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_interpreter_object_function_call()
    pass

