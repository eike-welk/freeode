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
Abstrakt syntax tree and tools for tree handling.

- Syntax tree with specialized nodes for all elements of the language.
- Iterator to iterate over the tree.
- Printer to convert tree to pretty printed string.
- Visitor to invoke different code depending on node type.

Additionaly this module contains some common infrastructure used by other 
modules of freeode:
- Class to store text locations together with file names.
- Excepions to carry user visible errors.
- Handling for dotted attribute names.
- The program's version string.
'''


#TODO: Propperties are currently undocumented in AST classes!
#TODO: Unit tests for the more complex Nodes would be usefull.


from __future__ import division

from types import ClassType, FunctionType, NoneType #, TupleType, StringType
import copy
import pyparsing


##TODO: svn command: svn propset svn:keywords Revision ast.py
#__fileVersion__ = "$LastChangedRevision: 43 $"
#__fileVersion__ = "$Rev: 43 $"


#version of the Siml compiler.
progVersion = '0.3.2'



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

    def __init__(self, kids=[], loc=None, dat=None):
        #TODO: write an init function that can accept any number of named arguments
        #Variabe number of arguments:
        #*args    : is a list of all normal arguments
        #**kwargs : is a dict of keyword arguments
        #Code for derived classes: super(A, self).__init__(*args, **kwds)
        super(Node, self).__init__()
        #self.parent = None
        self.kids = []
        '''list of children'''
        #appendChild checks the type
        for child in kids:
            self.appendChild(child)
        #the node's location in the parsed text
        self.loc  = loc
        '''the location in the program'''
        self.dat = dat
        '''any data; whatever is appropriate.'''


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
        #treat all other attributes as named attributes
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
        return TreePrinter(self).toStringTree()

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

    def __delitem__(self, index):
        '''Delete child at specified index'''
        del self.kids[index]

    def __getitem__(self, i):
        '''Access to childern through []'''
        return self.kids[i]
    #def __getslice__(self, low, high):
        #return self.kids[low:high]
    #def __setslice__(self, low, high, childList):
        #self.kids[low:high] = seq

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



class NodeBuiltInVal(Node):
    '''
    Represent a built in value in the AST.
    Example: pi

    self.dat : string representing the value
    '''
    #TODO: remove this class. These nodes should be replaced by regular
    #global constants (NodeAttrAccess)
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeBuiltInVal, self).__init__(kids, loc, dat)


class NodeBuiltInFuncCall(Node):
    '''
    Represent a built in function in the AST.
    Example: sin( ... )

    self.dat  : the function's name
    self.kids : the function's arguments
    '''
    #TODO: remove this class. These nodes should be replaced by regular 
    #function calls.
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeBuiltInFuncCall, self).__init__(kids, loc, dat)


class NodeNum(Node):
    '''
    Represent a real number in the AST.
    Example: 123.5
    Data attributes:
        kids    : []
        loc     : location in input string
        dat     : the number as a string
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeNum, self).__init__(kids, loc, dat)


class NodeString(Node):
    '''
    Represent a string in the AST.
    Example: 'hello world'
    Data attributes:
        kids    : []
        loc     : location in input string
        dat     : the string
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeString, self).__init__(kids, loc, dat)


class NodeParentheses(Node):
    '''
    Represent a pair of parentheses that enclose an expression, in the AST.
    Example: ( ... )
    Data attributes:
        kids[0] : the mathematical expression between the parentheses
        loc     : location in input string
        dat     : None
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeParentheses, self).__init__(kids, loc, dat)


