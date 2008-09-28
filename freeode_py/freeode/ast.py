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
import weakref
from weakref import proxy

import pyparsing


##TODO: svn command: svn propset svn:keywords Revision ast.py
#__fileVersion__ = "$LastChangedRevision: 43 $"
#__fileVersion__ = "$Rev: 43 $"


#version of the Siml compiler.
PROGRAM_VERSION = '0.4.0-dev-1'



class DuplicateAttributeError(Exception):
    '''
    Exception raised by NameSpace
    when the user tries to redefine an attribute.
    '''
    def __init__(self, msg='Duplicate Attribute.', attrName=None):
        Exception.__init__(self, msg)
        self.attrName = attrName

class UndefinedAttributeError(Exception):
    '''
    Exception: Attribute is unknown in namespace.
    '''
    def __init__(self, msg='Undefined Attribute.', attrName=None):
        Exception.__init__(self, msg)
        self.attrName = attrName


class NameSpace(object):
    '''
    Name space for modules, classes and functions.

    TODO: Convert this class to (or incorporate into)
          basic instance object "object".
          Instance object does not need to be a 'ast.node' subclass;
          only the functions need to contain pieces of the AST.
    '''
    def __init__(self):
        #the attributes of this name space
        self._nameSpaceAttrs = {} #weakref.WeakValueDictionary()
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
        #add attribute to name space - attributes must be unique
        if name in self._nameSpaceAttrs:
            #TODO: raise UserException? Error message as named argument?
            raise DuplicateAttributeError('Duplicate attribute: ' + name, name)
        self._nameSpaceAttrs[name] = newAttr
        return

    def setFuncAttr(self, name, newFunc):
        '''
        Special method to enter NodeFuncDef into namespace.

        Functions don't need to be unique. Therefore they are stored
        in special containers: "FunctionOverloadingResolver".
        '''
        if not isinstance(newFunc, NodeFuncDef):
            raise Exception('Argument 2 must be NodeFuncDef')

        oldAttr = self.getAttr(name, None)
        if oldAttr is None:
            self.setAttr(name, list(newFunc))
        elif isinstance(oldAttr, list):
            oldAttr.append(newFunc)
        else:
            raise UserException('Function can not have same name like data: '
                                + str(name), newFunc.loc)

    def update(self, otherNameSpace):
        '''
        Put attributes of otherNameSpace into this name space.
        Raises exceptions when attributes are redefined.
        '''
        for name, node in otherNameSpace._nameSpaceAttrs.iteritems():
            self.setAttr(name, node)

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
        return str(name) in self._nameSpaceAttrs

    def getAttr(self, name, default=None):
        '''Return attribute with that name from this name space'''
        return self._nameSpaceAttrs.get(str(name), default)

    def findDotName(self, dotName, default=None):
        '''
        Find dot name recursively and return attribute with this name.

        #TODO: raise UserException when attribute undefined?
        #      Error message could be named attribute."
        '''
        dotName = DotName(dotName) #make compatible with str too
        firstPart = self._nameSpaceAttrs.get(dotName[0], None)
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
            return default



class FlatNameSpace(NameSpace):
    '''A name space where attributes can have multiple dots in their name'''
    def __init__(self):
        NameSpace.__init__(self)

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
        if not isinstance(name, (str, DotName)):
            raise Exception('Argument name must be of type str or DotName! type(name): '
                            + str(type(name)) + ' str(name): ' + str(name))
        name = str(name)
        #add attribute to name space - attributes must be unique
        if name in self._nameSpaceAttrs:
            raise DuplicateAttributeError('Duplicate attribute: ' + name, name)
        self._nameSpaceAttrs[name] = newAttr
        return

    def findDotName(self, dotName, default=None):
        '''
        Find dot name recursively and return attribute with this name.
        '''
        dotName = DotName(dotName) #make compatible with str too
        attr = self.getAttr(dotName, None)
        if attr is not None:
            return attr
        #maybe partial name is known here.
        #Rest may be stored in child name space
        nameShort = dotName
        nameTail = DotName()
        while len(nameShort)>1:
            #remove last element
            nameTail += nameShort[-1]
            nameShort = nameShort[0:-1]
            #try to find shortened name; look up rest of name recursively
            attr = self.getAttr(nameShort, None)
            if attr is not None:
                return attr.findDotName(nameTail, default)
        return default



