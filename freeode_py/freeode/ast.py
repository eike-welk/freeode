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

#import freeode.third_party.pyparsing as pyparsing
from freeode.util import AATreeMaker

#version of the Siml compiler.
PROGRAM_VERSION = '0.4.0a3'
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
    
    #Object that creates an ASCII art tree from nodes
    __siml_aa_tree_maker__ = AATreeMaker()
    
    #we don't own instances of these classes.
    #tuple of types that are not copied deeply
    _weak_types = weakref.ProxyTypes + (weakref.ReferenceType,)
    
    def __init__(self, **args): 
        '''Create an attribute for each named argument.'''
        object.__init__(self)
        for key, value in args.iteritems():
            setattr(self, key, value)
            
    def aa_make_tree(self):       
        '''
        Create ASCII-art tree of this object, and of all data attributes it 
        contains recursively.
        '''
        return self.__siml_aa_tree_maker__.make_tree(self)   
             
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
#--------- Expression --------------------------------------------------------------
class NodeFloat(Node):
    '''
    Represent a real number in the AST.
    Example: 123.5
    Data attributes:
        loc     : location in input string
        value   : the number as a string???
    '''
    def __init__(self, value=None, loc=None):
        super(NodeFloat, self).__init__()
        self.value = value
        self.loc = loc


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
        name: str()
            Name of attribute: ('a')
        loc: 
            Location in input string
    '''
    def __init__(self, name=None, loc=None):
        Node.__init__(self)
        self.name = name
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
    def __init__(self, arguments=None, loc=None):
        super(NodeParentheses, self).__init__()
        #--- function call aspect -------------------------------------------#
        #self.function = None 
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = {}
        #unknown variable aspect
        self.type = None
        self.role = RoleUnkown
        self.is_known = None
        #--- information flow graph construction ----------------------------#
        self.inputs = None
        #for error messages
        self.loc = loc


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
        #--- function call aspect -------------------------------------------#
        self.function = None 
        self.operator = operator
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = {}  #for uniform handling with functions
        #decorations
        #self.function_object = None
        self.type = None
        self.role = RoleUnkown
        self.is_known = None
        #--- information flow graph construction ----------------------------#
        self.inputs = None
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
        #--- function call aspect -------------------------------------------#
        self.function = None 
        self.operator = operator
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = {}  #for uniform handling with functions
        #decorations
        self.type = None
        self.role = RoleUnkown
        self.is_known = None
        #--- information flow graph construction ----------------------------#
        self.inputs = None
        #for error messages
        self.loc = loc


class NodeFuncCall(Node):
    '''
    AST node for calling a function or method.
    
    This will be usually done by inserting the code of the function's body
    into the top level function. Similar to an inline function in C++.
    
    Data attributes:
    ----------------
        function: NodeIdentifier/callable object
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
        is_known: None/False
            - None for calls that have not been processed by the interpreter.
            - False for unevaluated function calls (some arguments are unknown 
            variables). Unevaluated calls can therefore be treated like 
            unknown variables.
        loc: 
            Location in input string
    '''
    #TODO: give NodeFuncCall a nice constructor
    def __init__(self, function=None, arguments=None, keyword_arguments=None, 
                 loc=None):
        super(NodeFuncCall, self).__init__()
        #--- function call aspect -------------------------------------------#
        self.function = function 
        self.arguments = arguments if arguments is not None else tuple()
        self.keyword_arguments = keyword_arguments \
                                 if keyword_arguments is not None else {}
        #--- for the type system (treatment of unevaluated calls) -----------#
        self.type = None
        self.role = RoleUnkown
        self.is_known = None
        #--- information flow graph construction ----------------------------#
        self.inputs = None
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
        

class NodeClause(Node):
    '''
    Building block of if ... elif ... else statement. (AST node)
    
    A clause consists of a condition (really an expression) and a list of 
    statements. The statements are executed when the condition is true. 
    This is inspired by Lisp's 'cond' special-function.
    http://www.cis.upenn.edu/~matuszek/LispText/lisp-cond.html
    
    Data attributes
    ---------------
    condition: Node()
        Expression that is evaluated. When the condition is true the 
        statements are executed. 
    statements: [Node]
        List of statements that are executed when the condition is true.
    loc: TextLocation
        Location in the program text which is represented by the node. 
        (For error messages.)    
    '''
    def __init__(self, condition=None, statements=None, loc=None):
        Node.__init__(self)
        self.condition = condition
        self.statements = statements
        #--- errors -----
        self.loc = loc
        #--- data flow analysis -------
        self.inputs = None
        self.outputs = None
        
        
class NodeIfStmt(Node):
    '''
    AST node for an if ... elif ... else statement
    
    TODO: maybe rename to NodeCondStmt ???
    
    Data attributes
    ---------------
    clauses: [NodeClause]
        Each element is a condition and a list of statements. The statements 
        are executed when the condition is true.
        The first element represents an if, the next elements represent elif 
        clauses, and a last element with a constant True/1 as the condition
        represents an else. 
    loc: TextLocation
        Location in the program text which is represented by the node. 
        (For error messages.)    
    '''
    def __init__(self, clauses=None, loc=None):
        super(NodeIfStmt, self).__init__()
        self.clauses = clauses if clauses is not None else []
        #--- errors -----
        self.loc = loc
        #--- data flow analysis -------
        self.inputs = None
        self.outputs = None


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
        #--- errors -----
        self.loc = None
        #--- data flow analysis -------
        self.inputs = None
        self.outputs = None


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
            
    TODO: For desingning this facility also look at:
          http://docs.python.org/library/functions.html#__import__
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


class EnumMeta(type):
    '''Metaclass for the Enum class. Contains Enum's magic __repr__ method'''
    def __repr__(self):
        return self.__name__
    
class Enum(object):
    '''
    Class for use as an enum or global constant.
    
    Don't instantiate this class! Inherit from it, and use the class object 
    itself as the enum or constant. When the class is converted to a 
    string it becomes its own class name. This is nice for debugging or pretty 
    printing.
    
    The class has a custom metaclass: EnumMeta.
    >>> type(Enum)
    <class 'freeode.ast.EnumMeta'>
    
    USAGE:
    ------
    >>> class EAST(Enum): pass
    >>> class WEST(Enum): pass
    >>> class NORTH(Enum): pass
    >>> class SOUTH(Enum): pass
    
    >>> print NORTH, SOUTH, EAST, WEST
    NORTH SOUTH EAST WEST
    '''
    __metaclass__ = EnumMeta
    

class AttributeRole(Enum):
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
    '''The attribute is a time derivative'''
#    userStr = 'algebraic_variable'


class NodeDataDef(Node):
    '''
    AST node for definition of a variable, parameter or submodel.
    Data Attributes:
        loc             : location in input string

        default_value   : Default value, initial value, value of a constant; interpreted
                          according to context. (mathematical expression)
                          (propperty stored in kids[0])

        name            : name of the attribute. str
        class_spec      : type of the new attribute; NodeIdentifier or NodeFuncCall
        role            : Is this attribute a state or algebraic variable, a constant
                          or a parameter? (AttributeRole subclass).
    '''
    def __init__(self, name=None, class_spec=None, role=RoleConstant, loc=None):
        Node.__init__(self)
        self.name = name
        self.class_spec = class_spec 
        self.role = role
        self.default_value = None
        self.loc = loc


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
        name: str
            Name of argument
        type: ast.Node usually ast.NodeIdentifier
            Type of argument
        default_value: ast.Node usually ast.NodeAttrAccess or ast.NodeFloat
            default value
        loc:
            Location in input file
    '''
    def __init__(self, name=None, type=None, default_value=None): #pylint:disable-msg=W0622
        Node.__init__(self)
        self.name = name
        self.type = type 
        self.default_value = default_value
        self.loc = None
        
        
        
class SimpleSignature(Node):
    """
    Contains arguments of a function definition and the return type.
    """
    def __init__(self, arguments=None, return_type=None, loc=None):
        '''
        ARGUMENTS
        ---------
        arguments: [ast.NodeFuncArg, ...] or SimpleSignature
            The functions arguments
        return_type: ast.Node usually ast.NodeIdentifier
            Type of the function's return value.
        loc: ast.TextLocation 
            Location where the function is defined in the program text.
        '''
        Node.__init__(self)
        
        #special case copy construction
        if isinstance(arguments, SimpleSignature):
            loc = arguments.loc
            arguments = arguments.arguments

        self.arguments = arguments if arguments is not None else []
        self.return_type = return_type
        self.loc = loc            



class NodeFuncDef(Node):
    """
    AST node for method/function definition.

    A function/method is comparable to an inline function or a template
    function in C++.

    The childern are the statements.
    
    Attributes:
        name: str
            Name of the function
        signature: SimpleSignature
            The function arguments (positional- and keyword-arguments) with 
            type annotations.
        statements: list(Node()]
            Statements of function body
        loc: 
            Location in input string
    """
    def __init__(self, name, signature, statements, loc=None):
        Node.__init__(self)
        self.name = name
        self.signature = signature #SimpleSignature([])
        self.statements = statements #[]
        self.loc = loc



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
    name: str
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
#        #TODO: or make iterator throw an exception with useful error message when
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

 

#TODO: make class work with inherited handler methods.
class Visitor(object):
    '''
    #TODO: abandon this code and replace by a suitable library! (No need to invent the wheel myself again.)
    #TODO: Replacement library should also support type checking!
    
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
        # pylint: disable-msg=W0212
        cls = self.__class__
        objCls = inObject.__class__
        #search handler function in cache
        handlerFunc = cls._cache.get(objCls, None)    
        if handlerFunc is None:
            #Handler function is not in cache
            #search handler function in rule table and store it in cache
            handlerFunc = self._findFuncInRuleTable(objCls)
            cls._cache[objCls] = handlerFunc    
        return handlerFunc(self, inObject, *args) 


    def _simpleDefaultFunc(self, inObject, *_args):
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

    pass #pylint: disable-msg=W0107