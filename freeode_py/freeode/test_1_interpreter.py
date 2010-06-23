# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2008 - 2010 by Eike Welk                                *
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
from __future__ import absolute_import              


from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises
    
    
    
#-------- Test IntArgumentList class ------------------------------------------------------------------------#
def test_Signature_1(): #IGNORE:C01111
    msg = 'Signature: construction'
    #skip_test(msg)
    print msg
    
    from freeode.util import UserException
    from freeode.interpreter import Signature, NodeFuncArg, IFloat
    
    #Test normal construction only positional argument: f(a, b)
    Signature([NodeFuncArg('a'), NodeFuncArg('b')])
    #Test normal construction with keyword arguments: f(a, b=1)
    val_1 = IFloat()
    Signature([NodeFuncArg('a'), NodeFuncArg('b', default_value=val_1)])
    
    #Errors:
    #argument list with two identical argument names: f(a, a)
    def raise_1():
        Signature([NodeFuncArg('a'), 
                   NodeFuncArg('a')])
    assert_raises(UserException, 3200120, raise_1)
        
    #argument list with keyword argument before positional argument: f(a=1, b)
    def raise_2():
        val_1 = IFloat()
        Signature([NodeFuncArg('a', default_value=val_1), NodeFuncArg('b')])
    assert_raises(UserException, 3200110, raise_2)
    
    
    
