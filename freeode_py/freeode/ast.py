# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2008 by Eike Welk                                       #
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


#TODO: Properties are currently undocumented in AST classes!
#TODO: Unit tests for the more complex Nodes would be useful.


from __future__ import division

from types import ClassType, FunctionType, NoneType #, TupleType, StringType
import copy
import pyparsing


##TODO: svn command: svn propset svn:keywords Revision ast.py
#__fileVersion__ = "$LastChangedRevision: 43 $"
#__fileVersion__ = "$Rev: 43 $"


#version of the Siml compiler.
progVersion = '0.3.2-dev-1'



class DuplicateAttributeError(Exception):
    '''
    Exception raised by NameSpace 
    when the user tries to redefine an attribute.
    '''
    def __init__(self, msg=None, duplicateAttribute=None):
        Exception.__init__(self, msg)
        self.duplicateAttribute = duplicateAttribute
        
        
class NameSpace(object):
    '''
    Name space for modules, classes and functions. 
    '''
    def __init__(self):
        #the attributes of this name space
        self.nameSpaceAttrs = {}
        #the next upper level name space
        self.enclosingScope = None
        #This object's name in the enclosing scope
        self.name = None
        
        
    def setAttr(self, name, newAttr):
        '''
        Add new attribute to the name space.
        
        Attributes can exist multiple times.
        
        Parameters
        ----------
        name: str, DotName
            Name of the new attribute
        newAttr: NodeDataDef, NodeClassDef, NodeFuncDef, NodeModule
            The new attribute, which is added to the name space.
        '''
        #Argument type checking and compatibility with DotName
        if isinstance(name, DotName):
            if len(name) > 1:
                raise Exception('DotName must have only one component!' 
                                + ' str(name): ' + str(name))
            name = str(name)
        elif not isinstance(name, str):
            raise Exception('Argument name must be of type str or DotName! type(name): ' 
                            + str(type(name)) + ' str(name): ' + str(name))
        #add attribute to name space
        #TODO: Functions get a function resolution object, (a list at first)
        if name in self.nameSpaceAttrs:
            raise DuplicateAttributeError('Duplicate attribute: ' + name, name)
            #TODO: special handling for functions: add function to function resolution object
        self.nameSpaceAttrs[name] = newAttr #This is a new attribute
        return
            
    def hasAttr(self, name):
        '''
        Test if attribute exists in this name space.
        
        Parameter
        ---------
        name: str, (DotName with one element)
            Attribute name to be tested.
            
        Returns
        ------- 
        bool
            True if a attribute of this name exists in this name space, 
            False otherwise.
        '''
        return str(name) in self.nameSpaceAttrs
    
    def getAttr(self, name, default=None):
        '''Return attribute with that name from this name space'''
        return self.nameSpaceAttrs.get(str(name), default)
        
    def findDotName(self, dotName, default=None):
        '''
        Find a dot name starting from this name space.
        
        Takes scope rules into account, and the lookup is maybe recursive.
        '''
        #TODO: make compatible with str too
        firstPart = self.nameSpaceAttrs.get(dotName[0], None)
        if firstPart is not None:
            #leftmost part of name exists in this name space
            if len(dotName) == 1:
                #only one part in dot name, the user wants this attribute
                return firstPart 
            elif isinstance(firstPart, NameSpace):
                #attribute is name space, try to resolve rest of name
                return firstPart.findDotName(dotName[1:], default)
            else:
                return default
        else:
            #leftmost part of name does not exist in this name space
            if self.enclosingScope is not None:
                #try to find name in higher level of scope hierarchy:
                # function --> class --> module 
                return self.enclosingScope.findDotName(dotName, default)
            else:
                return default
    
    def setEnclosingScope(self, uplevelScope):
        '''
        Change the upper level name space, 
        that is searched when a DotName is not found this name space.
        
        Used by self.findDotName(...), but not by self.getAttr(...).
        '''
        self.enclosingScope = uplevelScope

    def update(self, otherNameSpace):
        '''
        Put attributes of otherNameSpace into this name space.
        Raises exceptions when attributes are redefined.
        '''
        for name, node in otherNameSpace.nameSpaceAttrs.iteritems():
            self.setAttr(name, node)


class Node(object):
    '''
    Building block of a n-ary tree structure.
    The abstract syntax tree (AST), and the intermediate language tree (ILT),
    are made of nodes that have this class as their base class.

    Usage:
    >>> t1 = Node([Node([Node([],3,'leaf'), Node([],4,'leaf')], 2, 'branch'),
    ...            Node([],5,'leaf')], 1, 'root')

    print tree (loc attribute is abused here)(<BLANKLINE> does not work):
    > print t1
    Node:: dat: root loc: 1
    |   Node:: dat: branch loc: 2
    |   |   Node:: dat: leaf loc: 3
    |   |   Node:: dat: leaf loc: 4
    |   Node:: dat: leaf loc: 5

    access to children with  [] operator:
    >>> t1[0][1]
    Node(,[], 4, 'leaf')

    iterating over only the children of a node:
    >>> for n in t1:
    ...     print n.loc
    ...
    2
    5

    iterating over the whole tree:
    >>> for n,d in t1.iterDepthFirst(returnDepth=True):
    ...     print n.dat, ' depth: ', d
    ...
    root  depth:  0
    branch  depth:  1
    leaf  depth:  2
    leaf  depth:  2
    leaf  depth:  1
    '''

    def __init__(self, kids=None, loc=None, dat=None):
        #TODO: write an init function that can accept any number of named arguments
        #Variabe number of arguments:
        #*args    : is a list of all normal arguments
        #**kwargs : is a dict of keyword arguments
        #Code for derived classes: super(A, self).__init__(*args, **kwds)
        #self.parent = None
        #list of children
        self.kids = []
        #appendChild checks the type
        if kids is not None:
            for child in kids:
                self.appendChild(child)
        #the node's location in the parsed text
        self.loc  = loc
        #any data; whatever is appropriate
        self.dat = dat


    def __repr__(self):
        '''Create string representation that can also be used as code.'''
        className = self.__class__.__name__
        childStr = ',' + repr(self.kids)
        #if location and contents have their default value, don't print them
        if self.loc == None:
            locStr = ''
        else:
            locStr = ', ' + repr(self.loc)
        if self.dat == None:
            datStr =''
        else:
            datStr = ', ' + repr(self.dat)
        #treat all other nameSpaceAttrs as named nameSpaceAttrs
        standardAttributes = set(['kids', 'loc', 'dat'])
        extraAttrStr=''
        for key, attr in self.__dict__.iteritems():
            if key in standardAttributes:
                continue
            extraAttrStr += ', ' + key + '=' + repr(attr)
        #assemble the string
        reprStr = className  + '(' + childStr + locStr + datStr + \
                                    extraAttrStr + ')'
        return reprStr


    def __str__(self):
        '''Create pretty printed string represntation.'''
        return TreePrinter(self).makeTreeStr()

    def __iter__(self):
        '''let for loop iterate over children'''
        return self.kids.__iter__()

    def __len__(self):
        '''return number of children'''
        return len(self.kids)

    def appendChild(self, inNode):
        '''Append node to list of children'''
        #test if child is a node
        if(not isinstance(inNode, Node)):
            raise TypeError('Children must inherit from Node!')
        self.kids.append(inNode)

    def insertChild(self, index, inNode):
        '''
        Insert node into list of children.
        New child is inserted before the child at position self[index].
        '''
        #test if child is a node
        if(not isinstance(inNode, Node)):
            raise TypeError('Children must inherit from Node!')
        self.kids.insert(index, inNode)

    def insertChildren(self, index, inSequence):
        '''
        Insert a node's children into list of own children.
        
        New childen are inserted before the child at position self[index].
        
        Parameters
        ----------
        index: int
            The children are inserted before the this index.
        inSequence: Node
            Container of the children that will be inserted.
        
        Returns
        -------
        None
        '''
        if(not isinstance(inSequence, Node)):
            raise TypeError('Node.insertChildrenChildren: '
                            'argument 2 must inherit from Node!')
        self.kids[index:index] = inSequence.kids

    def __delitem__(self, index):
        '''Delete child at specified index'''
        del self.kids[index]

    def __getitem__(self, i):
        '''
        Retriev children through []
        
        Parameters
        ----------
        i: int, slice
            Index of element which is retrieved, or slice object describing 
            the subsequence which should be retrieved
            
        Returns
        -------
        Node, sequence of Node
            The nodes that should be returned
        '''
        return self.kids[i]
    
#    def __setitem__(self, i, item):
#        '''
#        Change children through []
#        
#        Parameters
    #        ----------
#        i: int, slice
#            Index of element which is changed, or slice object describing 
#            the subsequence which should be changed
#        item: Node, sequence of Node
#        
#        Returns
    #        -------
#        None
#        '''
#        #TODO: type checking
#        #TODO: How should Nodes be treated in case slices are given? 
#        #      As sequences or as single objects?
#        self.kids[i] = item

##    def __cmp__(self, o):
##        return cmp(self.type, o)

    def iterDepthFirst(self, returnDepth=False):
        '''
        Iterate over whole (sub) tree in a depth first manner.
        returnDepth :   if True the iterator returns a tuple (node, depth) otherwise it
                        returns only the current node.
        returns: a DepthFirstIterator instance
        '''
        return DepthFirstIterator(self, returnDepth)


    def copy(self):
        '''Return a (recursive) deep copy of the node.'''
        return copy.deepcopy(self)


class NodeNoneClass(Node):
    '''Node that takes the function of None.'''
    def __init__(self):
        super(NodeNoneClass, self).__init__(None, None, None)
#The single instance of NodeNoneClass. Should be used like None
nodeNone = NodeNoneClass()
    
    
#class NodeBuiltInVal(Node):
#    '''
#    Represent a built in value in the AST.
#    Example: pi
#
#    self.dat : string representing the value
#    '''
#    #TODO: remove this class. These nodes should be replaced by regular
#    #global constants (NodeAttrAccess)
#    def __init__(self, kids=[], loc=None, dat=None):
#        super(NodeBuiltInVal, self).__init__(kids, loc, dat)


class NodeNum(Node):
    '''
    Represent a real number in the AST.
    Example: 123.5
    Data nameSpaceAttrs:
        kids    : []
        loc     : location in input string
        dat     : the number as a string
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeNum, self).__init__(kids, loc, dat)


class NodeString(Node):
    '''
    Represent a string in the AST.
    Example: 'hello world'
    Data nameSpaceAttrs:
        kids    : []
        loc     : location in input string
        dat     : the string
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeString, self).__init__(kids, loc, dat)


class NodeParentheses(Node):
    '''
    Represent a pair of parentheses that enclose an expression, in the AST.
    Example: ( ... )
    Data nameSpaceAttrs:
        kids[0] : the mathematical expression between the parentheses
        loc     : location in input string
        dat     : None
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeParentheses, self).__init__(kids, loc, dat)


class NodeOpInfix2(Node):
    '''
    AST node for a (binary) infix operator: + - * / ^ and or
    Data nameSpaceAttrs:
        kids    : [LHS, RHS] both sides of the operator
        loc     : location in input string
        dat     : None
        operator: operator symbol e.g.: '+'
    '''
    def __init__(self, kids=None, loc=None, dat=None, operator=None):
        super(NodeOpInfix2, self).__init__(kids, loc, dat)
        self.operator = operator
        if not self.kids:
            self.kids = [Node(), Node()]

    #Get and set the left hand side
    def getLhs(self): return self.kids[0]
    def setLhs(self, inLhs): self.kids[0] = inLhs
    lhs = property(getLhs, setLhs, None,
                   'Left hand side of operator (proppery).')

    #Get and set the right hand side
    def getRhs(self): return self.kids[1]
    def setRhs(self, inRhs): self.kids[1] = inRhs
    rhs = property(getRhs, setRhs, None,
                   'Right hand side of operator (proppery).')


class NodeOpPrefix1(Node):
    '''
    AST node for a (unary) prefix operator: - not
        kids    : [RHS] the term on which the operator acts
        loc     : location in input string
        dat     : None
        operator: operator symbol e.g.: '+'
    '''
    def __init__(self, kids=None, loc=None, dat=None, operator=None):
        super(NodeOpPrefix1, self).__init__(kids, loc, dat)
        self.operator = operator

    #Get and set the right hand side
    def getRhs(self): return self.kids[0]
    def setRhs(self, inRhs): self.kids[0] = inRhs
    rhs = property(getRhs, setRhs, None,
                   'Right hand side of operator (proppery).')


class NodeIfStmt(Node):
    '''
    AST Node for an if ... the ... else statement
    Data nameSpaceAttrs:
        kids    : [<condition>, <then statements>, <else statements>]
        loc     : location in input string
        dat     : None
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeIfStmt, self).__init__(kids, loc, dat)
    #TODO: make compatible with multiple elif clauses:
    #      if ...: ... elif ...: ... elif...: ... else: ...
    #Condition property
#    def getCondition(self): return self.kids[0]
#    def setCondition(self, inCondtion): self.kids[0] = inCondtion
#    condition = property(getCondition, setCondition, None,
#        'Condition of if:...else:...end statement.')
#
#    #ifTruePart property
#    def getIfTruePart(self): return self.kids[1]
#    def setIfTruePart(self, inStatements): self.kids[1] = inStatements
#    ifTruePart = property(getIfTruePart, setIfTruePart, None,
#        'Statements executed when condition is true.')
#
#    #ifFalsePart property
#    def getElsePart(self):
#        if len(self.kids) == 3:
#            return self.kids[2]
#        else:
#            return NodeStmtList()
#    def setElsePart(self, inStatements):
#        if len(self.kids) == 3:
#            self.kids[2] = inStatements
#        else:
#            raise KeyError('NodeIfStmt has no "else" clause.')
#    elsePart = property(getElsePart, setElsePart, None,
#        'Statements executed when condition is false.')


class NodeAssignment(NodeOpInfix2):
    '''
    AST node for an assignment: '='
        kids    : [LHS, RHS] both sides of the assignment operator
        loc     : location in input string
        dat     : None
        operator: operator symbol e.g.: '+'
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeAssignment, self).__init__(kids, loc, dat, operator='=')


#TODO: rename to NodeFuncCall
class NodeFuncExecute(Node):
    '''
    AST Node for calling a function.  
    This will be usually done by inserting the code of the function's body
    into the top level function.
    Similar to an inline function in C++.
    Data nameSpaceAttrs:
        kids        : []
        loc         : location in input string
        dat         : None

        funcName   : Dotted name of the block. Tuple of strings:
                      ('model1','init')
    '''
    def __init__(self, kids=None, loc=None, dat=None, funcName=None):
        super(NodeFuncExecute, self).__init__(kids, loc, dat)
        self.funcName = funcName


class NodePrintStmt(Node):
    '''
    AST Node for printing something to stdout.
    Data nameSpaceAttrs:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None

        newline     : if True: add newline to end of output;
                      if False: don't add newline.
    '''
    def __init__(self, kids=None, loc=None, dat=None, newline=True):
        super(NodePrintStmt, self).__init__(kids, loc, dat)
        self.newline = newline


class NodeGraphStmt(Node):
    '''
    AST Node for creating a graph.
    Data nameSpaceAttrs:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeGraphStmt, self).__init__(kids, loc, dat)


class NodeStoreStmt(Node):
    '''
    AST Node for storing variables
    Data nameSpaceAttrs:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeStoreStmt, self).__init__(kids, loc, dat)


class NodeReturnStmt(Node):
    '''
    AST Node for the return statement
    Data nameSpaceAttrs:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : The return value (expression)
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeReturnStmt, self).__init__(kids, loc, dat)


class NodePragmaStmt(Node):
    '''
    AST Node for the pragma statement
    Data nameSpaceAttrs:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
        
        options     : the arguments of the prgma statements: list of strings
    '''
    def __init__(self, kids=None, loc=None, dat=None, options=None):
        super(NodePragmaStmt, self).__init__(kids, loc, dat)
        self.options = []
        if options: self.options = options


class NodeForeignCodeStmt(Node):
    '''
    AST Node for the foreign_code statement
    Data nameSpaceAttrs:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
        
        language    : the progamming languae of the foreign code: string
        method      : the insertion method - type of the foreign code: string
        code        : the piece of program code that should be inserted: string  
    '''
    def __init__(self, kids=None, loc=None, dat=None, language='', method='', code=''):
        super(NodeForeignCodeStmt, self).__init__(kids, loc, dat)
        self.language = language
        self.method = method
        self.code = code


class NodeImportStmt(Node):
    '''
    AST Node for the pragma statement
    Data nameSpaceAttrs:
        kids        : The modulse's AST
        loc         : location in input string
        dat         : None
        
        moduleName : str
            Name of the module that should be imported
        fromStmt : bool
            Put the module's nameSpaceAttrs directly into the namespace of the 
            module that executes this statement. Behave as Python's "from" 
            statement.
        attrsToImport : list of string
            List of nameSpaceAttrs that should be imported. Special symbol "*" 
            means all nameSpaceAttrs in the module. 
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
    Each child is a statement.
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeStmtList, self).__init__(kids, loc, dat)


class NodeDataDefList(NodeStmtList):
    '''
    AST Node for list of atribute definitions.
    Each child is an attribute definition statement.
    Used to identify these lists so they can be flattened with a pretty 
    simple algogithm.
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeDataDefList, self).__init__(kids, loc, dat)


class AttributeRole(object):
    '''
    Constants to denote the role of an attribute.

    Intention to create someting like enums.
    Additionally this solution provides a
    means for documentation and expresses the tree
    shaped relationship between the roles.
    '''
    pass
class RoleAny(AttributeRole):
    '''The attribute's role is undecided'''
    pass
class RoleConstant(AttributeRole):
    '''The attribute is a constant'''
    pass
class RoleParameter(AttributeRole):
    '''
    Attribute is a parameter of the simulation:
    - is constant during the simulation, but can vary between simulations.
    - is stored.
    '''
class RoleDataCanVaryDuringSimulation(AttributeRole):
    '''Data that can vary during the simulation. (Base class.)'''
    pass
class RoleFuncArgument(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a function/method argument:
    - can vary during the simulation
    - should be optmized away 
    - is not stored.
    '''
    pass
class RoleLocalVariable(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a local variable:
    - can vary during the simulation
    - should be optmized away 
    - is not stored.
    '''
    pass
class RoleVariable(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a state or algebraic variable:
    - can vary during the simulation
    - is stored.
    '''
    pass
class RoleStateVariable(RoleVariable):
    '''The attribute is a state variable'''
    pass
class RoleAlgebraicVariable(RoleVariable):
    '''The attribute is an algebraic variable'''
    pass


class NodeDataDef(Node, NameSpace):
    '''
    AST node for definition of a variable, parameter or submodel.
    Data nameSpaceAttrs:
        kids        : [<default value>, <instance attributes>]
        loc         : location in input string
        dat         : None

        name            : name of the attribute. can be dotted name which is stored
                          as a tuple of strings: ('aa', 'bb')
        className       : type of the attribute; possibly dotted name: ('aa', 'bb')
        role            : Is this attribute a state or algebraic variable, a constant
                          or a parameter? (AttributeRole subclass).
        targetName      : Name in the target language (dict).
                          Variables with derivatives have multiple target names.
                          Example:
                          {():'v_foo', ('time',):'v_foo_dt'}
                          TODO: replace by accessor functions to create more robust interface
                          TODO: Derivatives should be separate variables. These variables should 
                                be created in the intermediate language logic.
    '''
    def __init__(self, kids=None, loc=None, dat=None,
                        name=None, className=None, role=RoleAny, targetName=None):
        Node.__init__(self, kids, loc, dat)
        NameSpace.__init__(self)
        if not self.kids:
            self.kids = [nodeNone, NodeStmtList()]
        self.name = name
        self.className = className
        self.role = role
        self.targetName = targetName
        
    #Get or set the default value
    def getDefaultValue(self): 
        return self.kids[0]
    def setDefaultValue(self, defaultValue): 
        self.kids[0] = defaultValue
    defaultValue = property(getDefaultValue, setDefaultValue, None,
                   'Default value or initial value of the defined data (propperty).')
    #Get or set the recursive definitions
    def getStatements(self): 
        return self.kids[1]
    def setStatements(self, inDefs): 
        self.kids[1] = inDefs
    statements = property(getStatements, setStatements, None,
                   'Attribute definitions. Copied from class definition. (propperty).')


class NodeAttrAccess(Node):
    '''
    AST node for access to a variable or parameter.
    Data nameSpaceAttrs:
        kids    :  ? slice object if attribute is an array?
        loc     : location in input string
        dat     : None

        deriv      : Denote if a derivation operator acted on the attribute.
                     Empty tuple means no derivation took place. can be:
                     (,),('time',) or tuple of distibution domains
        name   : DotName('proc.model1.a'), the dot separated name (basically tuple of strings).
        targetName : name in the target language (string)
    '''
    def __init__(self, kids=None, loc=None, dat=None, deriv=None,
                 attrName=None, targetName=None):
        super(NodeAttrAccess, self).__init__(kids, loc, dat)
        self.deriv = deriv
        self.name = DotName(attrName)
        self.targetName = targetName


class NodeFuncDef(Node, NameSpace):
    """
    AST node for block (method, function?) definition.

    A block can be seen as a method that only modifies the class' nameSpaceAttrs.
    It has neither arguments nor return values. It is treated as an C++ inline
    function or template.

    The block's childern are the statements.
    Data nameSpaceAttrs:
        kids : [<argument list>, <function body>]
        loc  : location in input string
        dat  : None

        name       : name of the function; tuple of strings: ('init',)
        returnType : class name of return value; tuple of strings: ('Real',)
    """
    def __init__(self, kids=None, loc=None, dat=None, name=None, returnType=None):
        Node.__init__(self, kids, loc, dat)
        NameSpace.__init__(self)
        self.name = name
        if not self.kids:
            self.kids = [NodeStmtList(), NodeStmtList()]
        self.returnType = returnType

    #Get and set the argument list
    def getArgList(self): return self.kids[0]
    def setArgList(self, inArgs): self.kids[0] = inArgs; inArgs.dat = 'argument list'
    argList = property(getArgList, setArgList, None,
                   'The argument list (proppery).')

    #Get and set the function body
    def getFuncBody(self): return self.kids[1]
    def setFuncBody(self, inBody): self.kids[1] = inBody; inBody.dat = 'function body'
    funcBody = property(getFuncBody, setFuncBody, None,
                   'The function body (proppery).')


class NodeClassDef(Node, NameSpace):
    """
    AST node for class definition.
    Data nameSpaceAttrs:
        kids      : The statements, the block's code.
        loc       : location in input string
        dat       : None

        name : name of the class defined here.
        baseName : name of the class, from which this class inherits;
                    usually "Process", "Model"
    """
    def __init__(self, kids=None, loc=None, dat=None, name=None, baseName=None):
        Node.__init__(self, kids, loc, dat)
        NameSpace.__init__(self)
        self.name = name
        self.baseName = baseName
        
#    #Get or set the class body through a unified name
#    def getStatements(self): 
#        return self.kids
#    def setStatements(self, inDefs): 
#        self.kids = inDefs
#    statements = property(getStatements, setStatements, None,
#            'Attribute definitions and operations on constants. (propperty).')


class NodeModule(Node, NameSpace):
    '''
    Root node of a module (or of the program)
    Data nameSpaceAttrs:
        kids      : Definitions, the program's code.
        loc       : location in input string (~0)
        dat       : None
        
        name      : Name of the module
    '''
    def __init__(self, kids=None, loc=None, dat=None, name=None):
        Node.__init__(self, kids, loc, dat)
        NameSpace.__init__(self)
        self.name = name


class DepthFirstIterator(object):
    """
    Iterate over each node of a (AST) tree, in a depth first fashion.
    Designed for Node and its subclasses. It works for other nodes though:
    The nodes must have the functions __getitem__ and __len__.

    Usage:
    >>> t1 = Node([Node([Node([],3,'leaf'), Node([],4,'leaf')], 2, 'branch'),
    ...            Node([],5,'leaf')], 1, 'root')
    >>> for n in DepthFirstIterator(t1):
    ...     print n.dat
    ...
    root
    branch
    leaf
    leaf
    leaf
    """
    #TODO: Find out if this is really depth first iteration.

    def __init__(self, treeRoot, returnDepth=False):
        """
        treeRoot    : root node of the tree over which the iterator goes.
        returnDepth : if True the __next__ function returns a tuple
                      (node, depth) otherwise it only returns the current
                      node.
        """
        self.stack = [(treeRoot, 0)] #tuples (node, childIndex).
        self.depth = 0  #how deep we are in the tree.
        self.returnDepth = returnDepth #flag: shoult we return the current depth
        self.start = True #remember that we've just been initialized


    def __iter__(self):
        '''Called at start of for loop.'''
        return self


    def next(self):
        '''Go to the next node, return current node.'''
        #After tree has been traversed throw exception, don't start again
        if len(self.stack) == 0:
            raise StopIteration
        #start: special handling
        if self.start:
            self.start = False
            currNode, currChild = self.stack[-1]
            return self._createReturnVals(currNode, currChild)

        #go to next node.
        #get current state, from top of stack
        currNode, currChild = self.stack[-1]

        #if all children visited: go up one or more levels
        while currChild == len(currNode):
            self.stack.pop()
            #stop iterating, if no nodes are left on the stack
            if len(self.stack) == 0:
                raise StopIteration
            self.depth -= 1
            currNode, currChild = self.stack[-1] #get state from one level up

        #remember to visit next child when we come here again
        self.stack[-1] = (currNode, currChild+1)
        #TODO: Make iterator work also with objects that are not children of Node;
        #TODO: or make iterator throw an erception with useful error message when 
        #      non Node object is discovered
        #get node that will be visited next
        nextNode = currNode[currChild]
        #go to one level down, to current child.
        self.stack.append((nextNode, 0))
        self.depth += 1
        #return the next node
        return self._createReturnVals(nextNode, self.depth)


    def _createReturnVals(self, node, depth):
        if self.returnDepth:
            return (node, depth)
        else:
            return node



class TreePrinter(object):
    '''Print a tree of Node objects in a nice way.'''

    indentWidth = 4
    '''Number of chars used for indentation. Must be >= 1'''
    wrapLineAt = 150
    '''Length of line. Longer lines will be wrapped'''
    showID = False
    '''Also print the node's id()'''

    def __init__(self, root=None):
        '''
        Argument:
        root : Node
            the root of the tree, which will be printed
        '''
        #tree's root node.
        self.root = root
        #buffer for the textual reprentation
        self.treeStr = ''
        #partially completed line for line wrapping
        self.line = ''

    #TODO: def setIndentStr(self, indentStr): ??
    #          newIndentLevel(self, nLevel) ???
    def putStr(self, indentStr, contentStr):
        '''Put string into buffer and apply line wrapping'''
        #is there enough room to write?
        if len(indentStr) + 20 > self.wrapLineAt:
            wrapLineAt = len(indentStr)+60 #no: extend right margin
        else:
            wrapLineAt = self.wrapLineAt #yes: normal wrap
        #empty line has special meaning: new node is started
        if self.line == '':
            self.line = indentStr
        #Do the line wrapping
        if len(self.line) + len(contentStr) > wrapLineAt:
            #print self.line
            self.treeStr += self.line + '\n'
            self.line = indentStr + ': '
        #add content to buffer
        self.line += contentStr

    def endLine(self):
        '''End a partially completed line unconditionally'''
        self.treeStr += self.line + '\n'
        self.line = ''
        
    #TODO: implement makeSimpleStr(...) function that prints Node subclasses in one line
    def makeTreeStr(self, root=None):
        ''''Create string representation of Node tree.'''
        self.treeStr = '' 
        self.line = ''
        if root is not None:
            self.root = root
        #string to symbolize one indent level
        indentStepStr = '|' + ' '*int(self.indentWidth - 1)
        for node, depth in self.root.iterDepthFirst(True):
            #string for indentation
            indentStr = indentStepStr * depth 
            #First print class name and if desired node's ID
            self.putStr(indentStr, node.__class__.__name__ + ':: ') 
            if self.showID:
                self.putStr(indentStr, ' ID: ' + str(id(node)))
            #special case for foreign objects
            if not isinstance(node, Node):
                self.putStr(indentStr, str(node)); self.endLine()
                print self.treeStr
                raise Exception('All children must inherit from ast.Node!')
                #TODO enhance the iterator to work with none Node classes as leafs.
            #special handling for some important attributes
            self.putStr(indentStr, 'loc: ' + str(node.loc) + ' ')
            if isinstance(node, NameSpace):
                #print the name space speciffic attributes in short form
                #they are causing infinite recursion otherwise
                self.putStr(indentStr, 'nameSpaceAttrs.keys(): ' + 
                            str(node.nameSpaceAttrs.keys()) + ' ')
                if node.enclosingScope is None: 
                    self.putStr(indentStr, 'enclosingScope: ' + str(None) + ' ')
                else: 
                    self.putStr(indentStr, 'enclosingScope.name: ' + 
                                str(node.enclosingScope.name) + ' ')
            #the node's nameSpaceAttrs are printed in sorted order, 
            #but the special attributes are excluded
            specialAttrs = set(['loc', 'kids', 'nameSpaceAttrs', 'enclosingScope'])
            attrNameSet = set(node.__dict__.keys())
            attrNames= list(attrNameSet - specialAttrs)
            attrNames.sort()
            #get nameSpaceAttrs out node.__dict__
            for name1 in attrNames:
                #TODO:more robustness when other nameSpaceAttrs are Nodes too
                #TODO:more robustness against circular dependencies
                self.putStr(indentStr, name1 + ': ' + str(node.__dict__[name1]) + ' ')
            #put newline after complete node 
            self.endLine()
        return self.treeStr



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
        return DotName(tuple.__add__(self, other))

    def __radd__(self, other):
        '''Concatenate with tuple or DotName. Return: other + self.'''
        return DotName(tuple.__add__(other, self))
    #TODO: add indexing operations. Currently dn[1:] returns a tuple.



class UserException(Exception):
    '''Exception that transports user visible error messages'''
    def __init__(self, message, loc=None):
        Exception.__init__(self)
        self.message = message
        '''The error message'''
        self.loc = loc
        '''Position in the input string, where the error occured.
        Includes input string and file name'''

    def __str__(self):
        return 'Error! %s \n' % self.message + str(self.loc)



class MultiErrorException(UserException):
    '''Exception with many (user visible) error messages'''
    def __init__(self, errTupList):
        '''
        Arguments:
            errTupList : iterable (list) with tuples (message, loc)
        '''
        #init base class with first error; at least kind of sensible
        msg1, loc1 = errTupList[0]
        UserException.__init__(self, msg1, loc1)
        self.errTupList = errTupList
        '''iterable (list) with tuples (message, loc)'''

    def __str__(self):
        errMsg = 'Error!\n'
        for msg1, _loc1 in self.errTupList:
            errMsg += '%s \n    %s \n' % (msg1, str(self.loc))
        errMsg += '------------------------\n'
        errMsg += 'Total: %d Error(s).' % len(self.errTupList)
        return errMsg



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
    
    - Single dispatch
    - Switching which memberfuncion is used is done based on type and 
      inheritance
    - Ambigous situations can be avoided with a priority value. Functions with 
      high priority values are considered before functions with low priority 
      values. 
    - The algorithm for matching is 'issubclass'.
    - Association between type and memberfunction is done with decorators.

    USAGE:
    ------
        - Define class that inherits from visitor
        - Use @Visitor.when_type(classObject, priority) to define a handler 
          function for a speciffic type. 
        - Use @Visitor.default for the default function, which is called when 
          no handler functions matches.
        - In the main loop use self.dispatch(theObject) to call the handler 
          functions.
        
    >>> class NodeVisitor(Visitor):
    ...     def __init__(self):
    ...         Visitor.__init__(self)
    ...     @Visitor.when_type(NodeClassDef)
    ...     def visitClassDef(self, classDef):
    ...         print 'seen class def: ', classDef.name    
    ...     @Visitor.when_type(NodeFuncDef)
    ...     def visitFuncDef(self, funcDef):
    ...         print 'seen func def: ', funcDef.name
    ...     def mainLoop(self, tree):
    ...         for node in tree:
    ...             self.dispatch(node)
    
    >>> tr=Node()
    >>> tr.appendChild(NodeClassDef(name='c1'))
    >>> tr.appendChild(NodeClassDef(name='c2'))
     >>> tr.appendChild(NodeFuncDef(name='f1'))
    >>> tr.appendChild(NodeFuncDef(name='f2'))
    >>> nv = NodeVisitor()
    >>> nv.mainLoop(tr)    
    seen class def:  c1
    seen class def:  c2
    seen func def:  f1
    seen func def:  f2

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
        if not hasattr(cls, '_ruleTable'):
            #List of types, functions and priorities
            cls._ruleTable = []
            #Dictionary of types and functions, no inheritance is considered
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
        if handlerFunc == None:
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
        _dispatchIfType and _dispatchPriority data nameSpaceAttrs
        put them into the rule table.

        - The rule table is sorted according to _dispatchPriority.
        - If _dispatchIfType has the value None the function is considered
          the default function
        '''
        ruleTable = []
        defaultFunc = Visitor._simpleDefaultFunc #IGNORE:W0212
        #TODO: look into methods of parent classes too
        #loop over the class' nameSpaceAttrs and put them into the table if appropriate
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



#------------ testcode --------------------------------------------------
import unittest

class TestAST(unittest.TestCase):

    def setUp(self):
        '''perform common setup tasks for each test'''
        #create test data; loc is abused as number for node identification
        self.tree1 = Node([Node([Node([],3,'leaf'), Node([],4,'leaf')],
                               2, 'branch'),
                          Node([],5,'leaf')], 1, 'root')

    def test__init__(self):
        n1 = Node()
        self.assertEqual(n1.kids, [])
        self.assertEqual(n1.loc, None)
        self.assertEqual(n1.dat, None)
        n2 = Node([],1,'test')
        self.assertEqual(n2.loc, 1)
        self.assertEqual(n2.dat, 'test')
        self.assertRaises(TypeError, self.raise__init__1)
    def raise__init__1(self):
        Node('test')

    #missing: test__repr__

    def test__str__(self):
        #test printing and line wraping (it must not crash)
        #create additional node with many big nameSpaceAttrs
        nBig = Node([])
        nBig.test1 = 'qworieoqwiruuqrw'
        nBig.test2 = 'qworieoqwiruuqrw'
        nBig.test3 = 'qworieoqwiruuqrw'
        nBig.test4 = 'qworieoqwiruuqrw'
        nBig.test5 = 'qworieoqwiruuqrw'
        nBig.test6 = 'qworieoqwiruuqrw'
        nBig.test7 = 'qworieoqwiruuqrw'
        nBig.test8 = 'qworieoqwiruuqrw'
        nBig.test9 = 'qworieoqwiruuqrw'
        self.tree1[0][1].appendChild(nBig)
        _str1 = self.tree1.__str__()
        #to see it:
        #print
        #print self.tree1

    def test__iter__(self):
        #iteration, immediate children
        l = []
        for node1 in self.tree1:
            l.append(node1.loc)
        self.assertEqual(l, [2, 5])

    def test__len__(self):
        self.assertEqual(2, len(self.tree1))

    def test__appendChild__(self):
        self.tree1.appendChild(Node(loc=10))
        self.assertEqual(3, len(self.tree1))    #one child added
        self.assertEqual(10, self.tree1[2].loc) #at the end
        self.assertRaises(TypeError, self.raise__appendChild__)
    def raise__appendChild__(self):
        #append child checks the type
        self.tree1.appendChild('qwert')

    def test__insertChild__(self):
        self.tree1.insertChild(0, Node(loc=10))
        self.assertEqual(3, len(self.tree1))    #one child added
        self.assertEqual(10, self.tree1[0].loc) #at the begining
        self.assertRaises(TypeError, self.raise__insertChild__)
    def raise__insertChild__(self):
        #append child checks the type
        self.tree1.insertChild(0, 'qwert')

    def test__delChild(self):
        del self.tree1[0]
        self.assertEqual(1, len(self.tree1))   #one child removed
        self.assertEqual(5, self.tree1[0].loc) #at the begining

    def test__getitem__(self):
#        print
#        print self.tree1 #in case you need an overwiew
        self.assertEqual(1, self.tree1.loc)
        self.assertEqual(2, self.tree1[0].loc)
        self.assertEqual(3, self.tree1[0][0].loc)

    def testIterDepthFirst(self):
        #iteration, all child nodes recursive
        l = []
        for node1 in self.tree1.iterDepthFirst():
            l.append(node1.loc)
        self.assertEqual(l, [1, 2, 3, 4, 5])
        #iteration, all child nodes recursive also depth is returned
        l = []
        for node1, depth in self.tree1.iterDepthFirst(returnDepth=True):
            line = 'dat: %s, depth; %d' % (node1.dat, depth)
            l.append(line)
        self.assertEqual(l, ['dat: root, depth; 0',
                             'dat: branch, depth; 1',
                             'dat: leaf, depth; 2',
                             'dat: leaf, depth; 2',
                             'dat: leaf, depth; 1'])

    def testCopy(self):
        tree2 = self.tree1.copy() #create deep copy
        #assert that values are equal
        self.assertEqual(len(tree2), len(self.tree1))
        self.assertEqual(tree2.loc, self.tree1.loc)
        self.assertEqual(tree2[0].loc, self.tree1[0].loc)
        self.assertEqual(tree2[0][0].loc, self.tree1[0][0].loc)
        #assert that copy created new objects
        self.assertNotEqual(id(tree2), id(self.tree1))
        self.assertNotEqual(id(tree2[0]), id(self.tree1[0]))
        self.assertNotEqual(id(tree2[0][0]), id(self.tree1[0][0]))



class TestVisitor(unittest.TestCase):

    def setUp(self):
        '''perform common setup tasks for each test'''
        pass

#    def test__when_type(self):
#        #this tests implementation details
#        #define dummy class to test the decorators
#        class FooClass(Visitor):
#            @Visitor.when_type(list, 23)
#            def test(self):
#                print 'test(...) called'
#
#        #print FooClass.test._dispatchIfType
#        self.assertEqual(FooClass.test._dispatchIfType, list)
#        self.assertEqual(FooClass.test._dispatchPriority, 23)
#        fooInst = FooClass()
#        #print fooInst.test._dispatchIfType
#        #print fooInst.test._dispatchPriority
#        self.assertEqual(fooInst.test._dispatchIfType, list)
#        self.assertEqual(fooInst.test._dispatchPriority, 23)
#        #print fooInst._ruleTable
#        #fooInst.test()


    def test__dispatch(self):
        '''Visitor: Test normal operation.'''
        #define visitor class
        class FooClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            @Visitor.when_type(list)
            def visitList(self, _inObject):
                return 'list'
            @Visitor.when_type(int)
            def visitInt(self, _inObject):
                return 'int'
            @Visitor.when_type(float)
            def visitFloat(self, _inObject):
                return 'float'
            @Visitor.default
            def visitDefault(self, _inObject):
                return 'default'

        #test dispatching - dispatching multiple times also tries the cache
        fooInst = FooClass()
        #print fooInst.dispatch([])
        self.assertEqual(fooInst.dispatch([]), 'list')
        self.assertEqual(fooInst.dispatch([1,2]), 'list')
        self.assertEqual(fooInst.dispatch([]), 'list')
        #print fooInst.dispatch(1)
        self.assertEqual(fooInst.dispatch(1), 'int')
        self.assertEqual(fooInst.dispatch(2), 'int')
        self.assertEqual(fooInst.dispatch(3), 'int')
        #print fooInst.dispatch(1.0)
        self.assertEqual(fooInst.dispatch(1.0), 'float')
        #print fooInst.dispatch('qwert')
        self.assertEqual(fooInst.dispatch('qwert'), 'default')


    def test__switching_inheritance_priority(self):
        '''Visitor: Test switching based on inheritance and priority.'''
        #Define class hierarchy
        class Base(object):
            pass
        class Derived1(Base):
            pass
        class Derived2(Base):
            pass

        #define visitor class
        class TestVisitorClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            #Can handle all Base objects but has low priority
            @Visitor.when_type(Base, 1)
            def visitBase(self, _inObject):
                return 'Base'
            #Specialized method for Derived1 with high priority
            @Visitor.when_type(Derived1, 5)
            def visitDerived1(self, _inObject):
                return 'Derived1'
            @Visitor.when_type(int)
            def visitInt(self, _inObject):
                return 'int'

        #create some objects that the visitor should handle
        baseInst = Base()
        derived1Inst = Derived1()
        derived2Inst = Derived2()
        intInst = 2
        #create the visitor
        visitor = TestVisitorClass()

        #try the visitor
        self.assertEqual(visitor.dispatch(baseInst), 'Base')
        self.assertEqual(visitor.dispatch(derived1Inst), 'Derived1')
        self.assertEqual(visitor.dispatch(derived2Inst), 'Base')
        self.assertEqual(visitor.dispatch(intInst), 'int')

 
    def test_priority_2(self):
        '''Visitor: Test priority 2.'''
       
        class NodeVisitor(Visitor):
            def __init__(self):
                Visitor.__init__(self)
                
            #Handlers for derived classes - specialized 
            #- should have high priority    
            @Visitor.when_type(NodeClassDef, 2)
            def visitClassDef(self, classDef): #IGNORE:W0613
#                print 'seen class def: ' + classDef.name
                return ['NodeClassDef']
            @Visitor.when_type(NodeFuncDef, 2)
            def visitFuncDef(self, funcDef): #IGNORE:W0613
#                print 'seen func def: ' + funcDef.name
                return ['NodeFuncDef']

            #handler for a base class - general 
            #- should have low priority    
            @Visitor.when_type(Node, 1)
            def visitNode(self, node): #IGNORE:W0613
#                print 'seen Node: ' + str(node.dat)
                return ['Node']
                
            def mainLoop(self, tree):
                retList = []
                for node in tree:
                    retList += self.dispatch(node)
                return retList
    
        #create a syntax tree
        tr=Node()
        tr.appendChild(NodeClassDef(name='c1'))
        tr.appendChild(NodeClassDef(name='c2'))
        tr.appendChild(Node(dat='n1'))
        tr.appendChild(NodeFuncDef(name='f1'))
        tr.appendChild(NodeFuncDef(name='f2'))
        #visit all nodes
        nv = NodeVisitor()
        testList = nv.mainLoop(tr)   
#        print testList
     
        expectedList = ['NodeClassDef', 'NodeClassDef', 'Node', 'NodeFuncDef', 'NodeFuncDef']        
        self.assertEqual(testList, expectedList)
        
        
    def test__built_in_default_func(self):
        '''Visitor: Test the built in default function.'''
        #define visitor class
        class FooClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            @Visitor.when_type(list)
            def visitList(self, _inObject):
                return 'list'
            @Visitor.when_type(int)
            def visitInt(self, _inObject):
                return 'int'

        fooInst = FooClass()
        #print fooInst.dispatch([])
        self.assertEqual(fooInst.dispatch([]), 'list')
        #print fooInst.dispatch(1)
        self.assertEqual(fooInst.dispatch(1), 'int')
        #the built in default function raises an exception.
        try:
            self.assertEqual(fooInst.dispatch(1.0), 'float')
            #if we get till here there was an error
            raise Exception('Expected exception was not raised!')
        except TypeError: #IGNORE:W0704
            #print err
            pass


    def test__decorator_errors(self):
        '''Visitor: Test errors because of wrong decorator use.'''
        self.assertRaises(TypeError, self.raise__decorator_error_1)
        self.assertRaises(TypeError, self.raise__decorator_error_2)
        self.assertRaises(TypeError, self.raise__decorator_error_3)
        self.assertRaises(TypeError, self.raise__decorator_error_4)
    def raise__decorator_error_1(self):
        '''Error: No parameters for @Visitor.when_type.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.when_type
            def visitList(self, _inObject):
                return 'list'
    def raise__decorator_error_2(self):
        '''Error: Wrong 1st parameter for @Visitor.when_type.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.when_type([])
            def visitList(self, _inObject): 
                return 'list'
    def raise__decorator_error_3(self):
        '''Error: Wrong 2nd parameter for @Visitor.when_type.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.when_type(list, 'qwert')
            def visitList(self, _inObject):
                return 'list'
    def raise__decorator_error_4(self):
        '''Error: Parameters for @Visitor.default.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.default(int)
            def visitDefault(self, _inObject):
                return 'default'



class TestDotName(unittest.TestCase):

    def setUp(self):
        '''perform common setup tasks for each test'''
        pass

    def test__new__(self):
        '''DotName: Test constructor.'''
        #create DotName object from string
        abc = DotName('a.b.c')
        self.assertTrue(abc == ('a','b','c'))
        self.assertTrue(tuple(abc) == ('a','b','c'))
        #create DotName from other iterable
        abc1 = DotName(('a','b','c'))
        self.assertTrue(abc1 == ('a','b','c'))

    def test__str__(self):
        '''DotName: Test conversion to string.'''
        abc = DotName('a.b.c')
        self.assertTrue(str(abc) == 'a.b.c')

    def test__repr__(self):
        '''DotName: Test repr method.'''
        abc = DotName('a.b.c')
        self.assertTrue(repr(abc) == "DotName('a.b.c')")

    def test__add__(self):
        '''DotName: Test addition (concatenating).'''
        #addition of two DotNames
        abc = DotName('a.b.c')
        efg = DotName('e.f.g')
        abcefg = abc + efg
        self.assertTrue(abcefg == DotName('a.b.c.e.f.g'))
        self.assertTrue(isinstance(abcefg, DotName))
        #mixed addition with tuple 1
        abcefg = abc + ('e', 'f', 'g')
        self.assertTrue(abcefg == DotName('a.b.c.e.f.g'))
        self.assertTrue(isinstance(abcefg, DotName))
        #mixed addition with tuple 2
        abcefg = ('a', 'b', 'c') + efg
        self.assertTrue(abcefg == DotName('a.b.c.e.f.g'))
        self.assertTrue(isinstance(abcefg, DotName))



if __name__ == '__main__':
    # Self-testing code goes here.

    #perform the doctests
    def doDoctest():
        import doctest
        doctest.testmod()
    doDoctest()

    #perform the unit tests
    #unittest.main() #exits interpreter
    testSuite = unittest.TestSuite()
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAST))
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVisitor))
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDotName))
    unittest.TextTestRunner(verbosity=2).run(testSuite)

else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass

