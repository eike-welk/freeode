# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2009 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
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
Abstract syntax tree and tools for tree handling.

- Syntax tree with specialized nodes for all elements of the language.
- Iterator to iterate over the tree.
- Printer to convert tree to pretty printed string.
- Visitor to invoke different code depending on node type.

Additionally this module contains some common infrastructure used by other
modules of Freeode:
- Class to store text locations together with file names.
- Exceptions to carry user visible errors.
- Handling for dotted attribute names.
- The program's version string.
'''



from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410


from types import ClassType, FunctionType, NoneType #, TupleType, StringType
import copy
import weakref
#from weakref import proxy

import pyparsing


##TODO: svn command: svn propset svn:keywords Revision ast.py
#__fileVersion__ = "$LastChangedRevision: 43 $"
#__fileVersion__ = "$Rev: 43 $"


#version of the Siml compiler.
PROGRAM_VERSION = '0.4.0a1'
#How much debug information is printed
# 0: No debug information; 1: some; ....
DEBUG_LEVEL = 1


class Node(object):
    '''
    Base class for all elements of the AST.
    
    Features:
    __init__(...)
        Creates one attribute for each named argument.
    __str__(), aa_tree(...): 
        Creates Ascii-art tree representation of node and its 
        attributes.
    copy():
        Returns deep copy of node and of all attributes that are 'owned'
        by this node.
    '''
    #put attributes with these names at the top or bottom of ASCII-art tree
    aa_top = ['name']
    aa_bottom = ['loc']
    #Number of chars used for indentation. Must be >= 1
    aa_indent_width = 4
    #Length of line. Longer lines will be wrapped
    aa_wrap_line_at = 150
    #Also print the node's id() 
    aa_show_ID = True
    #Maximal nesting level, to catch infinite recursion.
    aa_max_nesting_level = 100
    #string to symbolize one indent level
    aa_indent_step_str = '|' + ' '*int(aa_indent_width - 1)
    
    #we dont own instances of these classes.
    #tuple of types that are not copied deeply
    _weak_types = weakref.ProxyTypes + (weakref.ReferenceType,)
    
    def __init__(self, **args): 
        '''Create an attribute for each named argument.'''
        object.__init__(self)
        for key, value in args.iteritems():
            setattr(self, key, value)
            
    def __str__(self):
        '''
        Create ASCII-art tree of this object, and of all data attributes it 
        contains recursively.
        '''
        return self._aa_make_tree()
    
    def _aa_attr_category(self, attr_name):
        '''
        Categorize attributes for Ascii-art
        
        Returns:
            -1: attribute does not exist
             0: not a Node
             1: proxy: not owned
            11: ref: not owned by this Node
             2: Node
             3: list(Node)
             # removed: 4: list(list(Node))
             5: dict(<any>:Node())
        '''
        #get attribute
        if attr_name in self.__dict__:
            attr = self.__dict__[attr_name]
        else:
            return -1 # attribute does not exist
        #categorize attribute
        if isinstance(attr, weakref.ProxyTypes):
            return 1 #proxy: not owned by this Node
        if isinstance(attr, weakref.ReferenceType):
            return 2 #ref: not owned by this Node
        if isinstance(attr, Node):
            return 100 # Node
        if isinstance(attr, list) and len(attr) > 0 and \
             isinstance(attr[0], Node):
            return 101 # list(Node)
        if isinstance(attr, dict):
            vals = attr.values()
            if len(vals) > 0 and isinstance(vals[0], Node):
                return 102 # dict(<any>:Node())
        return 0 #not a Node
            
    #TODO: re-implement this with the visitor class!
    def _aa_make_str_block(self, attr_name_list, indent_str, nesting_level):
        '''
        Convert attributes to a string. 
        
        Uses different algorithms for different attribute categories.
        Performs the line wrapping.
        '''
        #initialize buffers
        tree = ''
        line = indent_str
        #loop over list of attribute names
        for key in attr_name_list:
            cat = self._aa_attr_category(key)
            #Non Node classes, assumed to be small 
            #the atoms that really carry the information)
            if cat == 0:
                line += key + ' = ' + str(self.__dict__[key]) + '; '
                if len(line) > self.aa_wrap_line_at:
                    tree += line + '\n'
                    line = indent_str
            #proxy: not owned by this node (printed small)
            elif cat == 1:
                line += (key + ' = ' 
                         + str(self.__dict__[key].__class__.__name__) + ' :: '
                         + repr(self.__dict__[key]) + '; ')
                if len(line) > self.aa_wrap_line_at:
                    tree += line + '\n'
                    line = indent_str
            #ref: not owned by this node (printed small)
            elif cat == 2:
                line += (key + ' = ' 
                         + str(self.__dict__[key]().__class__.__name__) + ' :: '
                         + repr(self.__dict__[key]) + '; ')
                if len(line) > self.aa_wrap_line_at:
                    tree += line + '\n'
                    line = indent_str
            #Attribute is Node
            elif cat == 100:
                if line != indent_str: 
                    tree += line  + '\n'
                    line = indent_str
                tree += indent_str + key + ' = \n'
                tree += self.__dict__[key]._aa_make_tree(nesting_level +1)
            #Attribute is list(Node)
            elif cat == 101:
                if line != indent_str: 
                    tree += line  + '\n'
                    line = indent_str   
                tree += indent_str + key + ' = list :: \n'     
                for item in self.__dict__[key]:
                    tree += item._aa_make_tree(nesting_level +1)  
#                    tree += indent_str + '|- ,\n'
            #Attribute is dict(<any>:Node())
            elif cat == 102:
                if line != indent_str: 
                    tree += line  + '\n'
                    line = indent_str   
                tree += indent_str + key + ' = dict :: \n'  
                dict_of_node = self.__dict__[key] 
                name_list = dict_of_node.keys()
                name_list.sort()         
                for name in name_list:
                    item = dict_of_node[name]
                    tree += indent_str + ' ' + str(name) + ':\n'  #print key:
                    tree += item._aa_make_tree(nesting_level +1)  #print node
#                    tree += indent_str + '|- ,\n'
            else:
                raise Exception('Internal error! Unknown attribute category: ' 
                                + str(cat))
                
        if line != indent_str:
            tree += line  + '\n'
        return tree

    
    def _aa_make_tree(self, nesting_level=0):
        '''
        Create ASCII-art tree of this object, and of all data attributes it 
        contains recursively.
        
        The algorithm only recurses into nodes owned by this node. All other 
        objects will be printed in a very limited manner.
        
        The data attributes are be printed in four categories:
        top: 
            Attributes that should be viewed first, like 'name'.
            Attribute names are in Node.aa_top, or in self.aa_top.
        small:
            These attributes are assumed to have only a small textual 
            representation, which fits into one line:
            - Attributes which are not Node subclasses. 
            - Attributes which are not owned by this node. Only their class 
              name is mentioned.
        big:
            These attributes have only a big, multi line textual representations.
            - Node subclasses, lists of nodes, lists of lists of nodes.
        bottom:  
            Attributes that should be viewed last, like 'loc'.
            Attribute names are in Node.aa_bottom, or in self.aa_bottom.
        '''
        #TODO: new pretty printer mechanism to prevent duplicate printing
        #      currently the weak types are used. As they are not Node instances
        #      the pretty printer does not recurse into them 
        #catch infinite recursion
        if nesting_level > Node.aa_max_nesting_level:
            msg = 'Nesting of nodes too deep! (Infinite recursion?):' \
                  ' nesting_level = ' + str(nesting_level) + '\n'
#            print 'Warning: ' + msg
            return msg                  
        #initialize buffer
        tree_buffer = ''
        #string for indentation
        indent_str = self.aa_indent_step_str * nesting_level 
        
        #create four lists with different categories of attributes
        name_set = set(self.__dict__.keys())
        attr_top =    [a for a in self.aa_top    if a in name_set]
        attr_bottom = [a for a in self.aa_bottom if a in name_set]
        body = list(name_set - set(attr_bottom) - set(attr_top))
        body.sort()
        attr_small = [a for a in body if self._aa_attr_category(a) < 100]
        attr_big =    [a for a in body if self._aa_attr_category(a) >= 100]
        
        #create header with type information
        tree_buffer += indent_str + self.__class__.__name__ + ' ::'
        if self.aa_show_ID:
            tree_buffer += ' ID: ' + hex(id(self))
#        tree_buffer += ' ---------------------------------'
        tree_buffer += '\n'
        indent_str += '|'
        
        #convert the attributes to string
        tree_buffer += self._aa_make_str_block(attr_top,    indent_str, nesting_level)
        tree_buffer += self._aa_make_str_block(attr_small,  indent_str, nesting_level)
        tree_buffer += self._aa_make_str_block(attr_big,    indent_str, nesting_level)
        tree_buffer += self._aa_make_str_block(attr_bottom, indent_str, nesting_level)
        
        return tree_buffer
    
             
    def copy(self):
        '''
        Return a (recursive) deep copy of the node.

        Only objects owned by this object are copied deeply.
        For objects owned by other nodes proxies should be created:
        self.foo = proxy(other.foo)
        '''
        return copy.deepcopy(self)


    def __deepcopy__(self, memo_dict):
        '''
        Hook that does the copying for Node.copy.
        Called by copy.deepcopy()
        
        copy - weakref interaction problems:
        http://coding.derkeiler.com/Archive/Python/comp.lang.python/2008-02/msg01873.html
        '''
        #TODO: new ast.Node.copy mechanism for shallow copy, just referencing
        #create empty instance of self.__class__
        new_obj = Node.__new__(self.__class__)
        for name, attr in self.__dict__.iteritems():
            if isinstance(attr, Node._weak_types):
                #attribute owned by other object: no copy only reference
                setattr(new_obj, name, attr)
            else:
                #attribute owned by self: make deep copy
                new_attr = copy.deepcopy(attr, memo_dict)
                setattr(new_obj, name, new_attr)
        return new_obj


#---------- Nodes Start ------------------------------------------------------------*
#class NodeNoneClass(Node):
#    '''Node that takes the function of None.'''
#    def __init__(self):
#        super(NodeNoneClass, self).__init__()
##The single instance of NodeNoneClass. Should be used like None
#nodeNone = NodeNoneClass()

#--------- Expression --------------------------------------------------------------
class NodeFloat(Node):
    '''
    Represent a real number in the AST.
    Example: 123.5
    Data attributes:
        loc     : location in input string
        value   : the number as a string???
    '''
    def __init__(self):
        super(NodeFloat, self).__init__()
        self.value = None
        self.loc = None


class NodeString(Node):
    '''
    Represent a string in the AST.
    Example: 'hello world'
    Data attributes:
        loc     : location in input string
        value   : the string
    '''
    def __init__(self):
        super(NodeString, self).__init__()
        self.value = None
        self.loc = None


class NodeIdentifier(Node):
    '''
    AST node for an identifier. 
    
    Using an identifier always means some access to data.
    
    TODO: the '$' and 'deriv' operators will mean access to special variables 
          with mangeld names: $foo.bar --> foo.bar$time; deriv(foo, x) --> foo$x
    
    Data Attributes:
        name: DotName()
            Name of attribute: (DotName('a'); DotName('proc.model1.a'))
        loc: 
            Location in input string
    '''
    def __init__(self, name=None, loc=None):
        Node.__init__(self)
        self.name = DotName(name) if name is not None else None
        self.loc = loc


class NodeAttrAccess(Node):
    '''
    AST node for '.' (attribute access) operator. 
    Attributes:
    operator: '.' 
        For uniform handling with other operators
    arguments: list(Node, NodeIdentifier)
        The two operands of the '.' (attribute access) operator.
        self.arguments[0]: LHS: any expression that returns an InterpreterObject
        self.arguments[1]: RHS: NodeIdentifier
    loc: 
        Location in input string
    '''
    def __init__(self):
        super(NodeAttrAccess, self).__init__()
        self.operator = '.'
        self.arguments = tuple()
        self.loc = None        


class NodeDollarPrefix(Node):
    '''
    AST node for '$' (time derivation) operator.
    Attributes:
    operator: '$'  
        For uniform handling with other operators
    arguments: list(NodeIdentifier); list(InterpreterObject);
        self.arguments[0]: RHS: NodeIdentifier:
        State variable whose derivative should be returned
    loc: 
        Location in input string
   '''
    def __init__(self):
        super(NodeDollarPrefix, self).__init__()
        self.operator = '$'
        self.arguments = tuple()
        self.loc = None        


class NodeParentheses(Node):
    '''
    Represent a pair of parentheses that enclose an expression, in the AST.
    
    Example: ( ... )
    Treated like a special (do nothing) operator
    
    Data attributes:
        arguments: list(Node())
            Mathematical expression between the parentheses. 
            Naming is chosen to unify operators and function call
        type: InterpreterObject
            Type of the results of the operation. For decorating the AST.
        role: AttributeRole
            Role of the results of the operation. For decorating the AST.
        loc: TextLocation; None
            Location in input string
    '''
    def __init__(self, arguments=None):
        super(NodeParentheses, self).__init__()
        self.arguments = arguments if arguments is not None else tuple()
        self.type = None
        self.type = None
        self.role = RoleUnkown
        self.loc = None


class NodeOpInfix2(Node):
    '''
    AST node for a (binary) infix operator: + - * / ^ and or
    Data attributes:
        operator: 
            Operator symbol e.g.: '+'
        arguments:  tuple(Node(), Node())
            Expression on left and right of operator: 
            left: arguments[0], right: arguments[1]
            Naming is chosen to unify operators and function call
        keyword_arguments: 
            Dictionary of keyword arguments - only for uniform handling with functions
        function_object:
            The Siml function that the interpreter called when the function
            call was interpreted. (Because not all arguments were known at 
            compile time, an annotated function call was created.) 
        type: InterpreterObject
            Type of the results of the operation. For decorating the AST.
        role: AttributeRole
            Role of the results of the operation. For decorating the AST.
        loc: TextLocation; None
            Location in input string
    '''
    def __init__(self, operator='*_*', arguments=None, loc=None):
        super(NodeOpInfix2, self).__init__()
        self.operator = operator
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = {}  #for uniform handling with functions
        #decorations
        #self.function_object = None
        self.type = None
        self.role = RoleUnkown
        self.is_assigned = None
        #for error messages
        self.loc = loc


class NodeOpPrefix1(Node):
    '''
    AST node for a (unary) prefix operator: - not
    
    Data attributes:
        operator: 
            Operator symbol e.g.: '-'
        arguments:  tuple(Node())
            Expression on right side of operator
            Naming is chosen to unify operators and function call
        keyword_arguments: 
            Dictionary of keyword arguments - only for uniform handling with functions
        function_object:
            The Siml function that the interpreter called when the function
            call was interpreted. (Because not all arguments were known at 
            compile time, an annotated function call was created.) 
        type: InterpreterObject
            Type of the results of the operation. For decorating the AST.
        role: AttributeRole
            Role of the results of the operation. For decorating the AST.
        loc: 
            Location in input string
  '''
    def __init__(self, operator='*_*', arguments=None, loc=None):
        super(NodeOpPrefix1, self).__init__()
        self.operator = operator
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = {}  #for uniform handling with functions
        #decorations
        #self.function_object = None
        self.type = None
        self.role = RoleUnkown
        self.is_assigned = None
        #for error messages
        self.loc = loc


class NodeFuncCall(Node):
    '''
    AST node for calling a function or method.
    
    This will be usually done by inserting the code of the function's body
    into the top level function. Similar to an inline function in C++.
    
    Data attributes:
    ----------------
        name: NodeIdentifier/callable object
            expression that yields the function object, or the function 
            object that will be called. 
            The function object is present when an unevaluated function call 
            was generated.
        arguments: 
            Tuple of positional arguments
        keyword_arguments: 
            Dictionary of keyword arguments
            
        type: InterpreterObject
            Type of the results of the operation. (unevaluated function call)
        role: AttributeRole
            Role of the results of the operation. (unevaluated function call)
        is_assigned: None/True
            - None for calls that have not been processed by the interpreter.
            - True for unevaluated function calls (some arguments are unknown 
            variables). Unevaluated calls can therefore be treated like 
            unknown variables.
        loc: 
            Location in input string
            
    TODO: unify functions and operators and
    TODO: remove NodeOpInfix2, NodeOpPrefix1
    TODO:    is_operator: True/False
    TODO:    operator_placement: prefix/infix/suffix 
    '''
    #TODO: give NodeFuncCall a nice constructor
    def __init__(self, name=None, arguments=None, keyword_arguments=None, 
                 loc=None):
        super(NodeFuncCall, self).__init__()
        #TODO: rename to callable, function, function_object, callable_object
        #      because it may store a callable object, not just the object's 
        #      name. This would also allow unification with operators.
        self.name = name 
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = keyword_arguments \
                                 if keyword_arguments is not None else {}
        #--- for the type system (treatment of unevaluated calls) -----------#
        self.type = None
        self.role = RoleUnkown
        self.is_assigned = None
        #--- for error messages ---------------------------------------------#
        self.loc = loc


#-------------- Statements --------------------------------------------------
class NodePassStmt(Node):
    '''
    AST node to represent a pass statement. The pass statement does nothing.
    It is necessary to define empty compound statements (if, func, class).
    
    Data attributes:
        loc: 
            Location in input string
    '''
    def __init__(self, loc=None):
        super(NodePassStmt, self).__init__()
        self.loc = loc
        

class NodeExpressionStmt(Node):
    '''
    AST node intended for a function call. It can however contain any 
    expression. The expressions result is discarded.
    
    Data attributes:
        expression: Node()
            Expression that is evaluated. ( The expressions result is 
            discarded.) 
        loc: 
            Location in input string
    '''
    def __init__(self, expression=None, loc=None):
        super(NodeExpressionStmt, self).__init__()
        self.expression = expression
        self.loc = loc
        

class ConditionalBlock(Node):
    '''
    Building block of if ... elif ... else statement.
    
    One condition (really an expression) and a list of statements. The
    statements are executed when the condition is true. (AST node)
    
    Data attributes
    ---------------
    condition: Node()
        Expression that is evaluated. When the condition is true the 
        statements are executed. 
    statements: [Node]
        List of statements that are executed when the condition is true.
    '''
    def __init__(self, condition=None, statements=None):
        Node.__init__(self)
        self.condition = condition
        self.statements = statements
        
        
class NodeIfStmt(Node):
    '''
    AST node for an if ... elif ... else statement
    
    Data attributes
    ---------------
    cond_blocks: [ConditionalBlock]
        Each element is a condition and a list of statements. The statements 
        are executed when the condition is true.
        The first element represents an if, the next elements represent elif 
        clauses, and a last element with a constant True/1 as the condition
        represents an else. 
    '''
    def __init__(self, cond_blocks=None):
        super(NodeIfStmt, self).__init__()
        self.cond_blocks = cond_blocks if cond_blocks is not None else []


class NodeAssignment(Node):
    '''
    AST node for an assignment: 'a = 5'
    
    Data attributes:
        target: Node()
            Expression that describes which object should be changed
        expression: Node()
            Expression that computes the new value
        loc: 
            Location in input string    
    '''
    def __init__(self):
        super(NodeAssignment, self).__init__()
        self.target = None
        self.expression = None
        self.loc = None
        #self.function_object = None


#class NodePrintStmt(Node):
#    '''
#    AST Node for printing something to stdout.
#    
#    Data attributes:
#        arguments: list(Node())
#            the expressions of the argument list
#        newline: bool
#            if True: add newline to end of output;
#            if False: don't add newline.
#        loc: 
#            Location in input string    
#    '''
#    def __init__(self):
#        super(NodePrintStmt, self).__init__()
#        self.arguments = []
#        self.newline = None
#        self.loc = None


#class NodeGraphStmt(Node):
#    '''
#    AST Node for creating a graph.
#    Data attributes:
#        kids        : the expressions of the argument list
#        loc         : location in input string
#        dat         : None
#    '''
#    def __init__(self, kids=None, loc=None, dat=None):
#        super(NodeGraphStmt, self).__init__(kids, loc, dat)


#class NodeStoreStmt(Node):
#    '''
#    AST Node for storing variables
#    Data attributes:
#        kids        : the expressions of the argument list
#        loc         : location in input string
#        dat         : None
#    '''
#    def __init__(self, kids=None, loc=None, dat=None):
#        super(NodeStoreStmt, self).__init__(kids, loc, dat)


class NodeReturnStmt(Node):
    '''
    AST Node for the return statement
    Data attributes:
        arguments   : the expressions of the argument list
        loc         : location in input string
    '''
    def __init__(self, arguments=None, loc=None):
        Node.__init__(self)
        self.arguments = [] if arguments is None else arguments
        self.loc = loc


class NodePragmaStmt(Node):
    '''
    AST Node for the pragma statement
    Data attributes:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None

        options     : the arguments of the prgma statements: list of strings
    '''
    def __init__(self, kids=None, loc=None, dat=None, options=None):
        super(NodePragmaStmt, self).__init__(kids, loc, dat)
        self.options = []
        if options: self.options = options


#class NodeForeignCodeStmt(Node):
#    '''
#    AST Node for the foreign_code statement
#    Data attributes:
#        kids        : the expressions of the argument list
#        loc         : location in input string
#        dat         : None
#
#        language    : the progamming languae of the foreign code: string
#        method      : the insertion method - type of the foreign code: string
#        code        : the piece of program code that should be inserted: string
#    '''
#    def __init__(self, kids=None, loc=None, dat=None, language='', method='', code=''):
#        super(NodeForeignCodeStmt, self).__init__(kids, loc, dat)
#        self.language = language
#        self.method = method
#        self.code = code


class NodeImportStmt(Node):
    '''
    AST Node for the pragma statement
    Data attributes:
        kids        : The modulse's AST
        loc         : location in input string
        dat         : None

        moduleName : str
            Name of the module that should be imported
        fromStmt : bool
            Put the module's attributes directly into the namespace of the
            module that executes this statement. Behave as Python's "from"
            statement.
        attrsToImport : list of string
            List of attributes that should be imported. Special symbol "*"
            means all attributes in the module.
            if fromStmt == False, this list is ignored.
    '''
    def __init__(self, kids=None, loc=None, dat=None,
                 moduleName=None, fromStmt=False, attrsToImport=None):
        super(NodeImportStmt, self).__init__(kids, loc, dat)
        self.moduleName = moduleName
        self.fromStmt = fromStmt
        self.attrsToImport = [] if attrsToImport is None else attrsToImport


class NodeStmtList(Node):
    '''
    AST Node for list of statements
    
    Attributes:
    statements: list(Node())
        The list of statements.
    loc: TextLocation; None
        Location in input string
    '''
    def __init__(self):
        super(NodeStmtList, self).__init__()
        self.statements = []
        self.loc = None


class AttributeRole(object):
    '''
    Constants to denote the role of an attribute.

    Intention to create someting like enums.
    Additionally this solution provides a
    means for documentation and expresses the tree
    shaped relationship between the roles.
    '''
    pass
class RoleUnkown(AttributeRole):
    '''Role has not been determined yet.'''
    pass
class RoleConstant(AttributeRole):
    '''The attribute is a constant; it can only be changed at compile time.'''
#    userStr = 'const'
class RoleDataCanVaryAtRuntime(AttributeRole):
    '''Data that can vary while the compiled program runs. 
    Everything that is not RoleConstant. (Base class.)'''
class RoleParameter(RoleDataCanVaryAtRuntime):
    '''
    Attribute is a parameter of the simulation:
    - is constant during the simulation, but can vary between simulations.
    - is stored.
    '''
#    userStr = 'param'
class RoleVariable(RoleDataCanVaryAtRuntime):
    '''
    The attribute is a state or algebraic variable:
    - can vary during the simulation
    '''
#    userStr = 'variable'
class RoleInputVariable(RoleVariable):
    '''
    This variable is an input of the dynamic function. 
    It is computed by the solution algorithm, and it is usually regarded 
    as part of the solution.
    '''
class RoleStateVariable(RoleInputVariable):
    '''The attribute is a state variable'''
#    userStr = 'state_variable'
class RoleIntermediateVariable(RoleVariable):
    '''
    This variable is an intermediate value, that is computed inside the 
    dynamic function.
    '''
class RoleAlgebraicVariable(RoleIntermediateVariable):
    '''The attribute is an algebraic variable'''
#    userStr = 'algebraic_variable'
class RoleOutputVariable(RoleVariable):
    '''
    This variable is a returned from the simulation function.
    The solution algorithm needs this variable to compute the solution.
    '''
class RoleTimeDifferential(RoleOutputVariable):
    '''The attribute is an algebraic variable'''
#    userStr = 'algebraic_variable'


class NodeDataDef(Node):
    '''
    AST node for definition of a variable, parameter or submodel.
    Data Attributes:
        loc             : location in input string

        default_value   : Default value, initial value, value of a constant; interpreted
                          according to context. (mathematical expression)
                          (propperty stored in kids[0])

        name            : name of the attribute. DotName
        class_spec      : type of the new attribute; NodeIdentifier or NodeFuncCall
        role            : Is this attribute a state or algebraic variable, a constant
                          or a parameter? (AttributeRole subclass).
    '''
    def __init__(self, name=None, class_spec=None, role=RoleConstant, loc=None):
        Node.__init__(self)
        self.name = DotName(name) if name is not None else None
        self.class_spec = class_spec 
        self.role = role
        self.default_value = None


class NodeCompileStmt(NodeDataDef):
    '''
    AST node for compile statement.
    A data statement where the the functions are instantiated for flattening
    and code generation.

    mainFuncs : List of (generated) main functions: [NodeFuncDef]
    '''
    def __init__(self):
        NodeDataDef.__init__(self)
        self.role = RoleVariable


class NodeFuncArg(Node):
    '''
    One argument of a function 
    
    Attributes:
        name: DotName
            Name of argument
        type:
            Type of argument
        default_value:
            default value
        loc:
            Location in input file
    '''
    def __init__(self, name=None, type=None, default_value=None):
        Node.__init__(self)
        self.name = DotName(name)
        self.type = type 
        self.default_value = default_value
        self.loc = None
        
        
        
