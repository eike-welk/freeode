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
'''



import copy



class Node(object):
    '''
    Building block of a n-ary tree structure.  
    
    Usage:
    >>> t1 = Node('root 0.0', [Node('c 1.0', [Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    
    #access to children with  [] operator
    >>> t1[0][1]
    Node('c 2.1',[])
    
    >>> #iterating over only the children of a node:
    >>> for n in t1:
    ...     print n.typ
    ... 
    c 1.0
    c 1.1
    
    >>> #iterating over the whole tree:
    >>> for n,d in t1.iterDepthFirst(returnDepth=True):
    ...     print n.typ, 'depth: ', d
    ... 
    root 0.0 depth:  0
    c 1.0 depth:  1
    c 2.0 depth:  2
    c 2.1 depth:  2
    c 1.1 depth:  1
    >>>     
    '''

    def __init__(self, typ, kids=[], loc=None, dat=None):
        #TODO: write an init function that can accept any number of named arguments
        #Variabe number of arguments:
        #*args    : is a list of all normal arguments
        #**kwargs : is a dict of keyword arguments
        #Code for derived classes: super(A, self).__init__(*args, **kwds)
        super(Node, self).__init__()
        self.typ = typ      # type string
        #self.parent = None
        self.kids = kids[:] # list of children
        self.loc  = loc     # the location in the program
        self.dat = dat      # whatever is appropriate


    def __repr__(self):
        '''Create string representation that can also be used as code.'''
        className = self.__class__.__name__
        typeStr = repr(self.typ)
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
        standardAttributes = set(['typ', 'kids', 'loc', 'dat'])
        extraAttrStr=''
        for key, attr in self.__dict__.iteritems():
            if key in standardAttributes:
                continue
            extraAttrStr += ', ' + key + '=' + repr(attr)
        #assemble the string
        reprStr = className  + '(' + typeStr + childStr + locStr + datStr + \
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
        self.kids.append(inNode)
        
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
    #TODO:unify built in values and parametres
    def __init__(self, typ='builtInVal', kids=[], loc=None, dat=None):
        super(NodeBuiltInVal, self).__init__(typ, kids, loc, dat)
    
    
class NodeBuiltInFuncCall(Node):
    '''
    Represent a built in function in the AST. 
    Example: sin( ... )
    
    self.dat  : the function's name
    self.kids : the function's arguments 
    '''    
    #TODO: unify built in functions and blocks.
    def __init__(self, typ='funcCall', kids=[], loc=None, dat=None):
        super(NodeBuiltInFuncCall, self).__init__(typ, kids, loc, dat)
        
        
class NodeNum(Node):
    '''
    Represent a real number in the AST. 
    Example: 123.5
    
    self.dat  : the number as a string
    '''    
    def __init__(self, typ='num', kids=[], loc=None, dat=None):
        super(NodeNum, self).__init__(typ, kids, loc, dat)


class NodeParentheses(Node):
    '''
    Represent a pair of parentheses that enclose an expression, in the AST. 
    Example: ( ... )
    
    self.kids[0]  : the mathematical expression between the parentheses
    '''    
    def __init__(self, typ='paren', kids=[], loc=None, dat=None):
        super(NodeParentheses, self).__init__(typ, kids, loc, dat)


class NodeOpInfix2(Node):     
    '''
    AST node for a (binary) infix operator: + - * / ^ and or
        typ     : type string, usually: 'm_i2'
        kids    : [LHS, RHS] both sides of the operator
        loc     : location in input string
        dat     : operator symbol e.g.: '+'
    '''
    def __init__(self, typ='m_i2', kids=[], loc=None, dat=None):
        super(NodeOpInfix2, self).__init__(typ, kids, loc, dat)
        
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
        typ     : type string, usually: 'm_p1'
        kids    : [RHS] the term on which the operator acts
        loc     : location in input string
        dat     : operator symbol e.g.: '-'
    '''
    def __init__(self, typ='m_p1', kids=[], loc=None, dat=None):
        super(NodeOpPrefix1, self).__init__(typ, kids, loc, dat)
        
    def rhs(self):
        '''Return the right hand side'''
        return self.kids[0]
    def operator(self):
        '''Return the operator (string)'''
        return self.dat
    
        
class NodeAttrAccess(Node):
    '''
    AST node for access to a variable or parameter.
    Has additional attribute deriv.
        typ     : type string, usually: 'valA'
        kids    :  ? slice object if attribute is an array?
        loc     : location in input string
        dat     : None
        
        deriv   : [],['time'] or list of distibution domains
        attrName: ['proc', 'model1', 'a'], list of strings; the dot separated name.
    '''
    #TODO: rename into NodeAttrAccess
    def __init__(self, typ='valA', kids=[], loc=None, dat=None, deriv=[], 
                 attrName=[], targetName=None):
        '''
        deriv    : [],['time'] or list of distibution domains. Shows that
                   derivative of variable is accessed.
        attrName : dotted name as list of strings
        '''
        Node.__init__(self, typ, kids, loc, dat)
        self.deriv = deriv[:]
        self.attrName = attrName[:]#TODO: change into tuple
        self.targetName = targetName
        

class NodeAssignment(Node):
    '''
    AST node for an assignment: ':='
        typ     : type string, usually: 'assign'
        kids    : [LHS, RHS] both sides of the assignment operator
        loc     : location in input string
        dat     : ':='
    '''
    def __init__(self, typ='assign', kids=[], loc=None, dat=None):
        super(NodeAssignment, self).__init__(typ, kids, loc, dat)
        
    def lhs(self):
        '''Return the assignment's left hand side'''
        return self.kids[0]
    def rhs(self):
        '''Return the assignment's right hand side'''
        return self.kids[1]
        
        
class NodeBlockExecute(Node):
    '''
    AST Node for inserting the code of a sub-model's block
    (calling a user defined template function)
    '''
    def __init__(self, typ='blockExecute', kids=[], loc=None, dat=None, 
                 blockName=None, subModelName=None):
        super(NodeBlockExecute, self).__init__(typ, kids, loc, dat)
        self.blockName = blockName
        self.subModelName = subModelName
        
        
class NodeStmtList(Node):
    '''
    AST Node for list of statements
    Each child is a statement.
    '''
    def __init__(self, typ='stmtList', kids=[], loc=None, dat=None):
        super(NodeStmtList, self).__init__(typ, kids, loc, dat)


class NodeAttrDef(Node):
    '''
    AST node for definition of a variable, parameter or submodel.
        typ         : type string, usually: 'defAttr'
        kids        : []
        loc         : location in input string
        dat         : None     
        
        attrName        : identifier; name of the attribute
        className       : type of the attribute: Real for numbers, the class 
                          name for sub-models.
        role            : 'var', 'par' or None
        isSubmodel      : True or False
        isStateVariable : True or False
        targetName      : Name in the target language (string)
   '''
    def __init__(self, typ='defAttr', kids=[], loc=None, dat=None, 
                        attrName=None, className=None, role=None, 
                        isSubmodel=None, isStateVariable=None, targetName=None):
        Node.__init__(self, typ, kids, loc, dat)
        self.attrName = attrName #TODO: make this always a tuple. Currently AST: string ILT: tuple
        self.className = className
        self.role = role
        self.isSubmodel = isSubmodel
        self.isStateVariable = isStateVariable
        self.targetName = targetName
        
        
class NodeBlockDef(Node):
    """
    AST node for block (method, function?) definition.
    
    A block can be seen as a method that only modifies the class' attributes.
    It has neither arguments nor return values. It is treated as an C++ inline 
    function or template.
    
    The block's childern are the statements.
    """
    def __init__(self, typ='blockDef', kids=[], loc=None, dat=None, name=None):
        '''
        name : name of the block
        '''
        Node.__init__(self, typ, kids, loc, dat)
        self.name = name


class NodeClassDef(Node):
    """
    AST node for class definition.
    """
    def __init__(self, typ='classDef', kids=[], loc=None, dat=None, name=None, role=None):
        '''
        name : classname
        role : "process", "model" 
        '''
        Node.__init__(self, typ, kids, loc, dat)
        self.className = name
        self.role = role



class DepthFirstIterator(object):
    """
    Iterate over each node of a (AST) tree, in a depth first fashion.
    Designed for Node and its subclasses. It works for other nodes though:
    The nodes must have the functions __getitem__ and __len__.
    
    Usage:
    >>> t1 = Node('root 0.0', [Node('c 1.0', [Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    >>> for n in DepthFirstIterator(t1):
    ...     print repr(n)
    ... 
    Node('root 0.0',[Node('c 1.0',[Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    Node('c 1.0',[Node('c 2.0',[]), Node('c 2.1',[])])
    Node('c 2.0',[])
    Node('c 2.1',[])
    Node('c 1.1',[])
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
        #go to one level down, to current child. 
        nextNode = currNode[currChild]
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
    
    def __init__(self, root):
        '''root : the root of the tree, which will be printed'''
        self.root = root
        self.indentWidth = 4
            
            
    def printTree(self):
        print self.toStringTree()


    def toStringTree(self):
        treeStr = ''
        indentStepStr = '|' + ' '*int(self.indentWidth - 1)
        for node, depth in self.root.iterDepthFirst(True):
            indentStr = indentStepStr * depth
            
            #print attributes that are always present
            stdAttrStr = indentStr + node.__class__.__name__ + ' typ: ' + str(node.typ) + \
                         ' loc: ' + str(node.loc) + ' dat: ' + str(node.dat) + \
                         ' ID: ' + str(id(node))
            treeStr += stdAttrStr  + '\n'
            
            #print attributes that may be present in derived classes 
            standardAttributes = set(['typ', 'kids', 'loc', 'dat'])
            extraAttrStr = indentStr + ': '
            extraAttrNum = 0
            for key, attr in node.__dict__.iteritems():
                if key in standardAttributes:
                    continue
                extraAttrStr += key + ': ' + str(attr) + ' '
                extraAttrNum += 1
            #only add if there are extra attributes
            if extraAttrNum > 0:
                treeStr += extraAttrStr  + '\n'
        return treeStr



class UserException(Exception):
    '''Exception that transports user visible error messages'''
    def __init__(self, message, loc=None, str=None):
        Exception.__init__(self)
        self.message = message
        '''The error message'''
        self.loc = loc
        '''Position in the input string, where the error occured'''
        self.str = str
        '''When not none take this as the input string'''

    def __str__(self):
        return 'Error! ' + self.message + '\n At position: ' + str(self.loc)
    #TODO: better error message formating
    #TODO: include str in all Node(s) to facilate error message handling?



#------------ testcode --------------------------------------------------
if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #perform the doctests
    def doDoctest():
        import doctest
        doctest.testmod()   
    doDoctest()
    
    print 'Test the AST:'
    t1 = Node('root 0.0', [Node('c 1.0', [Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    
    print 'print the tree'
##    TreePrinter(t1).printTree()
    print t1

    print 'iterating over only the children of a node:'
    for n in t1:
        print n.typ

    print 'iterating over the whole tree:'
    for n,d in t1.iterDepthFirst(returnDepth=True):
        print n.typ, 'depth: ', d
        
    

    
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass

