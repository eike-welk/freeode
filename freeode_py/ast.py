############################################################################
#    Copyright (C) 2006 by Eike Welk   #
#    eike.welk@post.rwth-aachen.de   #
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
    '''Building block of a n-ary tree structure.'''

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
    AST node for access to a variable or parameter.
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



class TreeIterator(object):
    """
    Iterate over each node of a (AST) tree, in a depth first fashion.
    Designed for Node and its subclasses. It works for other nodes though:
    The nodes must have functions __getitem__ and __len__.
    """

    def __init__(self, treeRoot, returnDepth=False):
        """
        treeRoot    : root node of the tree over which the iterator goes.
        returnDepth : if True the __next__ function retuns a tuple
                      (node, depth) otherwise it only returns the current
                      node.
        """
        self.stack = [] #tuples (node, next_child) go here.
        self.depth = 0       #how deep we are in the tree.
        self.root = treeRoot
        self.returnDepth = returnDepth


    def __iter__(self):
        '''Called at start of for loop.'''
        return self


    def __next__(self):
        '''Go to the next element and return it.'''
        #start: go to root node, the child to visit is [0]
        if len(self.stack) == 0:
            self.stack = [(self.root, 0)]
            return self._handleReturnDepth(self.root, self.depth)

        #normal operation -----------------------
        currNode, currChild = self.stack[-1] #get current state

        #if no children left: go up one level
        while currChild == len(currNode):
            self.stack.pop()
            self.depth -= 1
            currNode, currChild = self.stack[-1] #get state from one level up

        #remember to visit next child when we come here again
        self.stack[-1] = (currNode, currChild+1)
        #go to one level down, to current child
        theChild = currNode[currChild]
        self.stack.append((theChild, 0))
        self.depth += 1
        return self._handleReturnDepth(theChild, self.depth)


    def _handleReturnDepth(self, node, depth):
        if self.returnDepth:
            return (node, depth)
        else:
            return node

#------------ testcode --------------------------------------------------
testAST = True
#testAST = False
if testAST:
    print '----------------------------------------------------'
    print 'Test the AST:'
    t1 = Node('root 0.0', [Node('c 1.0', [Node('c 2.0',[]), Node('c 2.1',[])]), Node('c 1.1',[])])
    print t1

    print 'iterating over only the children of a node:'
    for n in t1:
        print n.typ

    print 'iterating over the whole tree:'
    for n in TreeIterator(t1):
        print n.typ

    print '----------------------------------------------'
