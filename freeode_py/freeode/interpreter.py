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

#import copy
import weakref
from weakref import ref

from freeode.ast import *



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
        #TODO: self.statements = None #Statements of function ore module


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
    def set_attribute(self, name, newAttr):
        '''Change value of attribute.'''
        oldAttr = self.attributes[name]
        if newAttr.type() is not oldAttr.type():
            raise Exception('Wrong type! attribute: %s; \n'
                            'has type: %s; \nrequired type: %s' % 
                            (str(name), 
                             str(newAttr.type()), str(oldAttr.type())))
        #TODO: enforce: attributes can be set only once
        #TODO: maybe recursive copying of values under SIML's control 
        self.attributes[name] = newAttr.copy()
        return
        
    def get_attribute(self, name):
        '''Return attribute object'''
        #TODO: how are default values handled?
        if name not in self.attributes:
            raise UndefinedAttributeError(attr_name=name)
        attr = self.attributes[name]
        return attr
    
  
#---------- Built In Objects  ------------------------------------------------*
class InstClass(InterpreterObject):
    '''Class: generator for instances'''
    def __init__(self):
        InterpreterObject.__init__(self)
        #TODO: set meaningful type
        self.name = None
        self.constructor = None
    def make_instance(self): 
        pass

#TODO: InstClassBase     ???
#        --> SimlClass   ???
#        --> ClassFloat  ???
#        --> ClassString ???
#TODO: InstUserDefinedClass????
        
class InstModule(InterpreterObject):
    '''Represent one file'''
    def __init__(self):
        InterpreterObject.__init__(self)
        #TODO: set meaningful type
        self.type = None
        self.name = None
#        self.statements = None
        
class InstFunction(InterpreterObject):
    '''A Function or Method'''

#------- Built In Types --------------------------------------------------
class CreateBuiltInType(InterpreterObject): 
    '''
    Create instances built in classes (Float, String, ...)
    
    Instances of this class act as the class of built in objects
    Float, String, (Distribution, Array)
    These built in objects are mainly wrappers around Python objects.
    '''
    def __init__(self, class_name, python_class):
        InterpreterObject.__init__(self)
        #TODO: set meaningful type
        self.type = None
        self.name = DotName(class_name)
        self.python_class = python_class
   
    def make_instance(self, init_val=None):
        '''Return the new object'''
        return self.python_class(init_val, self)
        
        
class InstFloat(InterpreterObject):
    '''Floating point number'''
    #Example object to test if two operands are compatible
    #and if the operation is feasible
    type_compat_example = 1
    #TODO: instances can be only assigned once.
    #TODO: add self.default_value ??? (or into InterpreterObject?)
    def __init__(self, value, class_obj):
        InterpreterObject.__init__(self)
        self.type = ref(class_obj)
        if value is None:
            self.value = None
        else:
            self.value = float(value)
#the single object that should be used to create all floats
CLASS_FLOAT = CreateBuiltInType('Float', InstFloat)

  
class InstString(InterpreterObject):
    '''Character string'''
    #Example object to test if operation is feasible
    type_compat_example = 'aa'
    def __init__(self, value, class_obj):
        InterpreterObject.__init__(self)
        self.type = ref(class_obj)
        if value is None:
            self.value = None
        else:       
            self.value = str(value)
#the single object that should be used to create all strings
CLASS_STRING = CreateBuiltInType('String', InstString)
  
  
#--------- Interpreter -------------------------------------------------------*
class ExpressionVisitor(Visitor): 
    '''Compute the value of an expression'''
    def __init__(self):
        Visitor.__init__(self) 
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        
    @Visitor.when_type(NodeFloat)
    def visit_NodeFloat(self, node):
        '''Create floating point number'''
        #TODO: use CLASS_FLOAT to create the float object
        result = CLASS_FLOAT.make_instance(node.value)
        return result
        
    @Visitor.when_type(NodeString)
    def visit_NodeString(self, node):
        '''Create floating point number'''
        result = CLASS_STRING.make_instance(node.value)
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
            resultInst = CLASS_FLOAT.make_instance(result)
        else:
            resultInst = CLASS_STRING.make_instance(result)
        return resultInst
    
    def evaluate(self, expression):
        '''Compute and return value of expression'''
        return self.dispatch(expression)
        
        
        
class StatementVisitor(Visitor):
    '''Execute statements'''
    def __init__(self):
        Visitor.__init__(self) 
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        self.expression_visitor = None #TODO: create ExpressionVisitor here!
        
    @Visitor.when_type(NodePrintStmt)
    def visit_NodePrintStmt(self, node):
        '''Print every expression in the argument list'''
        for expr in node.arguments:
            result = self.expression_visitor.evaluate(expr)
            print result.value,
        if node.newline:
            print
        
    @Visitor.when_type(NodeDataDef)
    def visit_NodeDataDef(self, node):
        '''Create object and put it into symbol table'''
        #get the class object which we need to create the data object
        class_name = node.class_name
        class_object = self.environment.get_attribute(class_name)
        #create new object and store it in local scope
        new_object = class_object.make_instance()
        new_name = node.name
        self.environment.local_scope.create_attribute(new_name, new_object)
        #Save options
        new_object.role = node.role
        #evaluate default value and save it
        default_expr = node.default_value
        if default_expr is not None:
            default_value = self.expression_visitor.evaluate(default_expr)
            new_object.default_value = default_value
        
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
        #TODO: this can't work
        if lhs_attr.type == rhs_val.type:
            lhs_attr.value = rhs_val.value
        else:
            raise Exception('Type mismatch!')
        return
    
        
    def execute(self, statement):   
        self.dispatch(statement)
            
            
            
#------ Tests ----------------------------------------------------------------*   
def do_tests():
    '''Test the module.'''
    #simple expression
    doTest = True
    doTest = False
    if doTest:
        from simlparser import Parser
        ps = Parser()
        ex = ps.parseExpressionStr('0+1*2')
    #    ex = ps.parseExpressionStr('"a"+"b"')
        print ex
        
        exv = ExpressionVisitor()
        res = exv.evaluate(ex)
        print 'res = ', res 
        
#------ Test ----------------------------------------------------------------*   
    #expression with attribute access
    doTest = True
#    doTest = False
    if doTest:
        print 'Test expression evaluation .............................................................'
        from simlparser import Parser
        ps = Parser()
        ex = ps.parseExpressionStr('0+a*2')
#        ex = ps.parseExpressionStr('"a"+"b"')
        print ex
        
        mod = InstModule()
        mod.create_attribute(DotName('Float'), CLASS_FLOAT)
        mod.create_attribute(DotName('String'), CLASS_STRING)
        mod.create_attribute(DotName('a'), CLASS_FLOAT.make_instance(2))
        
        env = ExecutionEnvironment()
        env.global_scope = mod
        print mod
        
        exv = ExpressionVisitor()
        exv.environment = env
        res = exv.evaluate(ex)
        print 'res = ', res 
        
    #interpret statement
    doTest = True
#    doTest = False
    if doTest:
        print 'Test statement execution ...............................................................'
        prog_text = \
'''
print 'start'
data a:Float const #=6
a = 2*2 + 2**3 * 2**3**4
#if a > 2:
#    print 'a > 2: '
#else:
#    print 'a <= 2: '
print 'a = ', a
print 'end'
'''
#-------- Work ----------------------------------------s------------------------
        from simlparser import Parser
        ps = Parser()
        module_code = ps.parseModuleStr(prog_text)
        
        mod = InstModule()
#        mod.statements = module_code
        mod.create_attribute(DotName('Float'), CLASS_FLOAT)
        mod.create_attribute(DotName('String'), CLASS_STRING)
        print mod
        
        env = ExecutionEnvironment()
        env.global_scope = mod
        env.local_scope = mod
        
        exv = ExpressionVisitor()
        exv.environment = env
        
        stv = StatementVisitor()
        stv.environment = env
        stv.expression_visitor = exv
        
        for stmt in module_code.statements:
            stv.execute(stmt)
            
        print
        print mod
      
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
  