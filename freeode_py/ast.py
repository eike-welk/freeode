############################################################################
#    Copyright (C) 2006 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
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
__doc__ = \
'''
Implementation of an abstact syntax tree.
Module contains specialized nodes and tools for tree handling.
Additionaly it contins some common infrastructure used by the other modules
of freeode.
'''



import copy
import pyparsing



#version of the Siml compiler.
#global variable defined here is valid for all parts of the program.
global progVersion
progVersion = '0.3.0'

progRevision = '$REVISION$'


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
        
    def delChild(self, index):
        '''Delete child at specified index'''
        del self.kids[index]
        
    def __getitem__(self, i):
        '''Acces to childern through []'''
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
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeBuiltInVal, self).__init__(kids, loc, dat)
    
    
class NodeBuiltInFuncCall(Node):
    '''
    Represent a built in function in the AST. 
    Example: sin( ... )
    
    self.dat  : the function's name
    self.kids : the function's arguments 
    '''    
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
        dat     : operator symbol e.g.: '+'
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeOpInfix2, self).__init__(kids, loc, dat)
        
    def lhs(self):
        '''Return the left hand side'''
        return self.kids[0]
    def rhs(self):
        '''Return the right hand side'''
        return self.kids[1]
    def operator(self):
        '''Return the operator (string)'''
        return self.dat


class NodeOpPrefix1(Node):
    '''
    AST node for a (unary) prefix operator: - not
       kids    : [RHS] the term on which the operator acts
        loc     : location in input string
        dat     : operator symbol e.g.: '-'
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeOpPrefix1, self).__init__(kids, loc, dat)
        
    def rhs(self):
        '''Return the right hand side'''
        return self.kids[0]
    def operator(self):
        '''Return the operator (string)'''
        return self.dat
    
        
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
    def condition(self):
        return self.kids[0]
    def ifTruePart(self):
        return self.kids[1]
    def elsePart(self):
        if len(self.kids) == 3:
            return self.kids[2]
        else:
            return NodeStmtList()
        
        
class NodeAssignment(Node):
    '''
    AST node for an assignment: '='
        kids    : [LHS, RHS] both sides of the assignment operator
        loc     : location in input string
        dat     : '='
    '''
    def __init__(self, kids=[], loc=None, dat=None):
        super(NodeAssignment, self).__init__(kids, loc, dat)
        
    def lhs(self):
        '''Return the assignment's left hand side'''
        return self.kids[0]
    def rhs(self):
        '''Return the assignment's right hand side'''
        return self.kids[1]
        
        
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
    
    Intention to create someting like 
    enums. Classes are objects in python; not only 
    class instances.
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
        attrName   : ['proc', 'model1', 'a'], list of strings; the dot separated name.
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
                    usually"process", "model" 
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
            return self._handleReturnDepth(currNode, currChild)

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
        nextNode = currNode[currChild]
        #go to one level down, to current child. 
        self.stack.append((nextNode, 0))
        self.depth += 1
        #return the next node
        return self._handleReturnDepth(nextNode, self.depth)


    def _handleReturnDepth(self, node, depth):
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



def makeDotName(inTuple):
    '''
    Create a dotted name from a tuple of strings.
    The dotted names are parsed into (and stored as) tuples of strings.
    '''
    dotName = ''
    for namePart in inTuple:
        if dotName == '':
            dotName = namePart
        else:
            dotName += '.'+namePart
    return dotName



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
        return errMsg  

        

class TextLocation(object):
    '''
    Store the location of parsed pattern, or error.
    
    Includes the file's contents and the file's name.
    Object is intended to be stored in a Node's self.loc 
    data member.
    '''
    def __init__(self, atChar=None, textString=None, fileName=None):
        super(TextLocation, self).__init__()
        self.atChar = atChar
        self.str = textString
        self.name = fileName
        
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
        self.tree1.delChild(0)
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

        
        
if __name__ == '__main__':
    # Self-testing code goes here.

    #perform the doctests
    def doDoctest():
        import doctest
        doctest.testmod()   
    doDoctest()
    
    #perform the unit tests
    #unittest.main() #exits interpreter
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAST)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
#    print 'Test the AST:'
#    t1 = Node([Node([Node([],3,'leaf'), Node([],4,'leaf')], 2, 'branch'), 
#               Node([],5,'leaf')], 1, 'root')
#    print 'print the tree'
#    print t1
#    
#    print 'test line wrapping'
#    nBig = Node([])
#    nBig.test1 = 'qworieoqwiruuqrw'
#    nBig.test2 = 'qworieoqwiruuqrw'
#    nBig.test3 = 'qworieoqwiruuqrw'
#    nBig.test4 = 'qworieoqwiruuqrw'
#    nBig.test5 = 'qworieoqwiruuqrw'
#    nBig.test6 = 'qworieoqwiruuqrw'
#    nBig.test7 = 'qworieoqwiruuqrw'
#    nBig.test8 = 'qworieoqwiruuqrw'
#    nBig.test9 = 'qworieoqwiruuqrw'
#    t1[0][1].appendChild(nBig)
#    print t1
#
#    print 'iterating over only the children of a node:'
#    for n in t1:
#        print n.loc
#
#    print 'iterating over the whole tree:'
#    for n,d in t1.iterDepthFirst(returnDepth=True):
#        print n.dat, 'depth: ', d
        
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass

