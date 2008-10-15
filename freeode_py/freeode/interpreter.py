# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration and little bits of text and code came from:               *
#     'fourFn.py', 'simpleArith.py' example programs, by Paul McGuire,     *
#     the 'Spark' library by John Aycock,                                  *
#     and the Python Reference Manual by Guido van Rossum.                 *
#    Many thanks for their excellent contributions to publicly available   *
#    knowledge.                                                            *
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
import simlparser



#class Storage(Node):
#    '''
#    Represent storage and store metadata for an object (in the symbol table).
#    
#    An instance of this class is created with a data statement
#    
#    It inherits from Node only to get Ascii-art tree and copying.
#    '''
#    def __init__(self):
#        Node.__init__(self)
#        #value and default value: InterpreterObject
#        self.value = None
##        self.default_value = None
#        #required type of value and default_value: ref(InstClass)
#        self.type = None
#        #role:const, param, variable
#        self.attribute_role = None
        
        
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
        
        
class ExecutionEnvironment(object):
    '''
    Container for name spaces where symbols are looked up.
    Function findDotName searches the symbol in all name spaces.

    TODO: rename to stack frame?
    '''
    def __init__(self):
        #Name space for global variables. Module where the code was written.
        self.global_scope = None
        #Name space of the this pointer in a method. None outside methods.
        self.this_scope = None
        #scope for the local variables of a function
        self.local_scope = None
        #return value from function call
        self.return_value = None


    #def findDotName(self, dotName, default=None):
    def get_attribute(self, *posArg):
        '''
        Find a dot name in this environment.

        When the name is not found an exception is raised, or a default
        value is returned.
        Tries local name space, 'this' name space, global name space.

        Arguments
        ---------
        dotName : DotName
            Dotted name that is looked up in the different name spaces.
        default : object
            Object which is returned when dotName could not be found.
            If argument is omitted, a UndefinedAttributeError is raised.
        '''
        #get arguments from vector
        if len(posArg) == 1:
            dotName = posArg[0]
            default = None
            raiseErr = True
        elif len(posArg) == 2:
            dotName = posArg[0]
            default = posArg[1]
            raiseErr = False
        else:
            raise Exception('Required number of arguments 1 or 2. '
                            'Actual number of arguments: ' + str(len(posArg)))
        #try to find name in scope hierarchy:
        # function --> class --> module
        scopeList = [self.local_scope, self.this_scope, self.global_scope]
        attr = None
        for scope in scopeList:
            if scope is None:
                continue
            try:
                attr = scope.get_attribute(dotName)
                return attr
            except UndefinedAttributeError:
                pass
        #attribute could not be found in the scopes
        if raiseErr:
            raise UndefinedAttributeError(attr_name=dotName)
        else:
            return default            


        
class InterpreterObject(Node):
    '''
    Base class of all objects that the interpreter operates on.
    Can also be seen as part of structured symbol table
    
    It inherits from Node only to get Ascii-art tree and copying.
    
    TODO: data statement: 
          What happens when a data statement is interpreted?
          What distinguishes an instance from a variable?
    '''
    def __init__(self):
        Node.__init__(self)
        #The symbol table
        self.attributes = {}
        #weak reference to class of this instance
        self.type = None
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
      
    #TODO: def is_assignment_possible(...) ???  
    #TODO: def set_value(new_val): ??? changes the value of an attribute. 
    #      Checks compatibility. Must be re-implemented in leaf subclasses.
    #TODO: remove? object contents is instead changed?