def test_Signature_2(): #IGNORE:C01111
    msg = 'Signature: test calling (binding) signature has only positional arguments.'
    #skip_test(msg)
    print msg
    
    from freeode.util import UserException
    from freeode.interpreter import (Signature, NodeFuncArg, IFloat,
                                     Interpreter)
    
    #Interpreter for initial evaluation of type annotations
    intp = Interpreter()
    
    #argument list for testing
    sig = Signature([NodeFuncArg('a'),
                    NodeFuncArg('b')])
    sig.evaluate_type_specs(intp)
    #some interpreter level values
    val_1 = IFloat(1)
    val_2 = IFloat(2)
    
    #call with correct number of positional arguments
    arg_vals = sig.parse_function_call_args([val_1, val_2], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    #call with correct number of keyword arguments
    arg_vals = sig.parse_function_call_args([], {'a':val_1,  
                                                'b':val_2})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    #call with too few arguments
    def raise_1():
        sig.parse_function_call_args([], {})
    assert_raises(UserException, 3200280, raise_1)

        
    #call with too many positional arguments
    def raise_2():
        sig.parse_function_call_args([val_1, val_2, val_2], {})
    assert_raises(UserException, 3200250, raise_2)
       
    #call with unknown keyword argument
    def raise_3():
        sig.parse_function_call_args([], {'a':val_1,  
                                         'c':val_2})
    assert_raises(UserException, 3200260, raise_3)
        
    #call with duplicate keyword argument
    def raise_4():
        sig.parse_function_call_args([val_1, val_2], {'a':val_1})
    assert_raises(UserException, 3200270, raise_4)
    
    
    
def test_Signature_3(): #IGNORE:C01111
    msg =  'Signature: test calling (binding) with default arguments.'
    #skip_test(msg)
    print msg

    from freeode.interpreter import (Signature, NodeFuncArg, IFloat, 
                                     Interpreter)
    
    #Interpreter for initial evaluation of type annotations
    intp = Interpreter()
    
    #some interpreter level values
    val_1 = IFloat(1)
    val_2 = IFloat(2)
    #argument list for testing: def f(a, b=2)
    sig = Signature([NodeFuncArg('a'),
                    NodeFuncArg('b', default_value=val_2)], None)
    sig.evaluate_type_specs(intp)
    
    #call with one positional argument: f(1). For argument 'b' default value must be used.
    arg_vals = sig.parse_function_call_args([val_1], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    
    
def test_Signature_4(): #IGNORE:C01111
    msg =  'Signature: test type compatibility testing.'
    #skip_test(msg)
    print msg

    from freeode.interpreter import (Signature, NodeFuncArg,   
                                     IFloat, IString, Interpreter)
    
    #Interpreter for initial evaluation of type annotations
    intp = Interpreter()
    
    #some interpreter level values
    val_1 = IFloat(1)
    val_hello = IString('hello')
    #argument list for testing: f(a:Float, b:String)
    sig = Signature([NodeFuncArg('a', type=IFloat),
                    NodeFuncArg('b', type=IString)], None)
    sig.evaluate_type_specs(intp)
    
    #call with correct positional arguments: f(1, 'hello')
    arg_vals = sig.parse_function_call_args([val_1, val_hello], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 'hello'
    
    #call with correct keyword arguments: f(a=1, b='hello')
    arg_vals = sig.parse_function_call_args([], {'a':val_1, 
                                                'b':val_hello})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 'hello'
    
    #call with mixed positional and keyword arguments: f(1, b='hello')
    arg_vals = sig.parse_function_call_args([val_1], {'b':val_hello})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 'hello'
    
 
 
def test_signature_decorator(): #IGNORE:C01111
    msg = \
    '''
    Test decorator for python functions, that gives them a Signature object, 
    and some additional attributes for compatibility with Interpreter objects.
    '''
    #skip_test(msg)
    print msg

    from freeode.interpreter import InterpreterObject, signature
   
    #Some classes that can be used in the type specifications
    class Dummy1(InterpreterObject):
        pass
    class Dummy2(InterpreterObject):
        pass
    dummy2 = Dummy2()
    
    @signature(None, Dummy1) 
    def foo():
        return Dummy1()
    #print aa_make_tree(foo)
    assert foo.siml_signature.arguments is None     #pylint:disable-msg=E1101
    assert foo.siml_signature.return_type is Dummy1 #pylint:disable-msg=E1101
    
    @signature([Dummy1, Dummy2], None)
    def bar(_a, _b=dummy2):                          
        pass
    #print aa_make_tree(bar)
    args = bar.siml_signature.arguments            #pylint:disable-msg=E1101
    assert len(args) == 2          
    assert args[0].type is Dummy1 
    assert args[1].type is Dummy2
    assert args[1].default_value is dummy2
    assert bar.siml_signature.return_type is None  #pylint:disable-msg=E1101
    
    @signature([Dummy1, Dummy2], Dummy1) 
    def baz(a, _b=dummy2):                         
        return a
    #print aa_make_tree(baz)
    args = baz.siml_signature.arguments            #pylint:disable-msg=E1101
    assert len(args) == 2          
    assert args[0].type is Dummy1 
    assert args[1].type is Dummy2
    assert args[1].default_value is dummy2
    assert baz.siml_signature.return_type is Dummy1  #pylint:disable-msg=E1101



# -------- Test user defined class object ------------------------------------------------------------------------
def test_SimlClass_1(): #IGNORE:C01111
    msg = 'Test SimlClass: class without attributes'
    #skip_test(msg)
    print msg

    from freeode.interpreter import SimlClass, istype
       
    #construct a class object with SimlClass as base class
    #type(name, bases, dict) -> a new type
    c1=type('C1', (SimlClass,), {})
    
    #create an instance of the class
    i1 = c1()
    assert istype(i1, c1)
    


def test_SimlClass_2(): #IGNORE:C01111
    msg = 'Test SimlClass: class with data attribute and method.'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import SimlClass, SimlFunction, IFloat, istype
    from freeode.util import aa_make_tree
    
    #construct a class object with SimlClass as base class, with
    # - a1: IFloat data attribute
    # - m1: user defined method
    #type(name, bases, dict) -> a new type
    cls =type('C1', (SimlClass,), {'a1':IFloat(), 
                                   'm1':SimlFunction('m1')})
    #print aa_make_tree(cls)
    
    #create an instance of the class
    inst = cls()
    #print aa_make_tree(inst)
    
    assert istype(inst, cls)
    
    #the data attributes must be copied, not identical
    assert id(cls.a1) != id(inst.a1)
    assert istype(inst.a1, IFloat) 
    
    #the method must not be copied, it must be accessed through
    assert 'm1' not in inst.__dict__
    assert hasattr(inst, 'm1')

    

# -------- Test Siml wrapper for float classes ------------------------------------------------------------------
def test_IFloat_2(): #IGNORE:C01111
    msg = 'Test IFloat: constructor, istype function.'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IFloat, istype
    
    #test construction - Siml type must be right
    val1 = IFloat()
    assert istype(val1, IFloat)

    #no arguments
    val_none = IFloat()
    assert val_none.value is None
    
    #int argument
    val_1 = IFloat(1)
    assert val_1.value == 1.
    
    #float argument
    val_pi = IFloat(3.1415)
    assert val_pi.value == 3.1415
    
    #IFloat argument
    val_1_s = IFloat(val_1)
    assert  val_1_s.value == 1.

    try:
        IFloat('hello')
    except ValueError:
        print 'expected exception: number can not be constructed from string.'
    else:
        assert False, 'object was constructed with wrong init values'



def test_IFloat_3(): #IGNORE:C01111
    msg = 'Test IFloat: mathematical operators from Python'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IFloat
    
    val_2 = IFloat(2)
    val_3 = IFloat(3)
    
    assert (val_2 + val_3).value == val_2.value + val_3.value
    assert (val_2 - val_3).value == val_2.value - val_3.value
    assert (val_2 * val_3).value == val_2.value * val_3.value
    #for division to work the class needs a __truediv__ function, 
    #which it does not have 
    #assert (val_2 / val_3).value == val_2.value / val_3.value
    assert (val_2 % val_3).value == val_2.value % val_3.value
    assert (val_2 ** val_3).value == val_2.value ** val_3.value
    
    #assert abs(val_2).value == abs(val_2.value)
    assert (-val_2).value == -val_2.value



# -------- Test Siml wrapper for str classes ------------------------------------------------------------------
def test_IString_2(): #IGNORE:C01111
    msg = 'Test IString: construction, istype function'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IString, istype
     
    #test construction - Siml type must be right
    val1 = IString()
    assert istype(val1, IString)

    #no arguments
    val_none = IString()
    assert val_none.value is None
    
    #int argument
    val_1 = IString(1)
    assert val_1.value == '1'
    
    #float argument
    val_pi = IString(3.1415)
    assert val_pi.value == '3.1415'
    
    #str argument
    val_a = IString('a')
    assert val_a.value == 'a'
    
    #IString argument
    val_a_s = IString(val_a)
    assert  val_a_s.value == 'a'

    #Supply wrong arguments; must raise TypeError.
    def raise_1():
        IString([])
    assert_raises(TypeError, None, raise_1)



def test_IString_3(): #IGNORE:C01111
    msg = 'Test IString: string concatenation from Python'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IString
    
    val_a = IString('a')
    val_b = IString('b')
    
    assert (val_a + val_b).value == val_a.value + val_b.value



# -------- Test Siml wrapper for bool objects ------------------------------------------------------------------
def test_IBool_2(): #IGNORE:C01111
    msg = 'Test IString: constructor, istype function.'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IBool, istype
    
    #test construction from Python class - Siml type must still be right
    val1 = IBool()
    assert istype(val1, IBool)

    #no arguments
    val_none = IBool()
    assert val_none.value is None
    
    #bool argument
    val_true = IBool(True)
    assert val_true.value == True
    
    #int argument
    val_0 = IBool(0)
    assert val_0.value == False
    val_1 = IBool(1)
    assert val_1.value == True
    
    #float argument
    val_pi = IBool(3.1415)
    assert val_pi.value == True
    
    #str argument
    val_a = IBool('a')
    assert val_a.value == True
    
    #IString argument
    val_true_2 = IBool(val_true)
    assert  val_true_2.value == True

    #expected exception: wrong argument type.
    def raise_1():
        IBool([])
    assert_raises(TypeError, None, raise_1)

#TODO: Test comparison operators
#TODO: Test IBool to string conversion
#TODO: Test boolean operations (eventually)


# -------- Test expression evaluation ------------------------------------------------------------------------
def test_operator_dispatch_1(): #IGNORE:C01111
    msg = 'Test Interpreter: handling of operators with known Float values.'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import (IFloat, Interpreter)
    from freeode.ast import NodeOpInfix2, NodeOpPrefix1
    
    intp = Interpreter()
    
    val_2 = IFloat(2)
    val_3 = IFloat(3)
    
    op_sub = NodeOpInfix2('-', [val_2, val_3])
    res = intp.eval(op_sub)
    print res
    assert res.value == -1 
    
    op_neg = NodeOpPrefix1('-', [val_2])
    res = intp.eval(op_neg)
    print res
    assert res.value == -2 
    


def test_operator_dispatch_2(): #IGNORE:C01111
    msg = 'Test Interpreter: handling of operators with unknown Float values.'
    #skip_test(msg)
    print msg
    from freeode.interpreter import Interpreter, IFloat
    from freeode.ast import NodeOpInfix2, NodeOpPrefix1, RoleVariable

    intp = Interpreter()
    
    val_2 = IFloat()
    val_2.__siml_role__ = RoleVariable
    val_3 = IFloat()
    val_3.__siml_role__ = RoleVariable
    
    op_sub = NodeOpInfix2('-', [val_2, val_3])
    res = intp.eval(op_sub)
    print res
    assert isinstance(res, NodeOpInfix2)
    
    op_neg = NodeOpPrefix1('-', [val_2])
    res = intp.eval(op_neg)
    print res
    assert isinstance(res, NodeOpPrefix1)
    


def test_expression_evaluation_1(): #IGNORE:C01111
    msg = 'Test expression evaluation (only immediate values)'
    #skip_test(msg)
    print msg

    from freeode.interpreter import Interpreter
    import freeode.simlparser as simlparser
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('0+1*2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #interpret the expression
    intp = Interpreter()
    res = intp.eval(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == 2.0
    
    

def test_expression_evaluation_2(): #IGNORE:C01111
    msg = 'Test expression evaluation, all operators and brackets (only immediate values)'
    #skip_test(msg)
    print msg

    from freeode.interpreter import Interpreter
    import freeode.simlparser as simlparser
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('(((0-1+2)*3--1)/4)**5*(-1+2*--1**4)%6')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    #print ex
    
    #interpret the expression
    intp = Interpreter()
    res = intp.eval(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    #print res 
    assert res.value == 1
    
    

def test_expression_evaluation_3(): #IGNORE:C01111
    msg = 'Test expression evaluation (access to variables)'
    #skip_test(msg)
    print msg

    from freeode.interpreter import (IModule, IFloat,  
                                     Interpreter, ExecutionEnvironment)
    import freeode.simlparser as simlparser
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('1 + a * 2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #create module where name lives
    mod = IModule()
    val_2 = IFloat(2.0)
    mod.a = val_2
    print
    print 'Module where variable is located: --------------------------------------------'
    print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    
    #interpret the expression
    intp = Interpreter()
    intp.push_environment(env)
    res = intp.eval(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == 5.0
    
    

def test_expression_evaluation_4(): #IGNORE:C01111
    msg = 'Test expression evaluation (calling built in functions)'
    #skip_test(msg)
    print msg

    from freeode.interpreter import (IModule, ExecutionEnvironment,
                                     Interpreter, signature, IFloat)
    from freeode.util import aa_make_tree
    import freeode.simlparser as simlparser
    
    import math
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('sqrt(2)')
    print
    print 'AST (parser output): -----------------------------------------------'
    #print aa_make_tree(ex) 
    
    #create module where names live
    mod = IModule()
    #create sqrt function that can be called from Siml
    @signature([IFloat], IFloat)
    def sqrt(x): 
        return IFloat(math.sqrt(x.value))
    #put function into module
    mod.sqrt = sqrt
    print
    print 'Module where function is located: ----------------------------------'
    #print aa_make_tree(mod) 
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    #create visitor for evaluating the expression
    intp = Interpreter()
    intp.push_environment(env)
    #evaluate the expression
    res = intp.eval(ex)
    print
    print 'Result object: -----------------------------------------------------'
    print aa_make_tree(res)  
    assert res.value == math.sqrt(2)



def test_expression_evaluation_5(): #IGNORE:C01111
    msg = \
    '''
    Test expression evaluation (returning of partially evaluated expression 
    when accessing variables)
    '''
    #skip_test(msg)
    print msg

    from freeode.ast import RoleVariable, NodeOpInfix2
    from freeode.interpreter import (IModule, IFloat, ExecutionEnvironment, 
                                     Interpreter, istype)
    import freeode.simlparser as simlparser
    from freeode.util import aa_make_tree
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('a + 2*2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    #print aa_make_tree(ex)
    
    #create module where name lives
    mod = IModule()
    #create attribute 'a' with no value
    val_2 = IFloat()
    val_2.__siml_role__ = RoleVariable
    mod.a = val_2
    print
    print 'Module where variable is located: --------------------------------------------'
    #print aa_make_tree(mod)
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    
    #interpret the expression
    intp = Interpreter()
    intp.environment = env
    res = intp.eval(ex)
    print
    print 'Result object - should be an unevaluated expression: --------------------------------------------------------------'
    print aa_make_tree(res)
    assert isinstance(res, NodeOpInfix2)
    assert res.operator == '+'
    assert istype(res, IFloat)


def test_function_call_unknown_arguments_1(): #IGNORE:C01111
    msg = 'Test expression evaluation (calling built in functions), unknown arguments'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import (IModule, ExecutionEnvironment, 
                                     CodeGeneratorObject, Interpreter, signature, 
                                     IFloat, RoleVariable, istype, test_allknown)
    from freeode.ast import NodeFuncCall, NodeIdentifier
    from freeode.util import aa_make_tree
    import math
    
    #create module where the function lives
    mod = IModule()
    #create sqrt function that can be called from Siml
    @signature([IFloat], IFloat)
    def sqrt(x): 
        test_allknown(x)
        return IFloat(math.sqrt(x.value))
    #put function into module
    mod.sqrt = sqrt
    print
    print 'Module where function is located: --------------------------------------------'
    #print aa_make_tree(mod)
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    #create visitor for evaluating the expression
    intp = Interpreter()
    intp.push_environment(env) 
    
    #create a Siml value as function argument
    val_1 = IFloat()    
    val_1.__siml_role__ = RoleVariable
    #create function call with unkown argument
    call = NodeFuncCall(NodeIdentifier('sqrt'), [val_1], {})
    
    #evaluate the function call
    ret_val = intp.eval(call)
    print
    print 'Result object: --------------------------------------------------------------'
    print aa_make_tree(ret_val)
    #evaluating a function call with unknown arguments must return a function call
    assert isinstance(ret_val, NodeFuncCall)
    assert istype(ret_val, IFloat)
    
    

def test_function_call_unknown_arguments_2(): #IGNORE:C01111
    msg = 'Test Interpreter: call real library function with unknown argument'
    #skip_test(msg)
    print msg

    from freeode.interpreter import Interpreter, IFloat, istype
    from freeode.ast import NodeFuncCall, NodeIdentifier, RoleVariable

    #create the interpreter
    intp = Interpreter()    #IGNORE:W0612
    intp.create_test_module_with_builtins()
    #create a Siml value as function argument
    val_1 = IFloat()  
    val_1.__siml_role__ = RoleVariable  

    #create function call with unkown argument
    call = NodeFuncCall(NodeIdentifier('sqrt'), [val_1], {})
    #interpret call
    ret_val = intp.eval(call)
    #evaluating a function call with unknown arguments must return a function call
    assert isinstance(ret_val, NodeFuncCall)
    assert istype(ret_val, IFloat)
    
  
  
# -------- Test Interpreter - basic --------------------------------------------------------  
def test_Interpreter_create_path_1(): #IGNORE:C01111
    msg = 'Interpreter: create_path method: create non-existing path.'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import InterpreterObject, Interpreter
    from freeode.util import DotName
    
    #create an interpreter 
    intp = Interpreter()
    
    #the root object where the long name will be created
    root = InterpreterObject()
    #create all attributes so that this dotname can be looked up
    #o_name_1 should be the object representing the rightmost element (name)
    o_name_1 = intp.create_path(root, DotName('this.is_.a.long.dotted.name'))
    
    #see if all attributes have been created
    o_name_2 = root.this.is_.a.long.dotted.name #pylint:disable-msg=E1101
    #the create_path function must return the final element
    assert o_name_1 is o_name_2



def test_Interpreter_create_path_2(): #IGNORE:C01111
    msg = 'Interpreter: create_path method: return existing path, extend path'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import InterpreterObject, Interpreter
    from freeode.util import DotName
    
    #create an interpreter 
    intp = Interpreter()
    
    #the root object where the long name will be created
    root = InterpreterObject()
    #create all attributes so that this dotname can be looked up
    #o_name_1 should be the object representing the rightmost element (name)
    o_name_1 = intp.create_path(root, DotName('this.is_.a.long.dotted.name'))
    
    #access existing path, don't try to create it twice
    o_name_2 = intp.create_path(root, DotName('this.is_.a.long.dotted.name'))
    assert o_name_1 is o_name_2
    
    #extend existing path
    o_indeed = intp.create_path(root, DotName('this.is_.a.long.dotted.name.indeed'))
    o_indeed_2 = o_name_1.indeed                     #pylint:disable-msg=E1103
    assert o_indeed is o_indeed_2



def test_Interpreter__siml_dotname__(): 
    msg =  '''
    Interpreter: __siml_doname__ attribute.
    
    The interpreter creates a __siml_doname__ for each function, which is 
    unique and descriptive. This attribute is used to create a nicely named 
    name space for the function locals.
    
    This test involves parsing and interpreting a small program; but the 
    feature '__siml_doname__' is meant fo be used in conjunction with 
    'create_path', which is tested above.
    '''
    #skip_test(msg)
    print msg

    from freeode.interpreter import Interpreter
    from freeode.util import DotName, aa_make_tree #pylint:disable-msg=W0612
    
    #the mini test program
    prog_txt = \
'''
class A:
    func foo():
        pass
        
func bar():
    pass
'''
    
    intp = Interpreter()
    mod = intp.interpret_module_string(prog_txt, 'test-file', 'test')
    
#    print 'Module after interpretation: ----------------------------------'
#    print aa_make_tree(mod)
#    print 'Dotname of test.A.foo:'
#    print mod.A.foo.__siml_dotname__ 
#    print mod.bar.__siml_dotname__                           #pylint:disable-msg=E1101
    
    assert mod.A.foo.__siml_dotname__ == DotName('test.A.foo') #pylint:disable-msg=E1101
    assert mod.bar.__siml_dotname__ == DotName('test.bar')     #pylint:disable-msg=E1101



#def test_InterpreterObject_find_name(): #IGNORE:C01111
#    msg = 'InterpreterObject: find_name method.'
#    skip_test(msg)
#    print msg
#    from freeode.interpreter import (InterpreterObject, )
#    
#    obj = InterpreterObject()
#    attr1 = InterpreterObject()
#    attr2 = InterpreterObject()
#    
#    #put attributes into object
#    obj.create_attribute('attr1', attr1)
#    obj.create_attribute('attr2', attr2)
#    #find the names of the attributes
#    name1 = obj.find_name(attr1)
#    name2 = obj.find_name(attr2)
#    #verify that the found names are correct
#    assert name1 == 'attr1'
#    assert name2 == 'attr2'



def test_SimlFunction_1(): #IGNORE:C01111
    msg =  \
'''
Test SimlFunction: call user defined function 
User defined functions are created without parser.
'''    
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, SimlFunction, 
                                     Signature, IFloat, IString)
    from freeode.ast import NodeFuncArg, NodeReturnStmt, NodeIdentifier
    from freeode.util import UserException

    #create the interpreter
    intp = Interpreter()    #IGNORE:W0612
    lib = intp.built_in_lib
    #create a Siml value as function argument
    val_1 = IFloat(1)
    
    #create a function without statements (impossible in Siml)
    # func test(a:Float):
    #     ** nothing **
    f1 = SimlFunction('test', Signature([NodeFuncArg('a', IFloat)]), 
                      statements=[], global_scope=lib)
    #call with existing value
    intp.apply(f1, (val_1,))
    
    #create a function with return statement - uses interpreter for executing the statement
    # func test(a:Float) -> Float:
    #     return a
    f2 = SimlFunction('test', Signature([NodeFuncArg('a', IFloat)], IFloat), 
                      statements=[NodeReturnStmt([NodeIdentifier('a')])], 
                      global_scope=lib)
    #call function and see if value is returned
    ret_val = intp.apply(f2, (val_1,))
    assert ret_val.value == 1. #IGNORE:E1103

    #create a function with wrong return type
    # func test(a:Float) -> String:
    #     return a
    f3= SimlFunction('test', Signature([NodeFuncArg('a', IFloat)], IString), 
                      statements=[NodeReturnStmt([NodeIdentifier('a')])], 
                      global_scope=lib)
    def raise_1():
        intp.apply(f3, (val_1,))
    assert_raises(UserException, 3200320, raise_1)



def test_SimlFunction_3(): #IGNORE:C01111
    msg = \
'''
Test SimlFunction: storage of local variables during code collection.
User defined functions are created without parser.
'''
    skip_test(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, SimlFunction, IModule,
                                     Signature, IFloat)
    from freeode.ast import NodeFuncArg

    #create the interpreter 
    intp = Interpreter()        
    
    #create a Siml value as function argument
    val_1 = IFloat(1)

    #create a function without statements (impossible in Siml)
    # func test(a:Float):
    #     ** nothing **
    f1 = SimlFunction('test', Signature([NodeFuncArg('a', IFloat)]), 
                      statements=[], global_scope=intp.built_in_lib)
    #create module where the function lives
    mod1 = IModule('test-module')
    mod1.test = f1
    
    #call with existing value
    # and set interpreter up to collect code. In this mode local variables of all 
    # functions must become algebraic variables of the simulation object.
    intp.start_collect_code()
    intp.apply(f1, (val_1,))
    _stmts, fn_locals = intp.stop_collect_code()
    
    print fn_locals
    
    #there must be one element in the locals storage, some base namespace for 
    # the function argument 'a'
    assert len(fn_locals.attributes) > 0
    
    #get the local variable 'a' 
    ns_test = fn_locals.test
    ns_1    = ns_test.  get_attribute('1')
    float_a = ns_1.a
    assert float_a is val_1



def test_SimlFunction_descriptor_character():
    msg = \
    '''
    Test cooperation of user defined functions and classes. 
    User defined classes are descriptors, their __get__ method is tested here.'''
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import InterpreterObject, SimlFunction, SimlBoundMethod
    
    #Create a user defined function
    func1 = SimlFunction('func1')
    #Create class with one  method: func1
    #type(name, bases, dict) -> a new type
    Foo = type('Foo', (InterpreterObject,), 
               {'func1':func1})
    #Create instance of the new class
    foo = Foo()
    
    #test access via the class object - must return the function
    #print Foo.func1
    assert Foo.func1 is func1
    
    #test access via a class' instance - must return SimlBoundMethod
    #print foo.func1
    assert isinstance(foo.func1, SimlBoundMethod)
    assert foo.func1.im_func is func1
    assert foo.func1.im_self is foo
    
    
        
# -------- Test administrative functions ------------------------------------------------------------------------
def test_determine_result_role_1(): #IGNORE:C01111
    msg = 'Test determine_result_role: '
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IFloat, determine_result_role
    from freeode.ast import RoleConstant, RoleParameter, RoleVariable
    
    #some constants
    c_1 = IFloat()
    c_1.__siml_role__ = RoleConstant
    c_2 = IFloat()
    c_2.__siml_role__ = RoleConstant
    #some parameters
    p_1 = IFloat()
    p_1.__siml_role__ = RoleParameter
    p_2 = IFloat()
    p_2.__siml_role__ = RoleParameter
    #some variables
    v_1 = IFloat()
    v_1.__siml_role__ = RoleVariable
    v_2 = IFloat()
    v_2.__siml_role__ = RoleVariable
    
    #determine the most variable role among the arguments
    assert issubclass(determine_result_role((c_1, p_1, v_1), 
                                            {'a':c_2, 'b':p_2, 'c':v_2, }),  
                      RoleVariable)
    assert determine_result_role((c_1, p_1), 
                                 {'a':c_2, 'b':p_2}) == RoleParameter
    assert determine_result_role((c_1,), 
                                 {'a':c_2}) == RoleConstant
    


def test_determine_result_role_2(): #IGNORE:C01111
    msg = 'Test determine_result_role: errors'
    #skip_test(msg)
    print msg
    from freeode.interpreter import IFloat, determine_result_role
    from freeode.ast import (RoleConstant, RoleParameter, RoleVariable, 
                             RoleUnkown)
    
    #unknown role
    u = IFloat()
    u.__siml_role__ = RoleUnkown
    #some constants
    c_1 = IFloat()
    c_1.__siml_role__ = RoleConstant
    c_2 = IFloat()
    c_2.__siml_role__ = RoleConstant
    #some parameters
    p_1 = IFloat()
    p_1.__siml_role__ = RoleParameter
    p_2 = IFloat()
    p_2.__siml_role__ = RoleParameter
    #some variables
    v_1 = IFloat()
    v_1.__siml_role__ = RoleVariable
    v_2 = IFloat()
    v_2.__siml_role__ = RoleVariable
    
    #one argument with RoleUnknown - should raise exception
    def raise_1(): 
        determine_result_role((c_1, p_1, v_1, u), 
                              {'a':c_2, 'b':p_2, 'c':v_2, })
    assert_raises(ValueError, None, raise_1)
    #one argument with RoleUnknown - should raise exception
    def raise_2(): 
        determine_result_role((c_1, p_1), {'a':c_2, 'b':p_2, 'u':u})
    assert_raises(ValueError, None, raise_2)
    #one argument with RoleUnknown - should raise exception
    def raise_3(): 
        determine_result_role((c_1, u), {'a':c_2})
    assert_raises(ValueError, None, raise_3)



def test_is_role_more_variable_1(): #IGNORE:C01111
    msg = 'Test is_role_more_variable: compare the variable-character of two roles.'
    #skip_test(msg)
    print msg

    from freeode.interpreter import (is_role_more_variable)
    from freeode.ast import (RoleConstant, RoleParameter, RoleVariable, RoleUnkown)

    assert is_role_more_variable(RoleConstant, RoleParameter) is False
    assert is_role_more_variable(RoleParameter, RoleConstant) is True
    assert is_role_more_variable(RoleParameter, RoleVariable) is False
    assert is_role_more_variable(RoleVariable, RoleParameter) is True
    assert is_role_more_variable(RoleVariable, RoleUnkown) is False
    assert is_role_more_variable(RoleUnkown, RoleVariable) is True
    
    assert is_role_more_variable(RoleConstant, RoleConstant) is False
    assert is_role_more_variable(RoleParameter, RoleParameter) is False
    assert is_role_more_variable(RoleVariable, RoleVariable) is False
    assert is_role_more_variable(RoleUnkown, RoleUnkown) is False
    
    

def test_is_role_more_variable_2(): #IGNORE:C01111
    #skip_test('Test is_role_more_variable: exceptions for wrong types.')
    print 'Test is_role_more_variable: exceptions for wrong types.'
    from freeode.interpreter import (is_role_more_variable)
    from freeode.ast import (RoleConstant, RoleParameter)
    
    def raise_1(): 
        is_role_more_variable(float, RoleConstant)
    assert_raises(AssertionError, None, raise_1)
        
    def raise_2(): 
        is_role_more_variable(RoleParameter, float)
    assert_raises(AssertionError, None, raise_2)
        
    def raise_3(): 
        is_role_more_variable(RoleParameter, 1)
    assert_raises(AssertionError, None, raise_3)
        
        

def test_set_role_recursive_1(): #IGNORE:C01111
    #skip_test('Test set_role_recursive')
    print 'Test set_role_recursive'
    from freeode.interpreter import (InterpreterObject, set_role_recursive)
    from freeode.ast import (RoleConstant, RoleParameter, RoleVariable, 
                             RoleUnkown)
    
    #create a little tree of objects
    c1 = InterpreterObject()
    c1.__siml_role__ = RoleConstant
    p1 = InterpreterObject()
    p1.__siml_role__ = RoleParameter
    v1 = InterpreterObject()
    v1.__siml_role__ = RoleVariable
    u1 = InterpreterObject()
    u1.__siml_role__ = RoleUnkown
    root = InterpreterObject()
    root.__siml_role__ = RoleVariable
    root.c1 = c1 
    root.p1 = p1 
    root.v1 = v1 
    root.u1 = u1 
    #set the roles in the whole tree
    ########## This line varies ############
    set_role_recursive(root, RoleVariable) 
    #test the new roles
    assert root.__siml_role__ == RoleVariable
    assert c1.__siml_role__ == RoleConstant
    assert p1.__siml_role__ == RoleParameter
    assert v1.__siml_role__ == RoleVariable
    assert u1.__siml_role__ == RoleVariable
    
    #create a little tree of objects
    c1 = InterpreterObject()
    c1.__siml_role__ = RoleConstant
    p1 = InterpreterObject()
    p1.__siml_role__ = RoleParameter
    v1 = InterpreterObject()
    v1.__siml_role__ = RoleVariable
    u1 = InterpreterObject()
    u1.__siml_role__ = RoleUnkown
    root = InterpreterObject()
    root.__siml_role__ = RoleVariable
    root.c1 = c1 
    root.p1 = p1 
    root.v1 = v1 
    root.u1 = u1 
    #set the roles in the whole tree
    ########## This line varies ############
    set_role_recursive(root, RoleParameter) 
    #test the new roles
    assert root.__siml_role__ == RoleParameter
    assert c1.__siml_role__ == RoleConstant
    assert p1.__siml_role__ == RoleParameter
    assert v1.__siml_role__ == RoleParameter
    assert u1.__siml_role__ == RoleParameter
    
    #create a little tree of objects
    c1 = InterpreterObject()
    c1.__siml_role__ = RoleConstant
    p1 = InterpreterObject()
    p1.__siml_role__ = RoleParameter
    v1 = InterpreterObject()
    v1.__siml_role__ = RoleVariable
    u1 = InterpreterObject()
    u1.__siml_role__ = RoleUnkown
    root = InterpreterObject()
    root.__siml_role__ = RoleVariable
    root.c1 = c1 
    root.p1 = p1 
    root.v1 = v1 
    root.u1 = u1 
    #set the roles in the whole tree
    ########## This line varies ############
    set_role_recursive(root, RoleConstant) 
    #test the new roles
    assert root.__siml_role__ == RoleConstant
    assert c1.__siml_role__ == RoleConstant
    assert p1.__siml_role__ == RoleConstant
    assert v1.__siml_role__ == RoleConstant
    assert u1.__siml_role__ == RoleConstant
    
    

if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_Interpreter__siml_dotname__()
    pass #pylint:disable-msg=W0107
