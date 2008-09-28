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

from freeode.ast import *



class Storage(Node):
    '''
    Represent storage for an object (in the symbol table).
    
    An instance of this class is created with a data statement
    
    It inherits from Node only to get Ascii-art tree and copying.
    '''
    def __init__(self):
        Node.__init__(self)
        #value and default value: Instance
        self.value = None
        self.default_value = None
        #required type of value and default_value: InstClass
        self.type = None
        #role:const, param, variable
        self.attribute_role = None
        
        
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
        self.attributes = {}
  
  
class InstFloat(Instance):
    '''Floating point number'''
    def __init__(self, value):
        Instance.__init__(self)
        self.value = float(value)
  
class ExpressionEvaluator(Visitor): 
    '''Compute the value of an expression'''
    def __init__(self):
        Visitor.__init__(self) 
        
    @Visitor.when_type(NodeFloat)
    def visit_NodeFloat(self, node):
        '''Create floating point number'''
        result = InstFloat(node.value)
        return result
        
    @Visitor.when_type(NodeOpInfix2)
    def visit_NodeOpInfix2(self, node):
        '''Evaluate binary operator'''
        inst_lhs = self.dispatch(node.arguments[0])
        inst_rhs = self.dispatch(node.arguments[1])
        #let the Python interpreter find the right function for the operator
        #TODO: error handling
        result = eval('inst_lhs.value ' + node.operator + ' inst_rhs.value')
        return InstFloat(result)
    
    def evaluate(self, expression):
        '''Compute value of expression'''
        return self.dispatch(expression)
        
    
def do_tests():
    '''Test the module.'''
    from simlparser import Parser
    ps = Parser()
    ex = ps.parseExpressionStr('0+1*2')
    print ex
    
    eev = ExpressionEvaluator()
    res = eev.evaluate(ex)
    print 'res = ', res 
    
      
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
  