#    def set_attribute(self, name, newAttr):
#        '''Change value of attribute.'''
#        oldAttr = self.attributes[name]
#        if newAttr.type() is not oldAttr.type():
#            raise Exception('Wrong type! attribute: %s; \n'
#                            'has type: %s; \nrequired type: %s' % 
#                            (str(name), 
#                             str(newAttr.type()), str(oldAttr.type())))
#        #TODO: enforce: attributes can be set only once
#        #TODO: maybe recursive copying of values under SIML's control 
#        self.attributes[name] = newAttr.copy()
#        return
        
    def get_attribute(self, name):
        '''Return attribute object'''
        #TODO: how are default values handled?
        if name not in self.attributes:
            raise UndefinedAttributeError(attr_name=name)
        attr = self.attributes[name]
        return attr
    
  
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
        new_obj = self.python_class()
        new_obj.type = ref(self)
        return new_obj
        
        
class InstUserDefinedClass(InterpreterObject):
    '''Class: generator for instances'''
    def __init__(self):
        InterpreterObject.__init__(self)
        #TODO: set meaningful type
        self.type = None
        self.role = RoleConstant
        self.name = None
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        #save the current global namespace in the function. This otherwise 
        #access to global variables would have surprising results
        self.global_scope = None


#TODO: InstClassBase     ???
#        --> SimlClass   ???
#        --> ClassFloat  ???
#        --> ClassString ???
#TODO: InstUserDefinedClass????
        
class InstModule(InterpreterObject):
    '''Represent one file'''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.name = None
#        self.statements = None
#the single object that should be used to create all Modules
CLASS_MODULE = CreateBuiltInType('Module', InstModule)

        
        
class InstFunction(InterpreterObject):
    '''A Function or Method'''
    def __init__(self):
        InterpreterObject.__init__(self)
        self.type = None
        self.role = RoleConstant
        self.name = None
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        self.return_type = None
        #save the current global namespace in the function. This otherwise 
        #access to global variables would have surprising results
        self.global_scope = None
        #the scope of the object if applicable
        self.this_scope = None
#the single object that should be used to create all Functions
CLASS_FUNCTION = CreateBuiltInType('Function', InstFunction)


#------- Built In Data --------------------------------------------------
class InstFloat(InterpreterObject):
    '''Floating point number'''
    #Example object to test if two operands are compatible
    #and if the operation is feasible
    type_compat_example = 1
    def __init__(self):
        InterpreterObject.__init__(self)
        self.type = None
        self.value = None
