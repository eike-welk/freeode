# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2008 - 2010 by Eike Welk                                *
#    eike.welk@gmx.net                                                     *
#                                                                          *
#    Credits:                                                              *
#                                                                          *
#    Much of the semantics of this language were taken from the Python     *
#    programming language. Most information and little bits of text were   *
#    taken from the Python Reference Manual by Guido van Rossum.           *
#        http://docs.python.org/reference/                                 *
#    Many thanks to Guido and the Python team, for their excellent         *
#    contributions to free software and free documentation.                *
#                                                                          *
#    The special functions for boolean variables were taken from           *
#    PEP 335 by Greg Ewing                                                 *
#        http://www.python.org/dev/peps/pep-0335/                          *
#    Thank you for thinking hard about this problem, and then putting a    *
#    nice write-up about it in the public domain.                          *
#                                                                          *
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
Interpreter, that is run at compile time, for the SIML language.

The interpreter reads the AST from the parser. It generates
objects (the symbol table), it executes statements that configure the program,
and it collects the statements that will be part of the compiled program. The
interpreter can be seen as Siml's macro facility.

The output of the interpreter is an other program, which only contains 
types that are known to the code generator (float, bool, string). Currently
there are also no functions in the interpreter's output, except for the three
main functions: "initialize", "dynamic" and "final".
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#import copy
import weakref
from weakref import ref
import math
import os
import types
import inspect

from freeode.util import (UserException, DotName, TextLocation, AATreeMaker, 
                          aa_make_tree, DEBUG_LEVEL)
from freeode.ast import (RoleUnkown, RoleConstant, RoleParameter, RoleVariable, 
                         RoleAlgebraicVariable, RoleTimeDifferential, 
                         RoleStateVariable, RoleInputVariable,
                         SimpleSignature,
                         Node, NodeFuncArg, NodeFuncCall, NodeOpInfix2, 
                         NodeOpPrefix1, NodeParentheses, NodeIdentifier, 
                         NodeFloat, NodeString, NodeAttrAccess, 
                         NodeExpressionStmt, NodeAssignment, NodeIfStmt, 
                         NodeClause, NodeCompileStmt, NodeStmtList,
                         NodeClassDef, NodeFuncDef, NodeDataDef, NodePassStmt, 
                         NodeReturnStmt)
import freeode.simlparser as simlparser



class DuplicateAttributeError(Exception):
    '''
    Exception raised by InterpreterObject
    when the user tries to redefine an attribute.
    '''
    def __init__(self, msg='Duplicate Attribute', attr_name=None):
        if attr_name is not None:
            msg = msg + ': ' + str(attr_name)
        Exception.__init__(self, msg)
        self.attr_name = attr_name

class UndefinedAttributeError(Exception):
    '''
    Exception: Attribute is unknown in namespace.
    '''
    def __init__(self, msg='Undefined Attribute', attr_name=None):
        if attr_name is not None:
            msg = msg + ': ' + str(attr_name)
        Exception.__init__(self, msg)
        self.attr_name = attr_name

class IncompatibleTypeError(Exception):
    def __init__(self, msg='Incompatible types', loc=None):
        Exception.__init__(self, msg)
        self.loc = loc

class UnknownArgumentsException(Exception):
    def __init__(self, msg='Unknown arguments.', loc=None):
        Exception.__init__(self, msg)
        self.loc = loc


class ExecutionEnvironment(object):
    '''
    Container for name spaces where symbols are looked up.
    Function get_attribute(...) searches the symbol in all name spaces.

    Other languages call such objects stack frame.
    '''
    def __init__(self):
        #Name space for global variables. Module where the code was written.
        # type: InterpreterObject
        self.global_scope = None
        #Name space of the this pointer in a method. None outside methods.
        self.this_scope = None
        #scope for the local variables of a function
        self.local_scope = None

        #return value from function call
        self.return_value = None
        #default role for the data statement.
        self.default_data_role = RoleUnkown
        
        #function which is currently executed
        self.function = None


    def get_attribute(self, attr_name, default=UndefinedAttributeError()):
        '''
        Find a dot name in this environment.

        When the name is not found an exception is raised, or a default
        value is returned.
        Tries local name space, 'this' name space, global name space.

        Arguments
        ---------
        attr_name : str
            Dotted name that is looked up in the different name spaces.
        default : object (default value: UndefinedAttributeError())
            Object which is returned when attr_name can not be found.
            When argument is of type UndefinedAttributeError, an
            UndefinedAttributeError is raised instead (default behavior).
        '''
        #try to find name in scope hierarchy:
        # function --> class --> module
        scopeList = [self.local_scope, self.this_scope, self.global_scope]
        attr = None
        for scope in scopeList:
            if scope is None:
                continue
            try:
                attr = getattr(scope, attr_name)
                return attr
            except AttributeError: #IGNORE:W0704
                pass
        #attribute could not be found in the scopes
        if isinstance(default, UndefinedAttributeError):
            raise UndefinedAttributeError(attr_name=attr_name)
        else:
            return default



class InterpreterObject(object):
    '''
    Base class of all objects that the interpreter operates on, except for 
    classes and Python functions.
    Can also be seen as part of structured symbol table
    '''
    #Object that creates an ASCII art tree from nodes
    __siml_aa_tree_maker__ = AATreeMaker(top_names= ['__name__', '__siml_role__', '__siml_type__'], 
                                         )

    def __init__(self):
        object.__init__(self)
        #Reference to object one level up in the tree
        #type weakref.ref or None
        #self.parent = None
        #the same as __class__; necessary for unevaluated expressions, where 
        #__class__ is different to __siml_type__
        self.__siml_type__ = None
        #const, param, variable, ... (Comparable to storage class in C++)
        self.__siml_role__ = RoleUnkown
        #TODO: self.save ??? True/False or Save/Optimize/Remove attribute is saved to disk as simulation result

#    def __deepcopy__(self, memo_dict):
#        '''deepcopy that gets the parent right'''
#        copied_self = super(InterpreterObject, self).__deepcopy__(memo_dict)
#        for copied_attr in copied_self.attributes.itervalues():
#            copied_attr.parent = ref(copied_self)
#        return copied_self

#
#    def find_name(self, in_attr):
#        '''
#        Find the name of an attribute.
#
#        ARGUMENTS
#        ---------
#        in_attr: InterpreterObject
#            Attribute whose name will be searched. It must be an attribute of
#            this object (self). If "in_attr" is not found an Exception object
#            will be raised.
#
#        RETURNS
#        -------
#        str, DotName
#        The attribue's name.
#        '''
#        for attr_name, attr in self.attributes.iteritems():
#            if attr is in_attr:
#                break
#        else:
#            raise Exception('"in_attr" is not attribute of this object.')
#        return attr_name #IGNORE:W0631
#
    def create_path(self, path):
        '''
        Create an attribute and sub-attributes so that 'path' can be looked
        up in self. Attributes that don't exist will be created.

        ARGUMENTS
        ---------
        self: InterpreterObject
            Path will become attribute of this object
        path: DotName
            The path that will be created

        RETURNS
        -------
        The attribute represented by the rightmost element of the path.
        
        TODO: maybe move to Interpreter or to CodeCollector
        '''
        curr_object = self
        for name1 in path:
            if not curr_object.has_attribute(name1):
                new_obj = InterpreterObject()
                curr_object.create_attribute(name1, new_obj)
                curr_object = new_obj
            else:
                curr_object = curr_object.get_attribute(name1)
        return curr_object


    def get_complete_path(self):
        '''
        Get complete dotted name of the function.

        Goes recursively to all parents, asks them for their names, and
        creates a DotName out of the names. This will usually produce a
        three component DotName structured like this: module.class.function

        RETURNS
        -------
        DotName
        
        TODO: maybe move to Interpreter or to CodeCollector
        '''
        curr_object = self
        path = DotName(self.name)
        while curr_object.parent is not None:
            curr_object = curr_object.parent()      #IGNORE:E1102
            path = DotName(curr_object.name) + path
        return path


    def create_persistent_locals_ns(self):
        '''
        Create special, and unique namespace for storing local variables.

        When creating code, a function's local variables must be placed
        (as algebraic variables) in the simulation object. The code of all
        functions is inlined into the main functions. Therfore the local
        variables of each function invocation must be stored separately with
        unique names.

        The root namespace where the local variables are stored is supplied
        by the interpreter.
        
        TODO: maybe move to Interpreter or to CodeCollector
        '''
        #long name of function. like: bioreactor.conti.bacterial_growth
        func_path = self.get_complete_path()
        #name-space where all local variables go into
        locals_root = INTERPRETER.get_locals_storage()
        #create namespace with long name of this function
        locals_ns = locals_root.create_path(func_path[1:] +
                                            DotName(str(self.call_count)))
        return locals_ns


#class CallableObject(InterpreterObject):
#    '''
#    Base class of all functions.
#
#    CONSTRUCTOR ARGUMENTS
#    ---------------------
#    name: DotName, str
#        The function's name.
#    '''
#    def __init__(self, name):
#        InterpreterObject.__init__(self)
#        self.role = RoleConstant
#        self.is_known = True
#        self.name = name
##        If True: the function is a basic building block of the language.
##        The code generator can emit code for this function. The flattened
##        simulation object must only contain calls to these functions.
##        If False: This function must be replaced with a series of calls
##        to fundamental functions.
#        # TODO: rename to is_runtime_function
#        # TODO: remove! This is unnecessary
#        self.is_fundamental_function = False
#        self.codegen_name = None
#        self.signature = Signature()
#
#    def __call__(self, *args, **kwargs):
#        '''All Siml-functions must implement this method'''
#        raise NotImplementedError('__call__ method is not implemented. Use a derived class!')



class CodeGeneratorObject(InterpreterObject):
    '''
    Objects that represent data in the code that the compiler generates.

    Only these objects, and operations with these objects, should remain in a
    flattened simulation.
    '''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.time_derivative = None
        self.target_name = None
        #if True this object is a constant which is known at compile time. 
        #is_nown is really only meaningful for code-generator-objects. 
        self.is_known = False
   
   
def test_allknown(*args):
    '''
    Test if all arguments are known constants. 
    
    Raise UnknownArgumentsException if any argument is unknown; raising 
    UnknownArgumentsException (usually) tells the interpreter to generate code. 
    
    All arguments must be CodeGeneratorObject.
    '''
    for arg in args:
        if isinstance(arg, InterpreterObject) and arg.is_known:
            assert i_isrole(arg.__siml_role__, RoleConstant), \
                   'All objects that are known at compile time must be constants.'
            return
        else:
            raise UnknownArgumentsException()

        
        
class Signature(object):
    """
    Contains arguments and return type of a function.
    - Checks the arguments when function is created
    - Evaluates the type annotations, once before the arguments are parsed. 
    - Parses the arguments and checks their type when the function is called.
    - Checks the type of the return value.
    
    TODO: For inspiration look at 
        (http://www.python.org/dev/peps/pep-3107)
        http://www.python.org/dev/peps/pep-0362/
        http://oakwinter.com/code/typecheck/
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
        if isinstance(arguments, (SimpleSignature, Signature)):
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
                raise UserException('Positional arguments must come before '
                                    'keyword arguments!', self.loc, errno=3200110)
            #test: argument names must be unique
            if arg.name in self.argument_dict:
                raise UserException('Duplicate argument name "%s"!' 
                                    % str(arg.name), self.loc, errno=3200120) 
            self.argument_dict[arg.name] = arg


    def evaluate_type_specs(self, interpreter):
        '''
        Compute the types and default values of the arguments. 
        Compute return type.
        
        The ast.Nodes are replaced with InterpreterObjects; 
        the function needs to be run only once
        
        - TODO: Check: default values must evaluate to constants
        '''
        if self.arguments is not None:
            #evaluate argument type and default arguments
            for arg in self.arguments:
                if arg.type is not None:
                    type_ev = interpreter.eval(arg.type)
                    arg.type = type_ev
                if arg.default_value is not None:
                    dval_ev = interpreter.eval(arg.default_value)
                    arg.default_value = dval_ev
                #test type compatibility of default value and argument type
                if arg.type is not None and arg.default_value is not None:
                    self._test_arg_type_compatible(arg.default_value, arg)
        if self.return_type is not None:
            #evaluate return type
            if self.return_type is not None:
                type_ev = interpreter.eval(self.return_type)
                self.return_type = type_ev
        self.is_evaluated = True


    def parse_function_call_args(self, args_list, kwargs_dict):
        '''
        Executed when a function call happens.
        Fill the arguments of the call site into the arguments of the
        function definition. Does type-checking.

        The type specifications are evaluated immediately before the first 
        use of the object. They can't be evaluated when the object is 
        constructed because of (mutual) recursive references.
        
        ARGUMENTS
        ---------
        args_list: [<siml values, AST nodes>, ...]
            Positional arguments.
        kwargs_dict: {str(): <siml values, AST nodes>, ...}
            Keyword arguments.
        interpreter: Interpreter
            The Siml interpreter, for evaluating the type annotations

        RETURNS
        -------
        Dictionary of argument names and associated values.
        dict(<argument name>: <siml values, AST nodes>, ...)
        dict(str(): Node(), ...)
        '''
        #TODO: implement support for *args and **kwargs
        #  Description of semantics is here:
        #      http://docs.python.org/reference/expressions.html#calls
        #  A complete implementation is here:
        #      http://svn.python.org/view/sandbox/trunk/pep362/        
        if self.arguments is None:
            return None
        output_dict = {} #dict(<argument name>: <siml values>, ...)

        #test too many positional arguments
        if len(args_list) > len(self.arguments):
            raise UserException(
                'Too many arguments. '
                'Function accepts at most %d arguments; %d given. \n'
                'Function definition in: %s \n'
                % (len(self.arguments), len(args_list), str(self.loc)),
                loc=None, errno=3200250)
        #associate positional arguments to their names
        for arg_def, in_val in zip(self.arguments, args_list):
            #test for correct type
            self._test_arg_type_compatible(in_val, arg_def)
            #associate argument value with name
            output_dict[arg_def.name] = in_val

        #associate keyword arguments to their name
        for in_name, in_val in kwargs_dict.iteritems():
            #test: argument name must exist in function definition
            if in_name not in self.argument_dict:
                raise UserException('Unknown argument "%s". \n'
                                    'Function definition in: %s \n'
                                    % (str(in_name), str(self.loc)),
                                    loc=None, errno=3200260)
            #test for duplicate argument assignment (positional + keyword)
            if in_name in output_dict:
                raise UserException('Duplicate argument "%s". \n'
                                    'Function definition in: %s \n'
                                    % (str(in_name), str(self.loc)),
                                    loc=None, errno=3200270)
            #test for correct type,
            self._test_arg_type_compatible(in_val, self.argument_dict[in_name])
            #associate argument value with name
            output_dict[in_name] = in_val

        #associate default values to the remaining arguments
        for arg in self.default_args:
            if arg.name not in output_dict:
                output_dict[arg.name] = arg.default_value

        #check if all arguments were associated to a value
        arg_names_call = set(output_dict.keys())
        arg_names_func_def = set(self.argument_dict.keys())
        left_over_names = arg_names_func_def - arg_names_call
        if len(left_over_names) > 0:
            raise UserException('Too few arguments given. '
                                'Remaining arguments without value: %s \n'
                                'Function definition in: %s \n'
                                % (', '.join([str(n) for n in left_over_names]),
                                   str(self.loc) ),
                                loc=None, errno=3200280)
        return output_dict


    def _test_arg_type_compatible(self, in_object, arg_def):
        '''
        Test if a given value has the correct type.
        Raises exception when types are incompatible.

        ARGUMENTS
        ---------
        in_object: Node()
            The arguments value. May be an unevaluated piece of the AST, with
            type annotations.
        arg_def: ast.NodeFuncArg()
            Definition object of this argument.
            If arg_def.type is None: return True; no type checking is performed.
        '''
        if arg_def.type is None:
            return
        if not istype(in_object, arg_def.type):
            raise UserException(
                    'Incompatible types. \nVariable: "%s" '
                    'is defined as: %s \nHowever, argument type is: %s. \n'
                    'Function definition in: \n  %s\n'
                    % (arg_def.name, arg_def.type.__name__,
                       in_object.__siml_type__.__name__, str(self.loc)),
                    loc=None, errno=3200310)
    
    
    def test_return_type_compatible(self, retval):
        '''
        Test if the function's return value has the right type.
        '''
        if self.return_type is None:
            return
        if not istype(retval, self.return_type):
            raise UserException("Incompatible return type.\n"
                                "Type of returned object: %s \n"
                                "Specified return type  : %s \n"
                                'Function definition in: \n  %s\n'
                                % (retval.__siml_type__.__name__,
                                   self.return_type.__name__,
                                   str(self.loc)), 
                                loc=None, errno=3200320) 



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
            defaults = defaults if defaults else [] #defaults may be None
            siml_args = [NodeFuncArg(arg_name) for arg_name in args]
            for arg, dval in zip(reversed(siml_args), reversed(defaults)):
                arg.default_value = dval
            #Put Siml type definitions into argument list
            for arg, type1 in zip(siml_args, arg_types):
                arg.type = type1
        else:
            siml_args = None
        #install signature object
        loc = make_pyfunc_loc(func_to_decorate)
        func_to_decorate.siml_signature = Signature(siml_args, return_type, loc)
        #install more Siml infrastructure stuff
        func_to_decorate.siml_globals = InterpreterObject() #dummy global namespace
        func_to_decorate.__siml_role__ = RoleConstant
        func_to_decorate.__siml_type__ = type(func_to_decorate)
        
        return func_to_decorate

    return decorate_with_signature



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
        'Encode the behavior at name lookup. SimlFunction is a descriptor.'
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



class SimlClass(InterpreterObject):
    '''Base class of user defined classes.'''
    def __init__(self, name, bases, loc=None):
        '''Create a new class object.'''
        InterpreterObject.__init__(self)
        self.bases = bases
        self.loc = loc

    def __call__(self, *args, **kwargs):
        '''
        Create a new instance object.

        - Copies the data attributes into the new class.
        - Calls the __init__ function (at compile time) if present.
          The arguments are given to the __init__ function.
        '''
        #create new instance
        new_obj = InterpreterObject()
        new_obj.type = ref(self)
        #copy data attributes from class to instance
        #TODO: copy all attributes at once, to keep all relations between the data attributes
        for attr_name, attr in self.attributes.iteritems():
            if not siml_callable(attr):
                new_attr = attr.copy()
                new_obj.create_attribute(attr_name, new_attr, reparent=True)
        #run the __init__ compile time constructor
        if new_obj.has_attribute('__init__'):
            init_meth = new_obj.get_attribute('__init__')
            if not siml_callable(init_meth):
                raise UserException('"__init__" attribute must be a method (callable)!')
            #run the constructor
            INTERPRETER.apply(init_meth, args, kwargs)
        return new_obj



#---------- Built In Library  ------------------------------------------------*

#---------- Infrastructure -------------------------------------------------
class IModule(InterpreterObject):
    '''Represent one file'''
    #TODO: Add self.builtin - separate module for built in attributes
    #      Modules have modified attribute lookup:
    #      When attributes are not found in their namespace,
    #      the attributes are searched in the builtin namespace.
    #      This way the built in attributes do not need to be imported
    #      into the module's namespace, and they can be overridden.
    def __init__(self, name=None, file_name=None):
        InterpreterObject.__init__(self)
        self.__name__ = name
        self.__file__ = file_name
        self.__siml_type__ = IModule
        self.__siml_role__= RoleConstant



#------- Built In Data --------------------------------------------------
class INone(InterpreterObject):
    '''Siml's None object.'''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.__siml_type__ = INone
        self.__siml_role__= RoleConstant
        #TODO: see that no second NONE is created

    def __str__(self):#convenience for sane behavior from Python
        return 'NONE'
    
    @signature(None, None)
    def __siml_str__(self):
        '''__str__ called from Siml'''
        istr = IString('None')
        return istr

#The single None instance for Siml
NONE = INone()



#TODO: Class that acts as an instance of an undetermined class. Necessary for local
#      variables of true template functions. Currently only the arguments
#      of a function have this property. Instances would need to be treated
#      specially in assignments, similarly to RoleUnknown. It would always be
#      unassigned, with unknown value.
#
#      class IAny(InterpreterObject): #or IUnknownType
#          '''Instance of special undetermined class.'''


#Forward declarations of some types, for type annotations.
BOOLP = Proxy()
STRINGP = Proxy()
FLOATP = Proxy()

class IBool(CodeGeneratorObject):
    '''
    Memory location of a boolean value.

    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not.
    '''
    def __init__(self, init_val=None):
        CodeGeneratorObject.__init__(self)
        self.__siml_type__ = IBool
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (str, float, int, bool)):
                self.value = bool(init_val)
            elif isinstance(init_val, (CodeGeneratorObject)):
                if init_val.value is None:
                    ValueError('Object can not be initialized from unknown value.')
                self.value = bool(init_val.value)
            else:
                raise TypeError('Can not initialize IBool from type: %s'
                                % str(type(init_val)))
            #mark object as known at compile time
            self.__siml_role__ = RoleConstant
            self.is_known = True


    #comparison operators
    @signature([BOOLP, BOOLP], BOOLP) 
    def __eq__(self, other):
        test_allknown(self, other)
        return IBool(self.value == other.value)
    
    @signature([BOOLP, BOOLP], BOOLP) 
    def __ne__(self, other): 
        test_allknown(self, other)
        return IBool(self.value != other.value)
    
    #special functions for boolean operations (and or not)
    @signature([BOOLP], BOOLP) 
    def __siml_not__(self):
        '''Called for Siml "not".'''
        test_allknown(self)
        return IBool(not self.value)
    
    @signature([BOOLP, BOOLP], BOOLP) 
    def __siml_and2__(self, other):
        '''Called for Siml "and".'''
        test_allknown(self, other)
        return IBool(self.value and other.value)
    
    @signature([BOOLP, BOOLP], BOOLP) 
    def __siml_or2__(self, other):
        '''Called for Siml "or".'''
        test_allknown(self, other)
        return IBool(self.value or other.value)
    
    #assignment
    @signature([BOOLP, BOOLP], INone) 
    def __siml_assign__(self, other):
        '''Called for Siml assignment ("=") operator.'''
        if other.value is not None:
            if self.is_known:
                raise UserException('Duplicate assignment.')
            self.value = other.value
            self.is_known = True
        else:
            raise UnknownArgumentsException()
        
    #printing
    def __str__(self):#convenience for sane behavior from Python
        if self.value is None:
            return '<unknown Bool>'
        else:
            return self.value
        
    @signature([BOOLP], STRINGP) 
    def __siml_str__(self):
        '''__str__ called from Siml'''
        test_allknown(self)
        istr = IString(self.value)
        return istr

BOOLP.set(IBool)
#global constants True and False (More easy than introducing additional
#literal values)
TRUE = IBool(True)
FALSE = IBool(False)



class IString(CodeGeneratorObject):
    '''
    Memory location of a string

    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not.
    '''
    def __init__(self, init_val=None):
        CodeGeneratorObject.__init__(self)
        self.__siml_type__ = IString
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (str, float, int, bool)):
                self.value = str(init_val)
            elif isinstance(init_val, CodeGeneratorObject):
                if init_val.value is None:
                    ValueError('Object can not be initialized from unknown value.')
                self.value = str(init_val.value)
            else:
                raise TypeError('Can not init IString from type: %s'
                                % str(type(init_val)))
            #mark object as known at compile time
            self.__siml_role__ = RoleConstant
            self.is_known = True


    @signature([STRINGP, STRINGP], STRINGP) 
    def __add__(self, other):
        test_allknown(self, other)
        return IString(self.value + other.value)
    
    #comparisons
    @signature([STRINGP, STRINGP], IBool) 
    def __eq__(self, other):
        test_allknown(self, other)
        return IBool(self.value == other.value)
    
    @signature([STRINGP, STRINGP], IBool) 
    def __ne__(self, other):
        test_allknown(self, other)
        return IBool(self.value != other.value)
    
    #special function for assignment    
    @signature([STRINGP, STRINGP], INone) 
    def __siml_assign__(self, other):
        '''Called for Siml assignment ("=") operator.'''
        if isinstance(other, IString) and other.value is not None:
            if self.is_known:
                raise UserException('Duplicate assignment.')
            self.value = other.value
            self.is_known = True
        else:
            raise UnknownArgumentsException()
        
    #Printing
    def __str__(self):#convenience for sane behavior from Python
        if self.value is None:
            return '<unknown String>'
        else:
            return self.value
         
    @signature([STRINGP], STRINGP) 
    def __siml__str__(self):
        '''called from Siml'''
        test_allknown(self)
        return self

STRINGP.set(IString)


class IFloat(CodeGeneratorObject):
    '''
    Memory location of a floating point number

    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not.
    '''
    def __init__(self, init_val=None):
        CodeGeneratorObject.__init__(self)
        self.__siml_type__ = IFloat
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (float, int, str)):
                self.value = float(init_val)
            elif isinstance(init_val, IFloat):
                if init_val.value is None:
                    ValueError('Object can not be initialized from unknown value.')
                self.value = init_val.value
            else:
                raise TypeError('Expecting None, float, int or known IFloat in '
                                'constructor, but received %s'
                                % str(type(init_val)))
            #mark object as known at compile time
            self.__siml_role__ = RoleConstant
            self.is_known = True

    #arithmetic operators
    @signature([FLOATP, FLOATP], FLOATP) 
    def __add__(self, other):
        test_allknown(self, other)
        return IFloat(self.value + other.value)
    
    @signature([FLOATP, FLOATP], FLOATP) 
    def __sub__(self, other):
        test_allknown(self, other)
        return IFloat(self.value - other.value)
    
    @signature([FLOATP, FLOATP], FLOATP) 
    def __mul__(self, other):
        test_allknown(self, other)
        return IFloat(self.value * other.value)
    
    @signature([FLOATP, FLOATP], FLOATP) 
    def __div__(self, other):
        test_allknown(self, other)
        return IFloat(self.value / other.value)
    __truediv__ = __div__ #for division from Python
    
    @signature([FLOATP, FLOATP], FLOATP) 
    def __mod__(self, other):
        return IFloat(self.value % other.value)
    
    @signature([FLOATP, FLOATP], FLOATP) 
    def __pow__(self, other):
        test_allknown(self, other)
        return IFloat(self.value ** other.value)
    
    @signature([FLOATP], FLOATP) 
    def __neg__(self):
        test_allknown(self)
        return IFloat(-self.value)

    #comparison operators
    @signature([FLOATP, FLOATP], IBool) 
    def __lt__(self, other):
        test_allknown(self, other)
        return IBool(self.value < other.value)
    
    @signature([FLOATP, FLOATP], IBool) 
    def __le__(self, other):
        test_allknown(self, other)
        return IBool(self.value <= other.value)
    
    @signature([FLOATP, FLOATP], IBool) 
    def __eq__(self, other):
        test_allknown(self, other)
        return IBool(self.value == other.value)
    
    @signature([FLOATP, FLOATP], IBool) 
    def __ne__(self, other):
        test_allknown(self, other)
        return IBool(self.value != other.value)
    
    @signature([FLOATP, FLOATP], IBool) 
    def __gt__(self, other):
        test_allknown(self, other)
        return IBool(self.value > other.value)
    
    @signature([FLOATP, FLOATP], IBool) 
    def __ge__(self, other):
        test_allknown(self, other)
        return IBool(self.value >= other.value)

    @signature([FLOATP], FLOATP) 
    def __siml_diff__(self):
        '''
        Return time derivative of state variable. Called for '$' operator
        Create the variable that contains the derivative if necessary.

        TODO: delete??? Function has to be static because ???
        self may be an ast.Node; this
        method is responsible to create a good error message in this case.
        '''
        #Precondition: $ acts upon a variable
        if(not isinstance(self, IFloat) or #no expression (ast.Node)
           #self.parent is None or          #no anonymous intermediate value
           not i_isrole(self, RoleVariable)): #no constant or parameter or unknown
            raise UserException('Only named variables can have derivatives.')
        #create time derivative if necessary
        if self.time_derivative is None:
            make_derivative(self)
        #return the associated derived variable
        return self.time_derivative #IGNORE:E1102

    @signature([FLOATP, FLOATP], INone) 
    def __siml_assign__(self, other):
        '''Called for Siml assignment ("=") operator.'''
        if isinstance(other, IFloat) and other.value is not None:
            if self.is_known:
                raise UserException('Duplicate assignment.')
            self.value = other.value
            self.is_known = True
        else:
            raise UnknownArgumentsException()

    def __str__(self): #convenience for sane behavior from Python
        if self.value is None:
            return '<unknown Float>'
        else:
            return str(self.value)

    @signature([FLOATP], IString) 
    def __siml_str__(self):
        '''Called from Siml'''
        test_allknown(self)
        istr = IString(self.value)
        return istr

FLOATP.set(IFloat)

#create the special variable time
TIME = IFloat()
TIME.__siml_role__ = RoleAlgebraicVariable



#-------------- Service -------------------------------------------------------------------
@signature(None, INone)
def siml_print(*args, **kwargs):
    '''
    The runtime print function.

    The print function takes an arbitrary number of positional arguments.
    For each argument print calls its '__siml_str__' function to create a text
    representation of the object.
    
    TODO: How can user defined objects be printed at runtime?

    The function supports a number of keyword arguments:
    debug_level=0: Float
        Only produce output when the program's debug level is greater or equal 
        this value.
    end='\n': String
        This string is appendet at the end of the printed output.
        
    The function executes at runtime; calling this function always creates code.
    '''
    #check keyword arguments
    legal_kwarg_names = set(['debug_level', 'end'])
    for arg_name, in kwargs.keys():
        if arg_name not in legal_kwarg_names:
            raise UserException('Unknown keyword argument: %s' % arg_name)
    debug_level = kwargs.get('debug_level', None)
    if not istype(debug_level, IFloat):
        raise UserException('Argument "debug_level" must be of type Float')
    end = kwargs.get('end', None)
    if not istype(end, IString):
        raise UserException('Argument "end" must be of type IString')

    #create code that prints at runtime
    new_args = []
    for arg1 in args:
        #call argument's the __str__ method, the interpreter
        #will return an unevaluated function call or a unknown string variable.
        #This will transform a call to a user-defined __str__ method
        #into calls to fundamental __siml_str__ methods
        str_func = NodeAttrAccess((arg1, NodeIdentifier('__siml_str__')))
        str_call = NodeFuncCall(str_func, [], {})
        str_expr = INTERPRETER.eval(str_call)
        new_args.append(str_expr) #collect the call's result
    #create a new call to the print function
    print_call = NodeFuncCall(siml_print, new_args, {})
    decorate_call(print_call, INone)
    return print_call

    
    
@signature(None, INone)
def siml_printc(*args, **kwargs):
    '''
    The compile time print function.

    The print function takes an arbitrary number of positional arguments.
    The arguments are converted to strings and printed at compile time.
    
    The function supports a number of keyword arguments:
    debug_level=0: Float
        Only produce output when the program's debug level is greater or equal 
        this value.
    end='\n': String
        This string is appendet at the end of the printed output.
        
    The function executes at compile time; calling this function does not create 
    code.
    '''
    #TODO: Make Interpreter.apply recognize Python argument parsing errors,
    #      then all this ugly parameter parsing could be deleted. 
    #      also true for siml_print, siml_graph
    #TODO: Or implement *args, **kwargs in Siml.
    #check keyword arguments
    legal_kwarg_names = set(['debug_level', 'end'])
    for arg_name, in kwargs.keys():
        if arg_name not in legal_kwarg_names:
            raise UserException('Unknown keyword argument: %s' % arg_name)
    debug_level = kwargs.get('debug_level', None)
    if not isinstance(debug_level, IFloat):
        raise UserException('Argument "debug_level" must be of type Float')
    end = kwargs.get('end', None)
    if not isinstance(end, IString):
        raise UserException('Argument "end" must be of type IString')
    sep=' '
    
    #observe debug level
    if debug_level.value > DEBUG_LEVEL:
        return
    
    #create output string
    out_str = ''
    for arg1 in args:
        if isinstance(arg1, (INone, IBool, IString, IFloat)):
            out_str += str(arg1) + sep
        else:
            out_str += aa_make_tree(arg1) + sep
    out_str += end.value
    print out_str
            


@signature(None, INone)
def siml_graph(*args, **kwargs):
    '''
    The graph special-function.

    ARGUMENTS
    ---------
    Positional arguments:
    The graph function takes an arbitrary number of positional arguments.
    These values must be Floats that were created with a data statement, and
    whose values are also recorded during the solution process. The arguments
    are interpreted as all recorded values during the solution process, and
    not as a single value at a specific moment in time like variables
    normally are interpreted.

    However, the Python implementation here does nothing. The code generator
    generates a call to a function/method of the runtime when it sees
    a call to this function. (This case is treated specially in the code
    generator.)


    Keyword arguments:
    title: String
        The title of the graph, shown at the top.
    '''
    #check arguments
    for arg_val in args:
        if not isinstance(arg_val, IFloat):
            raise UserException(
                'The graph function can only display Float variables, '
                'that are recorded during the simulation. \n'
                'No expressions (2*x), and no intermediate variables '
                'if they are removed by the optimizer.')
    legal_kwargs = set(['title'])
    for arg_name, arg_val in kwargs.iteritems():
        if arg_name not in legal_kwargs:
            raise UserException('Unknown keyword argument: %s' % arg_name)
    title = kwargs.get('title', None)
    if not istype(title, IString):
        raise UserException('Argument "title" must be of type IString')

    #create a new call to the graph function and return it (unevaluated)
    raise UnknownArgumentsException('Exception to create function call.')



@signature([IString], INone)
def siml_save(file_name=None): #pylint:disable-msg=W0613
    '''
    The store function.

    At compile time the store function raises an error.
    At run time it stores all recorded variables in the file system.

    However, the Python implementation here does nothing. The code generator
    generates a call to a function/method of the runtime when it sees
    a call to this function.

    ARGUMENTS
    ---------
    file_name: String
        Filename of the stored variables.
    '''
    raise UnknownArgumentsException('Exception to create function call.')


@signature([IFloat, IFloat], INone)
def siml_solution_parameters(duration=None, reporting_interval=None): #pylint:disable-msg=W0613
    '''
    The solution_parameters function.

    At compile time this function raises an error.
    At run time it changes parameters of the solution algorithm.

    However, the Python implementation here does nothing. The code generator
    generates a call to a function/method of the runtime when it sees
    a call to this function.

    ARGUMENTS
    ---------
    duration: Float
        Duration of the simulation.
    reporting_interval: Float
        Interval at which the simulation results are recorded.
        Time between data points
    '''
    raise UnknownArgumentsException('Exception to create function call.')



def create_built_in_lib():
    '''
    Returns module with objects that are built into interpreter.
    '''
    lib = IModule('__built_in__', 'interpreter.py')

    #pylint:disable-msg=W0201
    #built in constants
    lib.__dict__['None'] = NONE
    lib.True = TRUE
    lib.False = FALSE
    lib.time = TIME
    #basic data types
    lib.NoneType = INone
    lib.Bool = IBool
    lib.String = IString
    lib.Float = IFloat
    #built in functions
    lib.__dict__['print'] = siml_print
    lib.printc = siml_printc
    lib.graph = siml_graph
    lib.save = siml_save
    lib.solution_parameters = siml_solution_parameters
    @signature(None, None)
    def w_istype(in_object, class_or_type_or_tuple):
        return IBool(istype(in_object, class_or_type_or_tuple))
    lib.isinstance = w_istype
    #math
    #TODO: replace by Siml function sqrt(x): return x ** 0.5 # this is more simple for units
    @signature([IFloat], IFloat)
    def w_sqrt(x): 
        test_allknown(x)
        return IFloat(math.sqrt(x.value))
    lib.sqrt = w_sqrt
    @signature([IFloat], IFloat)
    def w_sin(x):
        test_allknown(x)
        return IFloat(math.sin(x.value))
    lib.sin = w_sin
    @signature([IFloat], IFloat)
    def w_cos(x):
        test_allknown(x)
        return IFloat(math.cos(x.value))
    lib.cos = w_cos
    @signature([IFloat], IFloat)
    def w_tan(x):
        test_allknown(x)
        return IFloat(math.tan(x.value))
    lib.tan = w_tan
    
    @signature([IFloat, IFloat], IFloat)
    def w_max(a, b):
        test_allknown(a, b)
        return IFloat(max(a.value, b.value))
    lib.max = w_max
    @signature([IFloat, IFloat], IFloat)
    def w_min(a, b):
        test_allknown(a, b)
        return IFloat(min(a.value, b.value))
    lib.min = w_min

    return lib



#--------- Interpreter -------------------------------------------------------*
#TODO: replace(a, b)
#TODO: parent(o)
#TODO: find_name(o, parent)
#TODO: quote(expr)
#TODO: quasi_quote(expr)
#TODO: operator('x-x', expr, expr, ...)

def make_derivative(variable):
    '''
    Create time derivative of a variable.
    TODO: Can also associate two variables as state variable and time derivative.

    - Create derivative in variable's parent
    - Put weak reference to it into variable.time_derivative
    - Set the correct roles on both variables

    ARGUMENTS
    ---------
    variable: IFloat, ...
        The variable which is converted to a state variable, and for which
        a time derivative will be created.

    TODO: introduce second argument: derivative=None: IFloat
          The variable which will from now on act as a derivative.
          If argument is None, a new variable is created.
    TODO: remove wsiml_replace_attr(...)
    '''
    #TODO: Test: both arguments must be IFloat (or Array) objects.
    #TODO: Test if variable is already a state variable. Raise error if true.
    #TODO: Test if variable is a time differential. Raise error if true.
    #create the derived variable which will be associated to variable
    deri_var_class = variable.type()
    deri_var = deri_var_class()
    deri_var.role = RoleTimeDifferential

    #find state variable in parent (to get variable's name)
    var_name = variable.parent().find_name(variable)
    #put time derivative in parent, with nice name
    deri_name = var_name + '$time'
    #deri_name = make_unique_name(deri_name, variable.parent().attributes)
    variable.parent().create_attribute(deri_name, deri_var)

    #remember time derivative also in state variable
    variable.time_derivative = ref(deri_var)
    #mark variable as state variable
    variable.role = RoleStateVariable
    return


#def make_proxy(in_obj):
#    '''
#    Return a proxy object.
#
#    Will create a weakref.proxy object from normal objects and from
#    weakref.ref objects. If in_obj is already a proxy it will be returned.
#    '''
#    if isinstance(in_obj, weakref.ProxyTypes):
#        return in_obj
#    elif isinstance(in_obj, weakref.ReferenceType):
#        return weakref.proxy(in_obj())
#    else:
#        return weakref.proxy(in_obj)


#def siml_callable(siml_object):
#    '''Test if an object is callable'''
#    return isinstance(siml_object, CallableObject)



def istype(in_object, class_or_type_or_tuple):
    '''
    Check if an object's type is in class_or_type_or_tuple.

    Similar to isinstance(...) but works with unevaluated expressions too.
    If the expression (in_object) would evaluate to an object of the
    correct type, the function returns True.

    TODO: create new function i_isinstance(...) which checks at compile
          time if object is really an instance of a certain type; excluding
          unevaluated function calls.
    '''
    if in_object.__siml_type__ is not None:
        return issubclass(in_object.__siml_type__, class_or_type_or_tuple)
    else:
        return False


#def i_issubclass(in_type, class_or_type_or_tuple):
#    '''issubclass(...) but inside the SIML language'''
#    return issubclass(in_type, class_or_type_or_tuple)
#    #precondition: must be a SIML type
#    if not isinstance(in_type, type):
#        raise Exception('Argument "in_type" must be a class.')
#    #always create tuple of class objects
#    if not isinstance(class_or_type_or_tuple, tuple):
#        class_or_type_or_tuple = (class_or_type_or_tuple,)
#    #the test: there is no inheritance, so it is simple
#    return (in_type in class_or_type_or_tuple)


#def siml_setknown(siml_obj):
#    '''
#    Set decoration to express that the object is a known value.
#
#    TODO: remove??? each function should know by itself if it can do the 
#          computations or if code should be produced. Known/unknown is also 
#          difficult to decide for structured values. It is only meaningful
#          for code-generator-values (CodeGeneratorObject). 
#          Maybe there should be CodeGeneratorObject.isknown() .
#    '''
#    assert isinstance(siml_obj, InterpreterObject), \
#           'Function only works with InterpreterObject instances.'
#    siml_obj.role = RoleConstant
#    siml_obj.is_known = True
#    #TODO: use everywhere
#
#def siml_isknown(siml_obj):
#    '''
#    Test if an object is a known value, or an unevaluated expression.
#
#    RETURNS
#    -------
#    True:  argument is a known Siml value.
#    False: argument is an unevaluated expression or an unknown variable.
#
#    TODO: remove??? each function should know by itself if it can do the 
#          computations or if code should be produced. Known/unknown is also 
#          difficult to decide for structured values. It is only meaningful
#          for code-generator-values (CodeGeneratorObject). 
#          Maybe there should be CodeGeneratorObject.isknown() .
#    '''
#    assert isinstance(siml_obj, (InterpreterObject, NodeFuncCall,
#                                 NodeOpInfix2, NodeOpPrefix1,
#                                 NodeParentheses)), \
#           'Function only works with Siml objects and ast.Node.'
#    if isinstance(siml_obj, InterpreterObject) and siml_obj.is_known:
#        assert i_isrole(siml_obj.role, RoleConstant), \
#               'All objects that are known at compile time must be constants.'
#        return True
#    else:
#        return False


def i_isrole(role1, role2_or_tuple):
    '''
    Is role-1 a sub-role or equal to role-2.
    Also accepts a tuple of roles for the 2nd argument
    '''
    return issubclass(role1, role2_or_tuple)


def is_role_more_variable(role1, role2):
    '''
    Compare two roles with respect to their variable-character.

    These are the basic roles, the variable-character increases from left
    to right:
    RoleConstant, RoleParameter, RoleVariable, RoleUnkown
    const,        param,         variable,     role_unknown

    ARGUMENTS
    ---------
    role1, role2: AttributeRole
        The two roles to compare.

    RETURNS
    -------
    True/False
    True:  if role1 (argument 1) is more variable than role2 (argument 2).
    False: otherwise
    '''
    #TODO: Maybe speed this function up by giving each role a variability index
    #      that is stored inside the role object
    #list roles with increasing variable-character
    rank_list = [RoleConstant, RoleParameter, RoleVariable, RoleUnkown]
    #classify role1
    for index1 in range(len(rank_list)):
        if i_isrole(role1, rank_list[index1]):
            break
    else:
        raise ValueError('Unknown role %s' % str(role1))
    #classify role2
    for index2 in range(len(rank_list)):
        if i_isrole(role2, rank_list[index2]):
            break
    else:
        raise ValueError('Unknown role %s' % str(role2))
    #compare the roles' variable-character by comparing their positions in
    #the list
    return index1 > index2 #IGNORE:W0631


def determine_result_role(arguments, keyword_arguments={}): #IGNORE:W0102
    '''
    Determine the most variable role among function arguments.

    The function returns the role, that a function's return value should
    have, by looking at the function's arguments. The algorithm is used
    to determine the role of unknown return values of fundamental functions.
    Therefore role unknown is illegal.

    - The result's role is the most variable role from any argument. The ordering is:
    These are the basic roles, the variable-character increases from left
    to right:
    RoleConstant, RoleParameter, RoleVariable, RoleUnkown
    const,        param,         variable,     role_unknown

    - RoleUnknown is illegal, function raises ValueError if any parameter
    has this role.

    ARGUMENTS
    ---------
    arguments: [InterpreterObject, ...] or [ast.Node, ...]
    keyword_arguments: {str: InterpreterObject, ...} or {str: ast.Node, ...}

    RETURNS
    -------
    RoleConstant/RoleParameter/RoleParameter
    The role that the unknown return value will have.
    '''
    #put all arguments into a single tuple
    all_args = arguments + tuple(keyword_arguments.values())
    #loop over arguments and find most variable role
    max_var_role = RoleConstant
    for arg in all_args:
        if is_role_more_variable(arg.__siml_role__, max_var_role):
            max_var_role = arg.__siml_role__
        if arg.__siml_role__ is RoleUnkown:
            raise ValueError('RoleUnkown is illegal in arguments of '
                             'fundamental functions.')
    #convert: state variable, time differential --> algebraic variable
    #These two roles result only from taking time differentials
    if i_isrole(max_var_role, RoleVariable):
        max_var_role = RoleAlgebraicVariable
    return max_var_role


def set_role_recursive(tree, new_role):
    '''
    Set the role of a whole tree.

    The function recursively enters all of the tree's (child) attributes until
    it encounters fundamental objects.

    The root attribute's role is changed unconditionally. A child attribute's
    role is only changed if its current role is more variable than the new
    role. This algorithm makes it possible that a variable can have a constant
    child attribute (for example its unit of measurement).

    ARGUMENTS
    ---------
    tree: InterpreterObject()
        The attribute where the role is changed. May be a tree with
        child attributes.
    new_role:
        The new role.
    '''
    assert isinstance(tree, InterpreterObject)
    tree.__siml_role__ = new_role
    if isinstance(tree, CodeGeneratorObject):
        return
    #recurse into user defined objects
    for attr in tree.__dict__.itervalues():
        if isinstance(attr, InterpreterObject) and \
           is_role_more_variable(attr.__siml_role__, new_role):
            set_role_recursive(attr, new_role)


def decorate_call(call, return_type):
    '''
    Decorate function calls nodes.
    The call gets the same attributes like unknown variables

    This method works with all ast.Node objects that are similar to
    function calls.
    '''
    call.__siml_type__ = return_type
    #Choose most variable role: const -> param -> variable
    call.__siml_role__ = determine_result_role(call.arguments, call.keyword_arguments)
    #call.is_known = False

#    #compute set of input variables
#    #TODO: maybe put this into optimizer?
#    inputs = set()
#    for arg in list(call.arguments) + call.keyword_arguments.values():
#        if isinstance(arg, InterpreterObject):
#            inputs.add(arg)
#        elif isinstance(arg, (NodeFuncCall, NodeOpInfix2, NodeOpPrefix1,
#                              NodeParentheses)):
#            inputs.update(arg.inputs)
#        else:
#            raise Exception('Unexpected type of argument '
#                            'for Siml function. type: %s; value: %s'
#                            % (str(type(arg)), str(arg)))
#    call.inputs = inputs


#def make_unique_name(base_name, existing_names):
#    '''
#    Make a unique name that is not in existing_names.
#
#    If base_name is already contained in existing_names a number is appended
#    to base_name to make it unique.
#
#    Arguments:
#    base_name: DotName, str
#        The name that should become unique.
#    existing_names: container that supports the 'in' operation
#        Container with the existing names. Names are expected to be
#        DotName objects.
#
#    Returns: DotName
#        Unique name; base_name with number appended if necessary
#    '''
#    base_name = DotName(base_name)
#    for number in range(1, 100000):
#        if base_name not in existing_names:
#            return  base_name
#        #append number to last component of DotName
#        base_name = base_name[0:-1] + DotName(base_name[-1] + str(number))
#    raise Exception('Too many similar names')



class ReturnFromFunctionException(Exception):
    '''Functions return by raising this exception.'''
    #TODO: Use this exception to transport return value?
    def __init__(self, loc=None):
        Exception.__init__(self)
        self.loc = loc


class CompiledClass(InterpreterObject):
    '''The compile statement creates this kind of object.'''
    def __init__(self):
        super(CompiledClass, self).__init__()
        #name of compiled object (currently unused)
        self.instance_name = None
        #classname of compiled object (For each compiled object a Python
        #class is created. This class has same/similar name as the Siml class)
        self.class_name = None
        #InterpreterObject instances (usually IFloat) whose values are
        #supplied from the outside at runtime. Currently arguments of
        #initialization functions.
        self.external_inputs = []
#        #list of tuples: [(name, argument)] this way the arguments of main functions
#        #can get their target name. The argument names can appear multiple times in the simulation.
#        self.main_func_arg_names = []
        self.loc = None



#The one and only interpreter
INTERPRETER = None

class Interpreter(object):
    '''
    Interpret the program - execute the macros

    Result of the interpretation are flattened objects. 
    
    Create the data (symbol table)
    Create AST with expanded macros
    
    Entry points:
        eval(...)     : evaluate expressions
        apply(...)    : call functions
        exec_(...)    : execute lists of statements
        
        interpret_module_file(...)    : interpret file 
        interpret_module_string(...)  : interpret string
    '''
    def __init__(self):
        #the built in objects
        self.built_in_lib = create_built_in_lib()
        #directory of modules - the symbol table
        self.modules = {}
        #frame stack - should never be empty: top element is automatically
        # put into self.environment
        self.environment = ExecutionEnvironment() #for PyDev
        self.env_stack = []
        self.push_environment(ExecutionEnvironment())

        #storage for objects generated by the compile statement
        self.compiled_object_list = []
        #temporary storage for emitted statements - needed for compilation
        #This is a list of lists [[],[]]. The currently emitted statements
        #go into the topmost list. The nested structure is necessary for
        #compund (if ... else ...) statements.
        self.compile_stmt_collect = None
        #namespace (InterpreterObject) for storage of a function's local
        #variables - needed for compile statement
        self.locals_storage = None

        #tell all objects which is their interpreter
        #TODO: this global variable should go away some day
        global INTERPRETER
        INTERPRETER = self


    # --- Expressions -------------------------------------------
    #    
    #    Compute value of an expression.
    #
    #    Each eval_* function evaluates one type of AST-Node recursively.
    #    The functions return the expression's value. This value is either
    #    an Interpreter object (value was computed at runtime), or a further 
    #    annotated AST-tree (expression is dependent on unknown values).
    #
    #    The right function is selected with the function
    #        self.eval(...)

    def eval_InterpreterObject(self, node):
        '''Visit a part of the expression that was already evaluated:
        Do nothing, return the interpreter object.'''
        if isinstance(node, Proxy):
            return node.value
        else:
            return node

    def eval_NodeFloat(self, node):
        '''Create floating point number'''
        result = IFloat(node.value)
        return result

    def eval_NodeString(self, node):
        '''Create string'''
        result = IString(node.value)
        return result

    def eval_NodeIdentifier(self, node):
        '''Lookup Identifier and get attribute'''
        attr = self.environment.get_attribute(node.name)
        return attr

    def eval_NodeAttrAccess(self, node):
        '''Evaluate attribute access; ('.') operator'''
        #evaluate the object on the left hand side
        inst_lhs = self.eval(node.arguments[0])
        #the object on the right hand side must be an identifier
        id_rhs = node.arguments[1]
        if not isinstance(id_rhs, NodeIdentifier):
            raise UserException('Expecting identifier on right side of "." operator',
                                node.loc)
        #get attribute from object on lhs
        attr = getattr(inst_lhs, id_rhs.name)
        return attr


    def eval_NodeParentheses(self, node):
        '''
        Evaluate pair of parentheses: return expression between parentheses.

        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : Role of the argument
        - Node.is_known=False    : For consistency; the function call can pose as an
                                   unknown value, that has been already computed.

        - Node.arguments         : [ast.Node]
            List with unevaluated expression as first element.
        - Node.keyword_arguments : {} Empty dict
        '''
        #compute values of expression
        val_expr = self.eval(node.arguments[0])

        #see if there is an object between the brackets, that can express only
        #one value. No matter wether known or unknown, there are no brackets
        #necessary in this case. Return the object without brackets
        if isinstance(val_expr, (InterpreterObject, NodeFuncCall,
                                 NodeParentheses)):
            #return the object
            return val_expr
        #otherwise there is an unevaluated expression between the brackets.
        else:
            #create unevaluated parentheses node as the return value
            new_node = NodeParentheses((val_expr,), node.loc)
            #put decoration on new node
            decorate_call(new_node, val_expr.type)
            return new_node


    _prefopt_table = { '-' :'__neg__',
                      'not':'__siml_not__',
                      '$':'__siml_diff__', }

    def eval_NodeOpPrefix1(self, node):
        '''
        Evaluate unary operator and return result

        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : Role taken from the argument with the most variable role
        - Node.is_known=False    : For consistency; the function call can pose as an
                                   unknown value, that has been already computed.

        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are specified
                                   keyword arguments
        '''
        #compute values on rhs of operator
        inst_rhs = self.eval(node.arguments[0])
        #look at the operator symbol and determine the right method name(s)
        func_name = Interpreter._prefopt_table[node.operator]
        #get the special method from the operand's class and try to call the method.
        func = getattr(inst_rhs.__siml_type__, func_name)
        try:
            result = self.apply(func, (inst_rhs,))
            return result
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated expression
            new_node = NodeOpPrefix1(node.operator, (inst_rhs,), node.loc)
            #put on decoration
            new_node.function = func
            decorate_call(new_node, func.siml_signature.return_type)
            return new_node


    _binop_table = {'+': ('__add__','__radd__'),
                    '-': ('__sub__','__rsub__'),
                    '*': ('__mul__','__rmul__'),
                    '/': ('__div__','__rdiv__'),
                    '%': ('__mod__','__rmod__'),
                    '**':('__pow__','__rpow__'),
                    '<': ('__lt__', '__gt__'),
                    '<=':('__le__', '__ge__'),
                    '==':('__eq__', '__eq__'),
                    '!=':('__ne__', '__ne__'),
                    '>': ('__gt__', '__lt__'),
                    '>=':('__ge__', '__le__'),
                   'and':('__siml_and2__', '__siml_rand2__'),
                    'or':('__siml_or2__', '__siml_ror2__'),
                    }

    def eval_NodeOpInfix2(self, node):
        '''
        Evaluate binary operator and return result

        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : Role taken from the argument with the most variable role
        - Node.is_known=False  : For consistency; the function call can pose as an
                                   unknown value.

        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are specified
                                   keyword arguments
        '''
        #compute values on rhs and lhs of operator
        ev_lhs = self.eval(node.arguments[0])
        ev_rhs = self.eval(node.arguments[1])
        #look at the operator symbol and determine the right method name(s)
        lfunc_name, _rfunc_name = Interpreter._binop_table[node.operator]
        #get the special method from the LHS's class and try to call the method.
        func = getattr(ev_lhs.__siml_type__, lfunc_name)
        try:
            result = self.apply(func, (ev_lhs, ev_rhs))
            return result
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated expression
            new_node = NodeOpInfix2(node.operator, (ev_lhs, ev_rhs), node.loc)
            #put on decoration
            new_node.function = func
            decorate_call(new_node, func.siml_signature.return_type)
            return new_node
        except NotImplementedError:# IncompatibleTypeError?
            #TODO: if an operator is not implemented the special function should raise
            #      an NotImplementedError ??? IncompatibleTypeError exception, for
            #      generating better error messages and calling the right-handed methods.
            #      Alternatively the operators could return the special value
            #      NotImplemented like Python operators do.
            #TODO: Siml code can raise Siml_NotImplemented ??? Siml_IncompatibleTypeError
            #      errors, they should also generate the same error messages.
            raise Exception( 'Handling of "NotImplemented" exception is not yet implented!')
        #TODO: special methods for boolean operators 'and', 'or'
        #      To retain the shortcut semantics split the execution of the
        #      operator into two phases:
        #      - first call __and1__(self), __or1__(self) if these operators
        #        can compute the result they return True/False; otherwise they
        #        return the special value NeedOtherOperand.
        #      - if NeedOtherOperand was returned call:
        #        __and2__(self, other), __rand2__(self, other)
        #        __or2__(self, other),  __ror2__(self, other)
        #      Calls with unknown arguments might always end up as: __xx2__
        #
        #      There is a PEP on this topic:
        #      http://www.python.org/dev/peps/pep-0335/
        #
        #TODO: if unsuccessful in finding a suitable methods get the
        #      right-handed methods from the RHS and try to call it.
        #      float.__sub__(a, b) == float.__rsub__(b, a)
        #
        #TODO: *** Dispatching Binary Operators of Derived Classes ***
        #      If the right operand’s type is a subclass of the left operand’s
        #      type and that subclass provides the reflected method for the operation,
        #      this method will be called before the left operand’s non-reflected
        #      method. This behavior allows subclasses to override their ancestors’
        #      operations.



    def eval_NodeFuncCall(self, node):
        '''
        Evaluate a NodeFuncCall, which calls a call-able object (function).
        Execute the callable's code and return the return value.
       '''
        #find the right call-able object
        func_obj = self.eval(node.function)
        if isinstance(func_obj, Node):
            raise UserException('Call-able objects must be known at compile tile', 
                                node.loc)
        if not isinstance(func_obj, (SimlFunction, SimlBoundMethod, 
                                     types.FunctionType, types.MethodType)):
            raise UserException('Expecting call-able object!', node.loc)

        #evaluate all arguments in the caller's environment.
        ev_args = []
        for arg_val in node.arguments:
            ev_arg_val = self.eval(arg_val)
            ev_args.append(ev_arg_val)
        ev_args = tuple(ev_args)
        ev_kwargs = {}
        for arg_name, arg_val in node.keyword_arguments.iteritems():
            ev_arg_val = self.eval(arg_val)
            ev_kwargs[arg_name] = ev_arg_val

        try:
            #call the call-able object
            return self.apply(func_obj, ev_args, ev_kwargs)
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated function call
            new_call = NodeFuncCall(func_obj, ev_args, ev_kwargs, node.loc)
            decorate_call(new_call, func_obj.siml_signature.return_type)
            return new_call


    def apply(self, func_obj, posargs=tuple(), kwargs={}): #IGNORE:W0102
        '''
        Execute a function. 
        
        User defined and built in functions are both executed here.
        All arguments must be evaluated. 
        
        TODO: common functionality of function application should go here
        TODO: in the long run code generation could go here too. 
        '''
        #Get function from bound or unbound method and put this/self into arguments
        if hasattr(func_obj, 'im_func'):
            if func_obj.im_self is not None:
                posargs = (func_obj.im_self,) + posargs
            func_obj = func_obj.im_func
            
        #Evaluate the type specifications, but only once
        if not func_obj.siml_signature.is_evaluated:
            func_obj.siml_signature.evaluate_type_specs(self)
        #Type checking of arguments, and binding them to their names
        bound_args = func_obj.siml_signature\
                             .parse_function_call_args(posargs, kwargs)
        
        if isinstance(func_obj, SimlFunction):
            ret_val = self.apply_siml(func_obj, bound_args)
        else:
            ret_val = func_obj(*posargs, **kwargs) # pylint: disable-msg=W0142
        
        #TODO: maybe convert bool -> IBool, string -> IString, float -> IFloat
        #use Siml's None
        if ret_val is None:
            ret_val = NONE
        #type checking of return value
        func_obj.siml_signature.test_return_type_compatible(ret_val)

        return ret_val
    
    
    def apply_siml(self, func_obj, bound_args):
        '''
        Execute a user defined function.
        '''
#        #parse the arguments that we get from the caller, do type checking
#        parsed_args = func_obj.signature\
#                              .parse_function_call_args(posargs, kwargs, self)

        #Take 'this' name-space from the 'this' argument.
        # 'this' must be a Siml object, no unevaluated expression
        this_namespace = bound_args.get('this', None)
        if this_namespace and not isinstance(this_namespace, InterpreterObject):
            raise UserException('The "this" argument of a method '
                                'must be a known Siml object.')

        #Count calls for making nice name spaces for persistant locals
        func_obj.call_count += 1
        #create local name space (for function arguments and local variables)
        if self.is_collecting_code():
            #store local scope so local variables are accessible for
            #code generation
            local_namespace = func_obj.create_persistent_locals_ns()
        else:
            local_namespace = InterpreterObject()
        
        #put the function arguments into the local name-space
        for arg_name, arg_val in bound_args.iteritems():
            #create references for existing Siml values
            if isinstance(arg_val, InterpreterObject):
                setattr(local_namespace, arg_name, arg_val)
            #for unevaluated expressions a new variable is created,
            #and the expression is assigned to it
            else:
                arg_class = arg_val.__siml_type__
                new_arg = arg_class()
                new_arg.role = arg_val.__siml_role__
                #put object into local name-space and assign value to it
                setattr(local_namespace, arg_name, new_arg)
                self.assign(new_arg, arg_val, None)

        #Create new environment for the function.
        new_env = ExecutionEnvironment()
        new_env.global_scope = func_obj.siml_globals #global scope from function definition.
        new_env.this_scope = this_namespace
        new_env.local_scope = local_namespace
        #local variables in functions can take any role
        new_env.default_data_role = RoleUnkown
        #default return value is Siml-None
        new_env.return_value = NONE
        #current function for macro execution stack trace
        new_env.function = func_obj

        #execute the function's code in the new environment.
        self.push_environment(new_env)
        try:
            self.exec_(func_obj.statements)
        except ReturnFromFunctionException:           #IGNORE:W0704
            pass
        self.pop_environment()
        #the return value is stored in the environment (stack frame)
        ret_val = new_env.return_value

#        #Test if returned object has the right type.
#        func_obj.signature.test_return_type_compatible(ret_val)
        return ret_val
    
       
    def eval(self, expr_node):
        '''
        Evaluate an expression (recursively).
        
        Chooses the right handler function for the given node
        
        PARAMETER
        ---------
        expression: ast.Node
            A node that represents an expression
        
        RETURN
        ------
        ast.Node or InterpreterObject
        Result of evaluation. 
        '''
        if isinstance(expr_node, InterpreterObject):
            return self.eval_InterpreterObject(expr_node)
        elif isinstance(expr_node, NodeFloat):
            return self.eval_NodeFloat(expr_node)
        elif isinstance(expr_node, NodeString):
            return self.eval_NodeString(expr_node)
        elif isinstance(expr_node, NodeIdentifier):
            return self.eval_NodeIdentifier(expr_node)
        elif isinstance(expr_node, NodeAttrAccess):
            return self.eval_NodeAttrAccess(expr_node)
        elif isinstance(expr_node, NodeParentheses):
            return self.eval_NodeParentheses(expr_node)
        elif isinstance(expr_node, NodeOpPrefix1):
            return self.eval_NodeOpPrefix1(expr_node)
        elif isinstance(expr_node, NodeOpInfix2):
            return self.eval_NodeOpInfix2(expr_node)
        elif isinstance(expr_node, NodeFuncCall):
            return self.eval_NodeFuncCall(expr_node)
        elif isinstance(expr_node, (type, types.FunctionType, types.MethodType)):
            return expr_node
        else:
            raise Exception('Unknown node type for expressions: ' 
                            + str(type(expr_node)))

    
    # --- Statements ------------------------------------------
    #    Execute statements
    #
    #    Each eval_* function executes one type of statement (AST-Node).
    #    The functions do not return any value, they change the state of the
    #    interpreter. Usually they create or modify the attributes of the 
    #    current local scope (self.environment.local_scope).
    #
    #    The right function is selected with the inherited function
    #        self.exec_(...)
    
    def exec_NodePassStmt(self, _node): 
        '''
        Interpret 'pass' statement. Do nothing.
        The pass statement is necessary to define empty compound statements
        (if, func, class).
        '''
        return

    def exec_NodeReturnStmt(self, node):
        '''Return value from function call'''
        if len(node.arguments) == 0:
            #no return value
            self.environment.return_value = NONE
        else:
            #evaluate expression to compute return value
            retval = self.eval(node.arguments[0])
            self.environment.return_value = retval
        #Forcibly end function execution -
        #exception is caught in ExpressionVisitor.visit_NodeFuncCall(...)
        raise ReturnFromFunctionException(loc=node.loc)


    def exec_NodeExpressionStmt(self, node):
        '''Intended to call functions. Compute expression and forget result'''
        ret_val = self.eval(node.expression)
        if ret_val is None or isinstance(ret_val, InterpreterObject):
            #function was evaluated at compile time, forget result
            return
        else:
            #there is an unevaluated expression - create some code that
            #executes it at runtime
            if not self.is_collecting_code():
                raise UserException('Computations with unknown values are '
                                    'illegal here.', node.loc)
            new_stmt = NodeExpressionStmt(ret_val, node.loc)
            self.collect_statement(new_stmt)


    def exec_NodeAssignment(self, node):
        '''Assign value to a constant object, or emit assignment statement
        for code generation'''
        #compute value of expression on right hand side
        expr_val = self.eval(node.expression)
        #get a data attribute to store the value
        target_obj = self.eval(node.target)
        #perform the assignment
        self.assign(target_obj, expr_val, node.loc)


    def assign(self, target, value, loc):
        '''
        Assign value to target.

        If target and value are constant objects the value is changed
        else code for an assignment is emitted. (Annotated AST)

        Arguments:
            target: InterpreterObject
                Object where the information should be stored
            value: InterpreterObject, ast.Node
                Object that contains the information, that should be stored.
            loc: TextLocation, None
                Location in program text for error messages
        '''
        #TODO: assignment without defining the variable first (no data statement.)
        #      This is very useful inside a function.
        #      - Putting function arguments into the function's namespace
        #        could be handled this way too.

        #TODO: General smart infrastructure for enforcing single assignment
        #      and guaranteed assignment.
        #      The multiple init_xxx(...), initialize(...) methods lead to multiple
        #      assignments. Allowing intermediate variables to be used in initialize
        #      methods would lead to multiple assignments too.
        #TODO: Infrastructure to integrate protection against duplicate
        #      assignment with the 'if' statement.
        #      - In an 'if' statement with n clauses each variable must/should
        #      be assigned n times.
        #      - Local variables of functions however, will be created
        #      uniquely for each function invocation. They can therefore
        #      only be assigned once, even in an 'if' statement.
#        #Test if value has been assigned already.
#        if target.is_known:
#            raise UserException('Duplicate assignment.', loc)
#        target.is_known = True
        #Targets with RoleUnkown are converted to the role of value.
        #(for local variables of functions)
        if target.role is RoleUnkown:
            set_role_recursive(target, value.role)
        #get the assignment function
        assign_func = target.get_attribute('__siml_assign__')
        #Always call the function when it is not fundamental. The call
        #generates statements with fundamental functions.
        #Reason: When a function returns a user defined class, the role is
        #often role_unknown. The leaf attributes however, that are fundamental
        #types, have correct roles.
        #Also only assignments to leaf types must get to the code generator.
        if not assign_func.is_fundamental_function:
            self.apply(assign_func, (value,))
            return

        #Only fundamental functions from here on: ------------------
        #Test if assignment is possible according to the role.
        if is_role_more_variable(value.role, target.role):
            raise UserException('Incompatible roles in assignment. '
                                'LHS: %s RHS: %s' % (str(target.role),
                                                     str(value.role)), loc)
#        #In different regions of the program only some roles are legal as
#        #targets for assignments
#        #TODO: remove; this is tested in the optimizer/checker module
#        if not issubclass(target.role, self.interpreter.assign_target_roles):
#            raise UserException('Variable has illegal role as target for '
#                                'assignment. '
#                                '\nIllegal role: %s \nLegal roles %s'
#                                % (str(target.role),
#                                   str(self.interpreter.assign_target_roles)),
#                                   loc)
        #perform assignment - function is fundamental and target is constant
        if target.role is RoleConstant:
            try:
                self.apply(assign_func, (value,))
            except UnknownArgumentsException:
                UserException('Unknown value in assignment to constant.', loc)
            return
        #Generate code for one assignment (of fundamental types)
        #target is a parameter or a variable
        new_assign = NodeAssignment()
        new_assign.loc = loc
        new_assign.target = target
        new_assign.expression = value
        #create sets of input and output objects for the optimizer
        #TODO: maybe put this into optimizer?
        if isinstance(value, InterpreterObject):
            new_assign.inputs = set([value])
        else:
            #value is an expression
            new_assign.inputs = value.inputs
        new_assign.outputs = set([target])
        #append generated assignment statement to the alredy generated code.
        self.collect_statement(new_assign)


    def exec_NodeIfStmt(self, node):
        '''
        Interpret an "if" statement.

        If no code is generated (in constant contexts) the if statement works
        like in Python. All expressions must offcourse evaluate
        to constants; especially the conditions.

        If code is generated multiple clauses/branches of the 'if' statement
        must potentially be visited. This is the algorithm:
        - The interpreter visits each clause where the condition's truth
          value can not be determined at compile time (the condition evaluates
          to an expression or to an unknown variable).
        - The interpreter visits clauses where the condition evaluates to
          True at compile time.
        - A clauses where the condition evaluates to True is the last clause
          which is visited by the interpreter. Further clauses are ignored.
        - If statements that can be completely decided at compile time are
          optimized away.

        There are additional requirements for if statements when code is
        generated:
        - The last clause of every if statement must have a condition that
          evaluates to True (constant with value equivalent to True). In
          other words: In the compiled code each if statement must end
          with an else clause.
        - All clauses must assign to the same variables.
        '''
        #TODO: Infrastructure to integrate protection against duplicate
        #      assignment with the 'if' statement.
        #      - In an 'if' statement with n clauses each variable must/should
        #      be assigned n times.
        #      - Local variables of functions however, will be created
        #      uniquely for each function invocation. They can therefore
        #      only be assigned once, even in an 'if' statement.
        is_collecting_code = False
        is_seen_else_clause = False
        new_if = None
        #If code is created, create a node for an if statement
        if self.is_collecting_code():
            is_collecting_code = True
            new_if = NodeIfStmt(None, node.loc)
        try:
            #A clause consists of: <condition>, <list of statements>.
            #This is inspired by Lisp's 'cond' special-function.
            #http://www.cis.upenn.edu/~matuszek/LispText/lisp-cond.html
            for clause in node.clauses:
                #interpret the condition
                condition_ev = self.eval(clause.condition)
                if not istype(condition_ev, (CLASS_BOOL, CLASS_FLOAT)):
                    raise UserException('Conditions must evaluate to '
                                        'instances equivalent to Bool.',
                                        loc=clause.loc)#, errno=3700510)

                #Condition evaluates to constant False: Do not enter clause.
                if siml_isknown(condition_ev) and bool(condition_ev.value) is False:
                    continue
                #Condition evaluates to constant True
                #This is the last clause, the 'else' clause
                elif siml_isknown(condition_ev) and bool(condition_ev.value) is True:
                    is_seen_else_clause = True
                #Condition evaluates to unknown value
                #This is only legal when code is created
                elif not is_collecting_code:
                    raise UserException('Only conditions with constant values '
                                        'are legal in this context.',
                                        loc=clause.loc)#, errno=3700520)

                #If code is created, create node for a clause
                #Tell interpreter to put generated statements into body of clause
                if is_collecting_code:
                    new_clause = NodeClause(condition_ev, [], clause.loc)
                    new_if.clauses.append(new_clause)
                    self.push_statement_list(new_clause.statements)
                #interpret the statements
                self.exec_(clause.statements)
                #Tell interpreter to put generated statements into previous location
                if is_collecting_code:
                    self.pop_statement_list()

                if is_seen_else_clause:
                    break
        except ReturnFromFunctionException, e:
            raise UserException('Return statemens are illegal inside "if" '
                                'statements.', loc=e.loc)

        #Optimizations of the generated 'if' statement, and checking of
        #special constraints.
        #  The optimizations give the 'if' statement additionally the power of
        #  makros and C++ templates: Different code can be generated depending
        #  on the situation.
        #
        #remove 'if' statements where all clauses evaluated to false
        if is_collecting_code and len(new_if.clauses) == 0:
            new_if = None
        #see if 'if' statement has the required 'else' clause
        elif is_collecting_code and not is_seen_else_clause:
            last_clause = new_if.clauses[-1]
            raise UserException('Generated "if" statements must end with a '
                                'clause that is always True; usually an '
                                '"else".', loc=last_clause.loc, errno=3700530)
        #if there is only one clause (which is always executed),
        #optimize if statement away.
        elif is_collecting_code and len(new_if.clauses) == 1:
            for stmt in new_if.clauses[0].statements:
                self.collect_statement(stmt)
            new_if = None

        #Store generated if statement in interpreter
        if new_if is not None:
            self.collect_statement(new_if)
        return


    def exec_NodeFuncDef(self, node):
        '''Add function object to local namespace'''
        func_sig = Signature(node.signature)
        #save the current global namespace in the function. Otherwise
        #access to global variables would have surprising results
        #TODO: Implement closures, for nested functions:
        #      Copy the global dictionary and update it with the current
        #      local dictionary.
        #TODO: make copy of global namespace. needs:
        #      - new ast.Node.copy mechanism for shallow copy, referencing
        #      - new pretty printer mechanism to prevent duplicate printing
        global_scope = make_proxy(self.environment.global_scope)
        #create new function object and
        new_func = SimlFunction(node.name, func_sig,
                                node.statements, global_scope, node.loc)
        #put function object into the local namespace
        self.environment.local_scope.create_attribute(node.name, new_func)


    def exec_NodeClassDef(self, node):
        '''Define a class - create a class object in local name-space'''
        #TODO: code from SimlClass.__init__ should go here!
        
        #create new class object and put it into the local name-space
        new_class = SimlClass(node.name, bases=None, loc=node.loc)
        self.environment.local_scope.create_attribute(node.name, new_class)
        
        #Create new environment for code in class body
        new_env = ExecutionEnvironment()
        new_env.global_scope = self.environment.global_scope
        new_env.this_scope = None
        new_env.local_scope = new_class #functions and data are created inside the new class
        #Data attributes of user defined objects are by default variables
        new_env.default_data_role = RoleAlgebraicVariable

        #execute the function's code in the new environment.
        self.push_environment(new_env)
        try:
            self.exec_(node.statements)
        except ReturnFromFunctionException:
            print 'Warning: return statement in class declaration!'
        self.pop_environment()

        
    def exec_NodeStmtList(self, node):
        '''Visit node with a list of data definitions. Execute them.'''
        self.exec_(node.statements)


    #TODO: Create a nice syntax for the data/compile statement with arbitrary keywords.
    #TODO: A syntax for constructors - literals for user defined objects is needed.
    #      (A constructor maybe needs builtin functions like:
    #          set_assigned(...), setknown(...)
    #TODO: Maybe a syntax for anonymous types - tree literals should be introduced:
    #      data a:
    #          data b,c: Float param
    #          data d: String const
    #
    def visit_NodeDataDef(self, node):
        '''Create object and put it into symbol table'''
        #get the type object - a NodeIdentifier is expected as class_spec
        class_obj = self.eval(node.class_spec)
        if not isinstance(class_obj, type):
            raise UserException('Class expected.', node.loc)
        #Create the new object
        new_object = class_obj()

        #Set role
        role = node.role
        #The default role is set at beginning of:
        #module, class definition, function execution
        if role is None:
            role = self.environment.default_data_role
        #Set the role recursively for user defined classes
        set_role_recursive(new_object, role)

        #store new object in local scope
        new_name = node.name
        setattr(self.environment.local_scope, new_name, new_object)


    def exec_NodeCompileStmt(self, node):
        '''Create object and record program code.'''
        #TODO: Idea: replace the "compile" statement with a compile(...)
        #      function. This function could be written in Siml, and call
        #      several built in compilation functions.
        #      - This would make cusomization of the compilation algorithm
        #      quite easy for advanced users. They could write their own
        #      compilation functions.
        #      - Information that could be supplid by the users:
        #        - base class of generated python class.
        #        - which methods are the main methods
        #        - signatures of the main methods
        #        - which roles are legal for assignment
        #TODO: creatation of the tree-shaped object should be done by
        #      self.visit_NodeDataDef(...)
        #      so there is only one place where data objects are constructed.
        #TODO: break this method up into several methods, because it's really
        #      too big.
        #TODO: Structure of Compiled Object
        #        Object:
        #            - Functions
        #            - State Variables
        #            - Algebraic Variables
        #            - Parameters
        #            - Constants ?
        #        Function:
        #            - Inputs
        #            - Outputs
        #            - Internal temporary variables
        #            - Code
        #
        #Create data: --------------------------------------------------------------
        #get the type object - a NodeIdentifier is expected as class_spec
        class_obj = self.eval(node.class_spec)
        if not isinstance(class_obj, TypeObject):
            raise UserException('Class expected in compile statement.', node.loc)
        #Create the new object
        tree_object = class_obj()
        #set role
        set_role_recursive(tree_object, RoleAlgebraicVariable)
        #put new object also into module namespace, if name given
        if node.name is not None:
            self.environment.local_scope.create_attribute(node.name, tree_object)
#        print 'tree_object ------'
#        print tree_object

        #provide a module where local variables of functions can be stored
        func_locals = InterpreterObject()

        #specify and discover main functions ---------------------------------------
        #TODO: Implement automatic calling of main functions in child objects.
        #TODO: additional main function for steady-state simulations:
        #        init_steadystate(this, x01)
        #      The function is called repeatedly during a steady-state simulation
        #      to initialize the system with slightly different conditions. The
        #      argument x01 varies during the steady state simulation in small steps
        #      from 0 to 1. It is intended to control the variations of interesting
        #      parameters during the steady-state simulation.

        #In different parts of code only variables with speciffic roles
        #are valid targets of an assign statement.
        #      outside compile: only RoleConstant
        #      in "init":       only RoleParameter, RoleVariable, RoleConstant
        #      in "dynamic":    only RoleAlgebraicVariable, RoleConstant
        #      in "final":      only RoleVariable, RoleConstant

        #TODO: Mabe replace list with template object that is a CompiledClass
        #      The template class would include all required main functions.
        #      This way different output objects for optimization/solution of ODE
        #      could be realized. In principle such objects could be written in Siml
        #      Additional special propperties could be added by pragme statements.
        main_func_specs = \
            [Node(#target_roles=(RoleAlgebraicVariable, RoleTimeDifferential,
                                #RoleConstant),
                  call_argument_role=RoleInputVariable,
                  proto=SimlFunction('dynamic',
                                     Signature([NodeFuncArg('this')]),
                                     statements=[],
                                     global_scope=self.built_in_lib),
                  ),
             Node(#target_roles=(RoleParameter, RoleVariable, RoleConstant),
                  call_argument_role=RoleParameter,
                  proto=SimlFunction('initialize',
                                     Signature([NodeFuncArg('this')]),
                                     statements=[],
                                     global_scope=self.built_in_lib)),
             Node(#target_roles=(RoleVariable, RoleConstant),
                  call_argument_role=None,
                  proto=SimlFunction('final',
                                     Signature([NodeFuncArg('this')]),
                                     statements=[],
                                     global_scope=self.built_in_lib))]
        #Search additional main functions for changing parameters from outside
        #      'init_xxx(this, ...)'
        #      Any method with a name starting with 'init_' is considered an alternative
        #      initialization function, and it is created as a main function.
        for name, attr in tree_object.type().attributes.iteritems():
            if str(name).startswith('init_') and siml_callable(attr):
                new_spec = Node()
                new_spec.name = name
                #new_spec.target_roles = (RoleParameter, RoleVariable, RoleConstant)
                new_spec.call_argument_role = RoleParameter
                new_spec.proto = SimlFunction(name,
                                              Signature(attr.signature),
                                              statements=[],
                                              global_scope=self.built_in_lib)
                main_func_specs.append(new_spec)

        #Create code: ------------------------------------------------------------------
        #create (empty) flat object
        flat_object = CompiledClass()
        flat_object.instance_name = node.name
        flat_object.class_name = class_obj.name
        #flat_object.type = tree_object.type
        flat_object.loc = tree_object.type().loc
        #put special attribute time into flat object
        flat_object.create_attribute('time', TIME)

        #call the main functions of tree_object and collect code
        for spec in main_func_specs:
            func_name = spec.proto.name             #IGNORE:E1101
            #legal_roles = spec.target_roles         #IGNORE:E1101

            #get one of the main functions of the tree object
            try:
                func_tree = tree_object.get_attribute(func_name)
            except UndefinedAttributeError:
                #Create empty function for the missing main funcion
                func_flat = SimlFunction(func_name, Signature([NodeFuncArg('this')]),
                                         statements=[], global_scope=self.built_in_lib)
                flat_object.create_attribute(DotName(func_name), func_flat)
                print 'Warning: main function %s is not defined.' % str(func_name)
                continue

            #create argument list for call to main function
            args_list = []
            args_role = spec.call_argument_role
            for i, arg_def in enumerate(spec.proto.signature.arguments):
                #ignore 'this'
                if i == 0:
                    continue
                #create argument, which is always unknown. default type is Float
                if arg_def.type is None:
                    arg = IFloat()
                else:
                    arg = arg_def.type()()
                arg.role = args_role
                arg.target_name = str(arg_def.name) #TODO: This is bad hack!
                args_list.append(arg)
                #The arguments are not attributes of the simulation object
                flat_object.external_inputs.append(arg)

            #call the main function and collect code
            self.start_collect_code(func_locals=func_locals)
                                                #assign_target_roles=legal_roles)
            self.apply(func_tree, tuple(args_list), {})  
            stmt_list, dummy = self.stop_collect_code()
            #create a new main function for the flat object with the collected code
            func_flat = SimlFunction(func_name, spec.proto.signature,
                                     statements=stmt_list,
                                     global_scope=self.built_in_lib)
            #Put new main function into flat object
            flat_object.create_attribute(DotName(func_name), func_flat)

        #print 'func_locals ------------'
        #print func_locals

        #The external inputs should not get regular long names. They live in
        #their own list and are not attributes of the simulation object.
        external_inputs = set([id(o) for o in flat_object.external_inputs])

        #flatten tree_object (the data) recursively.
        flattened_attributes = set()
        flattened_attributes.update(external_inputs)
        def flatten(tree_obj, flat_obj, prefix):
            '''
            Put all attributes (all data leaf objects) into a new flat
            name-space. The attributes are not copied, but just placed under
            new (long, dotted) names in a new parent object. Therefore the
            references to the objects in the Symbol table stay intact.

            Arguments:
            tree_obj: InterpreterObject (Tree shaped), source.
            flat_obj: InterpreterObject (no tree) destination.
            prefix: DotName
                Prefix for attribute names, to create the long names.
            '''
            for name, data in tree_obj.attributes.iteritems():
                #don't flatten anything twice
                if id(data) in flattened_attributes:
                    continue
                flattened_attributes.add(id(data))

                long_name = prefix + DotName(name)
                #CodeGeneratorObject are the only data types of the compiled code
                if isinstance(data, CodeGeneratorObject):
                    #do not flatten constants
                    if not issubclass(data.role, (RoleParameter, RoleVariable)):
                        continue
                    flat_obj.create_attribute(long_name, data, reparent=True)
                #Recurse all other objects and see if they contain CodeGeneratorObject attributes
                else:
                    flatten(data, flat_obj, long_name)

        #flatten regular data first
        flatten(tree_object, flat_object, DotName())
        #flatten local variables
        flatten(func_locals, flat_object, DotName('__func_local__'))

        #store new object in interpreter
        self.add_compiled_object(flat_object)

    
    def exec_(self, stmt_list):
        '''
        Interpret a list of statements.

        Call right handler function for a single statement.
        '''
        try:
            for node in stmt_list:
                if isinstance(node, NodePassStmt):
                    self.exec_NodePassStmt(node)
                elif isinstance(node, NodeReturnStmt):
                    self.exec_NodeReturnStmt(node)
                elif isinstance(node, NodeExpressionStmt):
                    self.exec_NodeExpressionStmt(node)
                elif isinstance(node, NodeAssignment):
                    self.exec_NodeAssignment(node)
                elif isinstance(node, NodeIfStmt):
                    self.exec_NodeIfStmt(node)
                elif isinstance(node, NodeFuncDef):
                    self.exec_NodeFuncDef(node)
                elif isinstance(node, NodeClassDef):
                    self.exec_NodeClassDef(node)
                elif isinstance(node, NodeStmtList):
                    self.exec_NodeStmtList(node)
                elif isinstance(node, NodeCompileStmt): 
                    self.exec_NodeCompileStmt(node)
                elif isinstance(node, NodeDataDef):
                    self.visit_NodeDataDef(node)
                else:
                    raise Exception('Unknown node type for statements: ' 
                                    + str(type(node)))

        # Put good location information into UserExceptions that have none.
        except UserException, e:
            if e.loc is None:
                e.loc = node.loc
            raise
        # Create user visible 'Duplicate attribute' errors.
        except DuplicateAttributeError, e:
            raise UserException('Duplicate attribute %s.' % e.attr_name,
                                loc=node.loc, errno=3800910)
        # Create user visible 'Undefined attribute' errors.
        except UndefinedAttributeError, e:
            raise UserException('Undefined attribute "%s".' % e.attr_name,
                                loc=node.loc, errno=3800920)


    # --- code collection ------------------------------------------------------   
    def start_collect_code(self, stmt_list=None, func_locals=None, ):
        '''
        Set up everything for the code collection process

        ARGUMENTS
        ---------
        stmt_list: list/None
            List where the generated statements will be appended to.
        func_locals: InterpreterObject/None
            Namespace where each function's local variables will be stored.
        '''
        self.compile_stmt_collect = [[]] if stmt_list is None \
                                       else [stmt_list]
        self.locals_storage = InterpreterObject() if func_locals is None \
                                                  else func_locals

    def stop_collect_code(self, ): 
        '''
        End the code collection process

        RETURNS
        -------
        stmt_list: [ast.Node]
            List of statements that were generated by the code collection
            process. (Mainly assignments)
        func_locals: InterpreterObject
            Namespace where the local variables from each function invocation
            are stored
        '''
        if not self.is_collecting_code():
            raise Exception('Collecting statements (compilation) has not been enabled!')

        stmt_list, func_locals = self.compile_stmt_collect[0], self.locals_storage
        self.compile_stmt_collect = None
        self.locals_storage = None
        return stmt_list, func_locals

    def push_statement_list(self, statement_list):
        '''
        Put a statement list on the stack of lists.

        Called by compund statents, for example the "if" statement.
        '''
        if not self.is_collecting_code():
            raise Exception('Collecting statements (compilation) has not been enabled!')
        self.compile_stmt_collect.append(statement_list)

    def pop_statement_list(self):
        '''
        Remove a statement list from the stack of lists, and return it.

        Called by compund statents, for example the "if" statement.
        '''
        if not self.is_collecting_code():
            raise Exception('Collecting statements (compilation) has not been enabled!')
        return self.compile_stmt_collect.pop()

    def collect_statement(self, stmt):
        '''
        Put a statement into the current (top-most) statement list for code
        creation.

        The storage for statements is a list of lists to allow nested compound
        statements.
        '''
        if not self.is_collecting_code():
            raise Exception('Collecting statements (compilation) has not been enabled!')
        self.compile_stmt_collect[-1].append(stmt)

    def is_collecting_code(self):
        '''Return True if self.collect_statement can be successfully called.'''
        return self.compile_stmt_collect is not None

    def get_locals_storage(self):
        '''
        Return special storage namespace for local variables of functions.
        Only availlable when collecting code.

        (Used by SimlFunction.create_persistent_locals_ns()).
        '''
        if not self.is_collecting_code():
            raise Exception('Collecting statements (compilation) has not been enabled!')
        return self.locals_storage

    def add_compiled_object(self, flat_object):
        '''
        Add a flattened object to the list of output objects

        ARGUMENTS
        ---------
        flat_object: CompiledClass
            A flattened InterpreterObject, which is generated by the compile
            statement.
        '''
        self.compiled_object_list.append(flat_object)

    def get_compiled_objects(self):
        '''Return list of compiled objects'''
        return self.compiled_object_list


    # --- run code ---------------------------------------------------------------
    def interpret_module_file(self, file_name, module_name=None):
        '''Interpret a whole program. The program's file name is supplied.'''
        long_file_name = os.path.abspath(file_name)
        #open and read the file
        try:
            input_file = open(long_file_name, 'r')
            module_text = input_file.read()
            input_file.close()
        except IOError, theError:
            message = 'Could not read input file.\n' + str(theError)
            raise UserException(message, None)
        #parse the program
        return self.interpret_module_string(module_text, file_name, module_name)


    def interpret_module_string(self, text, file_name=None, module_name=None):
        '''Interpret the program text of a module.'''
        #create the new module and import the built in objects
        mod = IModule(module_name, file_name)
        #put module into root namespace (symbol table)
        self.modules[module_name] = mod
        #add built in attributes to model
        mod.__dict__.update(self.built_in_lib.__dict__)
        #set up stack frame (execution environment)
        env = ExecutionEnvironment()
        env.global_scope = mod
        env.local_scope = mod
        #Data attributes on module level are by default constants
        env.default_data_role = RoleConstant
        #create dummy function for macro error stack trace
        env.function = SimlFunction(name='__main__', 
                                    loc=TextLocation(0, text, file_name))
        #put the frame on the frame stack
        self.push_environment(env)
        #parse the program text
        prs = simlparser.Parser()
        ast = prs.parseModuleStr(text, file_name, module_name)
        #execute the statements - interpret the AST
        self.exec_(ast.statements)
        #remove frame from stack
        self.pop_environment()


    # --- manage frame stack --------------------------------------------------------------
    def push_environment(self, new_env):
        '''
        Put new stack frame on stack.
        Change environment in all visitors.
        '''
        self.env_stack.append(new_env)
        self.environment = new_env

    def pop_environment(self):
        '''
        Remove one stack frame from stack.
        Change environment in all visitors.
        '''
        old_env = self.env_stack.pop()
        new_env = self.env_stack[-1]
        self.environment = new_env
        return old_env

#    def get_environment(self):
#        '''Return the current (topmost) environment from the stack.'''
#        return self.env_stack[-1]


    # --- testing --------------------------------------------------------------------
    def create_test_module_with_builtins(self):
        '''
        Create a module object and a stack frame for testing.

        *** This method must only be osed for tests ***

        The module contains the built in library. After calling this method,
        statemnts and expressions can be interpreted like normal program
        text.
        '''
        print '*** create_test_module_with_builtins: '\
              'This method must only be used for tests ***'
        #create the new module and import the built in objects
        mod = IModule('test', '--no-file--')
        #put module into root namespace (symbol table)
        self.modules['test'] = mod
        mod.__dict__.update(self.built_in_lib.__dict__)
        #set up stack frame (execution environment)
        env = ExecutionEnvironment()
        env.global_scope = mod
        env.local_scope = mod
        #put the frame on the frame stack
        self.push_environment(env)



if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add doctest tests.
    pass