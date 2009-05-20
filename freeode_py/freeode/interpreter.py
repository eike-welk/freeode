# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2009 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Credits:                                                              *
#    Much of the semantics of this language were taken from the Python     *
#    programming language. Most information and little bits of text were   *
#    taken from the Python Reference Manual by Guido van Rossum.           *
#    Many thanks to Guido and the Python team, for their excellent         *
#    contributions to free software and free documentation.                *
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

from __future__ import division
#from __future__ import absolute_import              #IGNORE:W0410

#import copy
import weakref
from weakref import ref
import math

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
        
        
#TODO: Rename to frame?
class ExecutionEnvironment(object):
    '''
    Container for name spaces where symbols are looked up.
    Function get_attribute(...) searches the symbol in all name spaces.
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


    def get_attribute(self, dot_name, default=UndefinedAttributeError()):
        '''
        Find a dot name in this environment.

        When the name is not found an exception is raised, or a default
        value is returned.
        Tries local name space, 'this' name space, global name space.

        Arguments
        ---------
        dot_name : DotName
            Dotted name that is looked up in the different name spaces.
        default : object
            Object which is returned when dot_name can not be found.
            When argument is of type UndefinedAttributeError, an 
            UndefinedAttributeError is raised when dot_name can not be found.
        '''
        #try to find name in scope hierarchy:
        # function --> class --> module
        scopeList = [self.local_scope, self.this_scope, self.global_scope]
        attr = None
        for scope in scopeList:
            if scope is None:
                continue
            try:
                attr = scope.get_attribute(dot_name)
                return attr
            except UndefinedAttributeError: #IGNORE:W0704
                pass
        #attribute could not be found in the scopes
        if isinstance(default, UndefinedAttributeError):
            raise UndefinedAttributeError(attr_name=dot_name)
        else:
            return default            


        
class InterpreterObject(Node):
    '''
    Base class of all objects that the interpreter operates on.
    Can also be seen as part of structured symbol table
    
    It inherits from Node only to get Ascii-art tree and copying.
    
    type_ex: NodeFuncCall
        Call to class that would create the correct object. All classes are
        really templates. 
    '''
    #let these attributes appear first in the pretty printed tree  
    aa_top = ['name', 'type', 'type_ex']
    #reference to interpreter - TODO: global variables are bad
    interpreter = None
    
    def __init__(self):
        Node.__init__(self)
        #Reference to object one level up in the tree
        #type weakref.ref or None
        self.parent = None
        #The symbol table
        self.attributes = {}
        #weak reference to class of this instance
        self.type = None
        #Call to class that would create the correct object.
        self.type_ex = None
        #const, param, variable, ... (Comparable to storage class in C++)
        self.role = RoleUnkown
        #True/False was this object already assigned to
        self.is_assigned = False
        #TODO: self.save ??? True/False attribute is saved to disk as simulation result
        #TODO: self.default_value ??? (or into leaf types?)
        #TODO: self.auto_created ??? for automatically created variables that should be eliminated
  
    def create_attribute(self, name, newAttr):
        '''
        Put name into symbol table. Store newly constructed instance.
        This is called for a data statement.
        '''
        name = DotName(name)
        if name in self.attributes:
            raise DuplicateAttributeError(attr_name=name)
        self.attributes[name] = newAttr
        #set parent link for new objects, or when the parent has died.
        if newAttr.parent is None or newAttr.parent() is None: #IGNORE:E1102
            newAttr.parent = weakref.ref(self)
        
    def get_attribute(self, name):
        '''Return attribute object'''
        if name in self.attributes:
            return self.attributes[name]
        #Search for attribute in the type (class) object
        elif self.type is not None and self.type().has_attribute(name):
            #if attribute is a function, put it into a method wrapper
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
            if not curr_object.has_attribute(DotName(name1)):
                new_obj = InterpreterObject()
                curr_object.create_attribute(name1, new_obj)
                curr_object = new_obj
            else:
                curr_object = curr_object.get_attribute(DotName(name1))
        return curr_object
    

    
class CallableObject(InterpreterObject):
    '''Base class of all functions.'''
    def __init__(self, name):
        InterpreterObject.__init__(self)
        self.role = RoleConstant
        self.is_assigned = True
        self.name = DotName(name)

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
        self.is_assigned = True
        self.name = DotName(name)
        
    def __call__(self, *args, **kwargs):
        '''All Siml-classes must implement this method'''
        raise NotImplementedError('__call__ method is not implemented. Use a derived class!')
  
        
        
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
        SimpleArgumentList.__init__(self, arguments, loc)
        
        #replace type objects with weak references to them
        for arg in self.arguments:
            if isinstance(arg.type, TypeObject):
                arg.type = ref(arg.type)
    
    
    def evaluate_args(self, interpreter):
        '''
        Interpret the types and default values of the arguments.
        - type and type_ex data is looked up
        - default values are computed and must evaluate to constants
        '''
        expression_visitor = interpreter.statement_visitor.expression_visitor
        #evaluate argument type and default arguments
        for arg in self.arguments:
            if arg.type is not None:
                type_ev = expression_visitor.dispatch(arg.type)
                arg.type = ref(type_ev)
            if arg.default_value is not None:
                dval_ev = expression_visitor.dispatch(arg.default_value)
                arg.default_value = dval_ev
            #test type compatibility of default value and argument type
            if arg.type is not None and arg.default_value is not None:
                self._test_type_compatible(arg.default_value, arg)
        #raise NotImplementedError()
        return self
    
    
    def parse_function_call_args(self, args_list, kwargs_dict, loc=None):
        '''
        Executed when a function call happens.
        Fill the arguments of the call site into the arguments of the 
        function definition. Does type-checking.
        
        ARGUMENTS
        ---------
        args_list: [<siml values, AST nodes>, ...]
            Positional arguments.
        kwargs_dict: {DotName(): <siml values, AST nodes>, ...}
            Keyword arguments.
        
        RETURNS
        -------
        Dictionary of argument names and associated values.
        dict(<argument name>: <siml values, AST nodes>, ...)
        dict(DotName(): Node(), ...)
        '''
        output_dict = {} #dict(<argument name>: <siml values>, ...)
        
        #test too many positional arguments
        if len(args_list) > len(self.arguments):
            raise UserException('Function accepts at most %d arguments; %d given.'
                                % (len(self.arguments), len(args_list)), self.loc)
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
                raise UserException('Unknown argument "%s".' % in_name, self.loc)
            #test for duplicate argument assignment (positional + keyword)
            if in_name in output_dict:
                raise UserException('Duplicate argument "%s".' % in_name, self.loc)
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
                                'Remaining arguments without value: '
                                + ', '.join([str(n) for n in left_over_names]), 
                                self.loc)
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
                    'Incompatible types. Variable: "%s" '
                    'is defined as:\n %s \nHowever, argument type is: \n%s.'
                    % (arg_def.name, str(arg_def.type()), str(in_object.type())), 
                    self.loc)



#class BuiltInFunctionWrapper1(CallableObject):
#    '''
#    Represents a function written in Python; for functions like 'sqrt' and 'sin'.
#    
#    The object is callable from Python and Siml.
#    
#    When a call is invoked argument parsing is done similarly
#    to Pythons's function call. Optionally function arguments can have 
#    a type that must match too.
#        f(a:Float=2.5)
#    
#    When all arguments are known, the wrapped Python function is executed. The 
#    result of the computation is wrapped in its associated InterpreterObject
#    and returned. 
#    However if any argument is unknown, a decorated (and unevaluated) function 
#    call is returned. For operators NodeOpInfix2, NodeOpPrefix1 can be 
#    created - see arguments is_binary_op, is_prefix_op, op_symbol.
#    
#    ARGUMENTS
#    ---------
#    name
#        name of function
#    argument_definition: IntArgumentList
#        Argument definition of the function
#    return_type: TypeObject
#        Return type of the function.
#        When an unevaluated result is returned, this will be assigned to the 
#        type of the ast.Node.
#        If the return type is None, the function has no return value.
#    py_function:
#        Function that will be called when the result can be computed.
#        
#    is_binary_op: True/False
#        if True: the function is really a binary operator
#    is_prefix_op: True/False
#        if True: the function is really an unary prefix operator
#    op_symbol: str
#        The operator's symbol, for example '+'
#    
#    RETURNS
#    -------
#    Wrapped function result (InterpreterObject) or unevaluated expression 
#    (NodeFuncCall), or None
#    
#    Unevaluated expressions (ast.Node) get the following annotations:
#    - Node.type              : type of function result
#    - Node.function_object   : the function object (self)
#    - Node.role              : ???
#    - Node.name              : function's name; however function_object should 
#                               be used to identify function.
#
#    - Node.arguments         : Operators are returned with positional arguments.
#    - Node.keyword_arguments : For regular functions all arguments are specified
#                               keyword arguments
#    '''
#    def __init__(self, name, argument_definition=ArgumentList([]), 
#                             return_type=None, 
#                             py_function=lambda:None,
#                             is_binary_op=False, is_prefix_op=False, 
#                             op_symbol='*_*'):
#        CallableObject.__init__(self, name)
#        #IntArgumentList
#        self.argument_definition = argument_definition
#        #TypeObject or None
#        self.return_type = ref(return_type) if return_type is not None else None
#        #A Python function
#        self.py_function = py_function
#        
#        #--- Handling of unevaluated function calls -------------------------------
#        #TODO: maybe really store a sample ast.NodeFuncCall and copy it, instead 
#        #      of the following attributes. 
#        #      The solution would still need a flag for advising the algorithm 
#        #      to use placement arguments, because operators need placement 
#        #      arguments.
#        
#        #if True: the function is really an operator
#        self.is_binary_op = is_binary_op
#        #if True: the function is really an unary prefix operator
#        self.is_prefix_op = is_prefix_op
#        #string: The operator's symbol
#        self.op_symbol = op_symbol
#
#
#    def __call__(self, *args, **kwargs):
#        '''
#        Execute the wrapped function. 
#        
#        - Checks the arguments, incuding type checking. 
#        - If all arguments are known this function unpacks the values, and 
#        calls the wrapped function with regular Python objects as arguments. 
#        The return value is again wrapped into a Siml object.
#        - If any argument is unknown, an unevaluated function call or operator 
#        node is returned.
#        
#        ARGUMENTS
#        ---------
#        args: [InterpreterObject]
#            Positional arguments for the wrapped function
#        kwargs: {str: InterpreterObject}
#            Keyword arguments for the wrapped function
#        '''
#        loc = None
#        #try if argument definition matches
#        parsed_args = self.argument_definition\
#                          .parse_function_call_args(args, kwargs, loc)
#        #Try to get Python values out of the Siml values (unwrap).
#        py_args = {}
#        all_python_values_exist = True
#        for name, siml_val in parsed_args.iteritems():
#            if not (isinstance(siml_val, InterpreterObject) and hasattr(siml_val, 'value') and
#                    siml_val.value is not None):
#                all_python_values_exist = False
#                break
#            py_args[str(name)] = siml_val.value
#        #call the wrapped Python function if all argument values are known
#        if all_python_values_exist:
#            py_retval = self.py_function(**py_args)             #IGNORE:W0142
#            if self.return_type is not None:
#                #wrap return value in appropriate Siml object
#                siml_retval = self.return_type()(py_retval)
#                siml_retval.role = RoleConstant
#                siml_retval.is_assigned = True
#                return siml_retval
#            else:
#                return None
#        #create annotated NodeFuncCall/NodeOpInfix2/NodeOpPrefix1 if argument values are unknown
#        else:
#            #create right Node: NodeFuncCall/NodeOpInfix2/NodeOpPrefix1
#            if self.is_binary_op:
#                func_call = NodeOpInfix2()
#                func_call.operator = self.op_symbol
#            elif self.is_prefix_op:
#                func_call = NodeOpPrefix1()
#                func_call.operator = self.op_symbol
#            else:
#                func_call = NodeFuncCall()
#            #operators get positional arguments (easier for code generation)
#            if self.is_binary_op or self.is_prefix_op:     
#                func_call.arguments = args
#                func_call.keyword_arguments = kwargs #most likely empty
#            #Regular function calls get keyword arguments only.
#            #Default arguments from this function get to the code generator 
#            #this way.
#            else:
#                func_call.arguments = tuple()
#                func_call.keyword_arguments = parsed_args
#            #put on decoration
#            func_call.name = self.name
#            func_call.function_object = self
#            func_call.type = self.return_type
#            #Choose most variable role: const -> param -> variable
#            func_call.role = determine_result_role(func_call.arguments, 
#                                                   func_call.keyword_arguments)
#            func_call.is_assigned = True
#            return func_call
#        
#        
#    def put_into(self, siml_object):
#        '''Put function object into a siml_object using the right name.'''
#        siml_object.create_attribute(self.name, self)
#        return self
#    
#        #TODO: implement method create_python_function(...) that returns 
#        #      a Python function which wraps the BuiltInFunctionWrapper object.



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
    
    ARGUMENTS
    ---------
    name
        name of function
    argument_definition: IntArgumentList
        Argument definition of the function
    return_type: TypeObject
        Return type of the function.
        When an unevaluated result is returned, this will be assigned to the 
        type of the ast.Node.
        If the return type is None, the function has no return value.
    py_function:
        Function that will be called when the result can be computed.
    accept_unknown_values: True/False
        If True: call wrapped function also when arguments are unknown values.
        If False: raise UnknownArgumentsException when an unknown argument is 
        encountered.
    
    RETURNS
    -------
    Wrapped function result (InterpreterObject) or None
    '''
    def __init__(self, name, argument_definition=ArgumentList([]), 
                             return_type=None, 
                             py_function=lambda:None,
                             accept_unknown_values = False):
        CallableObject.__init__(self, name)
        #IntArgumentList
        self.argument_definition = argument_definition
        #TypeObject or None
        self.return_type = ref(return_type) if return_type is not None else None
        #A Python function
        self.py_function = py_function
        #Call wrapped function also when arguments are unknown values
        self.accept_unknown_values = accept_unknown_values


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
        loc = None
        #try if argument definition matches
        parsed_args = self.argument_definition\
                          .parse_function_call_args(args, kwargs, loc)
        #Test if all arguments are known values.
        parsed_args_2 = {}
        all_python_values_exist = True
        for name, siml_val in parsed_args.iteritems():
            if not (isinstance(siml_val, InterpreterObject) and 
                    hasattr(siml_val, 'value') and
                    siml_val.value is not None):
                all_python_values_exist = False
            #convert the names to regular strings
            parsed_args_2[str(name)] = siml_val
        #call the wrapped Python function if all argument values are known,
        #or if we don't care about unknown values.
        if all_python_values_exist or self.accept_unknown_values:
            #bad hack for Python implementation detail
            if 'self' in parsed_args_2:
                func_self = parsed_args_2['self']
                del parsed_args_2['self']
                retval = self.py_function(func_self, **parsed_args_2) #IGNORE:W0142
            else:
                retval = self.py_function(**parsed_args_2)            #IGNORE:W0142
            #add administrative data - known values at compile time are constants
            if retval is not None:
                retval.role = RoleConstant
                retval.is_assigned = True
            #Test return value.type
            if(self.return_type is not None and 
               not siml_issubclass(retval.type(), self.return_type())):
                raise Exception('Wrong return type in wrapped function.')
            
            return retval
        #Some argument values are unknown!
        #The expression visitor will create an annotated 
        #NodeFuncCall/NodeOpInfix2/NodeOpPrefix1
        else:
            raise UnknownArgumentsException()
        
        
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
        self.invocation_count = 0


    def __call__(self, *args, **kwargs):
        '''All functions must implement this method'''
        loc = None
        self.invocation_count += 1
        #parse the argumetnts that we get from the caller, do type checking
        parsed_args = self.argument_definition\
                          .parse_function_call_args(args, kwargs, loc)

        #Take 'this' namespace from the 'this' argument. 
        # 'this' must be a Siml object, no unevaluated expression
        this_namespace = parsed_args.get(DotName('this'), None)
        if ( (this_namespace is not None) and 
             (not isinstance(this_namespace, InterpreterObject))):
            raise UserException('The "this" argument (1st argument) '
                                'must be a known Siml object.')
        
        #create local scope (for function arguments and local variables)
        local_namespace = InterpreterObject()
        #store local scope so local variables are accessible for code generation
        if self.interpreter.is_collecting_code():
            self.store_locals_unique(local_namespace)
        
        #put the function arguments into the local namespace
        for arg_name, arg_val in parsed_args.iteritems():
            #call by reference for existing Siml values
            if isinstance(arg_val, InterpreterObject):
                local_namespace.create_attribute(arg_name, arg_val)
            #for unevaluated expressions a new variable is created,
            #and the expression is assigned to it
            else:
                #create new object. use exact information if available
                if arg_val.type_ex is not None:
                    assert False, "Let's see if this code is executed at all"
                    new_arg = self.interpreter.statement_visitor\
                              .expression_visitor.visit_NodeFuncCall(arg_val.type_ex)
                else:
                    new_arg = self.interpreter.statement_visitor\
                              .expression_visitor.call_siml_object(arg_val.type(), [], {}, loc) 
                new_arg.role = arg_val.role
                #put object into local name-space and assign value to it 
                local_namespace.create_attribute(arg_name, new_arg)
                self.interpreter.statement_visitor.assign(new_arg, arg_val, loc)
        
        #Create new environment for the function. 
        new_env = ExecutionEnvironment()
        new_env.global_scope = self.global_scope #global scope from function definition.
        new_env.this_scope = this_namespace
        new_env.local_scope = local_namespace
        self.interpreter.push_environment(new_env)

        #execute the function's code in the new environment.
        try:
            self.interpreter.run(self.statements)
        except ReturnFromFunctionException:           #IGNORE:W0704
            pass
        self.interpreter.pop_environment()
        #the return value is stored in the environment (stack frame)
        ret_val = new_env.return_value
        
        #Test if returned object has the right type.
        #No return type specification present - no check
        if self.return_type is None:
            return ret_val
        #there is a return type specification - enforce it
        elif (ret_val.type is not None and 
              siml_issubclass(ret_val.type(), self.return_type())):
            return ret_val
        raise UserException("The type of the returned object does not match "
                            "the function's return type specification.\n"
                            "Type of returned object: %s \n"
                            "Specified return type  : %s \n"
                            % (str(ret_val.type().name), 
                               str(self.return_type().name)))
    
    
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
    
    
    def store_locals_unique(self, local_namespace):
        '''
        Store local variables in a special namespace.
        
        When collecting code a function's local variables must be placed 
        as algebraic variables in the simulation object. The code of all
        functions is inlined into the main functions, and the local variables 
        of each function invocation must get unique names. 
        
        The special namespace where the local variables are stored is supplied 
        by the interpreter.
        '''
        #long name of function. like: bioreactor.conti.bacterial_growth
        func_path = self.get_complete_path()
        #namespace where all local variables go into
        all_locals_storage = self.interpreter.get_locals_storage()
        #create namespace with long name of this function
        func_locals_storage = all_locals_storage.create_path(func_path)
        #store the local variables individually by the invocation number
        func_locals_storage.create_attribute(str(self.invocation_count), 
                                             local_namespace)
        
        
    
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
    name: DotName
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
        
    def __call__(self, *args, **kwargs):
        new_args = (self.this,) + args
        return self.function(*new_args, **kwargs) #IGNORE:W0142
        
        
        
#class PrimitiveFunctionWrapper(CallableObject):
#    '''
#    Represents a function written in Python; for special functions.
#    
#    The object is callable from Python and Siml.
#    
#    No argument parsing or type checking is done. The wrapped Function
#    is responsible for this.
#    
#    The wrapped function is responsible for handling unevaluated/unknown 
#    arguments, and what object is returned when arguments are unknown.
#    
#    ARGUMENTS
#    ---------
#    name
#        name of function
#    py_function:
#        Wrapped function that will be called.
#    
#    RETURNS
#    -------
#    Anything that the wrapped function returns. 
#    '''
#    def __init__(self, name, py_function=lambda:None):
#        CallableObject.__init__(self, name)
#        self.py_function = py_function
#        
#    def __call__(self, *args, **kwargs):
#        return self.py_function(*args, **kwargs) #IGNORE:W0142
        
        
        
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
        new_env.global_scope = self.interpreter.get_environment().global_scope
        new_env.this_scope = None
        new_env.local_scope = self #functions and data are created 
        #                           in the local scope
        #execute the function's code in the new environment.
        self.interpreter.push_environment(new_env)
        try:
            self.interpreter.run(statements)
        except ReturnFromFunctionException:           
            print 'Warning: return statement in class declaration!'
#                raise Exception('Return statements are illegal in class bodies!')
        self.interpreter.pop_environment()


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
                new_attr.parent = None
                new_obj.create_attribute(attr_name, new_attr)
        #run the __init__ compile time constructor
        if new_obj.has_attribute(DotName('__init__')):
            init_meth = new_obj.get_attribute(DotName('__init__'))
            if not siml_callable(init_meth):
                raise UserException('"__init__" attribute must be a method (callable)!')
            #run the constructor
            init_meth(*args, **args)  #IGNORE:W0142
        return new_obj
            
        
        
#---------- Built In Library  ------------------------------------------------*

#---------- Infrastructure -------------------------------------------------
class BuiltInClassWrapper(TypeObject):  
    '''
    Siml class (meta-class) for the built in objects.
    
    Create instances of built in classes. 
    
    Instances of this class create instances of built in objects in Siml.
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
    def __init__(self):
        InterpreterObject.__init__(self)
        self.name = None
        self.file_name = None
        self.role = RoleConstant
#the single object that should be used to create all Modules
#CLASS_MODULE = IModule.init_funcs_and_class()

        
        
#------- Built In Data --------------------------------------------------
class IFloat(InterpreterObject):
    '''
    Memory location of a floating point number
    
    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not. 
    '''
    type_object = None
    
    def __init__(self, init_val=None):
        InterpreterObject.__init__(self)
        self.type = ref(IFloat.type_object)
        self.time_derivative = None
        self.target_name = None
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (float, int)):
                self.value = float(init_val)
            elif isinstance(init_val, IFloat) and init_val.value is not None:
                self.value = init_val.value
            else:
                raise TypeError('Expecting None, float, int or known IFloat in '
                                'constructor, but received %s' 
                                % str(type(init_val)))
    
    
    @staticmethod            
    def init_funcs_and_class():
        '''
        Create the class object for Siml and create the special methods for 
        operators (+ - * / % **).
        '''
        #create the class object for the Siml class system
        class_float = BuiltInClassWrapper('Float')
        class_float.py_class = IFloat
        IFloat.type_object = class_float
        
        #initialize the mathematical operators, put them into the class
        W = BuiltInFunctionWrapper
        #Binary operators
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
        #The prefix operator
        prefix_args = ArgumentList([NodeFuncArg('self', class_float)])
        W('__neg__', prefix_args, class_float, 
          py_function=IFloat.__neg__).put_into(class_float)  
        #Special function for assignment
        W('__assign__', binop_args, None, 
          py_function=IFloat.__assign__,
          accept_unknown_values=True).put_into(class_float) 
          
        #return the class object
        return class_float


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
    
    def __assign__(self, other): 
        if isinstance(other, IFloat) and other.value is not None:
            self.value = other.value
        else:
            raise UnknownArgumentsException()
        

#The class object used in Siml to create instances of IFloat
CLASS_FLOAT = IFloat.init_funcs_and_class()
    


class IString(InterpreterObject):
    '''
    Memory location of a string
    
    The variable's value can be known or unknown.
    The variable can be assigned a (possibly unknown) value, or not. 
    '''
    type_object = None
    
    def __init__(self, init_val=None):
        InterpreterObject.__init__(self)
        self.type = ref(IString.type_object)
        self.time_derivative = None
        self.target_name = None
        #initialize the value
        self.value = None
        if init_val is not None:
            if isinstance(init_val, (str, float, int)):
                self.value = str(init_val)
            elif isinstance(init_val, IString) and init_val.value is not None:
                self.value = init_val.value
            else:
                raise TypeError('Expecting None, str, float, int or known IString in '
                                'constructor, but received %s' 
                                % str(type(init_val)))
    
    
    @staticmethod            
    def init_funcs_and_class():
        '''
        Create the class object for Siml and create the special methods for 
        operators (+).
        '''
        #create the class object for the Siml class system
        class_string = BuiltInClassWrapper('String')
        class_string.py_class = IString
        IString.type_object = class_string
        
        #initialize the mathematical operators, put them into the class
        W = BuiltInFunctionWrapper
        #Binary operators
        binop_args = ArgumentList([NodeFuncArg('self', class_string), 
                                    NodeFuncArg('other', class_string)])
        W('__add__', binop_args, class_string, 
          py_function=IString.__add__).put_into(class_string)
        #Special function for assignment
        W('__assign__', binop_args, None, 
          py_function=IString.__assign__,
          accept_unknown_values=True).put_into(class_string) 
  
        #return the class object
        return class_string


    def __add__(self, other):
        return IString(self.value + other.value)
    
    def __assign__(self, other): 
        if isinstance(other, IString) and other.value is not None:
            self.value = other.value
        else:
            raise UnknownArgumentsException()


#The class object used in Siml to create instances of IFloat
CLASS_STRING = IString.init_funcs_and_class()
    


#-------------- Service -------------------------------------------------------------------  
class PrintFunction(CallableObject):
    '''The print function object.'''
    def __init__(self):
        CallableObject.__init__(self, 'print')
        
    def __call__(self, *args, **kwargs):
        #TODO: test for illegal arguments. legal: Float, String, UserDefinedClass?, any InterpreterObject?
        #test if all arguments are known
        unknown_argument = False
        for siml_arg in args:
            if (not hasattr(siml_arg, 'value')) or (siml_arg.value is None):
                unknown_argument = True
                break
        #create unevaluated function call
        if unknown_argument:
            func_call = NodeFuncCall()
            func_call.arguments = args
            func_call.keyword_arguments = kwargs 
            #put on decoration
            func_call.name = self.name
            func_call.function_object = self
            func_call.type = None
            func_call.role = None
            return func_call
        #print arguments - all arguments are known
        else:
            for siml_arg in args:
                print siml_arg.value,
            print
            return None
     
     
     
def create_built_in_lib():
    '''
    Returns module with objects that are built into interpreter.
    '''  
    Arg = NodeFuncArg
    WFunc = BuiltInFunctionWrapper
    
    lib = IModule()
    lib.name = DotName('__built_in__')

    #basic data types
    lib.create_attribute('Float', CLASS_FLOAT)
    lib.create_attribute('String', CLASS_STRING)
    #built in functions
    lib.create_attribute('print', PrintFunction())
    #math functions
    WFunc('sqrt', ArgumentList([Arg('x', CLASS_FLOAT)]), 
          return_type=CLASS_FLOAT, 
          py_function=lambda x: IFloat(math.sqrt(x.value))).put_into(lib)
    WFunc('sin', ArgumentList([Arg('x', CLASS_FLOAT)]), 
          return_type=CLASS_FLOAT, 
          py_function=lambda x: IFloat(math.sin(x.value))).put_into(lib)
    
    return lib
#the module of built in objects
BUILT_IN_LIB = create_built_in_lib()    
    
    
    
#--------- Interpreter -------------------------------------------------------*
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
    '''isinstance(...) but inside the SIML language. 
    If in_object is "ast.Node" instance (unevaluated expression), the function returns False.  '''
    #precondition: must be SIML object not AST node
    if not isinstance(in_object, InterpreterObject):
        return False
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
    #the test, there is no inheritance, so it is simple
    return (in_type in class_or_type_or_tuple)


def determine_result_role(arguments, keyword_arguments={}):
    '''
    Determine the most variable role among function arguments.
    
    The result's role is the most variable role from any argument.
    const -> param -> variable
    
    ARGUMENTS
    ---------
    arguments: [InterpreterObject, ...]
    keyword_arguments: {str: InterpreterObject, ...}
    
    RETURNS
    -------
    RoleConstant/RoleParameter/RoleParameter
    '''
    all_args = tuple(arguments) + tuple(keyword_arguments.values())
    is_const_role = lambda obj: issubclass(obj.role, RoleConstant)
    is_param_role = lambda obj: issubclass(obj.role, RoleParameter)
    is_varia_role = lambda obj: issubclass(obj.role, RoleVariable)
    const_role = map(is_const_role, all_args)
    param_role = map(is_param_role, all_args)
    varia_role = map(is_varia_role, all_args)
    
    if any(varia_role):
        return RoleVariable
    elif any(param_role):
        return RoleParameter
    elif all(const_role):
        return RoleConstant
    else:
        return RoleUnkown
    

#TODO: implement this!
#TODO: implement protocol for values: known/unknown, assigned/unassigned
def siml_isknown(siml_obj):
    '''
    Test if an object is a known value, or an unevaluated expression.
    
    RETURNS
    -------
    True:  argument is a known Siml value.
    False: argument is an unevaluated expression or an unknown variable.
    '''
    raise NotImplementedError('Function siml_isknown is not implemented!')


#TODO: remove!
def make_unique_name(base_name, existing_names):
    '''
    Make a unique name that is not in existing_names.
    
    If base_name is already contained in existing_names a number is appended 
    to base_name to make it unique.
    
    Arguments:
    base_name: DotName, str 
        The name that should become unique.
    existing_names: container that supports the 'in' operation
        Container with the existing names. Names are expected to be 
        DotName objects.
        
    Returns: DotName
        Unique name; base_name with number appended if necessary
    '''
    base_name = DotName(base_name)
    for number in range(1, 100000):
        if base_name not in existing_names:
            return  base_name
        #append number to last component of DotName
        base_name = base_name[0:-1] + DotName(base_name[-1] + str(number))
    raise Exception('Too many similar names')    
    
    
class ReturnFromFunctionException(Exception):
    '''Functions return by raising this exception.'''
    #TODO: Use this exception to transport return value?
    pass


#TODO: remove; replace by user defined class.
class CompiledClass(InterpreterObject):
    '''The compile statement creates this kind of object.'''
    def __init__(self):
        super(CompiledClass, self).__init__()
        self.loc = None
        
    

class ExpressionVisitor(Visitor): 
    '''
    Compute value of an expression.
    
    Each vistit_* function evaluates one type of AST-Node recursively. 
    The functions return the (partial) expression's value. This value is either 
    an Interpreter object, or a further annotated AST-tree.
    
    The right function is selected with the inherited function
        self.dispatch(...) 
    '''
    def __init__(self, interpreter):
        Visitor.__init__(self) 
        #the interpreter top level object - necessary for function call
        self.interpreter = interpreter
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        
    def set_environment(self, new_env):
        '''Change part of the symbol table which is currently used.'''
        self.environment = new_env
        
        
    def make_derivative(self, variable):    
        '''Create time derivative of given variable. 
        Put it into the variable's parent.'''
#        #mark attribute as state variable
#        variable.role = RoleStateVariable
        #create the associated derived variable
        deri_var = self.dispatch(variable.type_ex)
        deri_var.role = RoleAlgebraicVariable
        #find state variable's name in parent
        for var_name, var in variable.parent().attributes.iteritems():
            if var is variable: 
                break
        else:
            raise Exception('Broken parent reference! "variable" is not '
                            'in "variable.parent().attributes".')
        #put time derivative in parent, with nice name
        #TODO: use predictable variable name, that contains special character ($).
        deri_name = DotName(var_name[0] + '__dt')         #IGNORE:W0631
        deri_name = make_unique_name(deri_name, variable.parent().attributes)
        variable.parent().create_attribute(deri_name, deri_var)
        #remember time derivative also in state variable
        variable.time_derivative = weakref.ref(deri_var)
   
    
    @Visitor.when_type(InterpreterObject)
    def visit_InterpreterObject(self, node):
        '''Visit a part of the expression that was already evaluated: 
        Do nothing, return the interpreter object.'''
        return node
        
    @Visitor.when_type(NodeFloat)
    def visit_NodeFloat(self, node):
        '''Create floating point number'''
        result = CLASS_FLOAT()
        result.value = float(node.value)
        result.role = RoleConstant
        return result
        
    @Visitor.when_type(NodeString)
    def visit_NodeString(self, node):
        '''Create string'''
        result = CLASS_STRING()
        result.value = str(node.value)
        result.role = RoleConstant
        return result
        
    @Visitor.when_type(NodeIdentifier)
    def visit_NodeIdentifier(self, node): 
        '''Lookup Identifier and get attribute'''
        attr = self.environment.get_attribute(node.name)
        return attr
    
    @Visitor.when_type(NodeAttrAccess)
    def visit_NodeAttrAccess(self, node):
        '''Evaluate attribute access; ('.') operator'''
        #TODO: make this work with unevaluated expressions
        #evaluate the object on the left hand side
        inst_lhs = self.dispatch(node.arguments[0])
        #the object on the right hand side must be an identifier
        id_rhs = node.arguments[1]
        if not isinstance(id_rhs, NodeIdentifier):
            raise UserException('Expecting identifier on right side of "." operator',
                                node.loc)
        #get attribute from object on lhs
        attr = inst_lhs.get_attribute(id_rhs.name)
        return attr        
        
    @Visitor.when_type(NodeDollarPrefix)
    def visit_NodeDollarPrefix(self, node): 
        '''Return time derivative of state variable. 
        Create this special attribute if necessary'''
        #evaluate expression on RHS of operator
        variable = self.dispatch(node.arguments[0])
        #Precondition: $ acts upon a variable
        if not (siml_isinstance(variable, CLASS_FLOAT) and 
                issubclass(variable.role, RoleDataCanVaryAtRuntime)):
            raise UserException('Expecting variable after "$" operator.', 
                                node.loc)
        #change variable into state variable if necessary
        if variable.role is not RoleStateVariable:
            variable.role = RoleStateVariable
            self.make_derivative(variable)
        #return the associated derived variable
        return variable.time_derivative()


    @Visitor.when_type(NodeParentheses)
    def visit_NodeParentheses(self, node):
        '''
        Evaluate pair of parentheses: return expression between parentheses.
        
        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : ???
        - Node.name              : function's name; however function_object should 
                                   be used to identify function.
    
        - Node.arguments         : [ast.Node] 
            List with unevaluated expression as first element.
        - Node.keyword_arguments : {} Empty dict
        '''
        #compute values of expression
        val_expr = self.dispatch(node.arguments[0])
        #TODO: determine result type better
        #TODO: determine result role

        #see if there is an object between the brackets, that can potentially 
        #have a value. No matter wether known or unknown.
        if isinstance(val_expr, InterpreterObject):
            #return the object
            return val_expr
        #otherwise there is an unevaluated expression between the brackets. 
        else:
            #create unevaluated parentheses node as the return value 
            new_node = NodeParentheses()
            new_node.arguments = [val_expr]
            new_node.type = val_expr.type
            new_node.loc = node.loc
            new_node.role = node.role
            return new_node

    
    _prefopt_table = {'-':'__neg__'}

    @Visitor.when_type(NodeOpPrefix1)
    def visit_NodeOpPrefix1(self, node):
        '''
        Evaluate unary operator and return result
        
        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : ???
        - Node.name              : function's name; however function_object should 
                                   be used to identify function.
    
        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are specified
                                   keyword arguments
        '''
        #compute values on rhs of operator
        inst_rhs = self.dispatch(node.arguments[0])
        #look at the operator symbol and determine the right method name(s)
        func_name = ExpressionVisitor._prefopt_table[node.operator]
        #get the special method from the operand's class and try to call the method.
        func = inst_rhs.type().get_attribute(DotName(func_name))
        try:
            result = func(inst_rhs)
            return result
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated expression
            new_oper = NodeOpPrefix1()
            new_oper.operator = node.operator
            new_oper.arguments = [inst_rhs]
            new_oper.keyword_arguments = {}
            #put on decoration
            new_oper.function_object = func
            new_oper.type = func.return_type
            new_oper.is_assigned = True
            #Choose most variable role: const -> param -> variable
            new_oper.role = inst_rhs.role
            return new_oper
    
    
    _binop_table = {'+': ('__add__','__radd__'),
                    '-': ('__sub__','__rsub__'),
                    '*': ('__mul__','__rmul__'),
                    '/': ('__div__','__rdiv__'),
                    '%': ('__mod__','__rmod__'),
                    '**':('__exp__','__rexp__'), }
    
    @Visitor.when_type(NodeOpInfix2)
    def visit_NodeOpInfix2(self, node):
        '''
        Evaluate binary operator and return result
        
        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : Role taken from the argument with the most variable role
    
        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are specified
                                   keyword arguments
        '''
        #compute values on rhs and lhs of operator
        inst_lhs = self.dispatch(node.arguments[0])
        inst_rhs = self.dispatch(node.arguments[1])       
        #look at the operator symbol and determine the right method name(s)
        lfunc_name, rfunc_name = ExpressionVisitor._binop_table[node.operator]
        #get the special method from the LHS's class and try to call the method.
        func = inst_lhs.type().get_attribute(DotName(lfunc_name))
        try:
            result = func(inst_lhs, inst_rhs)
            return result
        except UnknownArgumentsException:
            #Some arguments were unknown create an unevaluated expression
            new_oper = NodeOpInfix2()
            new_oper.operator = node.operator
            new_oper.arguments = [inst_lhs, inst_rhs]
            new_oper.keyword_arguments = {}
            #put on decoration
            new_oper.function_object = func
            new_oper.type = func.return_type
            new_oper.is_assigned = True
            #Choose most variable role: const -> param -> variable
            new_oper.role = determine_result_role([inst_lhs, inst_rhs])
            return new_oper

        #TODO: if unsuccessful in finding a suitable function get the 
        #      right-handed function from the RHS and try to call it.
        #      float.__sub__(a, b) == float.__rsub__(b, a)
        #TODO: *** Dispatching Binary Operators of Derived Classes ***
        #      If the right operand’s type is a subclass of the left operand’s
        #      type and that subclass provides the reflected method for the operation, 
        #      this method will be called before the left operand’s non-reflected 
        #      method. This behavior allows subclasses to override their ancestors’ 
        #      operations.
        
    
    
    @Visitor.when_type(NodeFuncCall)
    def visit_NodeFuncCall(self, node):
        '''
        Evaluate a NodeFuncCall, which calls a call-able object (function).
        Execute the callable's code and return the return value.
 
        TODO:
        Unevaluated expressions (ast.Node) get the following annotations:
        - Node.type              : type of function result
        - Node.function_object   : the function object (self)
        - Node.role              : ???
        - Node.name              : function's name; however function_object should 
                                   be used to identify function.
    
        - Node.arguments         : Operators are returned with positional arguments.
        - Node.keyword_arguments : For regular functions all arguments are specified
                                   keyword arguments
       '''
        #TODO: honor node.function_object: 
        #      the indicator that the function to perform the operation is 
        #      already known. Generated code could be interpreted for a 2nd 
        #      time.
        #   
        #      if  node.function_object is not None:
        #          call_obj = node.function_object
        #find the right call-able object   
        call_obj = self.dispatch(node.name)
        if not isinstance(call_obj, CallableObject):
            raise UserException('Expecting callable object!', node.loc)
        
        #TODO: maybe a separate function starting here makes sense?
        #evaluate all arguments in the caller's environment.
        ev_args = []
        for arg_val in node.arguments:
            ev_arg_val = self.dispatch(arg_val)
            ev_args.append(ev_arg_val)
        ev_kwargs = {}
        for arg_name, arg_val in node.keyword_arguments:
            ev_arg_val = self.dispatch(arg_val)
            ev_kwargs[arg_name] = ev_arg_val
            
        #call the call-able object
        return call_obj(*ev_args, **ev_kwargs)     #IGNORE:W0142


        
class StatementVisitor(Visitor):
    '''
    Execute statements
         
    Each vistit_* function executes one type of statement (AST-Node). 
    The functions do not return any value, they change the state of the 
    interpreter. Usually they create or modify the attributes of the current
    local scope (self.environment.local_scope).
    
    The right function is selected with the inherited function
        self.dispatch(...) 
    '''
    def __init__(self, interpreter):
        Visitor.__init__(self) 
        #the interpreter top level object - necessary for return statement
        self.interpreter = interpreter
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        #object to evaluate expressions
        self.expression_visitor = ExpressionVisitor(interpreter)
        
    def set_environment(self, new_env):
        '''Change part of the symbol table which is currently used.'''
        self.environment = new_env
        self.expression_visitor.set_environment(new_env)
        
    @Visitor.when_type(NodeReturnStmt)
    def visit_NodeReturnStmt(self, node):
        '''Return value from function call'''
        #evaluate the expression of the returned value
        retval = self.expression_visitor.dispatch(node.arguments[0])
        self.environment.return_value = retval
        #Forcibly end function execution - 
        #exception is caught in ExpressionVisitor.visit_NodeFuncCall(...)
        #TODO: transport return value with the exception?
        raise ReturnFromFunctionException()

    @Visitor.when_type(NodeExpressionStmt)
    def visit_NodeExpressionStmt(self, node):
        '''Intened to call functions. Compute expression and forget result'''
        self.expression_visitor.dispatch(node.expression)
    
    
    @Visitor.when_type(NodeAssignment)
    def visit_NodeAssignment(self, node):
        '''Assign value to a constant object, or emit assignment statement 
        for code generation'''
        #compute value of expression on right hand side
        expr_val = self.expression_visitor.dispatch(node.expression)
        #get a data attribute to store the value
        target_obj = self.expression_visitor.dispatch(node.target)
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
            value: InterpreterObject
                Object that contains the information, that should be stored.
            loc: TextLocation, None
                Location in program text for error messages
        '''
        #TODO: assignment without defining the variable first (no data statement.)
        #      This would also be useful for function call
        #TODO: In different parts of code only variables with speciffic roles 
        #      are valid targets of an assign statement.
        #      outside compile: only RoleConstant
        #      in "initial":    only RoleParameter, RoleStateVariable 
        #      in "dynamic":    only RoleVariable
        #      in "final":      only RoleVariable
        
        #Test if value has been assigned already.
        #TODO: What are the semantics for user defined classes?
        if target.is_assigned:
            raise UserException('Duplicate assignment.', loc)
        target.is_assigned = True
        #Test if assignment is possible according to the role.
        #TODO: What are the semantics for user defined classes?
        assign_role_hierarchy = {
            RoleConstant:  (RoleConstant,),
            RoleParameter: (RoleConstant, RoleParameter),
            RoleVariable:  (RoleConstant, RoleParameter, RoleVariable),
            RoleUnkown:    (AttributeRole,)} #RoleUnkown matches anything
        for target_role, value_roles in assign_role_hierarchy.iteritems():
            if issubclass(target.role, target_role):
                if issubclass(value.role, value_roles):
                    break
                raise UserException('Incompatible roles in assignment.', loc)
        
        #Find the '__assign__' function in the object.
        assign_func = target.get_attribute(DotName('__assign__'))
        
        #Call the assign function
        try:
            assign_func(value)
        #Generate code if value is an unknown variable or an unevaluated expression
        except UnknownArgumentsException:
            new_assign = NodeAssignment()
            new_assign.target = target
            new_assign.expression = value
            new_assign.loc = loc
            self.interpreter.collect_statement(new_assign)
        

    @Visitor.when_type(NodeFuncDef)
    def visit_NodeFuncDef(self, node):
        '''Add function object to local namespace'''
        #ArgumentList does the argument parsing at the function call
        #evaluate the type specifications and the default arguments
        arguments_ev = ArgumentList(node.arguments)\
                       .evaluate_args(self.interpreter)
        #Evaluate the return type
        return_type_ev = None
        if node.return_type is not None:
            return_type_ev = self.expression_visitor.dispatch(node.return_type)
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
    
    
    @Visitor.when_type(NodeClassDef)
    def visit_NodeClassDef(self, node):
        '''Define a class - create a class object in local name-space'''
        #TODO: base classes
        #create new class object and put it into the local name-space
        new_class = SimlClass(node.name, bases=None, 
                              statements=node.statements, loc=node.loc)
        self.environment.local_scope.create_attribute(node.name, new_class)
        
        
    @Visitor.when_type(NodeStmtList)
    def visit_NodeStmtList(self, node):
        '''Visit node with a list of data definitions. Execute them.'''
        self.interpreter.run(node.statements)
        
        
    #TODO: Create a nice syntax for the data/compile statement with arbitrary keywords,
    #      and tree literals
    @Visitor.when_type(NodeDataDef)
    def visit_NodeDataDef(self, node):
        '''Create object and put it into symbol table'''
        #get the type object - a NodeIdentifier is expected as class_spec
        class_obj = self.expression_visitor.dispatch(node.class_spec)
        #Create the new object
        if isinstance(class_obj, TypeObject):
            new_object = class_obj()
        else:
            raise UserException('Class expected.', node.loc)
            
        #store new object in local scope
        new_name = node.name
        self.environment.local_scope.create_attribute(new_name, new_object)   
        
        #Set options
        new_object.role = node.role
        #The default role is variable
        if new_object.role is None:
            new_object.role = RoleVariable
        #create associated time derivative if the object is a state variable
        elif new_object.role is RoleStateVariable:
            self.expression_visitor.make_derivative(new_object)
        
        
    @Visitor.when_type(NodeCompileStmt)
    def visit_NodeCompileStmt(self, node):
        '''Create object and record program code.'''
        #TODO: creatation of the tree-shaped object should be done by 
        #      self.visit_NodeDataDef(...)
        #      so there is only one place where data objects are constructed.
        #Create data:
        #get the type object - a NodeIdentifier is expected as class_spec
        class_obj = self.expression_visitor.dispatch(node.class_spec)
        #Create the new object
        if isinstance(class_obj, TypeObject):
            tree_object = class_obj()
        else:
            raise UserException('Class expected.', node.loc)
        
        #create flat object
        flat_object = CompiledClass()
        flat_object.type = tree_object.type
        flat_object.loc = tree_object.type().loc 
        #------------------------------------------------------------------------------
        #TODO: providing a module where local variables can be stored, is a responsibility 
        #      of the code collection mechanism in the interpreter.
        #-------------------------------------------------------------------------------
       
        #TODO: Make list of main functions of all child objects for automatic calling 
        #Create code: 
        #call the main functions of tree_object and collect code
        main_func_names = [DotName('init'), DotName('dynamic'), DotName('final')]
        for func_name in main_func_names:
            #get one of the main functions of the tree object
            if func_name not in tree_object.attributes:
                continue
            func_tree = tree_object.get_attribute(func_name)
            #call the main function and collect code
            self.interpreter.compile_stmt_collect = []
            func_tree()
            #create a new main function for the flat object with the collected code
            func_flat = SimlFunction(func_name, ArgumentList([]), None, 
                                     statements=self.interpreter.compile_stmt_collect, 
                                     global_scope=None)                                 
            #Put new function it into flat object
            flat_object.create_attribute(func_name, func_flat)

        #flatten tree_object (the data) recursively.
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
                long_name = prefix + name
                if siml_isinstance(data, (CLASS_FLOAT, CLASS_STRING)):
                    flat_obj.create_attribute(long_name, data)
                else:
                    flatten(data, flat_obj, long_name)
            
        flatten(tree_object, flat_object, DotName())    
        #TODO: test: the methods of flat object must not use any data from 
        #      outside of flat_object.
     
        #store new object in interpreter
        new_name = node.name
        if new_name is None:
            #create unique name if none given
            new_name = tree_object.type().name
            new_name = make_unique_name(new_name, 
                                        self.interpreter.compile_module.attributes)
        self.interpreter.compile_module.create_attribute(new_name, flat_object)
        
        

class Interpreter(object):
    '''
    Interpret the constant parts of the program
    
    Contains some high-level entry points for the interpreter algorithm.
    These methods are used from outside (to start the interpreter) as 
    well as from inside the interpreter (to coordinate between StatementVisitor
    and expression visitor).
    '''
    def __init__(self):
        #object that interprets a single statement
        self.statement_visitor = StatementVisitor(self)
        #the built in objects - Initialize with empty object.
        self.built_in_lib = BUILT_IN_LIB
        #directory of modules - the symbol table
        self.modules = {}
        #frame stack - should never be empty: top element is automatically 
        # put into self.statement_visitor
        self.env_stack = []
        self.push_environment(ExecutionEnvironment())
        #storage for objects generated by the compile statement
        self.compile_module = IModule()
        self.compile_module.name = DotName('compiled_object_namespace')
        #list of emitted statements (temporary storage)
        self.compile_stmt_collect = None
        
        #tell the the interpreter objects which is their interpreter
        InterpreterObject.interpreter = weakref.proxy(self)
        
        
    def get_locals_storage(self):
        '''
        Return special storage namespace for local variables of functions.
        '''
        #TODO: implement this
        return InterpreterObject()
    
    def collect_statement(self, stmt):
        '''Collect statement for code generation.'''
        if self.compile_stmt_collect is None:
            raise UserException('Only operations with constants allowed here!', stmt.loc)
        self.compile_stmt_collect.append(stmt)
        
    def is_collecting_code(self):
        '''Return True if self.collect_statement can be successfully called.'''
        if self.compile_stmt_collect is None:
            return False
        else:
            return True
        
    def interpret_module_string(self, text, file_name=None, module_name=None):
        '''Interpret the program text of a module.'''
        #create the new module and import the built in objects
        mod = IModule()
        mod.name = module_name
        mod.file_name = file_name
        #put module into root namespace (symbol table)
        self.modules[module_name] = mod
        mod.attributes.update(self.built_in_lib.attributes)
        #set up stack frame (execution environment)
        env = ExecutionEnvironment()
        env.global_scope = make_proxy(mod)
        env.local_scope = make_proxy(mod)
        #put the frame on the frame stack
        self.push_environment(env)
        #parse the program text
        prs = simlparser.Parser()
        ast = prs.parseModuleStr(text, file_name, module_name)
        #execute the statements - interpret the AST
        self.run(ast.statements)
        #remove frame from stack
        self.pop_environment()

    def push_environment(self, new_env):
        '''
        Put new stack frame on stack. 
        Change environment in all visitors.
        '''
        self.env_stack.append(new_env)
        self.statement_visitor.set_environment(new_env)
            
    def pop_environment(self):
        '''
        Remove one stack frame from stack. 
        Change environment in all visitors.
        '''
        old_env = self.env_stack.pop()
        new_env = self.env_stack[-1] 
        self.statement_visitor.set_environment(new_env)
        return old_env
        
    def get_environment(self):
        '''Return the current (topmost) environment from the stack.'''
        return self.env_stack[-1]
        
    def run(self, stmt_list):
        '''Interpret a list of statements'''
        for node in stmt_list:
            self.statement_visitor.dispatch(node)
            
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
        mod.name = DotName('test')
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