#the single object that should be used to create all floats
CLASS_FLOAT = CreateBuiltInType('Float', InstFloat)

  
class InstString(InterpreterObject):
    '''Character string'''
    #Example object to test if operation is feasible
    type_compat_example = 'aa'
    def __init__(self):
        InterpreterObject.__init__(self)
        self.type = None
        self.value = None
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
    weakref.ref objects. If in_obj is already a projy it will be returned.
    '''
    if isinstance(in_obj, weakref.ProxyTypes):
        return in_obj
    elif isinstance(in_obj, weakref.ReferenceType):
        return weakref.proxy(in_obj())
    else:
        return weakref.proxy(in_obj)
    

def siml_isinstance(in_object, class_or_type_or_tuple):    
    '''isinstance but inside the SIML language'''
    if not isinstance(class_or_type_or_tuple, tuple):
        class_or_type_or_tuple = (class_or_type_or_tuple,)
    if in_object.type() in class_or_type_or_tuple:
        return True
    else:
        return False
    
    
class ReturnFromFunctionException(Exception):
    '''Functions return by raising this exception.'''
    pass


class ExpressionVisitor(Visitor): 
    '''Compute the value of an expression'''
    def __init__(self, interpreter):
        Visitor.__init__(self) 
        #the interpreter top level object - necessary for function call
        self.interpreter = interpreter
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        
    def set_environment(self, new_env):
        '''Change part of the symbol table which is currently used.'''
        self.environment = new_env

    @Visitor.when_type(NodeFloat)
    def visit_NodeFloat(self, node):
        '''Create floating point number'''
        result = CLASS_FLOAT.construct_instance()
        result.value = float(node.value)
        return result
        
    @Visitor.when_type(NodeString)
    def visit_NodeString(self, node):
        '''Create string'''
        result = CLASS_STRING.construct_instance()
        result.value = str(node.value)
        return result
        
    @Visitor.when_type(NodeIdentifier)
    def visit_NodeIdentifier(self, node):
        '''Lookup Identifier and get attribute'''
        attr = self.environment.get_attribute(node.name)
        return attr
    
    @Visitor.when_type(NodeOpInfix2)
    def visit_NodeOpInfix2(self, node):
        '''Evaluate binary operator'''
        inst_lhs = self.dispatch(node.arguments[0])
        inst_rhs = self.dispatch(node.arguments[1])
        #Compute the operation
        #let the Python interpreter find the right function for the operator
        #TODO: error handling
        #TODO: move this code somehow into the Instances 
        result = eval('inst_lhs.value ' + node.operator + ' inst_rhs.value')
        #Wrap the python result type in the Interpreter's instance types
        if isinstance(result, float):
            resultInst = CLASS_FLOAT.construct_instance()
            resultInst.value = result
        else:
            resultInst = CLASS_STRING.construct_instance()
            resultInst.value = result
        return resultInst
    
    @Visitor.when_type(NodeAttrAccess)
    def visit_NodeAttrAccess(self, node):
        '''Evaluate attribute access ('.') operator'''
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
        
    @Visitor.when_type(NodeFuncCall)
    def visit_NodeFuncCall(self, node):
        '''Call a call-able object (function, class) and execute its code.'''
        #find the right call-able object   
        call_obj = self.evaluate(node.name)
        if not isinstance(call_obj, (InstFunction, InstUserDefinedClass, 
                                     CreateBuiltInType)):
            raise UserException('Expecting callable object!', node.loc)
        
        #evaluate all arguments in the callers environment.
        ev_args = []
        for arg1 in node.arguments:
            ev_arg1 = self.evaluate(arg1)
            ev_args.append(ev_arg1)
        #TODO: evaluate keyword arguments too
        #create dictionary {argument_name:argument_value}
        arg_dict = {}
        for arg_def, arg_val in zip(call_obj.arguments, ev_args):
            arg_dict[arg_def.name] = arg_val
            
        #TODO: write general call-able objects (with __call__ method)
        #TODO: write SIML wrapper for Python function
        #different reactions on the different call-able objects
        #execute a function
        if isinstance(call_obj, InstFunction):
            #Create new environment for the function. 
            #Use global scope from function definition.
            new_env = ExecutionEnvironment()
            new_env.global_scope = call_obj.global_scope
            new_env.this_scope = call_obj.this_scope
            new_env.local_scope = InterpreterObject()
            #Create local variables for each argument, 
            #and assign the values to them.
            for arg_name, arg_val in arg_dict.iteritems():
                new_env.local_scope.create_attribute(arg_name, arg_val)
            #execute the function's code in the new environment.
            self.interpreter.push_environment(new_env)
            try:
                self.interpreter.run(call_obj.statements)
            except ReturnFromFunctionException:           #IGNORE:W0704
                pass
            self.interpreter.pop_environment()
            #the return value is stored in the environment (stack frame)
            return new_env.return_value
        #instantiate a user defined class. 
        elif isinstance(call_obj, InstUserDefinedClass):
            #create new object
            new_obj = InterpreterObject()
            new_obj.type = ref(call_obj)
            #Create new environment for object construction. 
            #Use global scope from class definition.
            new_env = ExecutionEnvironment()
            new_env.global_scope = call_obj.global_scope
            new_env.this_scope = None
            new_env.local_scope = new_obj
            #Create local variables for each argument, 
            #and assign the values to them.
            for arg_name, arg_val in arg_dict.iteritems():
                new_env.local_scope.create_attribute(arg_name, arg_val)
            #execute the function's code in the new environment.
            self.interpreter.push_environment(new_env)
            try:
                self.interpreter.run(call_obj.statements)
            except ReturnFromFunctionException:           #IGNORE:W0704
                pass
#                raise Exception('Return statements are illegal in function bodies!')
            self.interpreter.pop_environment()
            return new_obj
        #instantiate a built in class. 
        elif isinstance(call_obj, CreateBuiltInType):
            new_obj = call_obj.construct_instance()
            return new_obj
    
    def evaluate(self, expression):
        '''Compute and return value of expression'''
        return self.dispatch(expression)
        
        
        
class StatementVisitor(Visitor):
    '''Execute statements'''
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
        '''Print every expression in the argument list'''
        for expr in node.arguments:
            result = self.expression_visitor.evaluate(expr)
            print result.value,
        if node.newline:
            print
            
    @Visitor.when_type(NodeReturnStmt)
    def visit_NodeReturnStmt(self, node):
        '''Return value from function call'''
        #evaluate the expression of the returned value
        retval = self.expression_visitor.evaluate(node.arguments[0])
        self.environment.return_value = retval
        #Forcibly end function execution - 
        #exception is caught in ExpressionVisitor.visit_NodeFuncCall(...)
        raise ReturnFromFunctionException()

    @Visitor.when_type(NodeExpressionStmt)
    def visit_NodeExpressionStmt(self, node):
        '''Intened to call functions. Compute expression and forget result'''
        self.expression_visitor.evaluate(node.expression)
    
    @Visitor.when_type(NodeAssignment)
    def visit_NodeAssignment(self, node):
        '''Change value of an object'''
        #compute value of expression on right hand side
        rhs_expr = node.arguments[1]
        rhs_val = self.expression_visitor.evaluate(rhs_expr)
        #store the value in an existing data attribute
        lhs_expr = node.arguments[0]
        lhs_attr = self.expression_visitor.evaluate(lhs_expr)
        #TODO: work out how to do this correctly
        #TODO: this can't work with user defined classes
        if lhs_attr.type == rhs_val.type:
            lhs_attr.value = rhs_val.value
        else:
            raise Exception('Type mismatch!')
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
        '''Define a class - create a class object in local namespace'''
        #create new class object and put it into the local namespace
        new_class = InstUserDefinedClass()
        new_class.name = node.name
        self.environment.local_scope.create_attribute(node.name, new_class)
        #save the current global namespace in the function. This otherwise 
        #access to global variables would have surprising results
        new_class.global_scope = make_proxy(self.environment.global_scope)
        #TODO: Evaluate all expressions in default arguments and type specifications
        new_class.arguments = node.arguments
        new_class.keyword_arguments = node.keyword_arguments
        #reference the code
        new_class.statements = node.statements
        
        
    @Visitor.when_type(NodeDataDef)
    def visit_NodeDataDef(self, node):
        '''Create object and put it into symbol table'''
        #Objects are created by calling the class object.
        class_spec = node.class_name
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
                                 node.loc)
        
        #Create the new object - evaluate call to class object
        new_object = self.expression_visitor.visit_NodeFuncCall(class_spec)
        #Set options
        new_object.role = node.role
        #store new object in local scope
        new_name = node.name
        self.environment.local_scope.create_attribute(new_name, new_object)
        
        
    @Visitor.when_type(NodeCompileStmt)
    def visit_NodeCompileStmt(self, node):
        '''Create object and record program code.'''
        raise Exception('Compiling is not implemented yet')
        
        
    def execute(self, statement):  
        '''Execute one statement''' 
        self.dispatch(statement)
            
            

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
        
    def interpret_module_string(self, text, file_name=None, module_name=None):
        '''Interpret the program text of a module.'''
        #create the new module and import the built in objects
        mod = CLASS_MODULE.construct_instance()
        mod.name = module_name
        self.modules[module_name] = mod
        mod.attributes.update(self.built_in_lib.attributes)
        #set up new module's symbol table
        env = ExecutionEnvironment()
        env.global_scope = mod
        env.local_scope = mod
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
        for node in stmt_list:
            self.statement_visitor.execute(node)
            
            
            
#------ Tests ----------------------------------------------------------------*   
def do_tests():
    '''Test the module.'''
    Node.aa_show_ID = True
    #simple expression ------------------------------------------------------------------------
    doTest = True
#    doTest = False
    if doTest:
        print 'Test expression evaluation (only immediate values) .......................................'
        from simlparser import Parser
        ps = Parser()
        ex = ps.parseExpressionStr('0+1*2')
    #    ex = ps.parseExpressionStr('"a"+"b"')
        print ex
        
        exv = ExpressionVisitor(None)
        res = exv.evaluate(ex)
        print 'res = ', res 
        
        
    #expression with attribute access ---------------------------------------------------------------
    doTest = True
#    doTest = False
    if doTest:
        print 'Test expression evaluation (access to variables) ...................................'
        from simlparser import Parser
        ps = Parser()
        ex = ps.parseExpressionStr('1 + a * 2')
#        ex = ps.parseExpressionStr('"a"+"b"')
        print ex
        
        #create module where name lives
        mod = InstModule()
        val_2 = CLASS_FLOAT.construct_instance()
        val_2.value = 2.0
        mod.create_attribute(DotName('a'), val_2)
        
        env = ExecutionEnvironment()
        env.global_scope = mod
        print mod
        
        exv = ExpressionVisitor(None)
        exv.environment = env
        res = exv.evaluate(ex)
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
        from simlparser import Parser
        ps = Parser()
        module_code = ps.parseModuleStr(prog_text)
        
        #set up parsing the main module
        stv.environment.global_scope = mod
        stv.environment.local_scope = mod
        #TODO: import_from_module(module, name_list)
        # self.import_from_module(BUILTIN_MODULE, ['*'])
        #interpreter main loop
        for stmt in module_code.statements:
            stv.execute(stmt)
            
        print
        print mod
      
    #test interpreter object
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: function call ...............................................................'
        prog_text = \
'''
print 'start'

func foo(b):
    print 'in foo. b = ', b
    return b*b
    print 'after return'

data a:Float const
a = 2*2 + foo(3*4) + foo(2)
print 'a = ', a
print 'end'
'''
        #create the interpreter
        intp = Interpreter()
        intp.interpret_module_string(prog_text, None, 'test')
      
        print
        print intp.modules['test']
      
      
    #test interpreter object
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: class definition ...............................................................'
        prog_text = \
'''
print 'start'

data pi: Float
pi = 3.1415

class A:
    print 'in A definition'
    data a1: Float
    data a2: Float

class B:
    data b1: Float
    b1 = pi
    data b2: Float

data a: A
data b: B

a.a1 = 1
a.a2 = 2 * b.b1
print 'a.a1: ', a.a1, ', a.a2: ', a.a2

print 'end'
'''

        #create the interpreter
        intp = Interpreter()
        intp.interpret_module_string(prog_text, None, 'test')
      
        print
        print intp.modules['test']
      
      
    #test interpreter object
    doTest = True
#    doTest = False
    if doTest:
        print 'Test interpreter object: class methods ...............................................................'
        prog_text = \
'''
print 'start'

func times_3(x):
    print 'times_2: x=', x
    return 2*x
    
class A:
    data a1: Float
    data a2: Float
    
    func compute(x):
        print 'in compute_a2 x=', x
        a1 = x
        a2 = x + times_3(a1)
        return a2
        
data a: A
a.compute(3)
print 'a.a1 = ', a.a1
print 'a.a2 = ', a.a2

#compile test: A

print 'end'
'''
#-------- Work ----------------------------------------s------------------------
        #create the interpreter
        intp = Interpreter()
        intp.interpret_module_string(prog_text, None, 'test')
      
        print
        print intp.modules['test']
      
      
if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
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
  