class NodeOpInfix2(Node):
    '''
    AST node for a (binary) infix operator: + - * / ^ and or
    Data attributes:
        kids    : [LHS, RHS] both sides of the operator
        loc     : location in input string
        dat     : None
        operator: operator symbol e.g.: '+'
    '''
    def __init__(self, kids=[], loc=None, dat=None, operator=None):
        super(NodeOpInfix2, self).__init__(kids, loc, dat)
        self.operator = operator

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
    def __init__(self, kids=[], loc=None, dat=None, operator=None):
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
    Data attributes:
        kids    : [<condition>, <then statements>, <else statements>]
        loc     : location in input string
        dat     : None
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeIfStmt, self).__init__(kids, loc, dat)
        
    #Condition proppery
    def getCondition(self): return self.kids[0]
    def setCondition(self, inCondtion): self.kids[0] = inCondtion
    condition = property(getCondition, setCondition, None, 
        'Condition of if:...else:...end statement.')
    
    #ifTruePart proppery
    def getIfTruePart(self): return self.kids[1]
    def setIfTruePart(self, inStatements): self.kids[1] = inStatements
    ifTruePart = property(getIfTruePart, setIfTruePart, None, 
        'Statements executed when condition is true.')
    
    #ifFalsePart proppery
    def getElsePart(self):
        if len(self.kids) == 3:
            return self.kids[2]
        else:
            return NodeStmtList()
    def setElsePart(self, inStatements):
        if len(self.kids) == 3:
            self.kids[2] = inStatements
        else:
            raise KeyError('NodeIfStmt has no "else" clause.')
    elsePart = property(getElsePart, setElsePart, None, 
        'Statements executed when condition is false.')


class NodeAssignment(NodeOpInfix2):
    '''
    AST node for an assignment: '='
        kids    : [LHS, RHS] both sides of the assignment operator
        loc     : location in input string
        dat     : None
        operator: operator symbol e.g.: '+'
    '''
    def __init__(self, kids=[], loc=None, dat=None, operator=None):
        super(NodeAssignment, self).__init__(kids, loc, dat, operator)


class NodeFuncExecute(Node):
    '''
    AST Node for inserting the code of a sub-model's member function.
    Similar to calling a user defined template function.
    Data attributes:
        kids        : []
        loc         : location in input string
        dat         : None

        funcName   : Dotted name of the block. Tuple of strings:
                      ('model1','init')
    '''
    def __init__(self, kids=[], loc=None, dat=None, funcName=None):
        super(NodeFuncExecute, self).__init__(kids, loc, dat)
        self.funcName = funcName


class NodePrintStmt(Node):
    '''
    AST Node for printing something to stdout.
    Data attributes:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None

        newline     : if True: add newline to end of output;
                      if False: don't add newline.
    '''
    def __init__(self, kids=[], loc=None, dat=None, newline=True):
        super(NodePrintStmt, self).__init__(kids, loc, dat)
        self.newline = newline


class NodeGraphStmt(Node):
    '''
    AST Node for creating a graph.
    Data attributes:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeGraphStmt, self).__init__(kids, loc, dat)


class NodeStoreStmt(Node):
    '''
    AST Node for storing variables
    Data attributes:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeStoreStmt, self).__init__(kids, loc, dat)


class NodeStmtList(Node):
    '''
    AST Node for list of statements
    Each child is a statement.
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeStmtList, self).__init__(kids, loc, dat)


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
class RoleParameter(AttributeRole):
    '''The attribute is a parameter'''
    pass
class RoleVariable(AttributeRole):
    '''The attribute is a state or algebraic variable'''
    pass
class RoleStateVariable(RoleVariable):
    '''The attribute is a state variable'''
    pass
class RoleAlgebraicVariable(RoleVariable):
    '''The attribute is an algebraic variable'''
    pass


class NodeAttrDef(Node):
    '''
    AST node for definition of a variable, parameter or submodel.
    Data attributes:
        kids        : []
        loc         : location in input string
        dat         : None

        attrName        : name of the attribute. can be dotted name which is stored
                          as a tuple of strings: ('aa', 'bb')
        className       : type of the attribute; possibly dotted name: ('aa', 'bb')
        role            : Is this attribute a state or algebraic variable,
                          or a parameter? must be AttributeRole subclass.
        targetName      : Name in the target language (dict).
                          Variables with derivatives have multiple target names.
                          Example:
                          {():'v_foo', ('time',):'v_foo_dt'}
                          TODO: replace by accessor functions to create more robust interface
   '''
    def __init__(self, kids=[], loc=None, dat=None,
                        attrName=None, className=None, role=RoleAny, targetName=None):
        super(NodeAttrDef, self).__init__(kids, loc, dat)
        self.attrName = attrName
        self.className = className
        self.role = role
        #self.isAtomic = isAtomic
        self.targetName = targetName


class NodeAttrAccess(Node):
    '''
    AST node for access to a variable or parameter.
    Data attributes:
        kids    :  ? slice object if attribute is an array?
        loc     : location in input string
        dat     : None

        deriv      : Denote if a derivation operator acted on the attribute.
                     Empty tuple means no derivation took place. can be:
                     (,),('time',) or tuple of distibution domains
        attrName   : ('proc', 'model1', 'a'), tuple of strings; the dot separated name.
        targetName : name in the target language (string)
    '''
    def __init__(self, kids=[], loc=None, dat=None, deriv=None,
                 attrName=None, targetName=None):
        super(NodeAttrAccess, self).__init__(kids, loc, dat)
        self.deriv = deriv
        self.attrName = attrName
        self.targetName = targetName


class NodeFuncDef(Node):
    """
    AST node for block (method, function?) definition.

    A block can be seen as a method that only modifies the class' attributes.
    It has neither arguments nor return values. It is treated as an C++ inline
    function or template.

    The block's childern are the statements.
    Data attributes:
        kids : The statements, the block's code.
        loc  : location in input string
        dat  : None

        name : name of the block; tuple of strings: ('init',)
    """
    def __init__(self, kids=[], loc=None, dat=None, name=None):
        super(NodeFuncDef, self).__init__(kids, loc, dat)
        self.name = name


class NodeClassDef(Node):
    """
    AST node for class definition.
    Data attributes:
        kids      : The statements, the block's code.
        loc       : location in input string
        dat       : None

        className : name of the class defined here.
        superName : name of the class, from which this class inherits;
                    usually "Process", "Model"
    """
    def __init__(self, kids=[], loc=None, dat=None, className=None, superName=None):
        super(NodeClassDef, self).__init__(kids, loc, dat)
        self.className = className
        self.superName = superName


class NodeProgram(Node):
    '''
    Root node of the program
    Data attributes:
        kids      : Definitions, the program's code.
        loc       : location in input string (~0)
        dat       : None
