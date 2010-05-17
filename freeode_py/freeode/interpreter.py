# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2008 - 2010 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
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
and it collects the statements that will be part of the compiled program.
"""

#TODO: remove DotName, everything is a simple string after all.
#      DotName is may be needed after flattening.

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#import copy
import weakref
from weakref import ref
import math
import os
import types

from freeode.ast import *
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
                attr = scope.get_attribute(attr_name)
                return attr
            except UndefinedAttributeError: #IGNORE:W0704
                pass
        #attribute could not be found in the scopes
        if isinstance(default, UndefinedAttributeError):
            raise UndefinedAttributeError(attr_name=attr_name)
        else:
            return default



class InterpreterObject(Node):
    '''
    Base class of all objects that the interpreter operates on.
    Can also be seen as part of structured symbol table

    It inherits from Node only to get Ascii-art tree and copying.
    '''
    #let these attributes appear first in the pretty printed tree
    aa_top = ['name', 'type']
    #reference to interpreter - TODO: global variables are bad
    #interpreter = None

    def __init__(self):
        Node.__init__(self)
        #Reference to object one level up in the tree
        #type weakref.ref or None
        self.parent = None
        #The symbol table
        self.attributes = {}
        #weak reference to class of this instance
        self.type = None
        #const, param, variable, ... (Comparable to storage class in C++)
        self.role = RoleUnkown
        #True/False is the value of this object known?
        self.is_known = False
        #TODO: self.save ??? True/False attribute is saved to disk as simulation result
        #TODO: self.default_value ??? (or into leaf types?)
        #TODO: self.auto_created ??? for automatically created variables that should be eliminated

    def __deepcopy__(self, memo_dict):
        '''deepcopy that gets the parent right'''
        copied_self = super(InterpreterObject, self).__deepcopy__(memo_dict)
        for name, copied_attr in copied_self.attributes.iteritems():
            copied_attr.parent = ref(copied_self)
        return copied_self

    def create_attribute(self, name, newAttr, reparent=False):
        '''
        Put attribute into parent object. - Put name into symbol table.

        This method is called for a data statement.
        - When an attribute with the same name already exists a
        DuplicateAttributeError is raised.
        - This object (self) becomes the parent of newAttr, when newAttr
        does not already have a parent. However setting argument
        reparent=True forces changing newAttr's parent.

        ARGUMENTS
        ---------
        name: DotName, str
            Name of the new attribute
        newAttr: InterpreterObject
            The new attribute that will be put into this object.
        reparent: True/False
            - if True: set parent attribute of newAttr in any case.
            - if False (default): set parent attribute only if newAttr has no
            parent.
        '''
        if name in self.attributes:
            raise DuplicateAttributeError(attr_name=name)
        self.attributes[name] = newAttr
        #set parent link for new objects, or when the parent has died.
        if newAttr.parent is None or newAttr.parent() is None or reparent: #IGNORE:E1102
            newAttr.parent = weakref.ref(self)

    def get_attribute(self, name):
        '''Return attribute object'''
        if name in self.attributes:
            return self.attributes[name]
        #Search for attribute in the type (class) object
        elif self.type is not None and self.type().has_attribute(name):
            #if attribute is a function, put it into a method wrapper
            # TODO: change to Python's way of functioning?
            # See: http://wiki.python.org/moin/FromFunctionToMethod
            attr = self.type().get_attribute(name)
            if siml_callable(attr):
                attr = BoundMethod(attr.name, attr, self)
            return attr
        else:
            raise UndefinedAttributeError(attr_name=name)

    def has_attribute(self, name):
        '''Return true if object has an attribute with name "name"'''
        if name in self.attributes:
            return True
        #Search for attribute in the type (class) object
        elif self.type is not None and self.type().has_attribute(name):
            return True
        else:
            return False

#    def replace_attribute(self, name, newAttr, reparent=False):
#        '''
#        Replace an attribute.
#
#        ARGUMENTS
#        ---------
#        name: DotName, str
#            Name of the attribute that will be replaced
#        newAttr: InterpreterObject
#            The new attribute that will be put into this object.
#        reparent: True/False
#            - if True: set parent attribute of newAttr in any case.
#            - if False (default): set parent attribute only if newAttr has no
#            parent.
#
#        TODO: remove this function? It is only necessary for derivatives of
#              user defined classes which don't work.
#        '''
#        del self.attributes[name]
#        self.create_attribute(name, newAttr, reparent)

    def find_name(self, in_attr):
        '''
        Find the name of an attribute.

        ARGUMENTS
        ---------
        in_attr: InterpreterObject
            Attribute whose name will be searched. It must be an attribute of
            this object (self). If "in_attr" is not found an Exception object
            will be raised.

        RETURNS
        -------
        str, DotName
        The attribue's name.
        '''
        for attr_name, attr in self.attributes.iteritems():
            if attr is in_attr:
                break
        else:
            raise Exception('"in_attr" is not attribute of this object.')
        return attr_name #IGNORE:W0631

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



class CallableObject(InterpreterObject):
    '''
    Base class of all functions.

    CONSTRUCTOR ARGUMENTS
    ---------------------
    name: DotName, str
        The function's name.
    '''
    def __init__(self, name):
        InterpreterObject.__init__(self)
        self.role = RoleConstant
        self.is_known = True
        self.name = name
	# TODO: rename to is_runtime_function
        self.is_fundamental_function = False
        self.codegen_name = None
        '''
        If True: the function is a basic building block of the language.
        The code generator can emit code for this function. The flattened
        simulation object must only contain calls to these functions.
        If False: This function must be replaced with a series of calls
        to fundamental functions.
        '''
        self.return_type = None

    def __call__(self, *args, **kwargs):
        '''All Siml-functions must implement this method'''
        raise NotImplementedError('__call__ method is not implemented. Use a derived class!')


##In case type objects should be callable nevertheless.
#class TypeObject(CallableObject):  #IGNORE:W0223
#    '''Base class of all classes'''
#    def __init__(self, name):
#        CallableObject.__init__(self, name)

class TypeObject(InterpreterObject):
    '''Base class of all classes'''
    def __init__(self, name):
        InterpreterObject.__init__(self)
        self.role = RoleConstant
        self.is_known = True
        self.name = name

    def __call__(self, *args, **kwargs):
        '''All Siml-classes must implement this method'''
        raise NotImplementedError('__call__ method is not implemented. Use a derived class!')



class FundamentalObject(InterpreterObject):
    '''
    Objects that represent data in the code that the compiler generates.

    Only these objects, and operations with these objects, should remain in a
    flattened simulation.

    # TODO: Rename to RuntimeObject
    '''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.time_derivative = None
        self.target_name = None


class ArgumentList(SimpleArgumentList):
    """
    Contains arguments of a function definition.
    - Checks the arguments when function definition is parsed
    - Evaluates the arguments when the function definition is interpreted
    - Parses the arguments when the function is called.
    """
    def __init__(self, arguments, loc=None):
        '''
        ARGUMENTS
        ---------
        arguments: [ast.NodeFuncArg, ...] or SimpleArgumentList
            The functions arguments
        loc: ast.TextLocation
            Location where the function is defined in the program text
        '''
        #TODO: Maybe move code from SimpleArgumentList.__init__(...) to here.
        #      Nodes generated by the parser would then all be like C structs.
        SimpleArgumentList.__init__(self, arguments, loc)

        #replace type objects with weak references to them
        for arg in self.arguments:
            if isinstance(arg.type, TypeObject):
                arg.type = ref(arg.type)


    def evaluate_args(self, interpreter):
        '''
        Interpret the types and default values of the arguments.
        - default values are computed and must evaluate to constants
        #TODO: why is this function not called from the constructor?
        '''
        expression_visitor = interpreter.statement_visitor.expression_visitor
        #evaluate argument type and default arguments
        for arg in self.arguments:
            if arg.type is not None:
                type_ev = expression_visitor.eval(arg.type)
                arg.type = ref(type_ev)
            if arg.default_value is not None:
                dval_ev = expression_visitor.eval(arg.default_value)
                arg.default_value = dval_ev
            #test type compatibility of default value and argument type
            if arg.type is not None and arg.default_value is not None:
                self._test_type_compatible(arg.default_value, arg)
        #raise NotImplementedError()
        return self


    def parse_function_call_args(self, args_list, kwargs_dict):
        '''
        Executed when a function call happens.
        Fill the arguments of the call site into the arguments of the
        function definition. Does type-checking.

        ARGUMENTS
        ---------
        args_list: [<siml values, AST nodes>, ...]
            Positional arguments.
        kwargs_dict: {str(): <siml values, AST nodes>, ...}
            Keyword arguments.

        RETURNS
        -------
        Dictionary of argument names and associated values.
        dict(<argument name>: <siml values, AST nodes>, ...)
        dict(str(): Node(), ...)
        '''
        #TODO: offer two different formats to return the parsed arguments:
        #      - a tuple of positional arguments. (For function wrapper)
        #      - a dictionary of keyword arguments. (For Siml function)
        #TODO: implement support for *args and **kwargs
        #      Description of semantics is here:
        #      http://docs.python.org/reference/expressions.html#calls

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
            self._test_type_compatible(in_val, arg_def)
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
                raise UserException('Duplicate argument "%s".'
                                    'Function definition in: %s \n'
                                    % (str(in_name), str(self.loc)),
                                    loc=None, errno=3200270)
            #test for correct type,
            self._test_type_compatible(in_val, self.argument_dict[in_name])
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


    def _test_type_compatible(self, in_object, arg_def):
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
        if not siml_issubclass(in_object.type(), arg_def.type()):
            raise UserException(
                    'Incompatible types. \nVariable: "%s" '
                    'is defined as: %s \nHowever, argument type is: %s. \n'
                    'Argument definition in: %s \n'
                    % (arg_def.name, str(arg_def.type().name),
                       str(in_object.type().name), str(self.loc)),
                    loc=None, errno=3200310)



class BuiltInFunctionWrapper(CallableObject):
    '''
    Represents a function written in Python; for functions like 'sqrt' and 'sin'.

    The object is callable from Python and Siml.

    When a call is invoked argument parsing is done similarly
    to Pythons's function call. Optionally function arguments can have
    a type that must match too.
        f(a:Float=2.5)

    When all arguments are known, the wrapped Python function is executed. The
    result of the computation is wrapped in its associated InterpreterObject
    and returned.
    However if any argument is unknown, a decorated (and unevaluated) function
    call is returned. For operators NodeOpInfix2, NodeOpPrefix1 can be
    created - see arguments is_binary_op, is_prefix_op, op_symbol.

    CONSTRUCTOR ARGUMENTS
    ---------------------
    name
        name of function
    argument_definition: IntArgumentList
        Argument definition of the function
    return_type: TypeObject or None
        Type of the function's return value.
        When an unevaluated result is returned, this will be assigned to the
        type of the ast.Node.
        If the return type is None, there is no definition of a return type.
        Functions that return no value must put CLASS_NONETYPE here.
    py_function:
        Function that will be called when the result can be computed.
    accept_unknown_values: True/False - default: False
        If True: call wrapped function also when arguments are unknown values.
        If False: raise UnknownArgumentsException when an unknown argument is
        encountered.
    is_fundamental_function: True/False - default: True
        If True: the function is a basic building block of the language.
        The code generator can emit code for this function. The flattened
        simulation object must only contain calls to these functions.
        If False: This function must be replaced with a series of calls
        to fundamental functions.

    RETURNS
    -------
    Wrapped function result (InterpreterObject) or None
    '''
    def __init__(self, name, argument_definition=ArgumentList([]),
                             return_type=None,
                             py_function=lambda:None,
                             accept_unknown_values=False,
                             is_fundamental_function=True,
                             codegen_name=None):
        CallableObject.__init__(self, name)
        #ArgumentList(): The function's argument definition.
        self.argument_definition = argument_definition
        #TypeObject or None: The type of the function's return value
        self.return_type = ref(return_type) if return_type is not None else None
        #A Python function. Get function if argument is unbound method.
        self.py_function = py_function if isinstance(py_function, types.FunctionType) \
                           else  py_function.im_func
        #Call wrapped function also when arguments are unknown values
        self.accept_unknown_values = accept_unknown_values
        #If true, this function is a basic building block of the simulation
        self.is_fundamental_function = is_fundamental_function
        #Name, so the code generator can recognize the function
        self.codegen_name = codegen_name


    def __call__(self, *args, **kwargs):
        '''
        Execute the wrapped function.

        - Checks the arguments, incuding type checking.
        - If all arguments are known this function unpacks the values, and
        calls the wrapped function with regular Python objects as arguments.
        The return value is again wrapped into a Siml object.
        - If any argument is unknown, an unevaluated function call or operator
        node is returned.

        ARGUMENTS
        ---------
        args: [InterpreterObject]
            Positional arguments for the wrapped function
        kwargs: {str: InterpreterObject}
            Keyword arguments for the wrapped function
        '''
        #TODO: Convert float, str, bool, from and to Siml values.
        #      Converting arguments and return values should be controlled
        #      separately. This would make wrapper functions superfluent like
        #      like wsiml_isinstance(...)
        #try if argument definition matches
        parsed_args = self.argument_definition\
                          .parse_function_call_args(args, kwargs)
        #Test if all arguments are known values.
        parsed_args_2 = {} #TODO: remove! unnecessary!
        all_python_values_exist = True
        for name, siml_val in parsed_args.iteritems():
            if not siml_isknown(siml_val):
                all_python_values_exist = False
            #convert the names to regular strings
            parsed_args_2[str(name)] = siml_val
        #Test: call function or generate code
        #Generate code; there were unknown values, and we don't accept it.
        if not all_python_values_exist and not self.accept_unknown_values:
            #The expression visitor will create an annotated
            #NodeFuncCall/NodeOpInfix2/NodeOpPrefix1
            raise UnknownArgumentsException()
        #call the wrapped Python function
        #all argument values are known, or we don't care about unknown values.
        retval = self.py_function(**parsed_args_2)            #IGNORE:W0142

        #TODO: maybe always convert float, str, bool --> IFloat, IString, IBool?
        #use Siml's None
        if retval is None:
            retval = NONE
        #Test return value.type
        if(self.return_type is not None and
           not siml_issubclass(retval.type(), self.return_type())):
            raise Exception('Wrong return type in wrapped function.')

        return retval


    def put_into(self, siml_object):
        '''Put function object into a siml_object using the right name.'''
        siml_object.create_attribute(self.name, self)
        return self



class SimlFunction(CallableObject):
    '''
    Function written in Siml (user defined function).
    '''
    def __init__(self, name, argument_definition=ArgumentList([]),
                             return_type=None,
                             statements=None, global_scope=None):
        CallableObject.__init__(self, name)
        #IntArgumentList
        self.argument_definition = argument_definition
        #ref(TypeObject) or None
        self.return_type = ref(return_type) if return_type is not None else None
        #the statements of the function's body
        self.statements = statements if statements is not None else []
        #global namespace, stored when the function was defined
        self.global_scope = global_scope
        #count how often the function was called (to create unique names
        #for the local variables)
        self.call_count = 0
        #this function is no basic building block, because it must be interpreted.
        self.is_fundamental_function = False
        #--- data flow analysis -------
        self.inputs = None
        self.outputs = None


    def __call__(self, *args, **kwargs):
        raise Exception("User defined functions must be executed with apply.")


    def get_complete_path(self):
        '''
        Get complete dotted name of the function.

        Goes recursively to all parents, asks them for their names, and
        creates a DotName out of the names. This will usually produce a
        three component DotName structured like this: module.class.function

        RETURNS
        -------
        DotName
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
        '''
        #long name of function. like: bioreactor.conti.bacterial_growth
        func_path = self.get_complete_path()
        #name-space where all local variables go into
        locals_root = INTERPRETER.get_locals_storage()
        #create namespace with long name of this function
        locals_ns = locals_root.create_path(func_path[1:] +
                                            DotName(str(self.call_count)))
        return locals_ns



class BoundMethod(CallableObject):
    '''
    Represents a method of an object.
    Calls a function with the correct 'this' pointer.

    The object is callable from Python and Siml.

    No argument parsing or type checking are is done. The wrapped Function
    is responsible for this. The handling of unevaluated/unknown arguments,
    and unevaluated return values are left to the wrapped function.

    ARGUMENTS
    ---------
    name: str
        name of function
    function: CallableObject or (Python) function
        Wrapped function that will be called.
    this: InterpreterObject
        The first positional argument, that will be supplied to the wrapped
        function.

    RETURNS
    -------
    Anything that the wrapped function returns.
    '''
    def __init__(self, name, function, this):
        CallableObject.__init__(self, name)
        #the wrapped function
        self.function = function
        #the 'this' argument - put into list for speed reasons
        self.this = make_proxy(this)
        #if the wrapped function is fundamental, this method is fundamental too.
        self.is_fundamental_function = function.is_fundamental_function
        #the bound method has the same return type as the wrapped function
        self.return_type = function.return_type

    def __call__(self, *args, **kwargs):
        new_args = (self.this,) + args
        return self.function(*new_args, **kwargs) #IGNORE:W0142



class SimlClass(TypeObject):
    '''
    Represents class written in Siml - usually a user defined class.
    '''
    def __init__(self, name, bases, statements, loc=None):
        '''
        Create a new class object. Called for a class statement.

        The statements inside the class' body are interpreted here.
        '''
        TypeObject.__init__(self, name)
        self.bases = bases
#        self.statements = statements
        self.loc = loc

        #TODO: implement base classes
        if self.bases is not None:
            raise Exception('Base classes are not implemented!')

        #Create new environment for object construction.
        #Use global scope from class definition.
        new_env = ExecutionEnvironment()
        new_env.global_scope = INTERPRETER.get_environment().global_scope
        new_env.this_scope = None
        new_env.local_scope = self #functions and data are created
        #                           in the local scope - this class object
        #Data attributes of user defined objects are by default variables
        new_env.default_data_role = RoleAlgebraicVariable

        #execute the function's code in the new environment.
        INTERPRETER.push_environment(new_env)
        try:
            INTERPRETER.run(statements)
        except ReturnFromFunctionException:
            print 'Warning: return statement in class declaration!'
#                raise Exception('Return statements are illegal in class bodies!')
        INTERPRETER.pop_environment()


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
            init_meth(*args, **args)  #IGNORE:W0142
        return new_obj



#---------- Built In Library  ------------------------------------------------*

#---------- Infrastructure -------------------------------------------------
class BuiltInClassWrapper(TypeObject):
    '''
    Siml class for built in objects. - Create instances of built in objects.

    Instances of this class create instances of built in objects in Siml.
    (This Python object is therefore a metaclass.)
    They are the class/type of built in objects like:
    Float, String, Function, Class, ...
    The object is s thin wrapper around a Python class.

    TODO: research how real Pyton classes can be used as classes in Siml
    '''
    def __init__(self, name):
        TypeObject.__init__(self, name)
        #the wrapped class will set this
        self.py_class = None

    def __call__(self, *args, **kwargs):
        '''Create a new Siml object.'''
        return self.py_class(*args, **kwargs) #IGNORE:W0142

    def put_into(self, siml_object):
        '''Put class object into a siml module using the right name.'''
        siml_object.create_attribute(self.name, self)
        return self



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
        self.name = name
        self.source_file_name = file_name
        self.role = RoleConstant
#the single object that should be used to create all Modules
#CLASS_MODULE = IModule.init_funcs_and_class()



#------- Built In Data --------------------------------------------------
class INoneClass(BuiltInClassWrapper):
    '''Class object for Siml's None object'''
    def __call__(self, *args, **kwargs):
        '''Raise exception, there must be only a single None object.'''
        raise UserException('Creating multiple None objects is illegal.')

class INone(InterpreterObject):
    '''Siml's None object.'''
    #The Siml class, naturally shared by all instances
    type_object = None

    def __init__(self):
        InterpreterObject.__init__(self)
        self.type = ref(INone.type_object)
        self.is_known = True
        self.role = RoleConstant

    @staticmethod
    def create_class_object():
        '''
        Create the class object for Siml and create the special methods for
        operators (+).
        '''
        #create the class object for the Siml class system
        class_none = INoneClass('NoneType')
        class_none.py_class = INone
        INone.type_object = class_none
        #TODO: NoneType.__str__: implement, and get the circular references right
        return class_none

    def __str__(self):#convenience for sane behavior from Python
        return 'NONE'
    def _str(self):
        '''__str__ called from Siml'''
        istr = IString('None')
        istr.role = RoleConstant
        return istr
#The class object used in Siml for the single instance of INone
CLASS_NONETYPE = INone.create_class_object()
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



class IBool(FundamentalObject):
    '''
    Memory location of a boolean value.

    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not.
    '''
    #The Siml class, naturally shared by all instances
    type_object = None

    def __init__(self, init_val=None):
        FundamentalObject.__init__(self)
        self.type = ref(IBool.type_object)
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (str, float, int, bool)):
                self.value = bool(init_val)
            elif isinstance(init_val, (FundamentalObject)):
                if init_val.value is None:
                    ValueError('Object can not be initialized from unknown value.')
                self.value = bool(init_val.value)
            else:
                raise TypeError('Can not initialize IBool from type: %s'
                                % str(type(init_val)))
            #mark object as known at compile time
            self.role = RoleConstant
            self.is_known = True


    @staticmethod
    def create_class_object():
        '''
        Create the 'Bool' class object for Siml.
        '''
        #create the class object for the Siml class system
        class_bool = BuiltInClassWrapper('Bool')
        class_bool.py_class = IBool
        IBool.type_object = class_bool
        #return the class object
        return class_bool


    @staticmethod
    def update_class_object():
        '''
        Create all methods, put them into the class object.

        Must be called separately because of circular references:
        IBool uses IString (IBool.__str__) and IString uses IBool
        (IString.__eq__)
        '''
        class_bool = IBool.type_object
        W = BuiltInFunctionWrapper
        #Argument definition for binary operators
        binop_args = ArgumentList([NodeFuncArg('self', class_bool),
                                    NodeFuncArg('other', class_bool)])
        #Argument definition for unary functions and operators
        single_args = ArgumentList([NodeFuncArg('self', class_bool)])
        #comparison operators
        W('__eq__', binop_args, CLASS_BOOL,
          py_function=IBool.__eq__).put_into(class_bool)
        W('__ne__', binop_args, CLASS_BOOL,
          py_function=IBool.__ne__).put_into(class_bool)
        #special functions for boolean operations (and or not)
        #See: http://www.python.org/dev/peps/pep-0335/
        W('__not__', single_args, CLASS_BOOL,
          py_function=IBool._not).put_into(class_bool)
        W('__and2__', binop_args, CLASS_BOOL,
          py_function=IBool._and2).put_into(class_bool)
        W('__or2__', binop_args, CLASS_BOOL,
          py_function=IBool._or2).put_into(class_bool)
        #Special function for assignment
        W('__assign__', binop_args, CLASS_NONETYPE,
          py_function=IBool._assign,
          accept_unknown_values=True).put_into(class_bool)
        #Printing
        W('__str__', single_args, CLASS_STRING,
          py_function=IString._str, #IGNORE:W0212
          codegen_name='Bool.__str__').put_into(class_bool)


    #comparison operators
    def __eq__(self, other):
        return IBool(self.value == other.value)
    def __ne__(self, other):
        return IBool(self.value != other.value)
    #special functions for boolean operations (and or not)
    def _not(self):
        '''Called for Siml "not".'''
        return IBool(not self.value)
    def _and2(self, other):
        '''Called for Siml "and".'''
        return IBool(self.value and other.value)
    def _or2(self, other):
        '''Called for Siml "or".'''
        return IBool(self.value or other.value)
    #assignment
    def _assign(self, other):
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
    def _str(self):
        '''__str__ called from Siml'''
        istr = IString(self.value)
        istr.role = RoleConstant
        return istr

#The class object used in Siml to create instances of IBool
CLASS_BOOL = IBool.create_class_object()
#global constants True and False (More easy than introducing additional
#literal values)
TRUE = IBool(True)
FALSE = IBool(False)



class IString(FundamentalObject):
    '''
    Memory location of a string

    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not.
    '''
    #The Siml class, naturally shared by all instances
    type_object = None

    def __init__(self, init_val=None):
        FundamentalObject.__init__(self)
        self.type = ref(IString.type_object)
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (str, float, int, bool)):
                self.value = str(init_val)
            elif isinstance(init_val, FundamentalObject):
                if init_val.value is None:
                    ValueError('Object can not be initialized from unknown value.')
                self.value = str(init_val.value)
            else:
                raise TypeError('Can not init IString from type: %s'
                                % str(type(init_val)))
            #mark object as known at compile time
            self.role = RoleConstant
            self.is_known = True


    @staticmethod
    def create_class_object():
        '''
        Create the class object for Siml and create the special methods for
        operators (+).
        '''
        #create the class object for the Siml class system
        class_string = BuiltInClassWrapper('String')
        class_string.py_class = IString
        IString.type_object = class_string

        #create all methods, put them into the class
        W = BuiltInFunctionWrapper
        #Binary operators
        binop_args = ArgumentList([NodeFuncArg('self', class_string),
                                    NodeFuncArg('other', class_string)])
        W('__add__', binop_args, class_string,
          py_function=IString.__add__).put_into(class_string)
        #comparison operators == !=
        W('__eq__', binop_args, CLASS_BOOL,
          py_function=IString.__eq__).put_into(class_string)
        W('__ne__', binop_args, CLASS_BOOL,
          py_function=IString.__ne__).put_into(class_string)
        #Special function for assignment
        W('__assign__', binop_args, CLASS_NONETYPE,
          py_function=IString._assign,
          accept_unknown_values=True).put_into(class_string)
        #Printing
        single_args = ArgumentList([NodeFuncArg('self', class_string)])
        W('__str__', single_args, class_string,
          py_function=IString._str,
          codegen_name='String.__str__').put_into(class_string)
        #return the class object
        return class_string


    def __add__(self, other):
        return IString(self.value + other.value)
    #comparisons
    def __eq__(self, other):
        return IBool(self.value == other.value)
    def __ne__(self, other):
        return IBool(self.value != other.value)
    #special function for assignment
    def _assign(self, other):
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
    def _str(self):
        '''called from Siml'''
        return self

#The class object used in Siml to create instances of IFloat
CLASS_STRING = IString.create_class_object()

#Create the member functions of the Bool class.
#Must be called here because of circular references:
#IBool uses IString (IBool.__str__) and IString uses IBool (IString.__eq__)
IBool.update_class_object()



class IFloat(FundamentalObject):
    '''
    Memory location of a floating point number

    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not.
    '''
    #The Siml class, naturally shared by all instances
    type_object = None

    def __init__(self, init_val=None):
        FundamentalObject.__init__(self)
        self.type = ref(IFloat.type_object)
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
            siml_setknown(self)
            self.role = RoleConstant
            self.is_known = True


    @staticmethod
    def create_class_object():
        '''
        Create the class object for Siml and create the special methods for
        operators (+ - * / % **).
        '''
        #create the class object for the Siml class system
        class_float = BuiltInClassWrapper('Float')
        class_float.py_class = IFloat
        IFloat.type_object = class_float

        #TODO: sin, cos, tan, log should become member functions of the
        #      numerical base types. These functions must behave differently
        #      for each base type (Float, RawFloatArray)
        #initialize the mathematical operators, put them into the class
        W = BuiltInFunctionWrapper
        #Arithmetic operators
        #binary
        binop_args = ArgumentList([NodeFuncArg('self', class_float),
                                   NodeFuncArg('other', class_float)])
        W('__add__', binop_args, class_float,
          py_function=IFloat.__add__).put_into(class_float)
        W('__sub__', binop_args, class_float,
          py_function=IFloat.__sub__).put_into(class_float)
        W('__mul__', binop_args, class_float,
          py_function=IFloat.__mul__).put_into(class_float)
        W('__div__', binop_args, class_float,
          py_function=IFloat.__div__).put_into(class_float)
        W('__mod__', binop_args, class_float,
          py_function=IFloat.__mod__).put_into(class_float)
        W('__pow__', binop_args, class_float,
          py_function=IFloat.__pow__).put_into(class_float)
        #TODO: __abs__
        #TODO: __nonzero__ ??? #For truth value testing
        #The prefix operator
        prefix_args = ArgumentList([NodeFuncArg('self', class_float)])
        W('__neg__', prefix_args, class_float,
          py_function=IFloat.__neg__).put_into(class_float)
        #comparison operators
        W('__lt__', binop_args, CLASS_BOOL,
          py_function=IFloat.__lt__).put_into(class_float)
        W('__le__', binop_args, CLASS_BOOL,
          py_function=IFloat.__le__).put_into(class_float)
        W('__eq__', binop_args, CLASS_BOOL,
          py_function=IFloat.__eq__).put_into(class_float)
        W('__ne__', binop_args, CLASS_BOOL,
          py_function=IFloat.__ne__).put_into(class_float)
        W('__gt__', binop_args, CLASS_BOOL,
          py_function=IFloat.__gt__).put_into(class_float)
        W('__ge__', binop_args, CLASS_BOOL,
          py_function=IFloat.__ge__).put_into(class_float)
        #Special function for access to derivative
        W('__diff__', prefix_args, class_float,
          py_function=IFloat._diff_static,
          accept_unknown_values=True).put_into(class_float)
        #Special function for assignment
        W('__assign__', binop_args, CLASS_NONETYPE,
          py_function=IFloat._assign,
          accept_unknown_values=True).put_into(class_float)
        #Printing
        W('__str__', prefix_args, CLASS_STRING,
          py_function=IFloat._str,
          codegen_name='Float.__str__').put_into(class_float)
        #return the class object
        return class_float

    #arithmetic operators
    def __add__(self, other):
        return IFloat(self.value + other.value)
    def __sub__(self, other):
        return IFloat(self.value - other.value)
    def __mul__(self, other):
        return IFloat(self.value * other.value)
    def __div__(self, other):
        return IFloat(self.value / other.value)
    __truediv__ = __div__ #for division from Python
    def __mod__(self, other):
        return IFloat(self.value % other.value)
    def __pow__(self, other):
        return IFloat(self.value ** other.value)
    def __neg__(self):
        return IFloat(-self.value)

    #comparison operators
    def __lt__(self, other):
        return IBool(self.value < other.value)
    def __le__(self, other):
        return IBool(self.value <= other.value)
    def __eq__(self, other):
        return IBool(self.value == other.value)
    def __ne__(self, other):
        return IBool(self.value != other.value)
    def __gt__(self, other):
        return IBool(self.value > other.value)
    def __ge__(self, other):
        return IBool(self.value >= other.value)

    @staticmethod
    def _diff_static(self):
        '''
        Return time derivative of state variable. Called for '$' operator
        Create the variable that contains the derivative if necessary.

        Function has to be static because self may be an ast.Node; this
        method is responsible to create a good error message in this case.
        '''
        #Precondition: $ acts upon a variable
        if(not isinstance(self, IFloat) or #no expression(ast.Node
           self.parent is None or          #no anonymous intermediate value
           not issubclass(self.role, RoleVariable)): #no constant or parameter or unknown
            raise UserException('Only named variables can have derivatives.')
        #create time derivative if necessary
        if self.time_derivative is None:
            make_derivative(self)
        #return the associated derived variable
        return self.time_derivative() #IGNORE:E1102

    def _assign(self, other):
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
    def _str(self):
        '''Called from Siml'''
        istr = IString(self.value)
        return istr

#The class object used in Siml to create instances of IFloat
CLASS_FLOAT = IFloat.create_class_object()

#create the special variable time
TIME = IFloat()
TIME.role = RoleAlgebraicVariable
TIME.is_known = True



#-------------- Service -------------------------------------------------------------------
class PrintFunction(CallableObject):
    '''
    The print function object.

    The print function takes an arbitrary number of positional arguments.
    For each argument print calls its '__str__' function to create a text
    representation of the object.

    In constant sections it will immediately produce text output. If an
    argument does not have a '__str__' function it user Python's str().
    When the compiler collects (generates) code, it will create
    a call to the print function (in the runtime).
    '''
    def __init__(self):
        CallableObject.__init__(self, 'print')
        self.codegen_name = 'print'

    def __call__(self, *args, **kwargs):
        if INTERPRETER.is_collecting_code():
            #create code that prints at runtime
            new_args = []
            for arg1 in args:
                #call argument's the __str__ method, the expression visitor
                #may (will probably) return an unevaluated function call.
                #This will transform a call to a user-defined __str__ method
                #into calls to fundamental __str__ methods
                str_func = arg1.type().get_attribute('__str__')
                str_call = NodeFuncCall(str_func, [arg1], {}, None)
                str_expr = INTERPRETER.expression_visitor.eval(str_call)
                new_args.append(str_expr) #collect the call's result
            #create a new call to the print function
            print_call = NodeFuncCall(self, new_args, {}, None)
            decorate_call(print_call, CLASS_NONETYPE)
            return print_call
        else:
            #execute the print statement.
            line = ''
            for arg1 in args:
                try:
                    #Try to call the Siml '__str__' function
                    str_func = arg1.get_attribute('__str__')
                    arg1_str = INTERPRETER.expression_visitor.apply(
                                    str_func, tuple(), {}).value
                except (UndefinedAttributeError, AttributeError,
                        UnknownArgumentsException):
                    #Convert to string with Python's 'str' function
                    arg1_str = str(arg1)
                line += arg1_str
            print line
            return NONE



class GraphFunction(CallableObject):
    '''
    The graph special-function.

    ARGUMENTS
    ---------
    Positional arguments:
    The graph function takes an arbitrary number of positional arguments.
    These values must be Floats that were created with a data statement, and
    whose values are also recorded during the solution process. The arguments
    are interpreted as all recorded values during the solution process, and
    not as a single value at a speciffic moment in time like variables
    normally are interpreted.

    However, the Python implementation here does nothing. The code generator
    generates a call to a function/method of the runtime when it sees
    a call to this function. (This case is treated specially in the code
    generator.)


    Keyword arguments:
    title: String
        The title of the graph, shown at the top.
    '''
    #TODO: express this in Siml code, needs
    #      *args, **kwargs, isrecorded, isinstance, all_values
    def __init__(self):
        CallableObject.__init__(self, 'graph')
        self.codegen_name = 'graph'

    def __call__(self, *args, **kwargs):
        if INTERPRETER.is_collecting_code():
            #we generate code:
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

            #create a new call to the graph function and return it (unevaluated)
            graph_call = NodeFuncCall(self, args, kwargs, None)
            decorate_call(graph_call, CLASS_NONETYPE)
            return graph_call
        else:
            #If invoked at compile time create error.
            raise UserException('The "graph" function can only be called '
                                'when code is generated.')



def wsiml_save(file_name=None):
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
    if INTERPRETER.is_collecting_code():
        #create unevaluated function call indirectly
        raise UnknownArgumentsException('Exception to create function call.')
    else:
        #If invoked at compile time create error.
        raise UserException('The "store" function can only be called '
                            'when code is generated.')



def wsiml_solution_parameters(duration=None, reporting_interval=None):
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
    if INTERPRETER.is_collecting_code():
        #create unevaluated function call indirectly
        raise UnknownArgumentsException('Exception to create function call.')
    else:
        #If invoked at compile time create error.
        raise UserException('The "store" function can only be called '
                            'when code is generated.')



def wsiml_isinstance(in_object, class_or_type_or_tuple):
    '''
    isinstance(...) function for Siml.
    This function evaluates always at compile time, and never creates any code.
    '''
    return IBool(siml_isinstance(in_object, class_or_type_or_tuple))



#def wsiml_replace_attr(old, new):
#    '''
#    Take old object out of its parent, and put new object in its place
#
#    This function evaluates always at compile time, and never creates any code,
#    but its side effects change code that will be generated.
#
#    The function does not change the parent attribute. Therefore objects
#    modified with replace(...) are not exactly like normally created objects.
#
#    TODO: remove this function after make_derivative(variable, derivative=None) is implemented.
#    '''
#    if not isinstance(old, InterpreterObject) or \
#       old.parent is None or old.parent() is None:
#        raise UserException('1st argument "old" must be an existing object '
#                            '(usually created with a "data" statement), \n'
#                            'and it must have a living parent object.')
#    if not isinstance(new, InterpreterObject):
#        raise UserException('2nd argument "new" must be an existing object'
#                            '(usually created with a "data" statement).')
#    parent = old.parent()
#    name = parent.find_name(old)
#    parent.replace_attribute(name, new)


def create_built_in_lib():
    '''
    Returns module with objects that are built into interpreter.
    '''
    Arg = NodeFuncArg
    WFunc = BuiltInFunctionWrapper

    lib = IModule()
    lib.name = '__built_in__'

    #built in constants
    lib.create_attribute('None', NONE)
    lib.create_attribute('True', TRUE)
    lib.create_attribute('False', FALSE)
    lib.create_attribute('time', TIME)
    #basic data types
    lib.create_attribute('NoneType', CLASS_NONETYPE)
    lib.create_attribute('Bool', CLASS_BOOL)
    lib.create_attribute('String', CLASS_STRING)
    lib.create_attribute('Float', CLASS_FLOAT)
    #built in functions
    lib.create_attribute('print', PrintFunction())
    lib.create_attribute('graph', GraphFunction())
    WFunc('save', ArgumentList([Arg('file_name', CLASS_STRING)]),
          return_type=CLASS_NONETYPE,
          py_function=wsiml_save,
          codegen_name='save').put_into(lib)
    WFunc('solution_parameters',
          ArgumentList([Arg('duration', CLASS_FLOAT),
                        Arg('reporting_interval', CLASS_FLOAT)]),
          return_type=CLASS_NONETYPE,
          py_function=wsiml_solution_parameters,
          codegen_name='solution_parameters').put_into(lib)
    WFunc('isinstance',
          ArgumentList([Arg('in_object'),
                        Arg('class_or_type_or_tuple')]),
          return_type=CLASS_BOOL,
          accept_unknown_values=True,
          py_function=wsiml_isinstance).put_into(lib)
#    WFunc('replace_attr',
#          ArgumentList([Arg('old'), Arg('new')]),
#          return_type=CLASS_NONETYPE,
#          accept_unknown_values=True,
#          py_function=wsiml_replace_attr).put_into(lib)
    #math
    #TODO: replace by Siml function sqrt(x): return x ** 0.5 # this is more simple for units
    WFunc('sqrt', ArgumentList([Arg('x', CLASS_FLOAT)]),
          return_type=CLASS_FLOAT,
          py_function=lambda x: IFloat(math.sqrt(x.value)),
          codegen_name='sqrt').put_into(lib)
    WFunc('sin', ArgumentList([Arg('x', CLASS_FLOAT)]),
          return_type=CLASS_FLOAT,
          py_function=lambda x: IFloat(math.sin(x.value)),
          codegen_name='sin').put_into(lib)
    WFunc('cos', ArgumentList([Arg('x', CLASS_FLOAT)]),
          return_type=CLASS_FLOAT,
          py_function=lambda x: IFloat(math.cos(x.value)),
          codegen_name='cos').put_into(lib)
    WFunc('max', ArgumentList([Arg('a', CLASS_FLOAT), Arg('b', CLASS_FLOAT)]),
          return_type=CLASS_FLOAT,
          py_function=lambda a, b: IFloat(max(a.value, b.value)),
          codegen_name='max').put_into(lib)
    WFunc('min', ArgumentList([Arg('a', CLASS_FLOAT), Arg('b', CLASS_FLOAT)]),
          return_type=CLASS_FLOAT,
          py_function=lambda a, b: IFloat(min(a.value, b.value)),
          codegen_name='min').put_into(lib)

    return lib

#the module of built in objects
#BUILT_IN_LIB = create_built_in_lib()



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


def make_proxy(in_obj):
    '''
    Return a proxy object.

    Will create a weakref.proxy object from normal objects and from
    weakref.ref objects. If in_obj is already a proxy it will be returned.
    '''
    if isinstance(in_obj, weakref.ProxyTypes):
        return in_obj
    elif isinstance(in_obj, weakref.ReferenceType):
        return weakref.proxy(in_obj())
    else:
        return weakref.proxy(in_obj)


def siml_callable(siml_object):
    '''Test if an object is callable'''
    return isinstance(siml_object, CallableObject)



def siml_isinstance(in_object, class_or_type_or_tuple):
    '''
    Check if an object's type is in class_or_type_or_tuple.

    isinstance(...) but inside the SIML language.

    If in_object is an expression, which would evaluate to an object of the
    correct type, the function returns True.

    TODO: rename to: siml_istype
    TODO: create new function siml_isinstance(...) which checks at compile
          time if object is really an instance of a certain type; excluding
          unevaluated function calls.
    '''
    #the test: use siml_issubclass() on type attribute
    if in_object.type is not None:
        return siml_issubclass(in_object.type(), class_or_type_or_tuple)
    else:
        return False


def siml_issubclass(in_type, class_or_type_or_tuple):
    '''issubclass(...) but inside the SIML language'''
    #precondition: must be a SIML type
    if not isinstance(in_type, TypeObject):
        raise Exception('Argument "in_type" must be TypeObject.')
    #always create tuple of class objects
    if not isinstance(class_or_type_or_tuple, tuple):
        class_or_type_or_tuple = (class_or_type_or_tuple,)
    #the test: there is no inheritance, so it is simple
    return (in_type in class_or_type_or_tuple)


def siml_setknown(siml_obj):
    '''Set decoration to express that the object is a known value.'''
    assert isinstance(siml_obj, InterpreterObject), \
           'Function only works with InterpreterObject instances.'
    siml_obj.role = RoleConstant
    siml_obj.is_known = True
    #TODO: use everywhere

def siml_isknown(siml_obj):
    '''
    Test if an object is a known value, or an unevaluated expression.

    RETURNS
    -------
    True:  argument is a known Siml value.
    False: argument is an unevaluated expression or an unknown variable.
    '''
    assert isinstance(siml_obj, (InterpreterObject, NodeFuncCall,
                                 NodeOpInfix2, NodeOpPrefix1,
                                 NodeParentheses)), \
           'Function only works with Siml objects and ast.Node.'
    if(isinstance(siml_obj, InterpreterObject) and
       siml_isrole(siml_obj.role, RoleConstant) and siml_obj.is_known):
        return True
    else:
        return False


def siml_isrole(role1, role2_or_tuple):
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
        if issubclass(role1, rank_list[index1]):
            break
    else:
        raise ValueError('Unknown role %s' % str(role1))
    #classify role2
    for index2 in range(len(rank_list)):
        if issubclass(role2, rank_list[index2]):
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
        if is_role_more_variable(arg.role, max_var_role):
            max_var_role = arg.role
        if arg.role is RoleUnkown:
            raise ValueError('RoleUnkown is illegal in arguments of '
                             'fundamental functions.')
    #convert: state variable, time differential --> algebraic variable
    #These two roles result only from taking time differentials
    if siml_isrole(max_var_role, RoleVariable):
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
    tree.role = new_role
    if isinstance(tree, FundamentalObject):
        return
    for attr in tree.attributes.itervalues():
        if is_role_more_variable(attr.role, new_role):
            set_role_recursive(attr, new_role)


def decorate_call(call, return_type):
    '''
    Decorate function calls nodes.

    This method works with all ast.Node objects that are similar to
    function calls.
    '''
    #The call gets the same attributes like unknown variables
    call.type = return_type
    if not return_type is CLASS_NONETYPE:
        call.is_known = False
        #Choose most variable role: const -> param -> variable
        call.role = determine_result_role(call.arguments, call.keyword_arguments)
    else:
        #special rule for calls that return None. This value is offcourse a known constant
        call.is_known = True
        call.role = RoleConstant

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



class ExpressionVisitor(object):
    '''
    Compute value of an expression.

    Each vistit_* function evaluates one type of AST-Node recursively.
    The functions return the (partial) expression's value. This value is either
    an Interpreter object, or a further annotated AST-tree.

    The right function is selected with the inherited function
        self.eval(...)
    '''
    def __init__(self):
        #the places where attributes are stored (the symbol tables)
        self.environment = None

    def set_environment(self, new_env):
        '''Change part of the symbol table which is currently used.'''
        self.environment = new_env

    def visit_InterpreterObject(self, node):
        '''Visit a part of the expression that was already evaluated:
        Do nothing, return the interpreter object.'''
        return node

    def visit_NodeFloat(self, node):
        '''Create floating point number'''
        result = IFloat(node.value)
        return result

    def visit_NodeString(self, node):
        '''Create string'''
        result = IString(node.value)
        return result

    def visit_NodeIdentifier(self, node):
        '''Lookup Identifier and get attribute'''
        attr = self.environment.get_attribute(node.name)
        return attr

    def visit_NodeAttrAccess(self, node):
        '''Evaluate attribute access; ('.') operator'''
        #evaluate the object on the left hand side
        inst_lhs = self.eval(node.arguments[0])
        #the object on the right hand side must be an identifier
        id_rhs = node.arguments[1]
        if not isinstance(id_rhs, NodeIdentifier):
            raise UserException('Expecting identifier on right side of "." operator',
                                node.loc)
        #get attribute from object on lhs
        attr = inst_lhs.get_attribute(id_rhs.name)
        return attr


    def visit_NodeParentheses(self, node):
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
#            new_node.type = val_expr.type
#            new_node.role = val_expr.role
#            new_node.is_known = False
            return new_node


    _prefopt_table = { '-' :'__neg__',
                      'not':'__not__',
                      '$':'__diff__', }

    def visit_NodeOpPrefix1(self, node):
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
        func_name = ExpressionVisitor._prefopt_table[node.operator]
        #get the special method from the operand's class and try to call the method.
        func = inst_rhs.type().get_attribute(func_name)
        try:
            result = self.apply(func, (inst_rhs,))
            return result
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated expression
            new_node = NodeOpPrefix1(node.operator, (inst_rhs,), node.loc)
            #put on decoration
            new_node.function = func
            decorate_call(new_node, func.return_type)
#            #new_node.function_object = func
#            new_node.type = func.return_type
#            new_node.is_known = False
#            #Take the role from the argument
#            new_node.role = inst_rhs.role
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
                   'and':('__and2__', '__rand2__'),
                    'or':('__or2__', '__ror2__'),
                    }

    def visit_NodeOpInfix2(self, node):
        '''
        Evaluate binary operator and return result

        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : Role taken from the argument with the most variable role
        - Node.is_known=False  : For consistency; the function call can pose as an
                                   unknown value, that has been already computed.

        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are specified
                                   keyword arguments
        '''
        #compute values on rhs and lhs of operator
        inst_lhs = self.eval(node.arguments[0])
        inst_rhs = self.eval(node.arguments[1])
        #look at the operator symbol and determine the right method name(s)
        lfunc_name, rfunc_name = ExpressionVisitor._binop_table[node.operator]
        #get the special method from the LHS's class and try to call the method.
        func = inst_lhs.type().get_attribute(lfunc_name)
        try:
            result = self.apply(func, (inst_lhs, inst_rhs))
            return result
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated expression
            new_node = NodeOpInfix2(node.operator, (inst_lhs, inst_rhs), node.loc)
            #put on decoration
            new_node.function = func
            decorate_call(new_node, func.return_type)
#            #new_node.function_object = func
#            new_node.type = func.return_type
#            new_node.is_known = False
#            #Choose most variable role: const -> param -> variable
#            new_node.role = determine_result_role((inst_lhs, inst_rhs))
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



    def visit_NodeFuncCall(self, node):
        '''
        Evaluate a NodeFuncCall, which calls a call-able object (function).
        Execute the callable's code and return the return value.

        Expressions (ast.Node) with unknown variables get the following annotations:
        - Node.type              : type of function's result
        - Node.role              : role of return value, the roles of the function's
                                   arguments are inspected, and the most variable role
                                   is taken as the role of the return value.
        - Node.is_known=False  : For consistency; the function call can pose as an
                                   unknown value, that has been already computed.

        - Node.name              : The function object that would be called if the
                                   arguments were known.
        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are currently
                                   keyword arguments
       '''
        #find the right call-able object
        func_obj = self.eval(node.function)
        if not isinstance(func_obj, CallableObject):
            raise UserException('Expecting callable object!', node.loc)

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
            decorate_call(new_call, func_obj.return_type)
            return new_call


    def apply(self, func_obj, posargs=tuple(), kwargs={}): #IGNORE:W0102
        '''
        Execute a function. 
        
        User defined and built in functions are both executed here.
        All arguments must be evaluated. 
        
        TODO: common functionality of function application should go here
        '''
        #Get function from bound method and put self into arguments
        if isinstance(func_obj, BoundMethod):
            posargs = (func_obj.this,) + posargs
            func_obj = func_obj.function
            
        #TODO type checking of arguments (and removal from apply_***)
        
        if isinstance(func_obj, SimlFunction):
            ret_val = self.apply_siml(func_obj, posargs, kwargs)
        else:
            ret_val = func_obj(*posargs, **kwargs) # pylint: disable-msg=W0142
        
        #TODO type checking of return value (and removal from apply_***)
        return ret_val
    
    
    def apply_siml(self, func_obj, posargs, kwargs):
        '''
        Execute a user defined function.
        
        TODO: find common functionality with execution of built in functions
        '''
        #parse the arguments that we get from the caller, do type checking
        parsed_args = func_obj.argument_definition\
                          .parse_function_call_args(posargs, kwargs)

        #Take 'this' name-space from the 'this' argument.
        # 'this' must be a Siml object, no unevaluated expression
        this_namespace = parsed_args.get('this', None)
        if this_namespace and not isinstance(this_namespace, InterpreterObject):
            raise UserException('The "this" argument of methods '
                                'must be a known Siml object.')

        #Count calls for making nice name spaces for persistant locals
        func_obj.call_count += 1
        #create local name space (for function arguments and local variables)
        if INTERPRETER.is_collecting_code():
            #store local scope so local variables are accessible for
            #code generation
            local_namespace = func_obj.create_persistent_locals_ns()
        else:
            local_namespace = InterpreterObject()
        #put the function arguments into the local name-space
        for arg_name, arg_val in parsed_args.iteritems():
            #create references for existing Siml values
            if isinstance(arg_val, InterpreterObject):
                local_namespace.create_attribute(arg_name, arg_val)
            #for unevaluated expressions a new variable is created,
            #and the expression is assigned to it
            else:
                arg_class = arg_val.type()
                new_arg = arg_class()
                new_arg.role = arg_val.role
                #put object into local name-space and assign value to it
                local_namespace.create_attribute(arg_name, new_arg)
                INTERPRETER.statement_visitor.assign(new_arg, arg_val, None)

        #Create new environment for the function.
        new_env = ExecutionEnvironment()
        new_env.global_scope = func_obj.global_scope #global scope from function definition.
        new_env.this_scope = this_namespace
        new_env.local_scope = local_namespace
        #local variables in functions can take any role
        new_env.default_data_role = RoleUnkown

        #execute the function's code in the new environment.
        INTERPRETER.push_environment(new_env)
        try:
            INTERPRETER.run(func_obj.statements)
        except ReturnFromFunctionException:           #IGNORE:W0704
            pass
        INTERPRETER.pop_environment()
        #the return value is stored in the environment (stack frame)
        ret_val = new_env.return_value

        #TODO: simplify!
        #Test if returned object has the right type.
        #No return type specification present - no check
        if func_obj.return_type is None:
            return ret_val
        #there is a return type specification - enforce it
        elif (ret_val.type is not None and
              siml_issubclass(ret_val.type(), func_obj.return_type())):
            return ret_val
        raise UserException("The type of the returned object does not match "
                            "the function's return type specification.\n"
                            "Type of returned object: %s \n"
                            "Specified return type  : %s \n"
                            % (str(ret_val.type().name),
                               str(func_obj.return_type().name)))
        
        
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
            return self.visit_InterpreterObject(expr_node)
        elif isinstance(expr_node, NodeFloat):
            return self.visit_NodeFloat(expr_node)
        elif isinstance(expr_node, NodeString):
            return self.visit_NodeString(expr_node)
        elif isinstance(expr_node, NodeIdentifier):
            return self.visit_NodeIdentifier(expr_node)
        elif isinstance(expr_node, NodeAttrAccess):
            return self.visit_NodeAttrAccess(expr_node)
        elif isinstance(expr_node, NodeParentheses):
            return self.visit_NodeParentheses(expr_node)
        elif isinstance(expr_node, NodeOpPrefix1):
            return self.visit_NodeOpPrefix1(expr_node)
        elif isinstance(expr_node, NodeOpInfix2):
            return self.visit_NodeOpInfix2(expr_node)
        elif isinstance(expr_node, NodeFuncCall):
            return self.visit_NodeFuncCall(expr_node)
        else:
            raise Exception('Unknown node type for expressions: ' 
                            + str(type(expr_node)))
        
        
        
class StatementVisitor(object):
    '''
    Execute statements

    Each vistit_* function executes one type of statement (AST-Node).
    The functions do not return any value, they change the state of the
    interpreter. Usually they create or modify the attributes of the current
    local scope (self.environment.local_scope).

    The right function is selected with the inherited function
        self.exec_(...)
    '''
    def __init__(self, interpreter, expression_visitor):
        #the interpreter top level object - necessary for return statement
        self.interpreter = interpreter
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        #object to evaluate expressions
        self.expression_visitor = expression_visitor

    def set_environment(self, new_env):
        '''Change part of the symbol table which is currently used.'''
        self.environment = new_env
        #self.expression_visitor.set_environment(new_env)

    def visit_NodePassStmt(self, _node): 
        '''
        Interpret 'pass' statement. Do nothing.
        The pass statement is necessary to define empty compound statements
        (if, func, class).
        '''
        return

    def visit_NodeReturnStmt(self, node):
        '''Return value from function call'''
        if len(node.arguments) == 0:
            #no return value
            self.environment.return_value = NONE
        else:
            #evaluate expression to compute return value
            retval = self.expression_visitor.eval(node.arguments[0])
            self.environment.return_value = retval
        #Forcibly end function execution -
        #exception is caught in ExpressionVisitor.visit_NodeFuncCall(...)
        #TODO: transport return value with the exception?
        raise ReturnFromFunctionException(loc=node.loc)


    def visit_NodeExpressionStmt(self, node):
        '''Intened to call functions. Compute expression and forget result'''
        ret_val = self.expression_visitor.eval(node.expression)
        if ret_val is None or isinstance(ret_val, InterpreterObject):
            #function was evaluated at compile time, forget result
            return
        elif isinstance(ret_val, (NodeFuncCall, NodeOpInfix2, NodeOpPrefix1,
                                  NodeParentheses)):
            #TODO: remove all statements that have no effect, and warn about it
            #TODO: accept only calls to the print and graph functions
            #there is an unevaluated expression - create some code that
            #evaluates it at runtime
            if not self.interpreter.is_collecting_code():
                raise UserException('Computations with unknown values are '
                                    'illegal here.', node.loc)
            new_stmt = NodeExpressionStmt(ret_val, node.loc)
            self.interpreter.collect_statement(new_stmt)
        else:
            raise UserException('Illegal expression.', node.loc)


    def visit_NodeAssignment(self, node):
        '''Assign value to a constant object, or emit assignment statement
        for code generation'''
        #compute value of expression on right hand side
        expr_val = self.expression_visitor.eval(node.expression)
        #get a data attribute to store the value
        target_obj = self.expression_visitor.eval(node.target)
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
        assign_func = target.get_attribute('__assign__')
        #Always call the function when it is not fundamental. The call
        #generates statements with fundamental functions.
        #Reason: When a function returns a user defined class, the role is
        #often role_unknown. The leaf attributes however, that are fundamental
        #types, have correct roles.
        #Also only assignments to leaf types must get to the code generator.
        if not assign_func.is_fundamental_function:
            self.expression_visitor.apply(assign_func, (value,))
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
                self.expression_visitor.apply(assign_func, (value,))
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
        self.interpreter.collect_statement(new_assign)


    def visit_NodeIfStmt(self, node):
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
        if self.interpreter.is_collecting_code():
            is_collecting_code = True
            new_if = NodeIfStmt(None, node.loc)
        try:
            #A clause consists of: <condition>, <list of statements>.
            #This is inspired by Lisp's 'cond' special-function.
            #http://www.cis.upenn.edu/~matuszek/LispText/lisp-cond.html
            for clause in node.clauses:
                #interpret the condition
                condition_ev = self.expression_visitor.eval(clause.condition)
                if not siml_isinstance(condition_ev, (CLASS_BOOL, CLASS_FLOAT)):
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
                    self.interpreter.push_statement_list(new_clause.statements)
                #interpret the statements
                self.interpreter.run(clause.statements)
                #Tell interpreter to put generated statements into previous location
                if is_collecting_code:
                    self.interpreter.pop_statement_list()

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
                self.interpreter.collect_statement(stmt)
            new_if = None

        #Store generated if statement in interpreter
        if new_if is not None:
            self.interpreter.collect_statement(new_if)
        return


    def visit_NodeFuncDef(self, node):
        '''Add function object to local namespace'''
        #ArgumentList does the argument parsing at the function call
        #evaluate the type specifications and the default arguments
        arguments_ev = ArgumentList(node.arguments)\
                       .evaluate_args(self.interpreter)
        #Evaluate the return type
        return_type_ev = None
        if node.return_type is not None:
            return_type_ev = self.expression_visitor.eval(node.return_type)
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
        new_func = SimlFunction(node.name, arguments_ev, return_type_ev,
                                node.statements, global_scope)
        #put function object into the local namespace
        self.environment.local_scope.create_attribute(node.name, new_func)


    def visit_NodeClassDef(self, node):
        '''Define a class - create a class object in local name-space'''
        #create new class object and put it into the local name-space
        new_class = SimlClass(node.name, bases=None,
                              statements=node.statements, loc=node.loc)
        self.environment.local_scope.create_attribute(node.name, new_class)


    def visit_NodeStmtList(self, node):
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
        class_obj = self.expression_visitor.eval(node.class_spec)
        if not isinstance(class_obj, TypeObject):
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
        self.environment.local_scope.create_attribute(new_name, new_object)


    def visit_NodeCompileStmt(self, node):
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
        class_obj = self.expression_visitor.eval(node.class_spec)
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
                                     ArgumentList([NodeFuncArg('this')]),
                                     None, statements=[],
                                     global_scope=BUILT_IN_LIB),
                  ),
             Node(#target_roles=(RoleParameter, RoleVariable, RoleConstant),
                  call_argument_role=RoleParameter,
                  proto=SimlFunction('initialize',
                                     ArgumentList([NodeFuncArg('this')]),
                                     None, statements=[],
                                     global_scope=BUILT_IN_LIB)),
             Node(#target_roles=(RoleVariable, RoleConstant),
                  call_argument_role=None,
                  proto=SimlFunction('final',
                                     ArgumentList([NodeFuncArg('this')]),
                                     None, statements=[],
                                     global_scope=BUILT_IN_LIB))]
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
                                              attr.argument_definition.copy(),
                                              None, statements=[],
                                              global_scope=BUILT_IN_LIB)
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
                func_flat = SimlFunction(func_name, ArgumentList([NodeFuncArg('this')]),
                                         None, statements=[], global_scope=BUILT_IN_LIB)
                flat_object.create_attribute(DotName(func_name), func_flat)
                print 'Warning: main function %s is not defined.' % str(func_name)
                continue

            #create argument list for call to main function
            args_list = []
            args_role = spec.call_argument_role
            for i, arg_def in enumerate(spec.proto.argument_definition.arguments):
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
            self.interpreter.start_collect_code(func_locals=func_locals)
                                                #assign_target_roles=legal_roles)
            self.interpreter.expression_visitor.apply(func_tree, tuple(args_list), {})  
            stmt_list, dummy = self.interpreter.stop_collect_code()
            #create a new main function for the flat object with the collected code
            func_flat = SimlFunction(func_name, spec.proto.argument_definition,
                                     None, statements=stmt_list,
                                     global_scope=BUILT_IN_LIB)
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
                #FundamentalObject are the only data types of the compiled code
                if isinstance(data, FundamentalObject):
                    #do not flatten constants
                    if not issubclass(data.role, (RoleParameter, RoleVariable)):
                        continue
                    flat_obj.create_attribute(long_name, data, reparent=True)
                #Recurse all other objects and see if they contain FundamentalObject attributes
                else:
                    flatten(data, flat_obj, long_name)

        #flatten regular data first
        flatten(tree_object, flat_object, DotName())
        #flatten local variables
        flatten(func_locals, flat_object, DotName('__func_local__'))

        #store new object in interpreter
        self.interpreter.add_compiled_object(flat_object)

    
    def exec_(self, stmt_list):
        '''
        Interpret a list of statements.

        Call right handler function for a single statement.
        '''
        try:
            for node in stmt_list:
                if isinstance(node, NodePassStmt):
                    self.visit_NodePassStmt(node)
                elif isinstance(node, NodeReturnStmt):
                    self.visit_NodeReturnStmt(node)
                elif isinstance(node, NodeExpressionStmt):
                    self.visit_NodeExpressionStmt(node)
                elif isinstance(node, NodeAssignment):
                    self.visit_NodeAssignment(node)
                elif isinstance(node, NodeIfStmt):
                    self.visit_NodeIfStmt(node)
                elif isinstance(node, NodeFuncDef):
                    self.visit_NodeFuncDef(node)
                elif isinstance(node, NodeClassDef):
                    self.visit_NodeClassDef(node)
                elif isinstance(node, NodeStmtList):
                    self.visit_NodeStmtList(node)
                elif isinstance(node, NodeCompileStmt): 
                    self.visit_NodeCompileStmt(node)
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


        
#the module of built in objects
BUILT_IN_LIB = IModule() #just for pyparsings's code completion
#The one and only interpreter
INTERPRETER = None

class Interpreter(object):
    '''
    Interpret the constant parts of the program

    Contains some high-level entry points for the interpreter algorithm;
    and also data that is shared between different components of the
    interpreter. (Example: Frame stack)

    These methods are used from outside (to start the interpreter) as
    well as from inside the interpreter (to coordinate between StatementVisitor
    and expression visitor).
    '''
    def __init__(self):
        #object that interprets expressions
        self.expression_visitor = ExpressionVisitor()
        #object that interprets a single statement
        self.statement_visitor = StatementVisitor(self, self.expression_visitor)
        #the built in objects
        #TODO: this global variable should go away some day
        global BUILT_IN_LIB
        BUILT_IN_LIB = create_built_in_lib()
        self.built_in_lib = BUILT_IN_LIB
        #directory of modules - the symbol table
        self.modules = {}
        #frame stack - should never be empty: top element is automatically
        # put into self.statement_visitor
        self.env_stack = []
        self.push_environment(ExecutionEnvironment())
#        #roles that are currently legal as targets in assignment statements
#        self.assign_target_roles = (RoleConstant,)

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


    # --- code collection - compile statement ------------------------------------------------------
    def start_collect_code(self, stmt_list=None, func_locals=None, ):
#                           assign_target_roles=(RoleVariable, RoleConstant)):
        '''
        Set up everything for the code collection process

        ARGUMENTS
        ---------
        stmt_list: list/None
            List where the generated statements will be appended to.
        func_locals: InterpreterObject/None
            Namespace where each function's local variables will be stored.
        TODO: remove! assign_target_roles: (AttributeRole, ...)
            Roles that are currently legal for attributes that are targets
            (LHS) of assignment statements. (For example in the dynamic(...)
            method only intermediate variables and time differentials
            (RoleIntermediateVariable, RoleTimeDifferential) can be assigned
            to.
        '''
        self.compile_stmt_collect = [[]] if stmt_list is None \
                                       else [stmt_list]
        self.locals_storage = InterpreterObject() if func_locals is None \
                                                  else func_locals
#        self.assign_target_roles = assign_target_roles

    def stop_collect_code(self, ): #assign_target_roles=(RoleConstant,)):
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
#        self.assign_target_roles = assign_target_roles
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
        mod = IModule()
        mod.name = module_name
        mod.source_file_name = file_name
        #put module into root namespace (symbol table)
        self.modules[module_name] = mod
        #add built in attributes to model
        mod.attributes.update(self.built_in_lib.attributes)
        #set up stack frame (execution environment)
        env = ExecutionEnvironment()
        env.global_scope = make_proxy(mod)
        env.local_scope = make_proxy(mod)
        #Data attributes on module level are by default constants
        env.default_data_role = RoleConstant
        #put the frame on the frame stack
        self.push_environment(env)
        #parse the program text
        prs = simlparser.Parser()
        ast = prs.parseModuleStr(text, file_name, module_name)
        #execute the statements - interpret the AST
        self.run(ast.statements)
        #remove frame from stack
        self.pop_environment()

    def run(self, stmt_list):
        '''Interpret a list of statements'''
        self.statement_visitor.exec_(stmt_list)


    # --- manage frame stack --------------------------------------------------------------
    def push_environment(self, new_env):
        '''
        Put new stack frame on stack.
        Change environment in all visitors.
        '''
        self.env_stack.append(new_env)
        self.statement_visitor.set_environment(new_env)
        self.expression_visitor.set_environment(new_env)

    def pop_environment(self):
        '''
        Remove one stack frame from stack.
        Change environment in all visitors.
        '''
        old_env = self.env_stack.pop()
        new_env = self.env_stack[-1]
        self.statement_visitor.set_environment(new_env)
        self.expression_visitor.set_environment(new_env)
        return old_env

    def get_environment(self):
        '''Return the current (topmost) environment from the stack.'''
        return self.env_stack[-1]


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
        mod = IModule()
        mod.name = 'test'
        #put module into root namespace (symbol table)
        self.modules[mod.name] = mod
        mod.attributes.update(self.built_in_lib.attributes)
        #set up stack frame (execution environment)
        env = ExecutionEnvironment()
        env.global_scope = make_proxy(mod)
        env.local_scope = make_proxy(mod)
        #put the frame on the frame stack
        self.push_environment(env)



if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add doctest tests.
    pass