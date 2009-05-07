# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
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
Interpreter, that is run at compile time, for the SIML language.

The interpreter reads the AST from the parser. It generates constant 
objects (the symbol table) and changes (simplifies) the code.
"""

from __future__ import division
#from __future__ import absolute_import              #IGNORE:W0410

#import copy
import weakref
from weakref import ref

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
        self.parent = None
        #The symbol table
        self.attributes = {}
        #weak reference to class of this instance
        self.type = None
        #Call to class that would create the correct object.
        self.type_ex = None
        #const, param, variable, ... (Comparable to storage class in C++)
        self.role = None
        #TODO: self.save ??? True/False attribute is saved to disk as simulation result
        #TODO: self.default_value ??? (or into leaf types?)
  
    def create_attribute(self, name, newAttr):
        '''
        Put name into symbol table. Store newly constructed instance.
        This is called for a data statement.
        '''
        if name in self.attributes:
            raise DuplicateAttributeError(attr_name=name)
        self.attributes[name] = newAttr
        newAttr.parent = weakref.ref(self)
        
    def get_attribute(self, name):
        '''Return attribute object'''
        if name not in self.attributes:
            raise UndefinedAttributeError(attr_name=name)
        attr = self.attributes[name]
        return attr
    
    def has_attribute(self, name):
        '''Return true if object has an attribute with name "name"'''
        return name in self.attributes
    
    
  
class CallableObject(InterpreterObject):
    '''Base class of all functions.'''
    def __init__(self, name):
        InterpreterObject.__init__(self)
        self.role = RoleConstant
        self.name = DotName(name)

    def __call__(self, *args, **kwargs):
        '''All functions must implement this method'''
        raise NotImplementedError('__call__ method is not implemented. Use a derived class!')
    
    
    
class BuiltInFunctionWrapper(CallableObject):
    '''Represents a function written in Python.'''
    def __init__(self, name):
        CallableObject.__init__(self, name)
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        self.return_type = None
        #the wrapped function
        self.wrapped_func = None



#TODO: part of this class should go into the parser; for function and class parsing
#class NodeArgumentList(Node):
class IntArgumentList(Node):
    """
    Contains arguments of a function definition.
    - Evaluates the arguments when the function definition is interpreted
    - Parses the arguments when the function is called.
    """
    def __init__(self, arguments, loc=None):
        '''
        ARGUMENTS
        ---------
        arguments: [ast.NodeFuncArg, ...]
            The functions arguments
        loc: ast.TextLocation 
            Location where the function is defined
        '''
        Node.__init__(self)
        self.loc = loc
        #list of argument definitions    
        self.arguments = arguments
        #dict for quick access to argument definitions by name
        self.argument_dict = {}
        #arguments with default values (subset of self.arguments)
        self.default_args = []
        
        there_was_keyword_argument = False
        for arg in arguments:
            #check that positional arguments come first
            if arg.default_value is not None:
                there_was_keyword_argument = True
                self.default_args.append(arg)
            elif there_was_keyword_argument:
                raise UserException('Positional arguments must come before '
                                    'keyword arguments!', loc)
            #test: argument names must be unique
            if arg.name in self.argument_dict:
                raise UserException('Duplicate argument name "%s"!' 
                                    % str(arg.name), loc) 
            self.argument_dict[arg.name] = arg
        
    
    def interpret_args(self, interpreter):
        '''
        Interpret the types and default values of the arguments.
        - type and type_ex data is looked up
        - default values are computed and must evaluate to constants
        '''
        #TODO: implement!
        #TODO: test type compatibility of default arguments
        raise NotImplementedError()
    
    
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
                                % (len(self.arguments), len(args_list)), loc)
        #associate positional arguments to their names
        for arg_def, in_val in zip(self.arguments, args_list):
            #test for correct type
            self._test_type_compatible(in_val, arg_def, loc)
            #associate argument value with name
            output_dict[arg_def.name] = in_val
        
        #associate keyword arguments to their name
        for in_name, in_val in kwargs_dict.iteritems():
            #test: argument name must exist in function definition
            if in_name not in self.argument_dict:
                raise UserException('Unknown argument "%s".' % in_name, loc)
            #test for duplicate argument assignment (positional + keyword)
            if in_name in output_dict:
                raise UserException('Duplicate argument "%s".' % in_name, loc)
            #test for correct type, 
            self._test_type_compatible(in_val, self.argument_dict[in_name], loc)
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
                                loc)
        return output_dict


    def _test_type_compatible(self, in_object, arg_def, loc):
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
        if not siml_isinstance(in_object, arg_def.type()):
            raise IncompatibleTypeError(
                    'Incompatible types. Variable: "%s" '
                    'is defined as:\n %s \nHowever, argument type is: \n%s.'
                    % (arg_def.name, str(arg_def.type()), str(in_object.type())), 
                    loc)



#---------- Built In Types  ------------------------------------------------*
#---------- Infrastructure -------------------------------------------------
class CreateBuiltInType(InterpreterObject): 
    '''
    Create instances of built in classes. - The class of built in objects.
    
    Instances of this class act as the class/type of built in objects like:
    Float, String, Function, Class, ...
    The built in data objects (Float, String) are mainly wrappers around 
    Python objects. The infrastructure objects (Function, Class, Module)
    are a structured symbol table, that creates the illusion of a object 
    oriented programming language.    
    '''
    def __init__(self, class_name, python_class):
        InterpreterObject.__init__(self)
        self.type = None #TODO: set meaningful type
        self.name = DotName(class_name)
        self.python_class = python_class
        self.arguments = []
   
    def construct_instance(self):
        '''Return the new object'''
        #create object
        new_obj = self.python_class()
        #set up type information
        new_obj.type = ref(self)
        new_obj.type_ex = NodeFuncCall()
        new_obj.type_ex.name = weakref.proxy(self)
        new_obj.type_ex.arguments = []
        new_obj.type_ex.keyword_arguments = {}
        return new_obj
        
        
class InstUserDefinedClass(InterpreterObject):
    '''Class: generator for instances. Created by class statement.
    This node creates an instance of an user defined class.'''
    def __init__(self):
        InterpreterObject.__init__(self)
        #TODO: set meaningful type, type_ex
        self.role = RoleConstant
        self.name = None
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        #save the current global name-space in the class definition. This otherwise 
        #access to global variables would have surprising results
        self.global_scope = None 
        #text location where class was defined
        self.loc = None

        
class InstModule(InterpreterObject):
    '''Represent one file'''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.name = None
        self.file_name = None
        self.role = RoleConstant
#        self.statements = None
#the single object that should be used to create all Modules
CLASS_MODULE = CreateBuiltInType('Module', InstModule)

        
        
class InstFunction(InterpreterObject):
    '''A Function or Method'''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.role = RoleConstant
        self.name = None
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        self.return_type = None
        #save the current global name-space in the function. This otherwise 
        #access to global variables would have surprising results
        self.global_scope = None
        #the scope of the object if applicable
        self.this_scope = None
        #function's local variables are stored here, for flattening
        self.create_attribute(DotName('data'), InterpreterObject())
#the single object that should be used to create all Functions
CLASS_FUNCTION = CreateBuiltInType('Function', InstFunction)
    
    
#------- Built In Data --------------------------------------------------
class InstFloat(InterpreterObject):
    '''Floating point number'''
    #Example object to test if two operands are compatible
    #and if the operation is feasible
    type_compat_example = 1
    zero_value = 0
    def __init__(self):
        InterpreterObject.__init__(self)
        self.type = None
        self.value = None
        self.time_derivative = None
        self.target_name = None
#the single object that should be used to create all floats
CLASS_FLOAT = CreateBuiltInType('Float', InstFloat)

  
class InstString(InterpreterObject):
    '''Character string'''
    #Example object to test if operation is feasible
    type_compat_example = 'aa'
    zero_value = ''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.type = None
        self.value = None
        self.target_name = None
#the single object that should be used to create all strings
CLASS_STRING = CreateBuiltInType('String', InstString)
  
  
def create_built_in_lib():
    '''
    Returns module with objects that are built into interpreter.
    '''  
    lib = CLASS_MODULE.construct_instance()
    lib.name = DotName('__built_in__')
    lib.create_attribute(DotName('Module'), CLASS_MODULE)
    lib.create_attribute(DotName('Function'), CLASS_FUNCTION)
    lib.create_attribute(DotName('Float'), CLASS_FLOAT)
    lib.create_attribute(DotName('String'), CLASS_STRING)
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
    

def siml_isinstance(in_object, class_or_type_or_tuple):    
    '''isinstance(...) but inside the SIML language'''
    #precondition: must be SIML object not AST node
    if not isinstance(in_object, InterpreterObject):
        return False
    #always create tuple of class objects
    if not isinstance(class_or_type_or_tuple, tuple):
        classes = (class_or_type_or_tuple,)
    else:
        classes = class_or_type_or_tuple
    #the test, there is no inheritance, so it is simple
    if (in_object.type is not None) and (in_object.type() in classes):
        return True
    else:
        return False
    

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
        result = CLASS_FLOAT.construct_instance()
        result.value = float(node.value)
        result.role = RoleConstant
        return result
        
    @Visitor.when_type(NodeString)
    def visit_NodeString(self, node):
        '''Create string'''
        result = CLASS_STRING.construct_instance()
        result.value = str(node.value)
        result.role = RoleConstant
        return result
        
    @Visitor.when_type(NodeIdentifier)
    def visit_NodeIdentifier(self, node): #, intent=INTENT_READ):
        '''Lookup Identifier and get attribute'''
        attr = self.environment.get_attribute(node.name)
#        if (intent is INTENT_READ and attr.role is RoleConstant and 
#            attr.value is None):
#            raise UserException('Undefined value: %s!' % str(node.name), 
#                                node.loc)            
        return attr
    
    @Visitor.when_type(NodeAttrAccess)
    def visit_NodeAttrAccess(self, node):
        '''Evaluate attribute access; ('.') operator'''
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
        '''Evaluate pair of parentheses: return expression between parentheses.'''
        #compute values of expression
        val_expr = self.dispatch(node.arguments[0])
        #TODO: see if operation is feasible (for both compiled and interpreted code)
        result_type = val_expr.type
        #TODO: determine result type better
        #TODO: determine result role
        #see if operand is constant, number or string
        #if true compute the operation in the interpreter (at compile time)
        if   (siml_isinstance(val_expr, (CLASS_FLOAT, CLASS_STRING)) 
              and val_expr.role == RoleConstant                     ):
            #see if values exist
            #TODO: put this into identifier access, so error message can be 'Undefined value: "foo"!' 
            #      maybe with intent: write / read
            if val_expr.value is None:
                raise UserException('Value is used before it was computed!', node.loc)
            #return the constant
            return val_expr
        #generate code to compute the code between the brackets after compiling (at runtime)
        else:
            #create unevaluated operator as the return value 
            new_node = NodeParentheses()
            new_node.arguments = [val_expr]
            new_node.type = result_type
            new_node.loc = node.loc
            new_node.role = RoleDataCanVaryAtRuntime
            return new_node


    @Visitor.when_type(NodeOpPrefix1)
    def visit_NodeOpPrefix1(self, node):
        '''Evaluate unary operator and return result'''
        #compute values on rhs of operator
        inst_rhs = self.dispatch(node.arguments[0])
        #TODO: see if operation is feasible (for both compiled and interpreted code)
        result_type = inst_rhs.type
        #TODO: determine result type better
        #TODO: determine result role
        #see if operand is constant, number or string
        #if true compute the operation in the interpreter (at compile time)
        if   (siml_isinstance(inst_rhs, (CLASS_FLOAT, CLASS_STRING)) 
              and inst_rhs.role == RoleConstant                     ):
            #see if values exist
            #TODO: put this into identifier access, so error message can be 'Undefined value: "foo"!' 
            #      maybe with intent: write / read
            if inst_rhs.value is None:
                raise UserException('Value is used before it was computed!', node.loc)
            #Compute the operation
            #let the Python interpreter perform the operation on the value
            result = eval(node.operator + ' inst_rhs.value')
            #Wrap the python result type in the Interpreter's instance types
            if isinstance(result, float):
                resultInst = CLASS_FLOAT.construct_instance()
            else:
                resultInst = CLASS_STRING.construct_instance()
            resultInst.value = result
            resultInst.role = RoleConstant
            #see if predicted result is identical to real outcome (sanity check)
            if resultInst.type != result_type:
                raise UserException('Unexpected result type!', node.loc)
            return resultInst
        #generate code to compute the operation after compiling (at runtime)
        else:
            #create unevaluated operator as the return value 
            new_node = NodeOpPrefix1()
            new_node.operator = node.operator
            new_node.arguments = [inst_rhs]
            new_node.type = result_type
            new_node.loc = node.loc
            new_node.role = RoleDataCanVaryAtRuntime
            return new_node
    
    
    @Visitor.when_type(NodeOpInfix2)
    def visit_NodeOpInfix2(self, node):
        '''Evaluate binary operator and return result'''
        #compute values on rhs and lhs of operator
        inst_lhs = self.dispatch(node.arguments[0])
        inst_rhs = self.dispatch(node.arguments[1])
        #see if operation is feasible (for both compiled and interpreted code)
        if not (inst_lhs.type == inst_rhs.type):
            raise UserException('Type mismatch!', node.loc)
        result_type = inst_lhs.type
        #TODO: determine result type better
        #TODO: determine result role
        #see if operands are constant numbers or strings
        #if true compute the operation in the interpreter (at compile time)
        if   (    siml_isinstance(inst_lhs, (CLASS_FLOAT, CLASS_STRING))
              and inst_lhs.role == RoleConstant 
              and siml_isinstance(inst_rhs, (CLASS_FLOAT, CLASS_STRING)) 
              and inst_rhs.role == RoleConstant                     ):
            #see if values exist
            #TODO: put this into identifier access, so error message can be 'Undefined value: "foo"!' 
            #      maybe with intent: write / read
            if inst_lhs.value is None or inst_rhs.value is None:
                raise UserException('Value is used before it was computed!', node.loc)
            #Compute the operation
            #let the Python interpreter perform the operation on the value
            result = eval('inst_lhs.value ' + node.operator + ' inst_rhs.value')
            #Wrap the python result type in the Interpreter's instance types
            if isinstance(result, float):
                resultInst = CLASS_FLOAT.construct_instance()
            else:
                resultInst = CLASS_STRING.construct_instance()
            resultInst.value = result
            resultInst.role = RoleConstant
            #see if predicted result is identical to real outcome (sanity check)
            if resultInst.type != result_type:
                raise UserException('Unexpected result type!', node.loc)
            return resultInst
        #generate code to compute the operation after compiling (at runtime)
        else:
            #create unevaluated operator as the return value 
            new_node = NodeOpInfix2()
            new_node.operator = node.operator
            new_node.arguments = [inst_lhs, inst_rhs]
            new_node.type = result_type
            new_node.loc = node.loc
            new_node.role = RoleDataCanVaryAtRuntime
            return new_node
    
    
    @Visitor.when_type(NodeFuncCall)
    def visit_NodeFuncCall(self, node):
        '''
        Evaluate a NodeFuncCall, which calls a call-able object (function, class).
        Execute the callabe's code and return the return value.
        '''
        #find the right call-able object   
        call_obj = self.dispatch(node.name)
        if not isinstance(call_obj, (InstFunction, InstUserDefinedClass, 
                                     CreateBuiltInType)):
            raise UserException('Expecting callable object!', node.loc)
        
        #evaluate all arguments in the callers environment.
        ev_args = []
        for arg1 in node.arguments:
            ev_arg1 = self.dispatch(arg1)
            ev_args.append(ev_arg1)
        #call the call-able object
        return self.call_siml_object(call_obj, ev_args, node.loc)
        
    def call_siml_object(self, call_obj, args, loc):
        '''
        Call a call-able object (function, class) from Python code.
        Execute the call-able's code and return the return value.
        
        All arguments must be already evaluated.
        '''
        #associate argument values with argument names
        #create dictionary {argument_name:argument_value}
        arg_dict = {}
        for arg_def, arg_val in zip(call_obj.arguments, args):
            arg_dict[arg_def.name] = arg_val
            
        #TODO: write general call-able objects (with __call__ method)
        #TODO: write SIML wrapper for Python function
        
        #different reactions on the different call-able objects
        #execute a function
        if isinstance(call_obj, InstFunction):
            #create local scope (for function arguments and local variables)
            #store local scope so local variables are accessible for code generation
            local_scope = InterpreterObject()
            ls_storage = call_obj.get_attribute(DotName('data'))
            ls_name = make_unique_name(DotName('call'), ls_storage.attributes)
            ls_storage.create_attribute(ls_name, local_scope)
            #Create new environment for the function. 
            new_env = ExecutionEnvironment()
            new_env.global_scope = call_obj.global_scope #global scope from function definition.
            new_env.this_scope = call_obj.this_scope #object where function is defined
            new_env.local_scope = local_scope
            self.interpreter.push_environment(new_env)
            #Create local variables for each argument, 
            #and assign the values to them.
            for arg_name, arg_val in arg_dict.iteritems():
                #create new object. use exact information if available
                if arg_val.type_ex is not None:
                    new_arg = self.visit_NodeFuncCall(arg_val.type_ex)
                else:
                    new_arg = self.call_siml_object(arg_val.type(), [], loc) #TODO: remove when possible
                new_arg.role = arg_val.role
                #put object into local name-space and assign value to it 
                new_env.local_scope.create_attribute(arg_name, new_arg)
                self.interpreter.statement_visitor.assign(new_arg, arg_val, loc)
            #execute the function's code in the new environment.
            try:
                self.interpreter.run(call_obj.statements)
            except ReturnFromFunctionException:           #IGNORE:W0704
                pass
            self.interpreter.pop_environment()
            #the return value is stored in the environment (stack frame)
            return new_env.return_value
        #instantiate a user defined class. 
        elif isinstance(call_obj, InstUserDefinedClass):
            #TODO: move this into InstUserDefinedClass            
            #create new object
            new_obj = InterpreterObject()
            #set up type information
            new_obj.type = ref(call_obj)
            new_obj.type_ex = NodeFuncCall()
            new_obj.type_ex.name = make_proxy(call_obj)
            new_obj.type_ex.arguments = args
            new_obj.type_ex.keyword_arguments = {}
            #Create new environment for object construction. 
            #Use global scope from class definition.
            new_env = ExecutionEnvironment()
            new_env.global_scope = call_obj.global_scope
            new_env.this_scope = None
            new_env.local_scope = new_obj
            #Put arguments into local scope. No need to create new objects
            #because everything must be constant
            for arg_name, arg_val in arg_dict.iteritems():
                new_env.local_scope.create_attribute(arg_name, arg_val)
            #execute the function's code in the new environment.
            self.interpreter.push_environment(new_env)
            try:
                self.interpreter.run(call_obj.statements)
            except ReturnFromFunctionException:           #IGNORE:W0704
                pass
#                raise Exception('Return statements are illegal in class bodies!')
            self.interpreter.pop_environment()
            return new_obj
        #instantiate a built in class. 
        elif isinstance(call_obj, CreateBuiltInType):
            new_obj = call_obj.construct_instance()
            return new_obj
        
        
        
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
        
    @Visitor.when_type(NodePrintStmt)
    def visit_NodePrintStmt(self, node):
        '''Emit print statement and/or print expressions in argument list.'''
        #create new print node
        new_print = NodePrintStmt()
        new_print.newline = node.newline
        new_print.loc = node.loc
        #simplify all expressions in argument list
        #execute the print statement when debug level is >= 1
        for expr in node.arguments:
            result = self.expression_visitor.dispatch(expr)
            new_print.arguments.append(result)
            if DEBUG_LEVEL >= 1:
                print result.value,
        if DEBUG_LEVEL >= 1 and node.newline:
            print
        #emit code for print statement when collecting  code 
        #(and let unit tests without interpreter still run)
        if self.interpreter and self.interpreter.is_collecting_code():
            self.interpreter.collect_statement(new_print)
            
    @Visitor.when_type(NodeReturnStmt)
    def visit_NodeReturnStmt(self, node):
        '''Return value from function call'''
        #evaluate the expression of the returned value
        retval = self.expression_visitor.dispatch(node.arguments[0])
        self.environment.return_value = retval
        #Forcibly end function execution - 
        #exception is caught in ExpressionVisitor.visit_NodeFuncCall(...)
        #TODO: transport exception with the exception?
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
        #TODO: storing class, function, module, proxy 
        #TODO: storing user defined types requires a loop
        #find out if value can be stored in target (compile time or run time)
        if target.type != value.type:
            raise UserException('Type mismatch!', loc)
        #if RHS and LHS are constant values try to write LHS into RHS
        if   (    siml_isinstance(value, (CLASS_FLOAT, CLASS_STRING))
              and value.role == RoleConstant 
              and siml_isinstance(target, (CLASS_FLOAT, CLASS_STRING))
              and target.role == RoleConstant 
              ):
            #Test is RHS is known and LHS is empty
            if value.value is None:
                raise UserException('Value is used before it was computed!', loc)
            if target.value is not None:
                raise UserException('Trying to compute value twice!', loc)
            target.value = value.value
        #emit code for an assignment statement.
        else:
            #TODO: find out if value is an unevaluated expression and target variable at runtime
            new_assign = NodeAssignment()
            new_assign.target = target
            new_assign.expression = value
            new_assign.loc = loc
            self.interpreter.collect_statement(new_assign)
        return
    
    
    @Visitor.when_type(NodeFuncDef)
    def visit_NodeFuncDef(self, node):
        '''Add function object to local namespace'''
        #create new function object and put it into the local namespace
        new_func = CLASS_FUNCTION.construct_instance()
        new_func.name = node.name
        self.environment.local_scope.create_attribute(node.name, new_func)
        #save the current global namespace in the function. Otherwise 
        #access to global variables would have surprising results
        new_func.global_scope = make_proxy(self.environment.global_scope)
        #find out if this is a method (member function) or a function,
        #store the this object if it is a method.
        if not siml_isinstance(self.environment.local_scope, CLASS_MODULE):
            new_func.this_scope = make_proxy(self.environment.local_scope)
        #TODO: if the function is defined inside a class, add the this argument 
        #      to the front of the argument list. Maybe put right default value in place.
        #TODO: Evaluate all expressions in default arguments and type specifications
        #TODO: Put complete argument treatment algorithm into separate function:
        #      visit_NodeClassDef can use the same algorithm
        new_func.arguments = node.arguments
        new_func.keyword_arguments = node.keyword_arguments
        new_func.return_type = node.return_type
        #reference the code
        new_func.statements = node.statements

    
    @Visitor.when_type(NodeClassDef)
    def visit_NodeClassDef(self, node):
        '''Define a class - create a class object in local name-space'''
        #create new class object and put it into the local name-space
        new_class = InstUserDefinedClass()
        new_class.name = node.name
        self.environment.local_scope.create_attribute(node.name, new_class)
        #save the current global name-space in the class. Otherwise 
        #access to global variables would have surprising results
        new_class.global_scope = make_proxy(self.environment.global_scope)
        new_class.arguments = node.arguments
        new_class.keyword_arguments = node.keyword_arguments
        #reference the code
        new_class.statements = node.statements
        new_class.loc = node.loc
        
        
    @Visitor.when_type(NodeStmtList)
    def visit_NodeStmtList(self, node):
        '''Visit node with a list of data definitions. Execute them.'''
        self.interpreter.run(node.statements)
        
        
    def normalize_class_spec(self, class_spec):
        '''
        Bring class specification into standard form (call to class object)
        Common code for visit_NodeDataDef(...) and visit_NodeCompileStmt(...)
        
        Arguments:
        class_spec: NodeIdentifier or NodeFuncCall
            Name of new class or call to class object
        Returns: NodeFuncCall
            Call to class object
        '''
        #only the class name is given e.g.: Foo. Transform: Foo --> Foo()
        if isinstance(class_spec, NodeIdentifier):
            new_spec = NodeFuncCall()
            new_spec.name = class_spec
            new_spec.loc = class_spec.loc
            class_spec = new_spec
        #class name and constructor arguments are given e.g.: Foo(42)
        elif isinstance(class_spec, NodeFuncCall):
            pass
        #anything else is illegal. 
        else:
            raise UserException('Expecting class name (for example "Foo") or '
                                'call to class object (for example "Foo(a)")!',
                                 class_spec.loc)
        return class_spec
        
        
    @Visitor.when_type(NodeDataDef)
    def visit_NodeDataDef(self, node):
        '''Create object and put it into symbol table'''
        #create a call to the class object.
        class_spec = self.normalize_class_spec(node.class_name)
        #Create the new object - evaluate call to class object
        new_object =  self.expression_visitor.visit_NodeFuncCall(class_spec)
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
        #Create data:
        #Create a call to the class object
        class_spec = self.normalize_class_spec(node.class_name)
        #Create tree shaped object
        tree_object =  self.expression_visitor.visit_NodeFuncCall(class_spec)
        #create flat object
        flat_object = CompiledClass()
        flat_object.type = tree_object.type
        #TODO: better solution: find loc of class definition.
        flat_object.loc = tree_object.type().loc 
        
        #TODO: Make list of main functions of all child objects for automatic calling 
        #Create code: 
        #call the main functions of tree_object and collect code
        main_func_names = [DotName('init'), DotName('dynamic'), DotName('final')]
        for func_name in main_func_names:
            if func_name not in tree_object.attributes:
                continue
            func_tree = tree_object.get_attribute(func_name)
            #call the main functions and collect code
            self.interpreter.compile_stmt_collect = []
            self.expression_visitor.call_siml_object(func_tree, [], node.loc)
            #create a new main function with the collected code
            func_flat = CLASS_FUNCTION.construct_instance()
            func_flat.name = func_name
            func_flat.statements = self.interpreter.compile_stmt_collect
            #Put new function it into flat object
            flat_object.create_attribute(func_name, func_flat)
                                             
        #flatten tree_object (the data) recursively.
        def flatten(tree_obj, flat_obj, prefix):
            '''
            Put all attributes (all data leaf objects) into a new flat 
            name-space. The attributes are not copied, but just placed under
            new (long, dotted) names in a new parent object. Therefore the 
            references to the objects in the AST stay intact.
            
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
     
        #store new object in interpreter
        new_name = node.name
        if new_name is None:
            #create unique name if none given
            new_name = tree_object.type().name
            new_name = make_unique_name(new_name, 
                                        self.interpreter.compile_module.attributes)
        self.interpreter.compile_module.create_attribute(new_name, flat_object)
        
        
#    def execute(self, statement):  
#        '''Execute one statement''' 
#        self.dispatch(statement)
            
            

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
        #frame stack
        self.env_stack = []
        #storage for objects generated by the compile statement
        self.compile_module = CLASS_MODULE.construct_instance()
        self.compile_module.name = DotName('compiled_object_namespace')
        #list of emitted statements (temporary storage)
        self.compile_stmt_collect = None
        
        #tell the the interpreter objects which is their interpreter
        InterpreterObject.interpreter = ref(self)
        
        
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
        mod = CLASS_MODULE.construct_instance()
        mod.name = module_name
        mod.file_name = file_name
        self.modules[module_name] = mod
        mod.attributes.update(self.built_in_lib.attributes)
        #set up new module's symbol table
        env = ExecutionEnvironment()
        env.global_scope = make_proxy(mod)
        env.local_scope = make_proxy(mod)
        self.push_environment(env)
        #parse the program
        prs = simlparser.Parser()
        ast = prs.parseModuleStr(text, file_name, module_name)
        #execute the statements
        self.run(ast.statements)

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
        
    def run(self, stmt_list):
        '''Interpret a list of statements'''
        for node in stmt_list:
            self.statement_visitor.dispatch(node)
            
            
            
#------ Tests ----------------------------------------------------------------*   
def do_tests():
    '''Test the module.'''
    Node.aa_show_ID = True
    #simple expression ------------------------------------------------------------------------
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
        
        
    #expression with attribute access ---------------------------------------------------------------
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
        
        
    #interpret some simple statements----------------------------------------------------------------
    doTest = True
#    doTest = False
    if doTest:
        print 'Test statement execution ...............................................................'
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
        intp.interpret_module_string(prog_text, None, 'test')
      
        print '--------------- main module ----------------------------------'
        print intp.modules['test']
        #put collected statements into Node for pretty printing
        n = Node(stmts=intp.compile_stmt_collect)
        print '--------------- collected statements ----------------------------------'
        print n
      
      
    #test interpreter object
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: brackets ...............................................................'
        prog_text = \
'''
print 'start'

data a,b: Float const

func foo():
    a = 2 * (1+2)

foo()
print 'end'
'''

        #create the interpreter
        intp = Interpreter()
        intp.interpret_module_string(prog_text, None, 'test')
      
        print
        print intp.modules['test']
        print intp.compile_module
      
      
    #------------- Test interpreter: complete simple program ..................................................
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter: complete simple program ...............................................................'
        prog_text = \
'''
class Test:
    data V, h: Float 
    data A_bott, A_o, mu, q, g: Float param

    func dynamic():
        h = V/A_bott
#        $V = q - mu*A_o*sqrt(2*g*h)
        $V = q + - mu*A_o*(2*g*h)
#        print 'h: ', h,

    func init():
        V = 0
        A_bott = 1; A_o = 0.02; mu = 0.55; 
        q = 0.05
 
 
class RunTest:
    data g: Float param
    data test: Test

    func dynamic():
        test.dynamic()

    func init():
        g = 9.81
        test.init()
#        solutionParameters.simulationTime = 100
#        solutionParameters.reportingInterval = 1

    func final():
#        graph test.V, test.h
        print 'Simulation finished successfully.'
        

compile RunTest
'''
#-------- Work ----------------------------------------------------------------
        #create the interpreter
        intp = Interpreter()
        intp.interpret_module_string(prog_text, None, 'test')
      
        print
        print intp.modules['test']
        print intp.compile_module
      
      
if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add doctest tests. 
        
    #profile the tests
#    import cProfile
#    cProfile.run('doTests()')
    
    #run tests normally
    do_tests()
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
  