'''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeProgram, self).__init__(kids, loc, dat)


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
    #TODO: Find out if this is reeally depth first iteration.

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
        #get node that will be visited next
        #TODO: Make iterator work also with objects that are not children of Node.
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
    wrapLineAt = 100
    '''Length of line. Longer lines will be wrapped'''
    showID = False
    '''Also print the node's id()'''

    def __init__(self, root):
        '''
        Argument:
            root : the root of the tree, which will be printed
        '''
        self.root = root
        '''tree's root node.'''


    def printTree(self):
        print self.toStringTree()


    def toStringTree(self):
        treeStr = '' #buffer for whole tree
        indentStepStr = '|' + ' '*int(self.indentWidth - 1)
        for node, depth in self.root.iterDepthFirst(True):
            #set up indentation and wrapping
            indentStr = indentStepStr * depth #string for indentation
            if len(indentStr) + 20 > self.wrapLineAt:#enough room to write?
                wrapLineAt = len(indentStr)+60 #no: extend right margin
            else:
                wrapLineAt = self.wrapLineAt #yes: normal wrap

            #First print class name and if desired node's ID
            line = indentStr + node.__class__.__name__ + ':: ' #buffer one line
            if self.showID:
                line += ' ID: ' + str(id(node))
#            #special case for foreign objects
#            if not isinstance(node, Node):
#                treeStr += line + str(node) + '\n'
#                continue
            #the node's attributes are printed in sorted order
            attrNames = node.__dict__.keys()
            attrNames.sort()
            #get attributes out node.__dict__; print them (except kids)
            for name1 in attrNames:
                if name1 == 'kids':
                    continue # the children are printed through the outer loop
                string1 = name1 + ': ' + str(node.__dict__[name1]) + ' '
                #Do the line wrapping
                if len(line) + len(string1) > wrapLineAt:
                    treeStr += line + '\n'
                    line = indentStr + ': '
                line += string1
            treeStr += line + '\n'

        return treeStr



#def makeDotName(inTuple):
#    '''
#    Create a dotted name from a tuple of strings.
#    The dotted names are parsed into (and stored as) tuples of strings.
#    '''
#    dotName = ''
#    for namePart in inTuple:
#        if dotName == '':
#            dotName = namePart
#        else:
#            dotName += '.'+namePart
#    return dotName



#TODO: Add indexing operations 
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
        for msg1, loc1 in self.errTupList:
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
        return 'File "' + self.fileName() + '", line ' + str(self.lineNo())




class Visitor(object):
    '''
    Visitor for the AST
    
    TODO: better documentation with usage

    - Single dispatch
    - Switching which memberfuncion is used is done based on type 
      and inheritance.
    - The algorithm for matching is 'issubclass'
    - Association between type and memberfunction is done with decorators.
    
    Inspiration came from: 
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
        return handlerFunc(self, inObject, *args)
        
        
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
        for func1, cls1, prio1 in cls._ruleTable: 
            if issubclass(objCls, cls1):
                return func1
        #no specific handler could be found: return the default function
        func1, cls1, prio1 = cls._ruleTable[-1]
        return func1
        
        
    @classmethod
    def _createRuleTable(cls):
        '''
        Create the rule table.
        Look at all methods of the class, if they have 
        _dispatchIfType and _dispatchPriority data attributes
        put them into the rule table.
        
        - The rule table is sorted according to _dispatchPriority.
        - If _dispatchIfType has the value None the function is considered 
          the default function
        '''
        ruleTable = []
        defaultFunc = Visitor._simpleDefaultFunc
        #TODO: look into methods of parent classes too
        #loop over the class' attributes and put them into the table if appropriate
        for func in cls.__dict__.itervalues():
            if not isinstance(func, FunctionType):
                continue
            if not (hasattr(func, '_dispatchIfType') and 
                    hasattr(func, '_dispatchPriority')):
                continue
            if func._dispatchIfType == None:
                defaultFunc = func
            else:
                ruleTable.append((func, func._dispatchIfType, func._dispatchPriority))
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
        n2 = Node([],1,'test')
        self.assertEqual(n2.loc, 1)
        self.assertEqual(n2.dat, 'test')
        self.assertRaises(TypeError, self.raise__init__1)
    def raise__init__1(self):
        Node('test')

    #missing: test__repr__

    def test__str__(self):
        #test printing and line wraping (it must not crash)
        #create additional node with many big attributes
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
        str1 = self.tree1.__str__()
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
            def visitList(self, inObject):
                return 'list'
            @Visitor.when_type(int)
            def visitInt(self, inObject):
                return 'int'
            @Visitor.when_type(float)
            def visitFloat(self, inObject):
                return 'float'
            @Visitor.default
            def visitDefault(self, inObject):
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
        class TestVisitor(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            #Can handle all Base objects but has low priority
            @Visitor.when_type(Base, 1)
            def visitBase(self, inObject):
                return 'Base'
            #Specialized method for Derived1 with high priority
            @Visitor.when_type(Derived1, 5)
            def visitDerived1(self, inObject):
                return 'Derived1'
            @Visitor.when_type(int)
            def visitInt(self, inObject):
                return 'int'
        
        #create some objects that the visitor should handle
        baseInst = Base()
        derived1Inst = Derived1()
        derived2Inst = Derived2()
        intInst = 2
        #create the visitor
        visitor = TestVisitor()
        
        #try the visitor
        self.assertEqual(visitor.dispatch(baseInst), 'Base')
        self.assertEqual(visitor.dispatch(derived1Inst), 'Derived1')
        self.assertEqual(visitor.dispatch(derived2Inst), 'Base')
        self.assertEqual(visitor.dispatch(intInst), 'int')
       
        
    def test__built_in_default_func(self):
        '''Visitor: Test the built in default function.'''
        #define visitor class       
        class FooClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            @Visitor.when_type(list)
            def visitList(self, inObject):
                return 'list'
            @Visitor.when_type(int)
            def visitInt(self, inObject):
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
        except TypeError, err:
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
        class FooClass(Visitor):
            @Visitor.when_type
            def visitList(self, inObject):
                return 'list'
    def raise__decorator_error_2(self):
        '''Error: Wrong 1st parameter for @Visitor.when_type.'''
        class FooClass(Visitor):
            @Visitor.when_type([])
            def visitList(self, inObject):
                return 'list'
    def raise__decorator_error_3(self):
        '''Error: Wrong 2nd parameter for @Visitor.when_type.'''
        class FooClass(Visitor):
            @Visitor.when_type(list, 'qwert')
            def visitList(self, inObject):
                return 'list'
    def raise__decorator_error_4(self):
        '''Error: Parameters for @Visitor.default.'''
        class FooClass(Visitor):
            @Visitor.default(int)
            def visitDefault(self, inObject):
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
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAST))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVisitor))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDotName))
    unittest.TextTestRunner(verbosity=2).run(suite)
    
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass

