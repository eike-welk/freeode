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
#from freeode.interpreter import Signature


class Signature(object):
    """
    Contains arguments and return type of a function.
    
    Simplified dummy version of interpreter.Signature, to enable independent 
    testing.
    """
    #Object that creates an ASCII art tree from nodes
    __siml_aa_tree_maker__ = AATreeMaker()

    def __init__(self, arguments=None, return_type=None, loc=None):
        '''
        ARGUMENTS
        ---------
        arguments: [ast.NodeFuncArg, ...] or SimpleSignature or Signature or None
            The functions arguments
            arguments == None -> Don't check arguments.
        return_type: ast.Node or type or None
            Type of the function's return value.
            return_type == None -> Don't check return type.
        loc: ast.TextLocation 
            Location where the function is defined in the program text.
        '''
        object.__init__(self)
        #special case copy construction
        if isinstance(arguments, (Signature,)):
            loc = arguments.loc
            return_type = arguments.return_type
            arguments = arguments.arguments

        #--- auxiliary data --- 
        #dictionary for quick access to argument definitions by name
        #also for testing uniqueness and existence of argument names 
        self.argument_dict = {}
        #arguments with default values (subset of self.arguments)
        self.default_args = []
        #If True: the annotations have been evaluated; 
        #otherwise self._evaluate_type_specs must be called
        self.is_evaluated = False
        
        #--- core data --------
        #Location where the function is defined in the program text.
        self.loc = loc            
        #The functions arguments: [ast.NodeFuncArg, ...]
        self.arguments = None
        self.set_arguments(arguments) 
        #Type of the function's return value.
        self.return_type = return_type


    def set_arguments(self, arguments):
        '''
        Put the argument specification into the Signature.
         
        ARGUMENTS
        ---------
        arguments: [ast.NodeFuncArg, ...] or SimpleSignature or Signature or None
            The functions arguments
        '''
        self.arguments = arguments
        if arguments is None:
            return
        #Check arguments and fill self.argument_dict
        there_was_keyword_argument = False
        for arg in self.arguments:
            #check that positional arguments come first
            if arg.default_value is not None:
                there_was_keyword_argument = True
                self.default_args.append(arg)
            elif there_was_keyword_argument: 
                raise Exception('Positional arguments must come before '
                                    'keyword arguments!', self.loc, errno=3200110)
            #test: argument names must be unique
            if arg.name in self.argument_dict:
                raise Exception('Duplicate argument name "%s"!' 
                                    % str(arg.name), self.loc, errno=3200120) 
            self.argument_dict[arg.name] = arg



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
    
    
#def argument_type(*type_list):
#    'Decorator to define type_list of function arguments.'
#    def decorate_with_type(func_to_decorate):
#        #Create Signature object if necessary
#        if not hasattr(func_to_decorate, 'siml_signature'):
#            loc = make_pyfunc_loc(func_to_decorate)
#            func_to_decorate.siml_signature = Signature(loc=loc) 
#            func_to_decorate.siml_globals = InterpreterObject()
#            
#        #Get argument names and default values of Python function
#        args, _varargs, _keywords, defaults = inspect.getargspec(func_to_decorate)
#        siml_args = [NodeFuncArg(arg_name) for arg_name in args]
#        for arg, dval in zip(reversed(siml_args), reversed(defaults)):
#            arg.default_value = dval
#        #Combine with Siml type definitions
#        for arg, type1 in zip(siml_args, type_list):
#            arg.type = type1
#        func_to_decorate.siml_signature.set_arguments(siml_args)
#        return func_to_decorate
#
#    return decorate_with_type
#
#    
#def return_type(type_obj):
#    'Decorator to define return type of function.'
#    def decorate_with_type(func_to_decorate):
#        #Give function a signature object if it has none
#        if not hasattr(func_to_decorate, 'siml_signature'):
#            loc = make_pyfunc_loc(func_to_decorate)
#            func_to_decorate.siml_signature = Signature(loc=loc) 
#            func_to_decorate.siml_globals = InterpreterObject()
#            
#        #Put return type into signature
#        func_to_decorate.siml_signature.return_type = type_obj
#        return func_to_decorate
#    
#    return decorate_with_type


def signature(arg_types, return_type):
    '''
    Create Signature object for Python function. 
    
    ARGUMENTS
    ---------
    arg_types: list(type | Proxy)
        Types of the function's arguments.
    return_type: type | Proxy
        The function's return type.
        
    This is a decorator see:
        http://www.python.org/dev/peps/pep-0318/#current-syntax
    '''    
    assert isinstance(arg_types, list) or arg_types is None
    assert isinstance(return_type, (type, Proxy)) or return_type is None
    
    #This function does the real work
    def decorate_with_signature(func_to_decorate):
        #Create argument list
        if arg_types is not None:
            #Get from Python function: argument names, default values, 
            #create Siml argument list
            args, _varargs, _keywords, defaults = inspect.getargspec(func_to_decorate)
            siml_args = [NodeFuncArg(arg_name) for arg_name in args]
            for arg, dval in zip(reversed(siml_args), reversed(defaults)):
                arg.default_value = dval
            #Put Siml type definitions into argument list
            for arg, type1 in zip(siml_args, arg_types):
                arg.type = type1
        else:
            siml_args = None
        
        loc = make_pyfunc_loc(func_to_decorate)
        func_to_decorate.siml_signature = Signature(siml_args, return_type, loc)
        func_to_decorate.siml_globals = InterpreterObject() #dummy global namespace
        
        return func_to_decorate

    return decorate_with_signature
   

class SimlFunction(InterpreterObject):
    '''
    Function written in Siml (user defined function).
    '''
    def __init__(self, name, signature=Signature(), #pylint:disable-msg=W0621
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
    
#    @return_type(Dummy1) 
#    def foo():
#        return Dummy1()
#    #print aa_make_tree(foo)
#    assert foo.siml_signature.arguments is None     #pylint:disable-msg=E1101
#    assert foo.siml_signature.return_type is Dummy1 #pylint:disable-msg=E1101
#    
#    @argument_type(Dummy1, Dummy2)
#    def bar(_a, _b=dummy2):                          
#        pass
#    #print aa_make_tree(bar)
#    args = bar.siml_signature.arguments            #pylint:disable-msg=E1101
#    assert len(args) == 2          
#    assert args[0].type is Dummy1 
#    assert args[1].type is Dummy2
#    assert args[1].default_value is dummy2
#    assert bar.siml_signature.return_type is None  #pylint:disable-msg=E1101
#    
#    @argument_type(Dummy1, Dummy2)
#    @return_type(Dummy1) 
#    def baz(a, _b=dummy2):                         
#        return a
#    #print aa_make_tree(baz)
#    args = baz.siml_signature.arguments            #pylint:disable-msg=E1101
#    assert len(args) == 2          
#    assert args[0].type is Dummy1 
#    assert args[1].type is Dummy2
#    assert args[1].default_value is dummy2
#    assert baz.siml_signature.return_type is Dummy1  #pylint:disable-msg=E1101

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
    
    

test_SimlFunction_and_user_defined_class_creation()
test_wrappers()
#test_aa_tree_printing()
