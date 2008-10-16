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



#class FlatNameSpace(NameSpace):
#    '''A name space where attributes can have multiple dots in their name'''
#    def __init__(self):
#        NameSpace.__init__(self)
#
#    def setAttr(self, name, newAttr):
#        '''
#        Add new attribute to the name space.
#
#        Attributes can exist multiple times.
#
#        Parameters
#        name: str, DotName
#            Name of the new attribute
#        newAttr: NodeDataDef, NodeClassDef, NodeFuncDef, NodeModule
#            The new attribute, which is added to the name space.
#        '''
#        #Argument type checking and compatibility with DotName
#        if not isinstance(name, (str, DotName)):
#            raise Exception('Argument name must be of type str or DotName! type(name): '
#                            + str(type(name)) + ' str(name): ' + str(name))
#        name = str(name)
#        #add attribute to name space - attributes must be unique
#        if name in self._nameSpaceAttrs:
#            raise DuplicateAttributeError('Duplicate attribute: ' + name, name)
#        self._nameSpaceAttrs[name] = newAttr
#        return
#
#    def findDotName(self, dotName, default=None):
#        '''
#        Find dot name recursively and return attribute with this name.
#        '''
#        dotName = DotName(dotName) #make compatible with str too
#        attr = self.getAttr(dotName, None)
#        if attr is not None:
#            return attr
#        #maybe partial name is known here.
#        #Rest may be stored in child name space
#        nameShort = dotName
#        nameTail = DotName()
#        while len(nameShort)>1:
#            #remove last element
#            nameTail += nameShort[-1]
#            nameShort = nameShort[0:-1]
#            #try to find shortened name; look up rest of name recursively
#            attr = self.getAttr(nameShort, None)
#            if attr is not None:
#                return attr.findDotName(nameTail, default)
#        return default



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
            #Attribute is list(list(Node)) (cat = 4)
            #Attribute is dict(<any>:Node())
            elif cat == 102:
                if line != indent_str: 
                    tree += line  + '\n'
                    line = indent_str   
                tree += indent_str + key + ' = dict :: \n'     
                for key, item in self.__dict__[key].iteritems():
                    tree += indent_str + ' ' + str(key) + ':\n'  #print key:
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
        type:
            Type of the results of the operation. For decoorating the AST.
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
        self.type = None
        self.loc = None


class NodeAttrAccess(Node):
    '''
    AST node for dot operator. 
        type:
            Type of the results of the operation. For decoorating the AST.
    '''
    def __init__(self):
        super(NodeAttrAccess, self).__init__()
        self.operator = '.'
        self.arguments = []
        self.type = None
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
        type:
            Type of the results of the operation. For decoorating the AST.
        loc: 
            Location in input string
    '''
    def __init__(self):
        super(NodeParentheses, self).__init__()
        self.arguments = []
        self.type = None
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
        type:
            Type of the results of the operation. For decoorating the AST.
        loc: 
            Location in input string
    '''
    def __init__(self):
        super(NodeOpInfix2, self).__init__()
        self.operator = None
        self.arguments = []
        self.type = None
        self.loc = None


class NodeOpPrefix1(Node):
    '''
    AST node for a (unary) prefix operator: - not
    
    Data attributes:
        operator: 
            Operator symbol e.g.: '-'
        arguments:  list(Node())
            Expression on right side of operator
            Naming is chosen to unify operators and function call
        type:
            Type of the results of the operation. For decoorating the AST.
        loc: 
            Location in input string
  '''
    def __init__(self):
        super(NodeOpPrefix1, self).__init__()
        self.operator = None
        self.arguments = []
        self.type = None
        self.loc = None


class NodeFuncCall(Node):
    '''
    AST node for calling a function or method.
    
    This will be usually done by inserting the code of the function's body
    into the top level function. Similar to an inline function in C++.
    
    Data attributes:
        name: typically NodeIdentifier
            expression that yields the function object
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
        #TODO: keyword_arguments can't be dict, because dict does not store the 
        #      position/order in which the items are entered.
        self.keyword_arguments = {}
        self.loc = None


#-------------- Statements --------------------------------------------------
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
    def __init__(self):
        super(NodeExpressionStmt, self).__init__()
        self.expression = None
        self.loc = None
        

class NodeIfStmt(Node):
    '''
    AST node for an if ... the ... else statement
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
    
    Data attributes:
        operator: 
            Operator symbol always: '='
        arguments:  list(Node(), Node())
            Expression on left and right of operator: 
            left: arguments[0], right: arguments[1]
            Naming is chosen to unify operators and function call
        type:
            Type of the results of the operation. Not apliceable here. (None)
            Operation has no result, only side effect.
        loc: 
            Location in input string
            
    TODO: change attributes:
        target: Node()
            Expression that describes which object should be changed
        expression: Node()
            Expression that computes the new value
        loc: 
            Location in input string    
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
    def __init__(self):
        super(NodePrintStmt, self).__init__()
        self.arguments = []
        self.newline = None


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
    def __init__(self):
        super(NodeReturnStmt, self).__init__()
        self.arguments = []
        self.loc = None


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
    def __init__(self):
        super(NodeStmtList, self).__init__()
        self.statements = []


class NodeDataDefList(NodeStmtList):
    '''
    AST Node for list of atribute definitions.
    Each child is an attribute definition statement.
    Used to identify these lists so they can be flattened with a pretty
    simple algogithm.
    '''
    def __init__(self):
        super(NodeDataDefList, self).__init__()


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
    '''The attribute is a constant; it can only be changed at compile time.'''
#    userStr = 'const'
class RoleParameter(AttributeRole):
    '''
    Attribute is a parameter of the simulation:
    - is constant during the simulation, but can vary between simulations.
    - is stored.
    '''
#    userStr = 'param'
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
#    userStr = 'function argument'
class RoleLocalVariable(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a local variable:
    - can vary during the simulation
    - should be optmized away
    - is not stored.
    '''
#    userStr = 'local variable'
class RoleVariable(RoleDataCanVaryDuringSimulation):
    '''
    The attribute is a state or algebraic variable:
    - can vary during the simulation
    - is stored.
    '''
#    userStr = 'variable'
class RoleStateVariable(RoleVariable):
    '''The attribute is a state variable'''
#    userStr = 'state_variable'
class RoleAlgebraicVariable(RoleVariable):
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
        className       : type of the attribute; possibly dotted name: ('aa', 'bb')
        role            : Is this attribute a state or algebraic variable, a constant
                          or a parameter? (AttributeRole subclass).
    '''
    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.class_name = None #TODO: rename to class_spec this is eiter a NodeIdentifier or a NodeFuncCall
        self.role = None
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
        self.role = RoleCompiledObject


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
    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.type = None
        self.default_value = None
        self.loc = None
        
        
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
        self.name = None
        self.arguments = []
        self.keyword_arguments = []
        self.statements = []
        self.return_type = None
        self.loc = None



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
        n1 = Node(name='n1', type='leaf',   kids={}) 
        n2 = Node(name='n2', type='leaf',   kids={}) 
        n3 = Node(name='n3', type='trunk',  kids={'n1':n1, 'n2':n2}) 
        self.tree2 = n3

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
        #Test wrapping and lists
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
        _str1 = str(self.tree1)
#        print
#        print self.tree1
        #Test dicts
        _str2 = str(self.tree2)
#        print
#        print self.tree2

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
        #create additional weak attributes
        n1 = Node(name='weak1')
        n2 = Node(name='weak2')
        pr = weakref.proxy(n1)
#        pr = n1    #to make test fail
        wr = weakref.ref(n2)
        self.tree1.pr = pr                                                   #IGNORE:W0201
        self.tree1.kids[0].wr = wr                                           #IGNORE:E1101
        #create (mostly) deep copy
        tree1_c = self.tree1.copy() 
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
        #test copying of not owned (weak, shared) attributes
        #assert that values are equal
        self.assertTrue(tree1_c.pr.name == self.tree1.pr.name)               #IGNORE:E1101
        self.assertTrue(   tree1_c.kids[0].wr().name == 
                        self.tree1.kids[0].wr().name    )                    #IGNORE:E1101
        #assert no new objects were created
        self.assertTrue(id(tree1_c.pr) == id(self.tree1.pr))                 #IGNORE:E1101
        self.assertTrue(id(   tree1_c.kids[0].wr()) == 
                        id(self.tree1.kids[0].wr())    )                     #IGNORE:E1101
        # this assertion is an implementation detail
        self.assertTrue(id(   tree1_c.kids[0].wr) == 
                        id(self.tree1.kids[0].wr)    )                       #IGNORE:E1101



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

    def test__getitem__(self):
        '''DotName: Test access to parts of the object (foo[1], foo[0:4]).'''
        a_g = DotName('a.b.c.d.e.f.g')
        #subscription
        b = a_g[1]
        self.assertTrue(b == 'b')
        self.assertTrue(isinstance(b, str))
        e = a_g[4]
        self.assertTrue(e == 'e')
        self.assertTrue(isinstance(e, str))
        #simple slicing
        abc = a_g[0:3]
        self.assertTrue(abc == DotName('a.b.c'))
        self.assertTrue(isinstance(abc, DotName))
        c_c = a_g[2:3]
        self.assertTrue(c_c == DotName('c'))
        self.assertTrue(isinstance(c_c, DotName))
        empty = a_g[3:3]
        self.assertTrue(empty == DotName())
        self.assertTrue(isinstance(empty, DotName))
        #extendet slicing
        a_g2 = a_g[0:7:2]
        self.assertTrue(a_g2 == DotName('a.c.e.g'))
        self.assertTrue(isinstance(a_g2, DotName))
        #test boundary checking
        self.assertRaises(IndexError, self.raise__getitem__1)
        #This unexpectedly works, because the tuple implementation thinks 
        #it's OK
#        self.assertRaises(IndexError, self.raise__getitem__2)
        self.raise__getitem__2()
#        self.assertRaises(IndexError, self.raise__getitem__3)
        self.raise__getitem__3()
        return 
    def raise__getitem__1(self):
        '''Subscription out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[9]
    def raise__getitem__2(self):
        '''Simple slice out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[0:9]
    def raise__getitem__3(self):
        '''Extended slice out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[0:9:2]



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
#    testSuite.addTest(unittest.makeSuite(TestAST)) ???
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAST))
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVisitor))
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDotName))
    unittest.TextTestRunner(verbosity=2).run(testSuite)

else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass

