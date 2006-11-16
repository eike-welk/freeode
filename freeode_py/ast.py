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




class Node(object):
    '''
    Building block of a n-ary tree structure.  
    
    TODO: turn this into a doctest
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
    >>> for n,d in t1.iterateDepthFirst(returnDepth=True):
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
        object.__init__(self)
        self.typ = typ   # type string
        #self.parent = None
        self.kids = kids[:] # list of children
        self.loc  = loc     # the location in the program
        self.dat = dat      # whatever is appropriate


    def __repr__(self):
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

        reprStr = className  + '(' + typeStr + childStr + locStr + datStr + \
                                    extraAttrStr + ')'
        return reprStr

    #TODO: __str__() that prints the tree in a neat way

    #let for loop iterate over children
    def __iter__(self):
        return self.kids.__iter__()

    #return number of children
    def __len__(self):
        return len(self.kids)

    #Acces to childern throug []
    def __getitem__(self, i):
        return self.kids[i]
    #def __getslice__(self, low, high):
        #return self.kids[low:high]
    #def __setslice__(self, low, high, childList):
        #self.kids[low:high] = seq
        
##    def __cmp__(self, o):
##        return cmp(self.type, o)

    def iterateDepthFirst(self, returnDepth=False):
        '''
        Iterate over whole (sub) tree in a depth first manner.
        returnDepth :   if True the iterator returns a tuple (node, depth) otherwise it 
                        returns only the current node.
        returns: a DepthFirstIterator instance
        '''
        return DepthFirstIterator(self, returnDepth)

##    def copy(self):
##        '''
##        TODO: use built in copy module
##          import copy
##          x = copy.copy(y)        # make a shallow copy of y
##          x = copy.deepcopy(y)    # make a deep copy of y
##
##        Make a (recursive) deep copy of the object.
##        This will (currently) not work with attributes that are lists or
##        dictionaries!
##        See: http://www.python.org/search/hypermail/python-1993/0267.html
##        '''
##        newObject = self.__class__()     #Create new object with same class
##        #duplicate attributes
##        for key in self.__dict__.keys(): #key is a string
##            oldAttr = getattr(self, key)
##            if hasattr(oldAttr, 'copy'): #If attribute has a copy function then
##                newAttr = oldAttr.copy() #use the copy function to duplicate it
##            else:
##                newAttr = oldAttr #else shallow copy - attribute is believed to
##                                  #be immutable e.g.: number.
##            setattr(newObject, key, newAttr) #Put duplicated attribute into
##                                             #new object
##        return newObject




class NodeValAccess(Node):
    '''
    Specialized AST node for access to a variable or parameter.
    Has additional attribute deriv.
        typ: type string, usually: 'valA'
        kids: slice?
        loc: location in input string
        dat: list of identifiers; the dot separated name, from left to right.
        deriv: [],['time'] or list of distibution domains
    '''

    def __init__(self, typ='valA', kids=[], loc=None, dat=None, deriv=[]):
        '''
        deriv: [],['time'] or list of distibution domains. Shows that
        derivative of variable is accessed.
        '''
        Node.__init__(self, typ, kids, loc, dat)
        self.deriv = deriv[:]



#TODO: Create specialized nodes for attribute definition: 
#TODO:      Definition of numbers: 'defAttrVal'
#TODO:      Definition of sub-model 'defAttrClass' ? 'defAttrSubMod'




class DepthFirstIterator(object):
    """
    Iterate over each node of a (AST) tree, in a depth first fashion.
    Designed for Node and its subclasses. It works for other nodes though:
    The nodes must have the functions __getitem__ and __len__.
    
    Usage:
    >>> t1 = Node('root 0.0', [Node('c 1.0', [Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    >>> for n in DepthFirstIterator(t1):
    ...     print n
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
        indentStepStr = '|' + ' '*int(self.indentWidth - 1)
        for node, depth in self.root.iterateDepthFirst(True):
            indentStr = indentStepStr * depth
            
            #print attributes that are always present
            stdAttrStr = indentStr + node.__class__.__name__ + ' typ: ' + str(node.typ) + \
                         ' loc: ' + str(node.loc) + ' dat: ' + str(node.dat)
            print stdAttrStr
            
            #print attributes that may be present in derived classes 
            standardAttributes = set(['typ', 'kids', 'loc', 'dat'])
            extraAttrStr = indentStr + '  '
            extraAttrNum = 0
            for key, attr in node.__dict__.iteritems():
                if key in standardAttributes:
                    continue
                extraAttrStr += key + ':' + str(attr) + ' '
                extraAttrNum += 1
            
            if extraAttrNum > 0:
                print extraAttrStr
            

#------------ testcode --------------------------------------------------
if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #TODO: add doctest tests. 
    
    print 'Test the AST:'
    t1 = Node('root 0.0', [Node('c 1.0', [Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    print t1

    print 'iterating over only the children of a node:'
    for n in t1:
        print n.typ

    print 'iterating over the whole tree:'
    for n,d in t1.iterateDepthFirst(returnDepth=True):
        print n.typ, 'depth: ', d
        
    print 'print the tree'
    TreePrinter(t1).printTree()
    
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass

