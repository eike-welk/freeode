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
#        #value and default value: Instance
#        self.value = None
##        self.default_value = None
#        #required type of value and default_value: ref(InstClass)
#        self.type = None
#        #role:const, param, variable
#        self.attribute_role = None
        
        
class DuplicateAttributeError(Exception):
    '''
    Exception raised by Instance
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
        self.globalScope = None
        #Name space of the this pointer in a method. None outside methods.
        self.thisScope = None
        #scope for the local variables of a function
        self.localScope = None
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
        scopeList = [self.localScope, self.thisScope, self.globalScope]
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


        
class Instance(Node):
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
  
    def create_attribute(self, name, newAttr):
        '''
        Put name into symbol table. Store newly constructed instance.
        This is called for a data statement.
        '''
        if name in self.attributes:
            raise DuplicateAttributeError(attr_name=name)
        self.attributes[name] = newAttr
      
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
class InstClass(Instance):
    '''Class: generator for instances'''
    def __init__(self):
        Instance.__init__(self)
        #TODO: set meaningful type
        self.name = None
        self.constructor = None
    #TODO: def make_instance(): 

#TODO: InstClassBase     ???
#        --> SimlClass   ???
#        --> ClassFloat  ???
#        --> ClassString ???
#TODO: InstUserDefinedClass????
        
class InstModule(Instance):
    '''Represent one file'''
    def __init__(self):
        Instance.__init__(self)
        #TODO: set meaningful type
        self.name = None
        self.statements = None
        
        
class ClassFloat(InstClass):  
    '''Create instance of floating point number'''
    def __init__(self):
        InstClass.__init__(self) 
        self.name = DotName('Float')
    def make_instance(self):
        '''Return number'''
        return InstFloat(None)
#the single object that should be used to create all floats
CLASS_FLOAT = ClassFloat()
class InstFloat(Instance):
    '''Floating point number'''
    #TODO: instances can be only assigned once.
    def __init__(self, value):
        Instance.__init__(self)
        self.type = ref(CLASS_FLOAT)
        if value is None:
            self.value = None
        else:
            self.value = float(value)
  
  
class InstString(Instance):
    '''Character string'''
    def __init__(self, value):
        Instance.__init__(self)
        #TODO: set meaningful type
        self.value = str(value)
  
  #TODO: InstFunction
  
#--------- Interpreter -------------------------------------------------------*
class ExpressionEvaluator(Visitor): 
    '''Compute the value of an expression'''
    def __init__(self):
        Visitor.__init__(self) 
        #the places where attributes are stored (the symbol tables)
        self.environment = None
        
    @Visitor.when_type(NodeFloat)
    def visit_NodeFloat(self, node):
        '''Create floating point number'''
        #TODO: use CLASS_FLOAT to create the float object
        result = InstFloat(node.value)
        return result
        
    @Visitor.when_type(NodeString)
    def visit_NodeString(self, node):
        '''Create floating point number'''
        result = InstString(node.value)
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
        #let the Python interpreter find the right function for the operator
        #TODO: error handling
        #TODO: move this code somehow into the Instances 
        result = eval('inst_lhs.value ' + node.operator + ' inst_rhs.value')
        #create right instance type
        if isinstance(result, float):
            resultInst = InstFloat(result)
        else:
            resultInst = InstString(result)
        return resultInst
    
    def evaluate(self, expression):
        '''Compute value of expression'''
        return self.dispatch(expression)
        

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
        
        eev = ExpressionEvaluator()
        res = eev.evaluate(ex)
        print 'res = ', res 
        
#------ Tests ----------------------------------------------------------------*   
    #expression with attribute access
    doTest = True
#    doTest = False
    if doTest:
        from simlparser import Parser
        ps = Parser()
        ex = ps.parseExpressionStr('0+a*2')
    #    ex = ps.parseExpressionStr('"a"+"b"')
        print ex
        
        mod = InstModule()
        mod.create_attribute(DotName('Float'), CLASS_FLOAT)
        mod.create_attribute(DotName('a'), InstFloat(2))
        
        env = ExecutionEnvironment()
        env.globalScope = mod
        print mod
        
        eev = ExpressionEvaluator()
        eev.environment = env
        res = eev.evaluate(ex)
        print 'res = ', res 
        
    #interpret statement
    doTest = True
    doTest = False
    if doTest:
        from simlparser import Parser
        ps = Parser()
        stmts = ps.parseModuleStr('data a:Float\n')
        
        mod = InstModule()
        mod.statements = stmts
        mod.create_attribute('Float', ClassFloat())
        
      
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
  