class ExecutionEnvironment(object):
    '''
    Container for name spaces where symbols are looked up.
    Function findDotName searches the symbol in all name spaces.

    TODO: put into module intermediate?
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
    def findDotName(self, *posArg):
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
            attr = scope.findDotName(dotName, None)
            if attr is not None:
                return attr
        #attribute could not be found
        if raiseErr:
            raise UndefinedAttributeError(attrName=str(dotName))
        else:
            return default            


#    def setGlobalScope(self, inNameSpace):
#        '''
#        Change the global name space.
#        The global name space is finally searched when the DotName is neither
#        found locally (self._nameSpaceAttrs) nor in the scope of the "this"
#        pointer (self.thisScop).
#
#        Used by self.findDotName(...), but not by self.getAttr(...).
#        '''
#        self._globalScope = inNameSpace
##        if inNameSpace is None:
##            self._globalScope = None
##        elif isinstance(inNameSpace, weakref.ProxyTypes):
##            self._globalScope = inNameSpace
##        else:
##            self._globalScope = weakref.proxy(inNameSpace)
#
#    def getGlobalScope(self):
#        '''Return the global name space.'''
#        return self._globalScope
#
#    globalScope = property(getGlobalScope, setGlobalScope, None,
#                           'Global (module) name space.')
#
#    def setThisScope(self, inNameSpace):
#        '''
#        Change the name space of the "this" pointer.
#        The "this" name space is searched second, when the DotName is not
#        found locally. When the DotName is not fount in the "this" name space
#        the global name space is searched.
#
#        Used by self.findDotName(...), but not by self.getAttr(...).
#        '''
#        self._thisScope = inNameSpace
##        if inNameSpace is None:
##            self._thisScope = None
##        elif isinstance(inNameSpace, weakref.ProxyTypes):
##            self._thisScope = inNameSpace
##        else:
##            self._thisScope = weakref.proxy(inNameSpace)
#
#    def getThisScope(self):
#        '''Return the "this" name space.'''
#        return self._thisScope
#
#    thisScope = property(getGlobalScope, setGlobalScope, None,
#                           'Name space of the this pointer, class name space.')



##TODO: inherit FromNodeFuncDef ?
##TODO: rename to multimethod
#class FunctionOverloadingResolver(object):
#    '''
#    Store multiple functions with the same name.
#    Find the correct overloaded function, that matches a function call best.
#    '''
#
#    def __init__(self, inFuncDef=None):
#        '''
#        ARGUMENT
#        inFuncDef : NodeFuncDef
#            The first function stored in the container. Optional.
#        '''
#        self._functions = []
#        if inFuncDef is not None:
#            self.append(inFuncDef)
#
#    def append(self, inFuncDef):
#        '''Append a function to the list'''
#        if not isinstance(inFuncDef, NodeFuncDef):
#            raise Exception('Argument must be a NodeFuncDef! type(inFuncDef):'
#                            + str(type(inFuncDef)))
#        self._functions.append(inFuncDef)
#        return
#
#    def resolve(self, inFuncCall):
#        '''
#        Return a function that matches the function call's signature.
#        (currently always the last function in the list)
#        '''
#        return self._functions[-1]
#
##TODO: create MethodOverloadingResolver(OverloadingResolver):


######################## Old Node Object ###########################################
#class Node(object):
#    '''
#    Building block of a n-ary tree structure.
#    The abstract syntax tree (AST), and the intermediate language tree (ILT),
#    are made of nodes that have this class as their base class.
#
#    Usage:
#    >>> t1 = Node([Node([Node([],3,'leaf'), Node([],4,'leaf')], 2, 'branch'),
#    ...            Node([],5,'leaf')], 1, 'root')
#
#    print tree (loc attribute is abused here)(<BLANKLINE> does not work):
#    > print t1
#    Node:: dat: root loc: 1
#    |   Node:: dat: branch loc: 2
#    |   |   Node:: dat: leaf loc: 3
#    |   |   Node:: dat: leaf loc: 4
#    |   Node:: dat: leaf loc: 5
#
#    access to children with  [] operator:
#    >>> t1[0][1]
#    Node(,[], 4, 'leaf')
#
#    iterating over only the children of a node:
#    >>> for n in t1:
#    ...     print n.loc
#    ...
#    2
#    5
#
#    iterating over the whole tree:
#    >>> for n,d in t1.iterDepthFirst(returnDepth=True):
#    ...     print n.dat, ' depth: ', d
#    ...
#    root  depth:  0
#    branch  depth:  1
#    leaf  depth:  2
#    leaf  depth:  2
#    leaf  depth:  1
#
#    TODO: New, simpler 'node' implementation, that does not behave like a list
#          (without kids list).
#        Methods:
#        - copy(), __deepcopy__()
#        - __str__()
#        - __repr__() ???
#        - __init__() elegant and matching to repr + usage pattern ???
#    '''
#
#    def __init__(self, kids=None, loc=None, dat=None):
#        #TODO: write an init function that can accept any number of named arguments
#        #Variabe number of arguments:
#        #*args    : is a list of all normal arguments
#        #**kwargs : is a dict of keyword arguments
#        #Code for derived classes: super(A, self).__init__(*args, **kwds)
#        #self.parent = None
#        #list of children
#        self.kids = []
#        #appendChild checks the type
#        if kids is not None:
#            for child in kids:
#                self.appendChild(child)
#        #the node's location in the parsed text
#        self.loc  = loc
#        #any data; whatever is appropriate
#        self.dat = dat
#
#
#    def __repr__(self):
#        '''Create string representation that can also be used as code.'''
#        className = self.__class__.__name__
#        childStr = ',' + repr(self.kids)
#        #if location and contents have their default value, don't print them
#        if self.loc == None:
#            locStr = ''
#        else:
#            locStr = ', ' + repr(self.loc)
#        if self.dat == None:
#            datStr =''
#        else:
#            datStr = ', ' + repr(self.dat)
#        #treat all other attributes as named attributes
#        standardAttributes = set(['kids', 'loc', 'dat'])
#        extraAttrStr=''
#        for key, attr in self.__dict__.iteritems():
#            if key in standardAttributes:
#                continue
#            extraAttrStr += ', ' + key + '=' + repr(attr)
#        #assemble the string
#        reprStr = className  + '(' + childStr + locStr + datStr + \
#                                    extraAttrStr + ')'
#        return reprStr
#
#
#    def __str__(self):
#        '''Create pretty printed string represntation.'''
#        return TreePrinter(self).makeTreeStr()
#
#    def __iter__(self):
#        '''let for loop iterate over children'''
#        return self.kids.__iter__()
#
#    def __len__(self):
#        '''return number of children'''
#        return len(self.kids)
#
#    def appendChild(self, inNode):
#        '''Append node to list of children'''
#        #test if child is a node
#        if(not isinstance(inNode, Node)):
#            raise TypeError('Children must inherit from Node!')
#        self.kids.append(inNode)
#
#    def insertChild(self, index, inNode):
#        '''
#        Insert node into list of children.
#        New child is inserted before the child at position self[index].
#        '''
#        #test if child is a node
#        if(not isinstance(inNode, Node)):
#            raise TypeError('Children must inherit from Node!')
#        self.kids.insert(index, inNode)
#
#    def insertChildren(self, index, inSequence):
#        '''
#        Insert a node's children into list of own children.
#
#        New childen are inserted before the child at position self[index].
#
#        Parameters
#        index: int
#            The children are inserted before the this index.
#        inSequence: Node
#            Container of the children that will be inserted.
#
#        Returns
#        None
#        '''
#        if(not isinstance(inSequence, Node)):
#            raise TypeError('Node.insertChildrenChildren: '
#                            'argument 2 must inherit from Node!')
#        self.kids[index:index] = inSequence.kids
#
#    def __delitem__(self, index):
#        '''Delete child at specified index'''
#        del self.kids[index]
#
#    def __getitem__(self, i):
#        '''
#        Retriev children through []
#
#        Parameters
#        i: int, slice
#            Index of element which is retrieved, or slice object describing
#            the subsequence which should be retrieved
#
#        Returns
#        Node, sequence of Node
#            The nodes that should be returned
#        '''
#        return self.kids[i]
#
##    def __setitem__(self, i, item):
##        '''
##        Change children through []
##
##        Parameters
##        i: int, slice
##            Index of element which is changed, or slice object describing
##            the subsequence which should be changed
##        item: Node, sequence of Node
##
##        Returns
##        None
##        '''
##        #TODO: type checking
##        #TODO: How should Nodes be treated in case slices are given?
##        #      As sequences or as single objects?
##        self.kids[i] = item
#
###    def __cmp__(self, o):
###        return cmp(self.type, o)
#
#    def iterDepthFirst(self, returnDepth=False):
#        '''
#        Iterate over whole (sub) tree in a depth first manner.
#        returnDepth :   if True the iterator returns a tuple (node, depth) otherwise it
#                        returns only the current node.
#        returns: a DepthFirstIterator instance
#        '''
#        return DepthFirstIterator(self, returnDepth)
#
#
#    def copy(self):
#        '''
#        Return a (recursive) deep copy of the node.
#
#        Only children are copied deeply;
#        all other attributes are not copied. Only new references are made.
#        '''
#        return copy.deepcopy(self)
#
#
#    def __deepcopy__(self, memoDict):
#        '''Hook that does the copying.
#        Called by the function copy.deepcopy()'''
#        #create empty instance of self.__class__
#        newObj = Node.__new__(self.__class__)
#        for name, attr in self.__dict__.iteritems():
#            if name == 'kids':
#                #kids: make deep copy
#                newObj.kids = copy.deepcopy(self.kids, memoDict)
#            else:
#                #normal attribute: no copy, only reference.
#                setattr(newObj, name, attr)
#        return newObj



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
    aa_show_ID = False
    #Maximal nesting level, to catch infinite recursion.
    aa_max_nesting_level = 100
    #string to symbolize one indent level
    aa_indent_step_str = '|' + ' '*int(aa_indent_width - 1)
    
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
        return self.aa_make_tree()
    
    def aa_attr_category(self, attr_name):
        '''
        Categorize attributes for Ascii-art
        
        Returns:
            -1: attribute does not exist
            0: not a Node
            1: not owned
            2: Node
            3: list(Node)
            # removed: 4: list(list(Node))
            TODO: category for dict(string():Node())
        '''
        #get attribute
        if attr_name in self.__dict__:
            attr = self.__dict__[attr_name]
        else:
            return -1 # attribute does not exist
        #categorize attribute
        if isinstance(attr, weakref.ProxyTypes):
            return 1 #not owned by this Node
        elif isinstance(attr, Node):
            return 2 # Node
        elif isinstance(attr, list) and len(attr) > 0 and \
             isinstance(attr[0], Node):
            return 3 # list(Node)
#        elif isinstance(attr, list)    and len(attr) > 0    and \
#             isinstance(attr[0], list) and len(attr[0]) > 0 and \
#             isinstance(attr[0][0], Node):
#            return 4 # list(list(Node))
        else:
            return 0 #not a Node
            
    def aa_make_str_block(self, attr_name_list, indent_str, nesting_level):
        '''
        Convert attributes to a string. 
        
        Uses different algorithms for different attribute categories.
        Performs the line wrapping.
        '''
        #initialize buffers
        tree = ''
        line = indent_str
        #loop over list of attribute names
        for name in attr_name_list:
            cat = self.aa_attr_category(name)
            #Non Node classes, assumed to be small 
            #the atoms that really carry the information)
            if cat == 0:
                line += name + ' = ' + str(self.__dict__[name]) + '; '
                if len(line) > self.aa_wrap_line_at:
                    tree += line + '\n'
                    line = indent_str
            #Anything not owned by this node (printed small)
            elif cat == 1:
                line += (name + ' = ' 
                         + str(self.__dict__[name].__class__.__name__) + ' :: '
                         + repr(self.__dict__[name]) + '; ')
                if len(line) > self.aa_wrap_line_at:
                    tree += line + '\n'
                    line = indent_str
            #Attribute is Node
            elif cat == 2:
                if line != indent_str: 
                    tree += line  + '\n'
                    line = indent_str
                tree += indent_str + name + ' = \n'
                tree += self.__dict__[name].aa_make_tree(nesting_level +1)
            #Attribute is list(Node)
            elif cat == 3:
                if line != indent_str: 
                    tree += line  + '\n'
                    line = indent_str   
                tree += indent_str + name + ' = list :: \n'     
                for item in self.__dict__[name]:
                    tree += item.aa_make_tree(nesting_level +1)  
#                    tree += indent_str + '|- ,\n'
            #Attribute is list(list(Node))
#            elif cat == 4:
#                raise Exception('Feature unimplemented!')
            else:
                raise Exception('Internal error! Unknown attribute category: ' 
                                + str(cat))
                
        if line != indent_str:
            tree += line  + '\n'
        return tree

    
    def aa_make_tree(self, nesting_level=0):
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
        attr_small = [a for a in body if self.aa_attr_category(a) <= 1]
        attr_big =    [a for a in body if self.aa_attr_category(a) > 1]
        
        #create header with type information
        tree_buffer += indent_str + self.__class__.__name__ + ' ::'
        if self.aa_show_ID:
            tree_buffer += ' ID: ' + hex(id(self))
        tree_buffer += ' ---------------------------------\n'
        indent_str += '|'
        
        #convert the attributes to string
        tree_buffer += self.aa_make_str_block(attr_top,    indent_str, nesting_level)
        tree_buffer += self.aa_make_str_block(attr_small,  indent_str, nesting_level)
        tree_buffer += self.aa_make_str_block(attr_big,    indent_str, nesting_level)
        tree_buffer += self.aa_make_str_block(attr_bottom, indent_str, nesting_level)
        
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
        #create empty instance of self.__class__
        new_obj = Node.__new__(self.__class__)
        for name, attr in self.__dict__.iteritems():
            if not isinstance(attr, weakref.ProxyTypes):
                #attribute owned by self: make deep copy
                new_attr = copy.deepcopy(attr, memo_dict)
                setattr(new_obj, name, new_attr)
            else:
                #attribute owned by other object: no copy only reference
                setattr(new_obj, name, attr)
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
            Name of attribute (DotName('a'), DotName('proc.model1.a'))
        target_name : 
            name in the target language (string, DotName)
            Necessary? should be in node data (symbol table). See self.attr_ref
        attr_ref: 
            Reference to the attribute (definition, into symbol table) 
            which is accessed.
        attr_is_builtin:
            True if identifier encodes access to variable of builtin type. 
            Usefull for flattening. 
        loc: 
            Location in input string
    '''
    def __init__(self):
        super(NodeIdentifier, self).__init__()
        self.name = None
        #TODO: necessary? should be in node data. See self.attr_ref
        self.target_name = None 
        self.attr_ref = None
        self.attr_is_builtin = None #TODO: necessary? 
        self.loc = None


class NodeAttrAccess(Node):
    '''
    AST node for dot operator. 
    '''
    def __init__(self):
        super(NodeAttrAccess, self).__init__()
        #TODO: Implementation
        

class NodeParentheses(Node):
    '''
    Represent a pair of parentheses that enclose an expression, in the AST.
    
    Example: ( ... )
    Treated like a special (do nothing) operator
    
    Data attributes:
        arguments: list(Node())
            Mathematical expression between the parentheses. 
            Naming is chosen to unify operators and function call
        loc: 
            Location in input string
    '''
    def __init__(self):
        super(NodeParentheses, self).__init__()
        self.arguments = []
        self.loc = None


class NodeOpInfix2(Node):
    '''
    AST node for a (binary) infix operator: + - * / ^ and or
    Data attributes:
        operator: 
            Operator symbol e.g.: '+'
        arguments:  list(Node(), Node())
            Expression on left and right of operator: 
            left: arguments[0], right: arguments[1]
            Naming is chosen to unify operators and function call
        loc: 
            Location in input string
    '''
    def __init__(self):
        super(NodeOpInfix2, self).__init__()
        self.operator = None
        self.arguments = []
        self.loc = None


class NodeOpPrefix1(Node):
    '''
    AST node for a (unary) prefix operator: - not
    
        operator: 
            Operator symbol e.g.: '-'
        arguments:  list(Node())
            Expression on right side of operator
            Naming is chosen to unify operators and function call
        loc: 
            Location in input string
  '''
    def __init__(self):
        super(NodeOpPrefix1, self).__init__()
        self.operator = None
        self.arguments = []
        self.loc = None


class NodeFuncCall(Node):
    '''
    AST Node for calling a function or method.
    
    This will be usually done by inserting the code of the function's body
    into the top level function. Similar to an inline function in C++.
    
    Data attributes:
        name: DotName
            Dotted name of function
        attrRef: 
            Reference to the function (definition) which is accessed.
            Name choosen to ease unification with NodeIdentifier.
        arguments: 
            List of positional arguments
        keyword_arguments: 
            Dictionary of keyword arguments
        loc: 
            Location in input string
    '''
    def __init__(self):
        super(NodeFuncCall, self).__init__()
        self.name = None
        self.attr_ref = None
        self.attr_is_builtin = None
        self.arguments = []
        self.keyword_arguments = {}
        self.loc = None

#-------------- Statements --------------------------------------------------
class NodeIfStmt(Node):
    '''
    AST Node for an if ... the ... else statement
    Data attributes:
        kids    : [<condition>, <then statements>, <else statements>]
        loc     : location in input string
        dat     : None
    '''
    def __init__(self):
        super(NodeIfStmt, self).__init__()

    #TODO: design good interface for NodeIfStmt
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
        loc     : location in input string
        lhs     : Left hand side of operator
        rhs     : Right hand side of operator
        operator: '='
    '''
    def __init__(self):
        super(NodeAssignment, self).__init__()
        self.operator = '='


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
    def __init__(self, kids=None, loc=None, dat=None, newline=True):
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
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeGraphStmt, self).__init__(kids, loc, dat)


class NodeStoreStmt(Node):
    '''
    AST Node for storing variables
    Data attributes:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : None
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeStoreStmt, self).__init__(kids, loc, dat)


class NodeReturnStmt(Node):
    '''
    AST Node for the return statement
    Data attributes:
        kids        : the expressions of the argument list
        loc         : location in input string
        dat         : The return value (expression)
    '''
    def __init__(self, kids=None, loc=None, dat=None):
        super(NodeReturnStmt, self).__init__(kids, loc, dat)


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


class NodeForeignCodeStmt(Node):
    '''
    AST Node for the foreign_code statement
    Data attributes:
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
class RoleCompiledObject(AttributeRole):
    '''Mark objects that are compiled. TODO: seems to be no good solution.'''
    pass
class RoleConstant(AttributeRole):
    '''The attribute is a constant'''
    userStr = 'const'
class RoleParameter(AttributeRole):
    '''
    Attribute is a parameter of the simulation:
    - is constant during the simulation, but can vary between simulations.
    - is stored.
    '''
    userStr = 'param'
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
    userStr = 'function argument'
class RoleLocalVariable(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a local variable:
    - can vary during the simulation
    - should be optmized away
    - is not stored.
    '''
    userStr = 'local variable'
class RoleVariable(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a state or algebraic variable:
    - can vary during the simulation
    - is stored.
    '''
    userStr = 'variable'
class RoleStateVariable(RoleVariable):
    '''The attribute is a state variable'''
    userStr = 'state_variable'
class RoleAlgebraicVariable(RoleVariable):
    '''The attribute is an algebraic variable'''
    userStr = 'algebraic_variable'


class NodeDataDef(Node, NameSpace):
    '''
    AST node for definition of a variable, parameter or submodel.
    Data Attributes:
        kids            : [<default value>, <instance attributes>]
        loc             : location in input string
        dat             : None

        value           : Default value, initial value, value of a constant; interpreted
                          according to context. (mathematical expression)
                          (propperty stored in kids[0])
        body            : statements of a recursive data definition. The statements of a class
                          definition. (propperty stored in kids[0])

        name            : name of the attribute. DotName
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
        isBuiltinType   : If True: the data is a built in class. The inner
                          structure of these objects is invisible.
        noFlatten       : If True: Do not flatten this data tree. The class is
                          handled specially in a later step.
        TODO: isReference : Contains no own data; points to something else.
    '''
    def __init__(self, kids=None, loc=None, dat=None,
                        name=None, className=None, targetName=None,
                        role=None):
        Node.__init__(self, kids, loc, dat)
        NameSpace.__init__(self)
        if not self.kids:
            self.kids = [nodeNone, NodeStmtList()]
        self.name = name
        self.className = className
        self.targetName = targetName
        self.role = role
        self.isBuiltinType = False
        self.noFlatten = False
        #self.isAssigned = False #can not be done this easy because variables
        #                        #are assigned in initialize() and in dynamic()

    #Get or set the default value
    def getValue(self):
        return self.kids[0]
    def setValue(self, inValue):
        self.kids[0] = inValue
    value = property(getValue, setValue, None,
                   'Default value or initial value of the defined data (propperty).')
    #Get or set the recursive definitions
    def getStatements(self):
        return self.kids[1]
    def setStatements(self, inDefs):
        self.kids[1] = inDefs
    body = property(getStatements, setStatements, None,
                   'Attribute definitions. Copied from class definition. (propperty).')


class NodeCompileStmt(NodeDataDef):
    '''
    AST node for compile statement.
    A data statement where the the functions are instantiated for flattening
    and code generation.

    mainFuncs : List of (generated) main functions: [NodeFuncDef]
    '''
    def __init__(self, kids=None, loc=None, dat=None,
                        name=None, className=None, targetName=None):
        NodeDataDef.__init__(self, kids, loc, dat,
                             name, className, targetName, role=RoleCompiledObject)
        self.mainFuncs = []


class NodeFuncDef(Node):
    """
    AST node for method/function definition.

    A function/method is comparable to an inline function or a template
    function in C++.

    The childern are the statements.
    Attributes:
    -----------
    kids : [<argument list>, <function body>]
    loc  : location in input string
    dat  : None

    name       : name of the function; DotName
    returnType : class name of return value; tuple of strings: ('Real',)
    environment: container for namespaces. Functions store the global name space
                 where they were defined.
    """
    def __init__(self, kids=None, loc=None, dat=None, name=None, returnType=None):
        Node.__init__(self, kids, loc, dat)
#        NameSpace.__init__(self)
        self.name = name
        if not self.kids:
            self.kids = [NodeStmtList(), NodeStmtList()]
        self.returnType = returnType
        self.environment = ExecutionEnvironment()
        self.isBuiltIn = False

    #Get and set the argument list
    def getArgList(self): return self.kids[0]
    def setArgList(self, inArgs): self.kids[0] = inArgs; inArgs.dat = 'argument list'
    argList = property(getArgList, setArgList, None,
                       'The argument list (proppery).')

    #TODO: rename to "statements"? Rationale: same name like in NodeDataDef
    #Get and set the function body
    def getFuncBody(self): return self.kids[1]
    def setFuncBody(self, inBody): self.kids[1] = inBody; inBody.dat = 'function body'
    body = property(getFuncBody, setFuncBody, None,
                        'The function body (proppery).')


class NodeGenFunc(NodeFuncDef):
    '''
    Generated function, expanded template; ready for flattening.

    The missing information of the NodeFuncDef is filled in. These "functions"
    exist once for each time a function is called. To distinguish them from
    functions writen by the user, this Node type is necessary.

    Attributes:
    -----------
    targetName :
            Individual name for each generated instance. Used in flattening
            process to give individual names to the local variables.
    '''
    def __init__(self, kids=None, loc=None, dat=None, name=None,
                  returnType=None):
        NodeFuncDef.__init__(self, kids, loc, dat, name, returnType)
        self.targetName = None


class NodeClassDef(Node, NameSpace):
    """
    AST node for class definition.
    Data Attributes:
    ----------------
    kids     : The statements, the block's code.
    loc      : location in input string
    dat      : None

    name     : name of the class defined here.
    baseName : name of the class, from which this class inherits.
    base     : refference to base class definition

    isBuiltinType :
        True if this class is built into the compiler
    noFlatten :
        True if the compiler should not flatten the class
    defEnvironment :
        Execution environment at time of definition. The data statements (and
        the assignments to constants) are executed in this environment.
    """
    def __init__(self, kids=None, loc=None, dat=None, name=None, baseName=None):
        Node.__init__(self, kids, loc, dat)
        NameSpace.__init__(self)
        self.name = name
        self.baseName = baseName
        self.base = None
        self.isBuiltinType = False
        self.noFlatten = False
        self.defEnvironment = None #TODO: put data statements into a function?

    #Get or set the class body through a unified name
    def getStatements(self):
        return self
    def setStatements(self, inDefs):
        self.kids = inDefs.kids
    body = property(getStatements, setStatements, None,
            'Attribute definitions and operations on constants. (propperty).')


class NodeModule(Node):
    '''
    Root node of a module (or of the program)
    Attributes:
        loc       : location in input string (~0)
        name      : Name of the module
        target_name: Name useful in the context of flattening or code generation
    '''
    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.target_name = None
        self.statements = []
        self.loc = None


class NodeFlatModule(Node, FlatNameSpace):
    '''
    Module where all attributes have long, dotted names, and where all
    attributes are defined on the top (module) level.
    Data defs are only built in types.

    Attributes:
    -----------
    kids      : Definitions, the program's code.
    loc       : location in input string (~0)
    dat       : None

    name      : Name of the module
    targetName: Name useful in the context of flattening or code generation
    '''
    def __init__(self, kids=None, loc=None, dat=None, name=None):
        Node.__init__(self, kids, loc, dat)
        FlatNameSpace.__init__(self)
        self.name = name
        self.targetName = None

#---------- Nodes End --------------------------------------------------------*

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
 
        raise Exception('DepthFirstIterator: Feaature not implemented!')
        #TODO: make it work with new node class again!
        self.stack = [(treeRoot, 0)] #tuples (node, childIndex).
        self.depth = 0  #how deep we are in the tree.
        self.returnDepth = returnDepth #flag: shoult we return the current depth
        self.start = True #remember that we've just been initialized


    def __iter__(self):
        '''Called at start of for loop.'''
        return self


    #TODO: enhance DepthFirstIterator: remember already seen nodes in set.
    #TODO: make possible child[i] == None
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



#class TreePrinter(object):
#    '''Print a tree of Node objects in a nice way.'''
#
#    indentWidth = 4
#    '''Number of chars used for indentation. Must be >= 1'''
#    wrapLineAt = 150
#    '''Length of line. Longer lines will be wrapped'''
#    showID = False
#    '''Also print the node's id()'''
#
#    def __init__(self, root=None):
#        '''
#        Argument:
#        root : Node
#            the root of the tree, which will be printed
#        '''
#        #tree's root node.
#        self.root = root
#        #buffer for the textual reprentation
#        self.treeStr = ''
#        #partially completed line for line wrapping
#        self.line = ''
#
#    #TODO: def setIndentStr(self, indentStr): ??
#    #          newIndentLevel(self, nLevel) ???
#    def putStr(self, indentStr, contentStr):
#        '''Put string into buffer and apply line wrapping'''
#        #is there enough room to write?
#        if len(indentStr) + 20 > self.wrapLineAt:
#            wrapLineAt = len(indentStr)+60 #no: extend right margin
#        else:
#            wrapLineAt = self.wrapLineAt #yes: normal wrap
#        #empty line has special meaning: new node is started
#        if self.line == '':
#            self.line = indentStr
#        #Do the line wrapping
#        if len(self.line) + len(contentStr) > wrapLineAt:
#            #print self.line
#            self.treeStr += self.line + '\n'
#            self.line = indentStr + ': '
#        #add content to buffer
#        self.line += contentStr
#
#    def endLine(self):
#        '''End a partially completed line unconditionally'''
#        self.treeStr += self.line + '\n'
#        self.line = ''
#
#    def safeStr(self, inObj):
#        '''
#        Convert inObj to string without infinite recursion
#        into Node objects.
#        '''
#        if isinstance(inObj, Node):
#            return '<%s at %#x>' % (inObj.__class__.__name__, id(inObj))
#        else:
#            return str(inObj)
#
#    def makeTreeStr(self, root=None):
#        ''''Create string representation of Node tree.'''
#        #for fewer typing
#        putStr = self.putStr
#        safeStr = self.safeStr
#        #initialize
#        self.treeStr = ''
#        self.line = ''
#        if root is not None:
#            self.root = root
#        #string to symbolize one indent level
#        indentStepStr = '|' + ' '*int(self.indentWidth - 1)
#        for node, depth in self.root.iterDepthFirst(True):
#            #string for indentation
#            indentStr = indentStepStr * depth
#            #First print class name and if desired node's ID
#            putStr(indentStr, node.__class__.__name__ + ':: ')
#            if self.showID:
#                putStr(indentStr, ' ID: ' + str(id(node)))
#
#            #special case for non Node objects
#            if not isinstance(node, Node):
#                putStr(indentStr, str(node)); self.endLine()
#                print self.treeStr
#                raise Exception('All children must inherit from ast.Node!')
#                #TODO enhance the iterator to work with none Node classes as leafs.
#
#            #special handling for some important attributes
#            if hasattr(node, 'name'):
#                putStr(indentStr, 'name: ' + safeStr(node.name) + ' ')
#            if isinstance(node, NameSpace):
#                #print the name space speciffic attributes in short form
#                #they are causing infinite recursion otherwise
#                putStr(indentStr, '_nameSpaceAttrs.keys(): ' +
#                       str(node._nameSpaceAttrs.keys()) + ' ')
#            putStr(indentStr, 'loc: ' + safeStr(node.loc) + ' ')
#
#            #the node's attributes are printed in sorted order,
#            #but the special attributes are excluded
#            specialAttrs = set(['loc', 'kids', '_nameSpaceAttrs', 'name', 'mainFuncs'])
#            attrNameSet = set(node.__dict__.keys())
#            attrNames= list(attrNameSet - specialAttrs)
#            attrNames.sort()
#            #get attributes out node.__dict__
#            for name1 in attrNames:
#                #TODO:more robustness when other attributes are Nodes too
#                #TODO:more robustness against circular dependencies
#                putStr(indentStr, name1 + ': ' + safeStr(node.__dict__[name1]) + ' ')
#            #put newline after complete node
#            self.endLine()
#        return self.treeStr



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

    >>> tr=Node(kids=[])
    >>> tr.kids.append(NodeClassDef(name='c1'))
    >>> tr.kids.append(NodeClassDef(name='c2'))
    >>> tr.kids.append(NodeFuncDef(name='f1'))
    >>> tr.kids.append(NodeFuncDef(name='f2'))
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



#------------ testcode --------------------------------------------------
import unittest

class TestAST(unittest.TestCase):

    def setUp(self):
        '''Node: perform common setup tasks for each test'''
        #create a tree
        n5 = Node(name='n5', type='leaf',   kids=[])       
        n4 = Node(name='n4', type='leaf',   kids=[])       
        n3 = Node(name='n3', type='leaf',   kids=[])       
        n2 = Node(name='n2', type='branch', kids=[n3, n4])
        n1 = Node(name='n1', type='trunk',  kids=[n2, n5]) 
        self.tree1 = n1
#        print n1

    def test__init__(self):
        '''Node: Test the __init__ method'''
        #The init method creates one attribute for each named argument.
        #There are no default attributes.
        n1 = Node()
        self.assertTrue(len(n1.__dict__) == 0)
        n2 = Node(loc=1, dat='test')
        self.assertTrue(n2.loc == 1)       #IGNORE:E1101  
        self.assertTrue(n2.dat == 'test')  #IGNORE:E1101
        self.assertRaises(TypeError, self.raise__init__1)
    def raise__init__1(self):
        '''Node: Positional arguments raise exceptions'''
        Node('test')

    def test__str__(self):
        '''Node: Test printing and line wraping (it must not crash)'''
        #TODO: Make this smarter, printing and copying are the only 
        #      genuine functions of Node
        #Test wrapping
        #create additional node with many big attributes
        n_big = Node(  name='n_big', 
                        test1 = 'qworieoqwiruuqrw',
                        test2 = 'qworieoqwiruuqrw',
                        test3 = 'qworieoqwiruuqrw',
                        test4 = 'qworieoqwiruuqrw',
                        test5 = 'qworieoqwiruuqrw',
                        test6 = 'qworieoqwiruuqrw',
                        test7 = 'qworieoqwiruuqrw',
                        test8 = 'qworieoqwiruuqrw',
                        test9 = 'qworieoqwiruuqrw',
                        test10 = 'qworieoqwiruuqrw')
        self.tree1.kids[0].big = n_big                #IGNORE:E1101
        _str1 = self.tree1.__str__()
        #to see it:
#        print
#        print self.tree1
        

#    def testIterDepthFirst(self):
#        #TODO: Reenable when new iterator exists
#        #iteration, all child nodes recursive
#        l = []
#        for node1 in self.tree1.iterDepthFirst():
#            l.append(node1.loc)
#        self.assertEqual(l, [1, 2, 3, 4, 5])
#        #iteration, all child nodes recursive also depth is returned
#        l = []
#        for node1, depth in self.tree1.iterDepthFirst(returnDepth=True):
#            line = 'dat: %s, depth; %d' % (node1.dat, depth)
#            l.append(line)
#        self.assertEqual(l, ['dat: root, depth; 0',
#                             'dat: branch, depth; 1',
#                             'dat: leaf, depth; 2',
#                             'dat: leaf, depth; 2',
#                             'dat: leaf, depth; 1'])

    def testCopy(self):
        '''Node: Test copy function'''
        tree1_c = self.tree1.copy() #create deep copy
        #assert that values are equal
        self.assertTrue(len(tree1_c.__dict__) == len(self.tree1.__dict__))
        self.assertTrue(tree1_c.name == self.tree1.name)                     #IGNORE:E1101
        self.assertTrue(tree1_c.kids[0].name == self.tree1.kids[0].name)     #IGNORE:E1101
        self.assertTrue(   tree1_c.kids[0].kids[0].name == 
                        self.tree1.kids[0].kids[0].name    )                 #IGNORE:E1101
        #assert that copy created new objects
        self.assertFalse(id(tree1_c) == id(self.tree1))
        self.assertFalse(id(tree1_c.kids[0]) == id(self.tree1.kids[0]))      #IGNORE:E1101
        self.assertFalse(id(   tree1_c.kids[0].kids[0]) == 
                         id(self.tree1.kids[0].kids[0])    )                 #IGNORE:E1101
        #TODO: test copying of not owned (weak, shared) attributes



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

        class A(Node):
            pass
        class B(Node):
            pass
        
        class NodeVisitor(Visitor):
            def __init__(self):
                Visitor.__init__(self)

            #Handlers for derived classes - specialized
            #- should have high priority
            @Visitor.when_type(A, 2)
            def visitA(self, a_inst):                         #IGNORE:W0613
#                print 'seen class def: ' + classDef.name
                return ['A']
            @Visitor.when_type(B, 2)
            def visitB(self, b_inst):                          #IGNORE:W0613
#                print 'seen func def: ' + funcDef.name
                return ['B']

            #handler for a base class - general
            #- should have low priority
            @Visitor.when_type(Node, 1)
            def visitNode(self, node): #IGNORE:W0613
#                print 'seen Node: ' + str(node.dat)
                return ['Node']

            def mainLoop(self, tree):
                retList = []
                for node in tree.kids:
                    retList += self.dispatch(node)
                return retList

        #create a syntax tree
        tr = Node(kids=[])
        tr.kids.append(A(name='a1'))  #IGNORE:E1101
        tr.kids.append(A(name='a2'))  #IGNORE:E1101
        tr.kids.append(Node(name='n1'))           #IGNORE:E1101
        tr.kids.append(B(name='b1'))   #IGNORE:E1101
        tr.kids.append(B(name='b2'))   #IGNORE:E1101
        #visit all nodes
        nv = NodeVisitor()
        testList = nv.mainLoop(tr)
#        print testList

        expectedList = ['A', 'A', 'Node', 'B', 'B']
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
    #TODO: fix and reenable Doctest
    #doDoctest()

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

