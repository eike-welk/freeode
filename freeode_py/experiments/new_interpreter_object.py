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
    
    def aa_make_tree(self):       
        '''
        Create ASCII-art tree of this object, and of all data attributes it 
        contains recursively.
        '''
        return self.__siml_aa_tree_maker__.make_tree(self)   


def create_py_func_text_location(py_func):
    '''
    TODO: Create a text location object for a Python function
    See: 
        http://docs.python.org/library/inspect.html
    '''
#            file_name = func_to_decorate.__code__.co_filename
#            at_char = func_to_decorate.__code__.co_firstlineno
#            loc = TextLocation(at_char, textString, file_name)
    print inspect.getsourcefile(py_func)
    return None
    
    
def arguments(*args):
    'Decorator to define types of function arguments.'
    #http://docs.python.org/library/inspect.html
    #inspect.getargspec(func)
    def decorate_with_type(func_to_decorate):
        #Give function a signature object if it has none
        if not hasattr(func_to_decorate, 'siml_signature'):
            loc = create_py_func_text_location(func_to_decorate)
            func_to_decorate.siml_signature = Signature(loc=loc) 
        return func_to_decorate

    return decorate_with_type

    
def returns(return_type):
    'Decorator to define return type of function.'
    def decorate_with_type(func_to_decorate):
        #Give function a signature object if it has none
        if not hasattr(func_to_decorate, 'siml_signature'):
            loc = create_py_func_text_location(func_to_decorate)
            func_to_decorate.siml_signature = Signature(loc=loc) 
        #Put return type into signature
        func_to_decorate.siml_signature.return_type = return_type
        return func_to_decorate
    
    return decorate_with_type
    
   

def test_wrappers():
    'Test wrapping facility for python functions'
    
    @returns(InterpreterObject) 
    def foo():
        return InterpreterObject()
    
    
    
def test_aa_tree_printing():
    'Test the ascii art tree printing facility.'
    #print InterpreterObject.aa_make_tree(InterpreterObject)
    
    #Try to create a module
    builtin_module = InterpreterObject()
    builtin_module.Object = InterpreterObject
    print builtin_module.aa_make_tree()



test_wrappers()
#test_aa_tree_printing()
