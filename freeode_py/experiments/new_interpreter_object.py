# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2006 - 2010 by Eike Welk                                #
#    eike.welk@gmx.net                                                     #
#                                                                          #
#    License: GPL                                                          #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

'''
Try out infrastructure for new InterpreterObject

Usage of new facility for wrapping Python code:
      foo_proxy = Proxy()
      class Foo(IObject):
          @arguments(Int, foo_proxy)
          @returns(Int)
          def bar(a, b):
              return a
      foo_proxy.set(Foo) 

TODO: Creation of new user defined class
'''

import inspect

from freeode.ast import NodeFuncArg
from freeode.util import AATreeMaker, TextLocation
from freeode.interpreter import Signature


#class InterpreterObjectMeta(type):
#    '''Metaclass for the InterpreterObject class.'''
#    #Object that creates an ASCII art tree from nodes
#    __siml_aa_tree_maker__ = AATreeMaker()
#    
#    def aa_make_tree(self):       
#        '''
#        Create ASCII-art tree of this object, and of all data attributes it 
#        contains recursively.
#        '''
#        return self.__siml_aa_tree_maker__.make_tree(self)   
    
  
class InterpreterObject(object):
    '''
    Base class of all interpreter objects
    '''
    #__metaclass__ = InterpreterObjectMeta

    #Object that creates an ASCII art tree from nodes
    __siml_aa_tree_maker__ = AATreeMaker()



class Proxy(InterpreterObject):
    '''
    Place holder for an other object. Similar to a pointer but automatically
    dereferenced by the interpreter

    This class is part of the new facility for wrapping Python code:
    Usage:
    
      foo_proxy = Proxy()
      class Foo(IObject):
          @arguments(Int, foo_proxy)
          @returns(Int)
          def bar(a, b):
              return a
      foo_proxy.set(Foo) 
    '''
    def __init__(self, value=None):
        InterpreterObject.__init__(self)
        self.value = None
        self.set(value)
        
    def set(self, value):
        '''Let Proxy point to some object.'''
        self.value = value
    set.siml_signature = Signature() #pylint:disable-msg=W0612



def make_pyfunc_loc(py_func):
    '''Create a TextLocation object for a Python function.'''
    file_name = py_func.__code__.co_filename
    line_no = py_func.__code__.co_firstlineno
    loc = TextLocation(file_name=file_name, line_no=line_no)
    return loc
    
    
def argument_type(*type_list):
    'Decorator to define type_list of function arguments.'
    def decorate_with_type(func_to_decorate):
        #Create Signature object if necessary
        if not hasattr(func_to_decorate, 'siml_signature'):
            loc = make_pyfunc_loc(func_to_decorate)
            func_to_decorate.siml_signature = Signature(loc=loc) 
        #Get argument names and default values of Python function
        args, _varargs, _keywords, defaults = inspect.getargspec(func_to_decorate)
        siml_args = [NodeFuncArg(arg_name) for arg_name in args]
        for arg, dval in zip(reversed(siml_args), reversed(defaults)):
            arg.default_value = dval
        #Combine with Siml type definitions
        for arg, type1 in zip(siml_args, type_list):
            arg.type = type1
        func_to_decorate.siml_signature.set_arguments(siml_args)
        return func_to_decorate

    return decorate_with_type

    
def return_type(type_obj):
    'Decorator to define return type of function.'
    def decorate_with_type(func_to_decorate):
        #Give function a signature object if it has none
        if not hasattr(func_to_decorate, 'siml_signature'):
            loc = make_pyfunc_loc(func_to_decorate)
            func_to_decorate.siml_signature = Signature(loc=loc) 
        #Put return type into signature
        func_to_decorate.siml_signature.return_type = type_obj
        return func_to_decorate
    
    return decorate_with_type
    
   

class SimlFunction(InterpreterObject):
    '''
    Function written in Siml (user defined function).
    '''
    def __init__(self, name, signature=Signature(),
                  statements=None, global_scope=None, loc=None):
        #CallableObject.__init__(self, name)
        InterpreterObject.__init__(self)
        #The function's name
        self.__name__ = name
        #Function signature including return type
        self.siml_signature = signature
        #the statements of the function's body
        self.statements = statements if statements else []
        #global namespace, stored when the function was defined
        self.siml_globals = global_scope
        #count how often the function was called (to create unique names
        #for the local variables)
        self.call_count = 0
        #--- stack trace ---------
        self.loc = loc

    def __get__(self, obj, _my_type=None):
        if obj is None:
            #print 'called from class'
            return self
        else:
            #print 'called from instance'
            return SimlBoundMethod(self, obj)


class SimlBoundMethod(InterpreterObject):
    '''
    Represents a method of an object.
    Stores a function and the correct 'this' pointer.

    The object is only call-able from Siml. It has the same attributes like 
    Python's bound method. 

    No argument parsing or type checking are is done. The wrapped function
    is responsible for this. 
    '''
    def __init__(self, function, this):
        '''
        ARGUMENTS
        ---------
        function: CallableObject or (Python) function
            Wrapped function that will be called.
        this: InterpreterObject
            The first positional argument, that will be supplied to the wrapped
            function.
        '''
        #CallableObject.__init__(self, name)
        InterpreterObject.__init__(self)
        #the wrapped function
        self.im_func = function
        #the 'this' argument
        self.im_self = this



def test_SimlFunction_and_user_defined_class_creation():
    'Test the user defined function object, and creation of user defined classes.'
    
    #Create a new class the dynamic way, it has one user defined method: func1
    #type(name, bases, dict) -> a new type
    func1 = SimlFunction('func1')
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
    
    
        
def test_wrappers():
    'Test wrapping facility for python functions'
    
    class Dummy1(InterpreterObject):
        pass
    class Dummy2(InterpreterObject):
        pass
    dummy2 = Dummy2()
    
    @return_type(Dummy1) 
    def foo():
        return Dummy1()
    #print aa_make_tree(foo)
    assert foo.siml_signature.arguments is None     #pylint:disable-msg=E1101
    assert foo.siml_signature.return_type is Dummy1 #pylint:disable-msg=E1101
    
    @argument_type(Dummy1, Dummy2)
    def bar(_a, _b=dummy2):                          
        pass
    #print aa_make_tree(bar)
    args = bar.siml_signature.arguments            #pylint:disable-msg=E1101
    assert len(args) == 2          
    assert args[0].type is Dummy1 
    assert args[1].type is Dummy2
    assert args[1].default_value is dummy2
    assert bar.siml_signature.return_type is None  #pylint:disable-msg=E1101
    
    @argument_type(Dummy1, Dummy2)
    @return_type(Dummy1) 
    def baz(a, _b=dummy2):                         
        return a
    #print aa_make_tree(baz)
    args = baz.siml_signature.arguments            #pylint:disable-msg=E1101
    assert len(args) == 2          
    assert args[0].type is Dummy1 
    assert args[1].type is Dummy2
    assert args[1].default_value is dummy2
    assert baz.siml_signature.return_type is Dummy1  #pylint:disable-msg=E1101
    
    
    


test_SimlFunction_and_user_defined_class_creation()
test_wrappers()
#test_aa_tree_printing()