class SimpleArgumentList(Node):
    """
    Contains arguments of a function definition.
    - Checks the arguments when function definition is parsed
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
        Node.__init__(self)
        
        #special case copy construction
        if isinstance(arguments, SimpleArgumentList):
            loc = arguments.loc
            arguments = arguments.arguments

        #--- the primary data ------------------------------------------#
        #place in program text where function is defined
        self.loc = loc            
        #list of argument definitions [ast.NodeFuncArg, ...]
        self.arguments = arguments
        #--- convenience values -----------------------------------------#
        #dictionary for quick access to argument definitions by name
        #also for testing uniqueness and existence of argument names 
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
                                    'keyword arguments!', loc, errno=1064110)
            #test: argument names must be unique
            if arg.name in self.argument_dict:
                raise UserException('Duplicate argument name "%s"!' 
                                    % str(arg.name), loc, errno=1064120) 
            self.argument_dict[arg.name] = arg



class NodeFuncDef(Node):
    """
    AST node for method/function definition.

    A function/method is comparable to an inline function or a template
    function in C++.

    The childern are the statements.
    
    Attributes:
        name: DotName
            Name of the function
        arguments:
            Positional arguments
        keyword_arguments:
            Keyword arguments
        statements: list(Node()]
            Statements of function body
        return_type: 
            Class name of return value; tuple of strings: ('Real',)???
        loc: 
            Location in input string
    """
    def __init__(self):
        Node.__init__(self)
        self.name = DotName()
        self.arguments = SimpleArgumentList([])
        self.statements = []
        self.return_type = None
        self.loc = None



#class NodeGenFunc(NodeFuncDef):
#    '''
#    Generated function, expanded template; ready for flattening.
#
#    The missing information of the NodeFuncDef is filled in. These "functions"
#    exist once for each time a function is called. To distinguish them from
#    functions writen by the user, this Node type is necessary.
#
#    Attributes:
#    -----------
#    targetName :
#            Individual name for each generated instance. Used in flattening
#            process to give individual names to the local variables.
#    '''
#    def __init__(self, kids=None, loc=None, dat=None, name=None,
#                  returnType=None):
#        NodeFuncDef.__init__(self, kids, loc, dat, name, returnType)
#        self.targetName = None


class NodeClassDef(Node):
    """
    AST node for class definition.
    
    Data Attributes:
    name: DotName
        name of the class defined here.
    arguments: list(Node())
        Constructor arguments, the expressions between the brackets
    statements: list(Node())
        the statements of the class body
    loc: 
        location in input string, and file name
    """
    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        self.loc = None


class NodeModule(Node):
    '''
    Root node of a module (or of the program)
    Data Attributes:
    name: 
        Name of the module
    statements: list(Node())
        the statements of the class body
    loc: 
        location in input string (~0)
    '''
    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.statements = []
        self.loc = None


#class NodeFlatModule(Node):
#    '''
#    Module where all attributes have long, dotted names, and where all
#    attributes are defined on the top (module) level.
#    Data defs are only built in types.
#
#    Attributes:
#    kids      : Definitions, the program's code.
#    loc       : location in input string (~0)
#    dat       : None
#
#    name      : Name of the module
#    targetName: Name useful in the context of flattening or code generation
#    '''
#    def __init__(self, kids=None, loc=None, dat=None, name=None):
#        Node.__init__(self, kids, loc, dat)
#        self.name = name
#        self.targetName = None

#---------- Nodes End --------------------------------------------------------*

#class DepthFirstIterator(object):
#    """
#    Iterate over each node of a (AST) tree, in a depth first fashion.
#    Designed for Node and its subclasses. It works for other nodes though:
#    The nodes must have the functions __getitem__ and __len__.
#
#    Usage:
#    >>> t1 = Node([Node([Node([],3,'leaf'), Node([],4,'leaf')], 2, 'branch'),
#    ...            Node([],5,'leaf')], 1, 'root')
#    >>> for n in DepthFirstIterator(t1):
#    ...     print n.dat
#    ...
#    root
#    branch
#    leaf
#    leaf
#    leaf
#    """
#    #TODO: Find out if this is really depth first iteration.
#
#    def __init__(self, treeRoot, returnDepth=False):
#        """
#        treeRoot    : root node of the tree over which the iterator goes.
#        returnDepth : if True the __next__ function returns a tuple
#                      (node, depth) otherwise it only returns the current
#                      node.
#        """
# 
#        raise Exception('DepthFirstIterator: Feaature not implemented!')
#        #TODO: make it work with new node class again!
#        self.stack = [(treeRoot, 0)] #tuples (node, childIndex).
#        self.depth = 0  #how deep we are in the tree.
#        self.returnDepth = returnDepth #flag: shoult we return the current depth
#        self.start = True #remember that we've just been initialized
#
#
#    def __iter__(self):
#        '''Called at start of for loop.'''
#        return self
#
#
#    #TODO: enhance DepthFirstIterator: remember already seen nodes in set.
#    #TODO: make possible child[i] == None
#    def next(self):
#        '''Go to the next node, return current node.'''
#        #After tree has been traversed throw exception, don't start again
#        if len(self.stack) == 0:
#            raise StopIteration
#        #start: special handling
#        if self.start:
#            self.start = False
#            currNode, currChild = self.stack[-1]
#            return self._createReturnVals(currNode, currChild)
#
#        #go to next node.
#        #get current state, from top of stack
#        currNode, currChild = self.stack[-1]
#
#        #if all children visited: go up one or more levels
#        while currChild == len(currNode):
#            self.stack.pop()
#            #stop iterating, if no nodes are left on the stack
#            if len(self.stack) == 0:
#                raise StopIteration
#            self.depth -= 1
#            currNode, currChild = self.stack[-1] #get state from one level up
#
#        #remember to visit next child when we come here again
#        self.stack[-1] = (currNode, currChild+1)
#        #TODO: Make iterator work also with objects that are not children of Node;
#        #TODO: or make iterator throw an erception with useful error message when
#        #      non Node object is discovered
#        #get node that will be visited next
#        nextNode = currNode[currChild]
#        #go to one level down, to current child.
#        self.stack.append((nextNode, 0))
#        self.depth += 1
#        #return the next node
#        return self._createReturnVals(nextNode, self.depth)
#
#
#    def _createReturnVals(self, node, depth):
#        if self.returnDepth:
#            return (node, depth)
#        else:
#            return node



class DotName(tuple):
    '''
    Class that represents a dotted name ('pr1.m1.a').

    This class inherits from tuple, but can be sensibly constructed
    from a string: The dots are used to separate tuple components.
    >>> dn = DotName('a.b.c')
    >>> dn
    DotName('a.b.c')
    >>> tuple(dn)
    ('a', 'b', 'c')

    The str() function converts the object back to a dotted name.
    >>> str(dn)
    'a.b.c'

    The object can be freely mixed with tuples.
    >>> dn == ('a', 'b', 'c')
    True
    >>> dn + ('d', 'e', 'f')
    DotName('a.b.c.d.e.f')
    '''
    #Immutable classes are created by the _new_(...) method.
    def __new__(cls, iterable=None):
        '''Create tuple. Strings get special treatment.'''
        #Interpret string as dot separated list (of strings)
        if isinstance(iterable, str):
            iterable = iterable.split('.')
        #Special handling for no arguments (DotName())
        if iterable == None:
            return tuple.__new__(cls)
        else:
            return tuple.__new__(cls, iterable)

    def __str__(self):
        '''Create string with dots between tuple components.'''
        return '.'.join(self)

    def __repr__(self):
        '''Create string representation that can be used in Python program'''
        return "DotName('" + self.__str__() + "')"

    def __add__(self, other):
        '''Concatenate with tuple or DotName. Return: self + other.'''
        if isinstance(other, str):
            other = DotName(other)
        return DotName(tuple.__add__(self, other))

    def __radd__(self, other):
        '''Concatenate with tuple or DotName. Return: other + self.'''
        if isinstance(other, str):
            other = DotName(other)
        return DotName(tuple.__add__(other, self))

    def __getitem__(self, key):
        '''Access a part of the dotname. Called for foo[1], foo[0:4] '''
        #slices of DotName objects should also be DotName objects (not tuple).
        if isinstance(key, slice):
            return DotName(tuple.__getitem__(self, key))
        #access to single items should return the item (string not DotName).
        else:
            return tuple.__getitem__(self, key)

    def __getslice__(self, i, j):
        '''Implement simple slicing (because tuple implements it).'''
        return DotName(tuple.__getslice__(self, i, j))



class UserException(Exception):
    '''Exception that transports user visible error messages'''
    def __init__(self, message, loc=None, errno=None):
        Exception.__init__(self)
        self.message = message
        '''The error message'''
        self.loc = loc
        '''Position in the input string, where the error occured.
        Includes input string and file name'''
        self.errno = errno

    def __str__(self):
        if self.errno is None:
            num_str = ''
        else:
            num_str = '(#%s) ' % str(self.errno) 
        return 'Error! ' + num_str + self.message + '\n' + str(self.loc) + '\n'



#class MultiErrorException(UserException):
#    '''Exception with many (user visible) error messages'''
#    def __init__(self, errTupList):
#        '''
#        Arguments:
#            errTupList : iterable (list) with tuples (message, loc)
#        '''
#        #init base class with first error; at least kind of sensible
#        msg1, loc1 = errTupList[0]
#        UserException.__init__(self, msg1, loc1)
#        self.errTupList = errTupList
#        '''iterable (list) with tuples (message, loc)'''
#
#    def __str__(self):
#        errMsg = 'Error!\n'
#        for msg1, _loc1 in self.errTupList:
#            errMsg += '%s \n    %s \n' % (msg1, str(self.loc))
#        errMsg += '------------------------\n'
#        errMsg += 'Total: %d Error(s).' % len(self.errTupList)
#        return errMsg



class TextLocation(object):
    '''
    Store the location of a parsed pattern, or error.

    Includes the file's contents and the file's name.
    Object is intended to be stored in a Node's self.loc
    data member.
    '''

    def __init__(self, atChar=None, textString=None, fileName=None):
        super(TextLocation, self).__init__()
        self.atChar = atChar
        self.str = textString
        self.name = fileName

    def isValid(self):
        '''
        Return True if a meaningful line number and collumn can be computed.
        Return False otherwise.
        '''
        if self.atChar and self.str:
            return True
        else:
            return False

    def lineNo(self):
        '''Compute the line number of the stored location.'''
        if self.atChar and self.str:
            return pyparsing.lineno(self.atChar, self.str)
        else:
            return 0

    def col(self):
        '''Compute the column of the stored location.'''
        if self.atChar and self.str:
            return pyparsing.col(self.atChar, self.str)
        else:
            return 0

    def fileName(self):
        '''Return the filename.'''
        return str(self.name)

    def __str__(self):
        '''Return meaningfull string'''
        #Including the column is not useful because it is often wrong
        #for higher level errors. Preserving the text of the original
        #pyparsing error is transporting the column information for parsing
        #errors. Only parsing errors have useful column information.
        return '  File "' + self.fileName() + '", line ' + str(self.lineNo())



#TODO: make class work with inherited handler methods.
class Visitor(object):
    '''
    Visitor for the AST

    This class is useful when there are decisions necessary based on the type
    of an object. The class is an alternative to big if statements that
    look like this:

    if isinstance(node, NodeClassDef):
        .....
    elif isinstance(node, NodeFuncDef):
        ....
    elif isinstance(node, NodeDataDef):
        ....
    .....
    .....

    Features:
    - A designated (handler) method is called for each type.
    - Single dispatch
    - Switching which method is used is done based on type and
      inheritance
    - Ambigous situations can be avoided with a priority value. Functions with
      high priority values are considered before functions with low priority
      values.
    - The algorithm for matching is 'issubclass'.
    - Association between type and method is done with decorators.

    USAGE:
    ------
        - Define class that inherits from Visitor
        - Use @Visitor.when_type(classObject, priority) to define a handler
          method for a speciffic type.
        - Use @Visitor.default for the default function, which is called when
          no handler method matches.
        - In the main loop use self.dispatch(theObject) to call the appropriate 
          handler method.

    >>> class NodeVisitor(Visitor):
    ...     def __init__(self):
    ...         Visitor.__init__(self)
    ...     @Visitor.when_type(NodeClassDef)
    ...     def visitClassDef(self, classDef):
    ...         print 'seen class def'
    ...     @Visitor.when_type(NodeFuncDef)
    ...     def visitFuncDef(self, funcDef):
    ...         print 'seen func def'
    ...     def mainLoop(self, node_list):
    ...         for node in node_list:
    ...             self.dispatch(node)

    >>> nl = []
    >>> nl.append(NodeClassDef())
    >>> nl.append(NodeClassDef())
    >>> nl.append(NodeFuncDef())
    >>> nl.append(NodeFuncDef())
    >>> nv = NodeVisitor()
    >>> nv.mainLoop(nl)
    seen class def
    seen class def
    seen func def
    seen func def
    
    An example with priorities is part of the unit tests:
    TestVisitor.test_priority_2

    CREDITS
    -------
    Ideas were taken from:
    Phillip J. Eby's 'simplegeneric' library and his very good online articles:
    http://cheeseshop.python.org/pypi/simplegeneric/0.6
    http://peak.telecommunity.com/DevCenter/VisitorRevisited

    External documentation:
    - Single dispatch:
    See: http://cheeseshop.python.org/pypi/simplegeneric/0.6
    See: http://peak.telecommunity.com/DevCenter/VisitorRevisited
    - Multiple dispatch:
    See: http://www.artima.com/weblogs/viewpost.jsp?thread=101605
    See: http://gnosis.cx/download/gnosis/magic/multimethods.py
    - Introduction to Decorators
    http://personalpages.tds.net/~kent37/kk/00001.html

    Thanks to all authors for writing high quality online articles
    and free software.
    '''

    def __init__(self):
        cls = self.__class__
        #Create rule table and cache only once.
        #TODO: make sure that only '_ruleTable' in most derived class is found.
        if not hasattr(cls, '_ruleTable'):
            #List of types, functions and priorities
            cls._ruleTable = []
            #Dictionary of types and functions, no inheritance is considered
            #TODO: better self._cache ??? currently:
            #  - all instances use same cache: OK
            #  - when new visitor is instanciated the cache is emptied: Bad 
            cls._cache = {}
            #populate the rule table if necessary
            self._createRuleTable()


    def dispatch(self, inObject, *args):
        '''
        Call the different handler functions depending on the type of inObject
        '''
        cls = self.__class__
        objCls = inObject.__class__
        #search handler function in cache
        handlerFunc = cls._cache.get(objCls, None)    #IGNORE:E1101
        if handlerFunc is None:
            #Handler function is not in cache
            #search handler function in rule table and store it in cache
            handlerFunc = self._findFuncInRuleTable(objCls)
            cls._cache[objCls] = handlerFunc    #IGNORE:E1101
        return handlerFunc(self, inObject, *args) #IGNORE:W0142


    def _simpleDefaultFunc(self, inObject, *args):
        raise TypeError('No function to handle type %s in class %s'
                        % (str(type(inObject)), str(type(self))))


    @classmethod
    def _findFuncInRuleTable(cls, objCls):
        '''
        Find a function to handle a given class in the rule table.
        If no matching rules could be found return the default rule

        The algorithm for matching is 'issubclass'
        '''
        #find handler function for class 'objCls'
        for func1, cls1, _prio1 in cls._ruleTable:
            if issubclass(objCls, cls1):
                return func1
        #no specific handler could be found: return the default function
        func1, cls1, _prio1 = cls._ruleTable[-1] #IGNORE:E1101
        return func1


    @classmethod
    def _createRuleTable(cls):
        '''
        Create the rule table.
        Look at all methods of the class, if they have
        _dispatchIfType and _dispatchPriority attributes
        put them into the rule table.

        - The rule table is sorted according to _dispatchPriority.
        - If _dispatchIfType has the value None the function is considered
          the default function
        '''
        ruleTable = []
        defaultFunc = Visitor._simpleDefaultFunc #IGNORE:W0212
        #TODO: look into methods of parent classes too
        #loop over the class' attributes and put them into the table if appropriate
        for func in cls.__dict__.itervalues():
            if not isinstance(func, FunctionType):
                continue
            if not (hasattr(func, '_dispatchIfType') and
                    hasattr(func, '_dispatchPriority')):
                continue
            if func._dispatchIfType == None: #IGNORE:W0212
                defaultFunc = func
            else:
                ruleTable.append((func, func._dispatchIfType, func._dispatchPriority)) #IGNORE:W0212
        #sort rule table according to priority
        getPrio = lambda tup: tup[2]
        ruleTable.sort(key=getPrio, reverse=True)
        #put default function at end of table
        ruleTable.append((defaultFunc, NoneType, 0.0))
        #store the tble in the most derived class
        cls._ruleTable = ruleTable


    @staticmethod
    def when_type(inType, inPriority=1.0):
        '''
        Decorator to mark a method with some extra data members that carry
        information with which argument type it should be invoked.

        Use as decorator in method definition:
            @Visitor.when_type(int, 5)
            def handleInt(self, intVal):
                .....

        ARGUMENTS:
            inType     : The type of the (second) argument for which
                         the decorated method is associated.
                         TODO: May also be a tuple of types.
            inPriority : The priority if multiple methods fit on one type.
                         Higher numbers mean higher priority.
        '''
        #Test if arguments are of the required type
        legalTypes = (type, ClassType)
        if not isinstance(inType, legalTypes):
            raise TypeError(
                'Visitor.when_type: Argument 1 must be a type or class, but it is: %s'
                % str(type(inType)))
        if not isinstance(inPriority, (int, float)):
            raise TypeError(
                'Visitor.when_type: Argument 2 must be an int or float number, '
                'but it is: %s'
                % str(type(inPriority)))
        #create function that really attatches the decorations
        #(the extra data members)
        def decorateWithType(funcToDecorate):
            if not isinstance(funcToDecorate, FunctionType):
                raise TypeError(
                    'Visitor.when_type: Can only decorate class methods, '
                    'but I got: %s'
                    % str(type(funcToDecorate)))
            funcToDecorate._dispatchIfType = inType
            funcToDecorate._dispatchPriority = float(inPriority)
            return funcToDecorate
        #give the decorator function to the Pyton interpreter;
        #the interpreter will call the function.
        return decorateWithType


    @staticmethod
    def default(funcToDecorate):
        '''
        Decorator to mark a function as the default function

        Use as decorator in method definition:
            @Visitor.default
            def handleAnyType(self, val):

        The decorated method will have the least priority.
        There can be only one default function in a class definition.
        '''
        if not isinstance(funcToDecorate, FunctionType):
            raise TypeError(
                'Visitor.default: Can only decorate class methods, '
                'but I got: %s \n'
                '(No arguments for @Visitor.default are allowed)'
                % str(type(funcToDecorate)))
        funcToDecorate._dispatchIfType = None
        funcToDecorate._dispatchPriority = 0.0
        return funcToDecorate



if __name__ == '__main__':
    # Self-testing code goes here.

    #perform the doctests
    import doctest
    doctest.testmod()

    pass