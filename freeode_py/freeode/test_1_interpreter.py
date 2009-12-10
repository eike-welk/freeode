# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2008 - 2009 by Eike Welk                                *
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

#Special construction to make PyDev and pylint happy. Both checkers can't 
#see into the py.test namespace
try:                      
    from py.test import skip as skip_test #IGNORE:E0611
    from py.test import fail as fail_test #IGNORE:E0611
except ImportError:
    print 'No py library, many tests may fail!'



# -------- Test InterpreterObject class ----------------------------------------------------------------------
def test_InterpreterObject_1(): #IGNORE:C01111
    msg = 'InterpreterObject: basic operation'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (InterpreterObject, UndefinedAttributeError,
                                     DuplicateAttributeError, )

    o1 = InterpreterObject()
    attr1 = InterpreterObject()
    attr2 = InterpreterObject()
    
    #create small tree of objects:
    # o1
    #  +--- attr1
    #  +--- attr2
    o1.create_attribute('attr1', attr1)
    o1.create_attribute('attr2', attr2)
    
    #test for existence of attributes
    assert o1.has_attribute('attr1')
    assert o1.has_attribute('attr2')
    assert not o1.has_attribute('foo') 
    
    #retrieval of attributes
    assert o1.get_attribute('attr1') == attr1
    assert o1.get_attribute('attr2') == attr2
    
    #attempt to retrieve non-existing attribute
    try: 
        o1.get_attribute('foo')
    except UndefinedAttributeError: 
        print 'Expected exception: undefined attribute'
    else:
        assert False, 'Code should raise exception'
    
    #attempt to create attribute with name that already exists
    try: 
        o1.create_attribute('attr1', attr1)
    except DuplicateAttributeError:
        print 'Expected exception: duplicate attribute'
    else:
        assert False, 'Code should raise exception'
    
    

def test_InterpreterObject_method_retrieval(): #IGNORE:C01111
    msg = \
    '''
    InterpreterObject: attributes are also searched in the class object
    If the attributes taken from the class are call-able they are wrapped in a bound method.
    '''
    #skip_test(msg)
    print msg
    from freeode.interpreter import (InterpreterObject, UndefinedAttributeError,
                                     BoundMethod, CallableObject, ref)
    #the class
    cls = InterpreterObject()
    cls_attr1 = InterpreterObject()
    cls_func1 = CallableObject('cls_func1')
    cls.create_attribute('cls_attr1', cls_attr1)
    cls.create_attribute('cls_func1', cls_func1)
    
    #the tested object
    o1 = InterpreterObject()
    o1.type = ref(cls)
    o1_attr1 = InterpreterObject()
    o1_func1 = CallableObject('o1_func1')
    o1.create_attribute('o1_attr1', o1_attr1)
    o1.create_attribute('o1_func1', o1_func1)
    
    #test for existence of attributes
    assert o1.has_attribute('o1_attr1')
    assert o1.has_attribute('o1_func1')
    assert o1.has_attribute('cls_attr1')
    assert o1.has_attribute('cls_func1')
    assert not o1.has_attribute('foo') 

    #retrieval of attributes 
    #attributes of the instance are retrieved without modifications
    assert o1.get_attribute('o1_attr1') == o1_attr1
    assert o1.get_attribute('o1_func1') == o1_func1
    #data attributes of the class are retrieved without modifications
    assert o1.get_attribute('cls_attr1') == cls_attr1
    #method (callable) attributes are put into a wrapper object 
    assert o1.get_attribute('cls_func1').function == cls_func1
    assert isinstance(o1.get_attribute('cls_func1'), BoundMethod)

    #attempt to retrieve non-existing attribute
    try: 
        o1.get_attribute('foo')
    except UndefinedAttributeError: 
        print 'Expected exception: undefined attribute'
    else:
        assert False, 'Code should raise exception'



def test_InterpreterObject_create_path_1(): #IGNORE:C01111
    msg = 'InterpreterObject: create_path method: create non-existing path.'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (InterpreterObject, DotName)
    
    #the root object where the long name will be created
    root = InterpreterObject()
    #create all attributes so that this dotname can be looked up
    #o_name_1 should be the object representing the rightmost element (name)
    o_name_1 = root.create_path(DotName('this.is.a.long.dotted.name'))
    
    #see if all attributes have been created
    o_this = root.get_attribute('this')
    o_is = o_this.get_attribute('is')
    o_a = o_is.get_attribute('a')
    o_long = o_a.get_attribute('long')
    o_dotted = o_long.get_attribute('dotted')
    o_name_2 = o_dotted.get_attribute('name')
    #the function must return the final element
    assert o_name_1 is o_name_2



def test_InterpreterObject_create_path_2(): #IGNORE:C01111
    msg = 'InterpreterObject: create_path method: return existing path, extend path'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (InterpreterObject, DotName)
    
    #the root object where the long name will be created
    root = InterpreterObject()
    #create all attributes so that this dotname can be looked up
    #o_name_1 should be the object representing the rightmost element (name)
    o_name_1 = root.create_path(DotName('this.is.a.long.dotted.name'))
    
    #access existing path, don't try to create it twice
    o_name_2 = root.create_path(DotName('this.is.a.long.dotted.name'))
    assert o_name_1 is o_name_2
    
    #extend existing path
    o_indeed = root.create_path(DotName('this.is.a.long.dotted.name.indeed'))
    o_name_3 = o_indeed.parent()
    assert o_name_1 is o_name_3



def test_InterpreterObject_replace_attribute(): #IGNORE:C01111
    msg = 'InterpreterObject: replace_attribute method.'
    skip_test(msg)
    print msg
    from freeode.interpreter import (InterpreterObject)
    
    obj = InterpreterObject()
    attr1 = InterpreterObject()
    attr2 = InterpreterObject()
    
    #put an attribute into the object
    obj.create_attribute('test', attr1)
    assert obj.get_attribute('test') is attr1
    #replace the attribute with an other object
    obj.replace_attribute('test', attr2)
    assert obj.get_attribute('test') is attr2
    
 
    
def test_InterpreterObject_find_name(): #IGNORE:C01111
    msg = 'InterpreterObject: find_name method.'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (InterpreterObject, )
    
    obj = InterpreterObject()
    attr1 = InterpreterObject()
    attr2 = InterpreterObject()
    
    #put attributes into object
    obj.create_attribute('attr1', attr1)
    obj.create_attribute('attr2', attr2)
    #find the names of the attributes
    name1 = obj.find_name(attr1)
    name2 = obj.find_name(attr2)
    #verify that the found names are correct
    assert name1 == 'attr1'
    assert name2 == 'attr2'
    
    
    
#-------- Test IntArgumentList class ------------------------------------------------------------------------#
def test_IntArgumentList_1(): #IGNORE:C01111
    msg = 'IntArgumentList: construction'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (ArgumentList, NodeFuncArg, UserException, CLASS_FLOAT)
    
    #Test normal construction only positional argument: f(a, b)
    ArgumentList([NodeFuncArg('a'),
                  NodeFuncArg('b')], None)
    #Test normal construction with keyword arguments: f(a, b=1)
    val_1 = CLASS_FLOAT()
    ArgumentList([NodeFuncArg('a'),
                  NodeFuncArg('b', default_value=val_1)], None)
    
    #argument list with two identical argument names: f(a, a)
    try:
        ArgumentList([NodeFuncArg('a'),
                      NodeFuncArg('a')], None)
    except UserException, e:
        print 'Caught expected exception (argument names must be unique)'
        print e
    else:
        fail_test('This code should raise an exception (argument names must be unique).') #IGNORE:E1101
        
    #argument list with keyword argument before positional argument: f(a=1, b)
    try:
        val_1 = CLASS_FLOAT()
        ArgumentList([NodeFuncArg('a', default_value=val_1),
                      NodeFuncArg('b')], None)
    except UserException, e:
        print 'Caught expected exception (keyword argument before positional argument)'
        print e
    else:
        fail_test('This code should raise an exception (keyword argument before positional argument).') #IGNORE:E1101
#    assert 1==0
    
    
    
def test_IntArgumentList_2(): #IGNORE:C01111
    print 'ArgumentList: test argument processing at call site'
    from freeode.interpreter import (ArgumentList, NodeFuncArg, UserException, CLASS_FLOAT)
    
    #argument list for testing
    al = ArgumentList([NodeFuncArg('a'),
                       NodeFuncArg('b')], None)
    #some interpreter level values
    val_1 = CLASS_FLOAT()
    val_1.value = 1
    val_2 = CLASS_FLOAT()
    val_2.value = 2
    
    #call with correct number of positional arguments
    arg_vals = al.parse_function_call_args([val_1, val_2], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    #call with correct number of keyword arguments
    arg_vals = al.parse_function_call_args([], {'a':val_1,  
                                                'b':val_2})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    #call with too few arguments
    try:
        al.parse_function_call_args([], {})
    except UserException, e:
        print 'Caught expected exception (too few arguments)'
        print e
    else:
        fail_test('This code should raise an exception (too few arguments).') #IGNORE:E1101
        
    #call with too many positional arguments
    try:
        al.parse_function_call_args([val_1, val_2, val_2], {})
    except UserException, e:
        print 'Caught expected exception (too many positional arguments)'
        print e
    else:
        fail_test('This code should raise an exception (too many positional arguments).') #IGNORE:E1101
       
    #call with unknown keyword argument
    try:
        al.parse_function_call_args([], {'a':val_1,  
                                         'c':val_2})
    except UserException, e:
        print 'Caught expected exception (unknown keyword argument)'
        print e
    else:
        fail_test('This code should raise an exception (unknown keyword argument).') #IGNORE:E1101
        
    #call with duplicate keyword argument
    try:
        al.parse_function_call_args([val_1, val_2], {'a':val_1})
    except UserException, e:
        print 'Caught expected exception (duplicate keyword argument)'
        print e
    else:
        fail_test('This code should raise an exception (duplicate keyword argument).') #IGNORE:E1101
    #assert 1==0
    
    
    
def test_IntArgumentList_2_1(): #IGNORE:C01111
    print 'ArgumentList: __init__: strings are converted to DotName, default argument for loc'
    from freeode.interpreter import (ArgumentList, NodeFuncArg, CLASS_FLOAT)
    
    #argument list for testing
    al = ArgumentList([NodeFuncArg('a'),
                       NodeFuncArg('b')])
    #some interpreter level values
    val_1 = CLASS_FLOAT()
    val_1.value = 1
    val_2 = CLASS_FLOAT()
    val_2.value = 2
    
    #call with correct number of positional arguments
    arg_vals = al.parse_function_call_args([val_1, val_2], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    #call with correct number of keyword arguments
    arg_vals = al.parse_function_call_args([], {'a':val_1,  
                                                'b':val_2})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    
    
def test_IntArgumentList_3(): #IGNORE:C01111
    print 'ArgumentList: test calling with default arguments.'
    from freeode.interpreter import (ArgumentList, NodeFuncArg, CLASS_FLOAT)
    
    #some interpreter level values
    val_1 = CLASS_FLOAT()
    val_1.value = 1
    val_2 = CLASS_FLOAT()
    val_2.value = 2
    #argument list for testing: def f(a, b=2)
    al = ArgumentList([NodeFuncArg('a'),
                       NodeFuncArg('b', default_value=val_2)], None)
    
    #call with one positional argument: f(1). For argument 'b' default value must be used.
    arg_vals = al.parse_function_call_args([val_1], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 2
    
    
    
def test_IntArgumentList_4(): #IGNORE:C01111
    print 'ArgumentList: test type compatibility testing.'
    from freeode.interpreter import (ArgumentList, NodeFuncArg,   
                                     CLASS_FLOAT, CLASS_STRING)
    
    #some interpreter level values
    val_1 = CLASS_FLOAT(1)
    val_hello = CLASS_STRING('hello')
    #argument list for testing: f(a:Float, b:String)
    al = ArgumentList([NodeFuncArg('a', type=CLASS_FLOAT),
                       NodeFuncArg('b', type=CLASS_STRING)], None)
    
    #call with correct positional arguments: f(1, 'hello')
    arg_vals = al.parse_function_call_args([val_1, val_hello], {})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 'hello'
    
    #call with correct keyword arguments: f(a=1, b='hello')
    arg_vals = al.parse_function_call_args([], {'a':val_1, 
                                                'b':val_hello})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 'hello'
    
    #call with mixed positional and keyword arguments: f(1, b='hello')
    arg_vals = al.parse_function_call_args([val_1], {'b':val_hello})
    assert arg_vals['a'].value == 1
    assert arg_vals['b'].value == 'hello'
    
 
 
# -------- Test wrapper object for Python functions ------------------------------------------------------------------------
def test_BuiltInFunctionWrapper_1(): #IGNORE:C01111
    print 'BuiltInFunctionWrapper: test function call with known arguments, no Interpreter.'
    from freeode.interpreter import (BuiltInFunctionWrapper,
                                     ArgumentList, NodeFuncArg,   
                                     CLASS_FLOAT)
    import math
    
    #create sqrt function with named arguments
    sqrt = lambda x: CLASS_FLOAT(math.sqrt(x.value)) 
    #some interpreter level values
    val_2 = CLASS_FLOAT(2)

    #create a function object that wraps the sqrt function
    func = BuiltInFunctionWrapper('sqrt', 
                                  ArgumentList([NodeFuncArg('x', CLASS_FLOAT)]), 
                                  return_type=CLASS_FLOAT, 
                                  py_function=sqrt)
    #call function: sqrt(2)
    siml_ret = func(val_2)
    assert siml_ret.value == math.sqrt(2) #IGNORE:E1101
    
    
                                      
def test_BuiltInFunctionWrapper_2(): #IGNORE:C01111
    print 'BuiltInFunctionWrapper: test function call with unknown arguments, no Interpreter.'
    from freeode.interpreter import (BuiltInFunctionWrapper,
                                     ArgumentList, NodeFuncArg, ref,  
                                     CLASS_FLOAT,UnknownArgumentsException, 
                                     NodeOpInfix2,)
    import math
    
    #create sqrt function with named arguments
    sqrt = lambda x: CLASS_FLOAT(math.sqrt(x.value)) 
    #create unknown interpreter level values
    val_x = CLASS_FLOAT()
    #create fragment of unknown expression
    binop_u = NodeOpInfix2()
    binop_u.type = ref(CLASS_FLOAT)
    #create a function object that wraps the sqrt function
    func = BuiltInFunctionWrapper('sqrt', 
                                  ArgumentList([NodeFuncArg('x', CLASS_FLOAT)]), 
                                  return_type=CLASS_FLOAT, 
                                  py_function=sqrt)
    
    #call function: sqrt( <unknown value> )
    try:
        siml_ret = func(val_x)
    except UnknownArgumentsException:
        print 'Expected exception recieved: unknown arguments.'
    else:
        assert False, 'Expected exception: unknown arguments.'
    
    #call function: sqrt( <expression fragment> )
    try:
        siml_ret = func(binop_u)
    except UnknownArgumentsException:
        print 'Expected exception recieved: unknown arguments.'
    else:
        assert False, 'Expected exception: unknown arguments.'
        
    
                                      
# -------- Test user defined class object ------------------------------------------------------------------------
def test_SimlClass_1(): #IGNORE:C01111
    #skip_test('Test expression evaluation (only immediate values)')
    print 'Test SimlClass: class without statements'
    from freeode.interpreter import SimlClass, Interpreter
    
    #The SimlClass object contains the interpreter as a class variable 
    #It uses its methods and terefore only functions after the interpreter 
    #was constructed
    intp = Interpreter()
    
    #construct a class with no statements and no base classes
    #class Test1:
    #    <nothing; impossible in Siml>
    c1=SimlClass('Test1', None, [], None)
    
    #create an instance of the class
    i1 = c1()
    
    assert i1.type() == c1
    


def test_SimlClass_2(): #IGNORE:C01111
    #skip_test('Test expression evaluation (only immediate values)')
    print 'Test SimlClass: class with one data member'
    from freeode.interpreter import SimlClass, Interpreter
    from freeode.ast import NodeDataDef, NodeIdentifier
    
    #The SimlClass object contains the interpreter as a class variable 
    #It uses its methods and therefore only functions when there is an 
    #interpreter object.
    intp = Interpreter()
    #set up the built in library
    intp.create_test_module_with_builtins()
    
    #construct a class with no statements and no base classes
    #class Test1:
    #    Data a:Float
    data_stmt = NodeDataDef('a1', NodeIdentifier('Float'))
    cls = SimlClass('Test1', None, 
                 [data_stmt], 
                 None)
    assert cls.has_attribute('a1')
    
    #create an instance of the class
    inst = cls()
    
    assert inst.type() == cls
    assert inst.has_attribute('a1')
    #the attributes must be copied, not identical
    cls_a1 = cls.get_attribute('a1')
    inst_a1 = inst.get_attribute('a1')
    assert id(cls_a1) != id(inst_a1)
    assert cls_a1.type() == inst_a1.type()
    

# -------- Test wrapper for built in classes ------------------------------------------------------------------
def test_BuiltInClassWrapper_1(): #IGNORE:C01111
    #skip_test('Test BuiltInClassWrapper: construction, put into module')
    print 'Test BuiltInClassWrapper: construction, put into module'
    from freeode.interpreter import BuiltInClassWrapper, InterpreterObject
    
    #test object construction 
    class Dummy(InterpreterObject):
        pass
    siml_dummy_class = BuiltInClassWrapper('Dummy')
    siml_dummy_class.py_class = Dummy
    
    dummy = siml_dummy_class()
    assert isinstance(dummy, Dummy)
    
    #test inclusion in module - convenience function
    mod = InterpreterObject()
    siml_dummy_class.put_into(mod)
    
    assert mod.get_attribute('Dummy') is siml_dummy_class
    
    

# -------- Test Siml wrapper for float classes ------------------------------------------------------------------
def test_IFloat_1(): #IGNORE:C01111
    #skip_test('Test IFloat: construction from Siml class')
    print 'Test IFloat: construction from Siml class'
    from freeode.interpreter import IFloat, CLASS_FLOAT, siml_isinstance
    
    #test construction from Siml class
    val = CLASS_FLOAT()
    assert isinstance(val, IFloat)
    assert siml_isinstance(val, CLASS_FLOAT)
    
    #test construction from Python class - Siml type must still be right
    val1 = IFloat()
    assert siml_isinstance(val1, CLASS_FLOAT)



def test_IFloat_2(): #IGNORE:C01111
    #skip_test('Test IFloat: constructor')
    print 'Test IFloat: constructor'
    from freeode.interpreter import IFloat
    
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
    #skip_test('Test IFloat: mathematical operators from Python') #IGNORE:E1101
    print 'Test IFloat: mathematical operators from Python'
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



def test_IFloat_4(): #IGNORE:C01111
    #skip_test('Test IFloat: special functions for mathematical operators from Siml')
    print 'Test IFloat: special functions for mathematical operators from Siml'
    from freeode.interpreter import IFloat
    
    val_2 = IFloat(2)
    val_3 = IFloat(3)
    
    #look the methods up and call them; then assert that the result is correct
    res = val_2.get_attribute('__add__')(val_3)
    assert res.value == 2 + 3
    res = val_2.get_attribute('__sub__')(val_3)
    assert res.value == 2 - 3
    res = val_2.get_attribute('__mul__')(val_3)
    assert res.value == 2 * 3
    res = val_2.get_attribute('__div__')(val_3)
    assert res.value == 2 / 3
    res = val_2.get_attribute('__mod__')(val_3)
    assert res.value == 2 % 3
    res = val_2.get_attribute('__pow__')(val_3)
    assert res.value == 2 ** 3
    res = val_2.get_attribute('__neg__')()
    assert res.value == -2 


#TODO: test comparison operators

# -------- Test Siml wrapper for str classes ------------------------------------------------------------------
def test_IString_1(): #IGNORE:C01111
    #skip_test('Test IString: construction from Siml class')
    print 'Test IString: construction from Siml class'
    from freeode.interpreter import IString, CLASS_STRING, siml_isinstance
    
    #test construction from Siml class
    val = CLASS_STRING()
    assert isinstance(val, IString)
    assert siml_isinstance(val, CLASS_STRING)
    
    #test construction from Python class - Siml type must still be right
    val1 = IString()
    assert siml_isinstance(val1, CLASS_STRING)



def test_IString_2(): #IGNORE:C01111
    #skip_test('Test IString: constructor')
    print 'Test IString: constructor'
    from freeode.interpreter import IString
    
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

    try:
        IString([])
    except TypeError:
        print 'expected exception: wrong argument type.'
    else:
        assert False, 'object was constructed with wrong initial values'



def test_IString_3(): #IGNORE:C01111
    #skip_test('Test IString: mathematical operators from Python') #IGNORE:E1101
    print 'Test IString: mathematical operators from Python'
    from freeode.interpreter import IString
    
    val_a = IString('a')
    val_b = IString('b')
    
    assert (val_a + val_b).value == val_a.value + val_b.value



def test_IString_4(): #IGNORE:C01111
    #skip_test('Test IString: special functions for mathematical operators from Siml')
    print 'Test IString: special functions for mathematical operators from Siml'
    from freeode.interpreter import IString
    
    val_a = IString('a')
    val_b = IString('b')
    
    #look the methods up and call them; then assert that the result is correct
    res = val_a.get_attribute('__add__')(val_b)
    assert res.value == 'ab'



# -------- Test Siml wrapper for bool objects ------------------------------------------------------------------
def test_IBool_1(): #IGNORE:C01111
    msg = 'Test IBool: construction from Siml class'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IBool, CLASS_BOOL, siml_isinstance
    
    #test construction from Siml class
    val = CLASS_BOOL()
    assert isinstance(val, IBool)
    assert siml_isinstance(val, CLASS_BOOL)
    
    #test construction from Python class - Siml type must still be right
    val1 = IBool()
    assert siml_isinstance(val1, CLASS_BOOL)



def test_IBool_2(): #IGNORE:C01111
    msg = 'Test IString: constructor'
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import IBool
    
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

    try:
        IBool([])
    except TypeError:
        print 'expected exception: wrong argument type.'
    else:
        assert False, 'object was constructed with wrong initial values'

#TODO: Test comparison operators
#TODO: Test IBool to string conversion
#TODO: Test boolean operations (eventually)


# -------- Test expression evaluation ------------------------------------------------------------------------
def test_operator_dispatch_1(): #IGNORE:C01111
    #skip_test('Test ExpressionVisitor: handling of binary operators with Float values.')
    print 'Test ExpressionVisitor: handling of binary operators with Float values.'
    from freeode.interpreter import (IFloat, ExpressionVisitor)
    from freeode.ast import NodeOpInfix2, NodeOpPrefix1
    
    expr_visit = ExpressionVisitor()
    
    val_2 = IFloat(2)
    val_3 = IFloat(3)
    
    op_sub = NodeOpInfix2('-', [val_2, val_3])
    res = expr_visit.dispatch(op_sub)
    print res
    assert res.value == -1 
    
    op_neg = NodeOpPrefix1('-', [val_2])
    res = expr_visit.dispatch(op_neg)
    print res
    assert res.value == -2 
    


def test_operator_dispatch_2(): #IGNORE:C01111
    msg = 'Test ExpressionVisitor: handling of binary operators with unknown Float values.'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (IFloat, ExpressionVisitor)
    from freeode.ast import NodeOpInfix2, NodeOpPrefix1, RoleVariable

    expr_visit = ExpressionVisitor()
    
    val_2 = IFloat()
    val_2.role = RoleVariable
    val_3 = IFloat()
    val_3.role = RoleVariable
    
    op_sub = NodeOpInfix2('-', [val_2, val_3])
    res = expr_visit.dispatch(op_sub)
    print res
    assert isinstance(res, NodeOpInfix2)
    
    op_neg = NodeOpPrefix1('-', [val_2])
    res = expr_visit.dispatch(op_neg)
    print res
    assert isinstance(res, NodeOpPrefix1)
    


def test_expression_evaluation_1(): #IGNORE:C01111
    #skip_test('Test expression evaluation (only immediate values)')
    print 'Test expression evaluation (only immediate values)'
    from freeode.interpreter import ExpressionVisitor
    import freeode.simlparser as simlparser
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('0+1*2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #interpret the expression
    exv = ExpressionVisitor()
    res = exv.dispatch(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == 2.0
    
    

def test_expression_evaluation_2(): #IGNORE:C01111
    #skip_test('Test expression evaluation (only immediate values)')
    print 'Test expression evaluation, all operators and brackets (only immediate values)'
    from freeode.interpreter import ExpressionVisitor
    import freeode.simlparser as simlparser
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('(((0-1+2)*3--1)/4)**5*(-1+2*--1**4)%6')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    #print ex
    
    #interpret the expression
    exv = ExpressionVisitor()
    res = exv.dispatch(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    #print res 
    assert res.value == 1
    
    

def test_expression_evaluation_3(): #IGNORE:C01111
    #skip_test('Test expression evaluation (access to variables)')
    print 'Test expression evaluation (access to variables)'
    from freeode.interpreter import (IModule, CLASS_FLOAT, RoleConstant, 
                                     ExpressionVisitor, ExecutionEnvironment)
    import freeode.simlparser as simlparser
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('1 + a * 2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #create module where name lives
    mod = IModule()
    val_2 = CLASS_FLOAT(2.0)
    val_2.role = RoleConstant
    mod.create_attribute('a', val_2)
    print
    print 'Module where variable is located: --------------------------------------------'
    print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    
    #interpret the expression
    exv = ExpressionVisitor()
    exv.environment = env
    res = exv.dispatch(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == 5.0
    
    

def test_expression_evaluation_4(): #IGNORE:C01111
    #skip_test('Test expression evaluation (access to variables)')
    print 'Test expression evaluation (calling built in functions)'
    from freeode.interpreter import (simlparser, IModule, ExecutionEnvironment,
                                     ExpressionVisitor, BuiltInFunctionWrapper, 
                                     ArgumentList, NodeFuncArg,
                                     CLASS_FLOAT)
    import math
    
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('sqrt(2)')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #create module where names live
    mod = IModule()
    #create sqrt function with named arguments
    sqrt = lambda x: CLASS_FLOAT(math.sqrt(x.value))
    #create a function object that wraps the sqrt function
    func = BuiltInFunctionWrapper('sqrt', 
                                  ArgumentList([NodeFuncArg('x', CLASS_FLOAT)]), 
                                  return_type=CLASS_FLOAT, 
                                  py_function=sqrt)
    #put function into module
    mod.create_attribute('sqrt', func)
    print
    print 'Module where function is located: --------------------------------------------'
    print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    #create visitor for evaluating the expression
    exv = ExpressionVisitor()
    exv.environment = env
    #evaluate the expression
    res = exv.dispatch(ex)
    print
    print 'Result object: --------------------------------------------------------------'
    print res 
    assert res.value == math.sqrt(2)



def test_expression_evaluation_5(): #IGNORE:C01111
    #skip_test('Test disabled')
    print 'Test expression evaluation (returning of partially evaluated expression when accessing variables)'
    from freeode.interpreter import (IModule, CLASS_FLOAT, RoleVariable, 
                                     ExecutionEnvironment, ExpressionVisitor,
                                     NodeOpInfix2)
    import freeode.simlparser as simlparser
    #parse the expression
    ps = simlparser.Parser()
    ex = ps.parseExpressionStr('a + 2*2')
    print
    print 'AST (parser output): -----------------------------------------------------------'
    print ex
    
    #create module where name lives
    mod = IModule()
    #create attribute 'a' with no value
    val_2 = CLASS_FLOAT()
    val_2.value = None
    val_2.role = RoleVariable
    mod.create_attribute('a', val_2)
    print
    print 'Module where variable is located: --------------------------------------------'
    print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    
    #interpret the expression
    exv = ExpressionVisitor()
    exv.environment = env
    res = exv.dispatch(ex)
    print
    print 'Result object - should be an unevaluated expression: --------------------------------------------------------------'
    print res 
    assert isinstance(res, NodeOpInfix2)
    assert res.operator == '+'



def test_ExpressionVisitor_unknown_arguments_1(): #IGNORE:C01111
    msg = 'Test expression evaluation (calling built in functions), unknown arguments'
    #skip_test(msg)
    print msg
    from freeode.interpreter import (IModule, ExecutionEnvironment,
                                     ExpressionVisitor, 
                                     BuiltInFunctionWrapper, ArgumentList,
                                     CLASS_FLOAT, RoleVariable)
    from freeode.ast import (NodeFuncCall, NodeIdentifier, NodeFuncArg)
    import math
    
    #create module where the function lives
    mod = IModule()
    #create sqrt function with named arguments
    sqrt = lambda x: CLASS_FLOAT(math.sqrt(x.value))
    #create a function object that wraps the sqrt function
    func = BuiltInFunctionWrapper('sqrt', 
                                  ArgumentList([NodeFuncArg('x', CLASS_FLOAT)]), 
                                  return_type=CLASS_FLOAT, 
                                  py_function=sqrt)
    #put function into module
    mod.create_attribute('sqrt', func)
    print
    print 'Module where function is located: --------------------------------------------'
    #print mod
    
    #create environment for lookup of variables (stack frame)
    env = ExecutionEnvironment()
    env.global_scope = mod
    #create visitor for evaluating the expression
    exv = ExpressionVisitor()
    exv.environment = env
    
    #create a Siml value as function argument
    val_1 = CLASS_FLOAT()    
    val_1.role = RoleVariable
    #create function call with unkown argument
    call = NodeFuncCall(NodeIdentifier('sqrt'), [val_1], {})
    
    #evaluate the function call
    ret_val = exv.dispatch(call)
    print
    print 'Result object: --------------------------------------------------------------'
    print ret_val 
    #evaluating a function call with unknown arguments must return a function call
    assert isinstance(ret_val, NodeFuncCall)
    assert ret_val.type() is CLASS_FLOAT
    
    

def test_ExpressionVisitor_unknown_arguments_2(): #IGNORE:C01111
    #skip_test('Test ExpressionVisitor: call library function with unknown argument')
    print 'Test ExpressionVisitor: call library function with unknown argument'
    from freeode.interpreter import (Interpreter, CLASS_FLOAT, )
    from freeode.ast import (NodeFuncCall, NodeIdentifier, RoleVariable)

    #create the interpreter - initializes INTERPRETER
    # this way SimlFunction can access the interpreter.
    intp = Interpreter()    #IGNORE:W0612
    intp.create_test_module_with_builtins()
    #create a Siml value as function argument
    val_1 = CLASS_FLOAT()  
    val_1.role = RoleVariable  

    #create function call with unkown argument
    call = NodeFuncCall(NodeIdentifier('sqrt'), [val_1], {})
    #interpret call
    ret_val = intp.statement_visitor.expression_visitor.dispatch(call)
    #evaluating a function call with unknown arguments must return a function call
    assert isinstance(ret_val, NodeFuncCall)
    assert ret_val.type() is CLASS_FLOAT
    


# --------- Test basic execution of statements (no interpreter object) ----------------------------------------------------------------
def test_basic_execution_of_statements(): #IGNORE:C01111
    #skip_test('Test basic execution of statements (no interpreter object)')
    print 'Test basic execution of statements (no interpreter object) .................................'
    from freeode.interpreter import (IModule, CLASS_FLOAT, CLASS_STRING,
                                     ExecutionEnvironment,
                                     ExpressionVisitor, StatementVisitor)
    import freeode.simlparser as simlparser
    from freeode.ast import RoleConstant
    
    prog_text = \
'''
data a:Float const 
data b:Float const 
a = 2*2 + 3*4
b = 2 * a

data c:String const
c = 'Hello ' + 'world!'
'''

    #create the built in library
    mod = IModule()
    mod.create_attribute('Float', CLASS_FLOAT)
    mod.create_attribute('String', CLASS_STRING)
#    print
#    print 'global namespace - before interpreting statements - built in library: ---------------'
#    print mod
           
    #create dummy interpreter class, needed for assignment statement
    class Interpreter(object):
        def __init__(self):
            self.assign_target_roles = (RoleConstant,)
    #initialize the interpreter
    intp = Interpreter()
    env = ExecutionEnvironment()
    exv = ExpressionVisitor()
    exv.environment = env
    stv = StatementVisitor(None, exv)
    stv.interpreter = intp
    stv.environment = env
    #set up parsing the main module
    stv.environment.global_scope = mod
    stv.environment.local_scope = mod

    #parse the program text
    ps = simlparser.Parser()
    module_code = ps.parseModuleStr(prog_text)
    
    #interpreter main loop
    for stmt in module_code.statements:
        stv.dispatch(stmt)
        
#    print
#    print 'global namespace - after interpreting statements: -----------------------------------'
#    print mod
    
    assert mod.get_attribute('a').value == 16             #IGNORE:E1103
    assert mod.get_attribute('b').value == 2*16           #IGNORE:E1103
    assert mod.get_attribute('c').value == 'Hello world!' #IGNORE:E1103
  
  
  
# -------- Test interpreter object - basic --------------------------------------------------------  
def test_SimlFunction_1(): #IGNORE:C01111
    #skip_test('Test disabled')
    print 'Test SimlFunction: call user defined function ...............................................................'
    print 'User defined functions are created without parser.'
    from freeode.interpreter import (Interpreter, SimlFunction, 
                                     ArgumentList, CLASS_FLOAT, CLASS_STRING,
                                     BUILT_IN_LIB)
    from freeode.ast import (NodeFuncArg, NodeReturnStmt, 
                             NodeIdentifier, UserException)

    #create the interpreter - initializes INTERPRETER
    # this way SimlFunction can access the interpreter.
    intp = Interpreter()    #IGNORE:W0612
    #create a Siml value as function argument
    val_1 = CLASS_FLOAT(1)
    
    #create a function without statements (impossible in Siml)
    # func test(a:Float):
    #     ** nothing **
    f1 = SimlFunction('test', ArgumentList([NodeFuncArg('a', CLASS_FLOAT)]), 
                      return_type=None, statements=[], global_scope=BUILT_IN_LIB)
    #call with existing value
    f1(val_1)
    
    #create a function with return statement - uses interpreter for executing the statement
    # func test(a:Float) -> Float:
    #     return a
    f2 = SimlFunction('test', ArgumentList([NodeFuncArg('a', CLASS_FLOAT)]), 
                      return_type=CLASS_FLOAT, 
                      statements=[NodeReturnStmt([NodeIdentifier('a')])], 
                      global_scope=BUILT_IN_LIB)
    #call function and see if value is returned
    ret_val = f2(val_1)
    assert ret_val.value == 1.

    #create a function with wrong return type
    # func test(a:Float) -> String:
    #     return a
    f3= SimlFunction('test', ArgumentList([NodeFuncArg('a', CLASS_FLOAT)]), 
                      return_type=CLASS_STRING, 
                      statements=[NodeReturnStmt([NodeIdentifier('a')])], 
                      global_scope=BUILT_IN_LIB)
    try:
        ret_val = f3(val_1)
    except UserException:
        print 'Getting expected exception: type mismatch at function return'
    else:
        fail_test('There was wrong return type, but no exception!') #IGNORE:E1101



def test_SimlFunction_2(): #IGNORE:C01111
    print 'SimlFunction: get_complete_path method'
    from freeode.interpreter import (SimlFunction, DotName)
    
    #the root object where the long name will be created
    root = SimlFunction('root')
    sub1 = SimlFunction('sub1')
    sub2 = SimlFunction('sub2')

    root.create_attribute('sub1', sub1)
    sub1.create_attribute('sub2', sub2)
    
    print root
    
    long_name = sub2.get_complete_path()
    
    assert long_name == DotName('root.sub1.sub2')



def test_SimlFunction_3(): #IGNORE:C01111
    #skip_test('Test disabled')
    print 'Test SimlFunction: storage of local variables during code collection.'
    print 'User defined functions are created without parser.'
    from freeode.interpreter import (Interpreter, SimlFunction, IModule,
                                     ArgumentList, CLASS_FLOAT, BUILT_IN_LIB)
    from freeode.ast import (NodeFuncArg)

    #create the interpreter - initializes INTERPRETER
    
    intp = Interpreter()    #IGNORE:W0612
    
    
    #create a Siml value as function argument
    val_1 = CLASS_FLOAT(1)

    #create a function without statements (impossible in Siml)
    # func test(a:Float):
    #     ** nothing **
    f1 = SimlFunction('test', ArgumentList([NodeFuncArg('a', CLASS_FLOAT)]), 
                      return_type=None, statements=[], global_scope=BUILT_IN_LIB)
    #create module where the function lives
    mod1 = IModule('test-module')
    mod1.create_attribute('test', f1)
    
    #call with existing value
    # and set interpreter up to collect code. In this mode local variables of all 
    # functions must become algebraic variables of the simulation object.
    intp.start_collect_code()
    f1(val_1)
    stmts, fn_locals = intp.stop_collect_code()
    
    print fn_locals
    
    #there must be one element in the locals storage, some base namespace for 
    # the function argument 'a'
    assert len(fn_locals.attributes) > 0
    
    #get the local variable 'a' 
    ns_test = fn_locals.get_attribute('test')
    ns_1    = ns_test.  get_attribute('1')
    float_a = ns_1.     get_attribute('a')
    assert float_a is val_1



# -------- Test administrative functions ------------------------------------------------------------------------
def test_determine_result_role_1(): #IGNORE:C01111
    msg = 'Test determine_result_role: '
    #skip_test(msg)
    print msg
    from freeode.interpreter import IFloat, determine_result_role
    from freeode.ast import RoleConstant, RoleParameter, RoleVariable
    
    #some constants
    c_1 = IFloat()
    c_1.role = RoleConstant
    c_2 = IFloat()
    c_2.role = RoleConstant
    #some parameters
    p_1 = IFloat()
    p_1.role = RoleParameter
    p_2 = IFloat()
    p_2.role = RoleParameter
    #some variables
    v_1 = IFloat()
    v_1.role = RoleVariable
    v_2 = IFloat()
    v_2.role = RoleVariable
    
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
    u.role = RoleUnkown
    #some constants
    c_1 = IFloat()
    c_1.role = RoleConstant
    c_2 = IFloat()
    c_2.role = RoleConstant
    #some parameters
    p_1 = IFloat()
    p_1.role = RoleParameter
    p_2 = IFloat()
    p_2.role = RoleParameter
    #some variables
    v_1 = IFloat()
    v_1.role = RoleVariable
    v_2 = IFloat()
    v_2.role = RoleVariable
    
    #one argument with RoleUnknown - should raise exception
    try: 
        determine_result_role((c_1, p_1, v_1, u), 
                              {'a':c_2, 'b':p_2, 'c':v_2, })
    except ValueError, e:
        print 'Exception is OK.'
        print e
    else:
        assert False, 'Exception missing.'
    #one argument with RoleUnknown - should raise exception
    try:
        determine_result_role((c_1, p_1), {'a':c_2, 'b':p_2, 'u':u})
    except ValueError, e:
        print 'Exception is OK.'
        print e
    else:
        assert False, 'Exception missing.'
    #one argument with RoleUnknown - should raise exception
    try:
        determine_result_role((c_1, u), {'a':c_2})
    except ValueError, e:
        print 'Exception is OK.'
        print e
    else:
        assert False, 'Exception missing.'



def test_is_role_more_variable_1(): #IGNORE:C01111
    #skip_test('Test is_role_more_variable: compare the variablenes of two roles.')
    print 'Test is_role_more_variable: compare the variablenes of two roles.'
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
    
    try: 
        is_role_more_variable(float, RoleConstant)
    except ValueError, e:
        print 'Exception is OK!'
        print e
    else:
        assert False, 'Exception missing'
        
    try: 
        is_role_more_variable(RoleParameter, float)
    except ValueError, e:
        print 'Exception is OK!'
        print e
    else:
        assert False, 'Exception missing'
        
    try: 
        is_role_more_variable(RoleParameter, 1)
    except TypeError, e:
        print 'Exception is OK!'
        print e
    else:
        assert False, 'Exception missing'
        
        

def test_set_role_recursive_1(): #IGNORE:C01111
    #skip_test('Test set_role_recursive')
    print 'Test set_role_recursive'
    from freeode.interpreter import (InterpreterObject, set_role_recursive)
    from freeode.ast import (RoleConstant, RoleParameter, RoleVariable, 
                             RoleUnkown)
    
    #create a little tree of objects
    c1 = InterpreterObject()
    c1.role = RoleConstant
    p1 = InterpreterObject()
    p1.role = RoleParameter
    v1 = InterpreterObject()
    v1.role = RoleVariable
    u1 = InterpreterObject()
    u1.role = RoleUnkown
    root = InterpreterObject()
    root.role = RoleVariable
    root.create_attribute('c1', c1)
    root.create_attribute('p1', p1)
    root.create_attribute('v1', v1)
    root.create_attribute('u1', u1)
    #set the roles in the whole tree
    ########## This line varies ############
    set_role_recursive(root, RoleVariable) 
    #test the new roles
    assert root.role == RoleVariable
    assert c1.role == RoleConstant
    assert p1.role == RoleParameter
    assert v1.role == RoleVariable
    assert u1.role == RoleVariable
    
    #create a little tree of objects
    c1 = InterpreterObject()
    c1.role = RoleConstant
    p1 = InterpreterObject()
    p1.role = RoleParameter
    v1 = InterpreterObject()
    v1.role = RoleVariable
    u1 = InterpreterObject()
    u1.role = RoleUnkown
    root = InterpreterObject()
    root.role = RoleVariable
    root.create_attribute('c1', c1)
    root.create_attribute('p1', p1)
    root.create_attribute('v1', v1)
    root.create_attribute('u1', u1)
    #set the roles in the whole tree
    ########## This line varies ############
    set_role_recursive(root, RoleParameter) 
    #test the new roles
    assert root.role == RoleParameter
    assert c1.role == RoleConstant
    assert p1.role == RoleParameter
    assert v1.role == RoleParameter
    assert u1.role == RoleParameter
    
    #create a little tree of objects
    c1 = InterpreterObject()
    c1.role = RoleConstant
    p1 = InterpreterObject()
    p1.role = RoleParameter
    v1 = InterpreterObject()
    v1.role = RoleVariable
    u1 = InterpreterObject()
    u1.role = RoleUnkown
    root = InterpreterObject()
    root.role = RoleVariable
    root.create_attribute('c1', c1)
    root.create_attribute('p1', p1)
    root.create_attribute('v1', v1)
    root.create_attribute('u1', u1)
    #set the roles in the whole tree
    ########## This line varies ############
    set_role_recursive(root, RoleConstant) 
    #test the new roles
    assert root.role == RoleConstant
    assert c1.role == RoleConstant
    assert p1.role == RoleConstant
    assert v1.role == RoleConstant
    assert u1.role == RoleConstant
    
    

if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_InterpreterObject_find_name()
    pass