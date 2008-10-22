# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration and little bits of text and code came from:               *
#     'fourFn.py', 'simpleArith.py' example programs, by Paul McGuire,     *
#     the 'Spark' library by John Aycock,                                  *
#     and the Python Reference Manual by Guido van Rossum.                 *
#    Many thanks for their excellent contributions to publicly available   *
#    knowledge.                                                            *
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

from freeode.interpreter import *



#TODO: Convert to unit test framework
#-------- Test expression evaluation (only immediate values) ------------------------------------------------------------------------
doTest = True
#    doTest = False
if doTest:
    print 'Test expression evaluation (only immediate values) .......................................'
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('0+1*2')
#    ex = ps.parseExpressionStr('"a"+"b"')
    print ex
    
    exv = ExpressionVisitor(None)
    res = exv.dispatch(ex)
    print 'res = ', res 
    
    
#----------- Test expression evaluation (access to variables) ---------------------------------------------------------------
doTest = True
#    doTest = False
if doTest:
    print 'Test expression evaluation (access to variables) ...................................'
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('1 + a * 2')
#        ex = ps.parseExpressionStr('"a"+"b"')
    print ex
    
    #create module where name lives
    mod = InstModule()
    val_2 = CLASS_FLOAT.construct_instance()
    val_2.value = 2.0
    val_2.role = RoleConstant
    mod.create_attribute(DotName('a'), val_2)
    
    env = ExecutionEnvironment()
    env.global_scope = mod
    print mod
    
    exv = ExpressionVisitor(None)
    exv.environment = env
    res = exv.dispatch(ex)
    print 'res = ', res 
    
    
    #Test expression evaluation (returning of partially evaluated expression when accessing variables)-------------------
    doTest = True
#    doTest = False
    if doTest:
        print 'Test expression evaluation (returning of partially evaluated expression when accessing variables) ...................................'
        ps = simlparser.Parser()
        ex = ps.parseExpressionStr('a + 2*2')
#        ex = ps.parseExpressionStr('"a"+"b"')
        print ex
        
        #create module where name lives
        mod = InstModule()
        #create attribute
        val_2 = CLASS_FLOAT.construct_instance()
        val_2.value = None
        val_2.role = RoleVariable
        mod.create_attribute(DotName('a'), val_2)
        
        env = ExecutionEnvironment()
        env.global_scope = mod
        print mod
        
        exv = ExpressionVisitor(None)
        exv.environment = env
        res = exv.dispatch(ex)
        print 'res = ', res 
    
    
#--------- Test basic execution of statements (no interpreter object) ----------------------------------------------------------------
doTest = True
#    doTest = False
if doTest:
    print 'Test basic execution of statements (no interpreter object) ...............................................................'
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
    print mod
           
    #init the interpreter
    env = ExecutionEnvironment()
    exv = ExpressionVisitor(None)
    exv.environment = env
    stv = StatementVisitor(None)
    stv.environment = env
    stv.expression_visitor = exv

    #parse the program text
    ps = simlparser.Parser()
    module_code = ps.parseModuleStr(prog_text)
    
    #set up parsing the main module
    stv.environment.global_scope = mod
    stv.environment.local_scope = mod
    #interpreter main loop
    for stmt in module_code.statements:
        stv.dispatch(stmt)
        
    print
    print mod
  
  
#---------- Test interpreter object: function call ------------------------------------------------
doTest = True
#    doTest = False
if doTest:
    print 'Test interpreter object: function call ...............................................................'
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
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
  
  
#-------- Test interpreter object: class definition --------------------------------------------------------
doTest = True
#    doTest = False
if doTest:
    print 'Test interpreter object: class definition ...............................................................'
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
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
  
  
#--------- Test interpreter object: method call ---------------------------------------
doTest = True
#    doTest = False
if doTest:
    print 'Test interpreter object: method call ...............................................................'
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
    intp.interpret_module_string(prog_text, None, 'test')
  
    print
    print intp.modules['test']
  
      
#---------------- Test interpreter object: emit code simple ----------------------------------------
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: emit code simple ...............................................................'
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
      
        print '--------------- main module ----------------------------------'
        print intp.modules['test']
        #put collected statements into Node for pretty printing
        n = Node(stmts=intp.compile_stmt_collect)
        print '--------------- collected statements ----------------------------------'
        print n
        
      
    #------------- Test interpreter object: compile statement ...............................................................
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: compile statement ...............................................................'
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
        intp.interpret_module_string(prog_text, None, 'test')
      
        print
        print intp.modules['test']
        print intp.compile_module
      
      
    #------------------------- Test interpreter object: "$" operator ...............................................
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: "$" operator ...............................................................'
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
      
      

  
      