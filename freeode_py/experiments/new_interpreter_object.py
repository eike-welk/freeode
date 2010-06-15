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

TODO: Write wrapping facility
Usage of new facility for wrapping Python code:
      foo_proxy = Proxy()
      class Foo(IObject):
          @arguments(Int, foo_proxy)
          @returns(Int)
          def bar(a, b):
              return a
      foo_proxy.set(Foo) 

TODO: New SimlFunction
TODO: Creation of new user defined class
'''

import inspect

from freeode.ast import NodeFuncArg
from freeode.util import AATreeMaker, TextLocation, aa_make_tree
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



def make_pyfunc_loc(py_func):
    '''
    Create a TextLocation object for a Python function
    '''
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
        func_to_decorate.siml_signature.arguments = siml_args        
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
    
   

def test_wrappers():
    'Test wrapping facility for python functions'
    
    @return_type(InterpreterObject) 
    def foo():
        return InterpreterObject()
    #print aa_make_tree(foo)
    
    @argument_type(InterpreterObject, InterpreterObject)
    def bar(a, b=2):
        pass
    #print aa_make_tree(bar)
    
    @argument_type(InterpreterObject, InterpreterObject)
    @return_type(InterpreterObject) 
    def baz(a, b=2):
        return InterpreterObject()
    print aa_make_tree(baz)
    
    
    
def test_aa_tree_printing():
    'Test the ascii art tree printing facility.'
    #print InterpreterObject.aa_make_tree(InterpreterObject)
    
    #Try to create a module
    builtin_module = InterpreterObject()
    builtin_module.Object = InterpreterObject
    print aa_make_tree(builtin_module)



test_wrappers()
#test_aa_tree_printing()
