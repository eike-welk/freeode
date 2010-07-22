# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2010 - 2010 by Eike Welk                                #
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
Utility classes and functions.
'''

from __future__ import division
from __future__ import absolute_import          

import os
import sys
import copy
import functools
from subprocess import Popen, PIPE
from types import NoneType
import freeode.third_party.pyparsing as pyparsing

#version of the Siml compiler.
PROGRAM_VERSION = '0.4.0'
#How much debug information is printed
# Control the amount of debug information that is printed
DEBUG_AREAS = set(['general', 'perf'])



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
    


def func(function_or_method):
    '''
    Convert bound and unbound methods into functions.
    
    Works with Python and Siml methods. If argument is a function it is 
    returned unchanged. 
    '''
    if hasattr(function_or_method, 'im_func'):
        return function_or_method.im_func
    else:
        return function_or_method
    
    
    
class AATreeMaker(object):
    '''
    Create an ASCII-art tree to visualize arbitrary Python objects. All of its
    data attributes are processed recursively.
    
    The algorithm is configurable, attributes can be exempted from the 
    recursive traversal and only be represented by a short string. The object 
    is protected against infinite loops by a remembering all converted objects 
    in a set.
    
    To work with this class an object must have an attribute 
        '__siml_aa_tree_maker__' of type AATreeMaker. 
    This will usually be a class attribute. All objects that don't have such an
    attribute are converted with the built in function 'repr'. 
    
    The data attributes are put into four categories. The constructor arguments  
    customize the behavior.
    top: 
        Attributes that should be viewed first, like 'name'. These attributes 
        are converted to short strings.
    short, xshort:
        These attributes are assumed to have a relatively small textual 
        representation, which fits into one line:
        - Objects which are built in types (str, int, ...). 
        - Objects which are not owned by this node. For attributes specified 
          in the argument 'xshort' only the class name is returned.
    long:
        These attributes have a big textual representation, spanning multiple 
        lines.
        - Objects which contain a AATreeMaker, lists and dicts of such objects.
    bottom:  
        Attributes that should be viewed last, like 'loc'. These attributes 
        are converted to short strings.
        
    USAGE
    -----
    Call function 
        make_tree 
    to create an ASCII-art tree.
    '''
    
    #Name of the tree maker objects
    tree_maker_name = '__siml_aa_tree_maker__'
    
    def __init__(self,                              #pylint: disable-msg=W0102
                  top_names=['name'], 
                  xshort_names=[], short_names=[], short_types=[],
                  long_names=[], 
                  bottom_names=['loc'],  
                  left_margin_elem='| ', max_depth=50, 
                  line_width=80, show_ID=True):
        '''
        Parameters to customize the behavior can be specified here.
        
        PARAMETER
        ---------
        top_names: [str]. Default: ['name']
            Attributes whose names are in this list are put at the top of the 
            sub tree. The short (repr) representation is used.
            
        xshort_names: [str]. Default: [] 
            Attributes in this list only represented by their class names.
            
        short_names: [str]. Default: [] 
            Attributes whose names are in this list are converted by repr.
            
        short_types: [type]. Default: []  
            Attributes with these types are always converted with the 'short'
            algorithm.
            
        long_names: [str]. Default: []  
            Attributes whose names are in this list are always converted with
            the long algorithm. Important for lists that can be empty.
            
        bottom_names: [str]. Default: ['loc']
            Attributes whose names are in this list are put at the top of the 
            sub tree. The short (repr) representation is used.
            
        left_margin_elem: str. Default: '| '
            The left margin is made by concatenating copies of this string.
            
        max_depth: int. Default: 50
            Maximum recursion depth.
            
        show_ID: bool. Default: True
            Show the ID of the current object, and of xshort objects.
        '''
        self.top_names = top_names
        self.xshort_names = xshort_names
        self.xshort_set = set(xshort_names)
        self.short_names = short_names
        self.short_types = tuple(short_types)
        self.long_names = long_names 
        self.bottom_names = bottom_names
        self.left_margin_elem = left_margin_elem
        self.max_depth = max_depth
        self.line_width = line_width
        self.show_ID = show_ID
        
        
    def make_tree(self, in_obj, curr_depth=0, memo_set=None, 
                   left_margin_elem=None, line_width=None):
        '''Convert in_obj to a ASCII art tree, recursively.'''
        memo_set = memo_set if memo_set else set()
        line_width = line_width if line_width else self.line_width        
        left_margin_elem = left_margin_elem if left_margin_elem \
                             else self.left_margin_elem
        
        memo_set.add(id(in_obj)) #against infinite recursion                    
        left_margin_1 = left_margin_elem * curr_depth
        #protect against wrapping
        if curr_depth > self.max_depth:
            return left_margin_1 + 'Max depth exceeded!\n'
        
        #put attributes into different lists
        top_attr, short_attr, long_attr, bottom_attr = self._group_attributes(in_obj)
        
        #create the text
        tree = ''
        tree += self._make_header_block(in_obj, left_margin_1, line_width)
        left_margin = left_margin_1 + left_margin_elem
        tree += self._make_short_block(in_obj, top_attr, left_margin, memo_set, line_width)
        tree += self._make_short_block(in_obj, short_attr, left_margin, memo_set, line_width)
        tree += self._make_long_block(in_obj, long_attr, curr_depth, left_margin, 
                                     memo_set, line_width, left_margin_elem)
        tree += self._make_short_block(in_obj, bottom_attr, left_margin, memo_set, line_width)
        
        return tree
    
    
    def _group_attributes(self, in_obj):
        '''
        Create lists that say where an attribute is printed and which 
        algorithm is used.
        '''
        if not hasattr(in_obj, '__dict__'):
            return [], [], [], []
        
        attr_dict = in_obj.__dict__
        attr_names = set(attr_dict.keys())
        
        #Get the attributes that are displayed first and last. 
        #They are not sorted, and they can appear twice.
        top_attr =    [a for a in self.top_names    if a in attr_names]
        bottom_attr = [a for a in self.bottom_names if a in attr_names]
        attr_names -= set(top_attr) | set(bottom_attr)
        
        #Get attributes that should be converted by str, specified by name
        short_attr = [a for a in self.short_names + self.xshort_names if a in attr_names]
        attr_names -= set(short_attr)
        #Get attributes that should be converted to trees, specified by name
        long_attr = [a for a in self.long_names if a in attr_names]
        attr_names -= set(long_attr)
        
        #Search for attributes of certain types and put them into short_attr or 
        #long_attr lists
        short_types = self.short_types
        for name, attr in attr_dict.iteritems():
            if name not in attr_names:
                continue
            #The user can specify types that should be converted by str
            if isinstance(attr, short_types):
                short_attr.append(name)
                attr_names.remove(name)
            #Attributes that contain a tree maker are converted to trees
            elif hasattr(attr, self.tree_maker_name):
                long_attr.append(name)
                attr_names.remove(name)
            #Lists or tuples where an element contains a tree maker
            elif isinstance(attr, (list, tuple)):
                for elem in attr:
                    if hasattr(elem, self.tree_maker_name):
                        long_attr.append(name)
                        attr_names.remove(name)
                        break
            #dicts where an element contains a tree maker
            elif isinstance(attr, dict):
                for elem in attr.itervalues():
                    if hasattr(elem, self.tree_maker_name):
                        long_attr.append(name)
                        attr_names.remove(name)
                        break
        
        #all remaining attributes are considered no tree
        short_attr += list(attr_names)
            
        long_attr.sort()    
        short_attr.sort() 
        return top_attr, short_attr, long_attr, bottom_attr
        
        
    def _make_header_block(self, in_obj, left_margin, _line_width):
        '''Create header with type information'''
        tree = left_margin + in_obj.__class__.__name__ 
        if self.show_ID:
            tree += ' at ' + hex(id(in_obj))
        tree += '\n'
        return tree
    
    
    def _make_short_block(self, in_obj, attr_list, left_margin, memo_set, line_width):
        '''
        Create text block, use repr to convert attributes. 
        These are the atoms that really carry the information
        '''
        tree = ''
        line = left_margin
        for name in attr_list:
            attribute = getattr(in_obj, name)
            #Convert one attribute to a string
            line += name + ' = ' \
                    + self._make_short_string(attribute, memo_set, name) + '; '
            #do line wrapping
            if len(line) > line_width:
                tree += line + '\n'
                line = left_margin

        if line != left_margin:
            tree += line + '\n'
        return  tree
    
    
    def _make_long_block(self, in_obj, attr_list, curr_depth, left_margin, 
                          memo_set, line_width, left_margin_elem):
        '''Create text block for sub trees.'''
        tree = ''
        for name in attr_list:
            attribute = getattr(in_obj, name)
            

            #Attribute is list or tuple
            if isinstance(attribute, (list, tuple)):
                tree += left_margin + name + ' = [ \n'     
                for item in attribute:
                    tree += self._make_long_string(item, memo_set, curr_depth + 1, 
                                                  left_margin_elem, line_width, 
                                                  name)
                tree += left_margin + '] \n'
            #Attribute is dict; names are sorted
            elif isinstance(attribute, dict):
                tree += left_margin + name + ' = { \n'     
                name_list = attribute.keys()
                name_list.sort()         
                for name in name_list:
                    item = attribute[name]
                    tree += left_margin + str(name) + ':\n'  #print key:
                    tree += self._make_long_string(item, memo_set, curr_depth + 1, 
                                                  left_margin_elem, line_width, 
                                                  name)
                tree += left_margin + '} \n'
            #Simple ttribute with tree maker
            else:
                tree += left_margin + name + ' = \n' \
                        + self._make_long_string(attribute, memo_set, curr_depth,  
                                                left_margin_elem, line_width, 
                                                name)
        return  tree
    

    def _make_short_string(self, attribute, memo_set, name=None):
        '''Convert one object to a string, use repr for the conversion'''
        duplicate = id(attribute) in memo_set and not isinstance(attribute, str)
        memo_set.add(id(attribute)) #against infinite recursion
        #make very short
        if (name in self.xshort_set or duplicate) and \
           not isinstance(attribute, (bool, NoneType, EnumMeta, type)):
            line = '<' + attribute.__class__.__name__ 
            if self.show_ID:
                line += ' at ' + hex(id(attribute))
            if duplicate:
                line += ' (dup)'
            line += '>'
        #the atoms that really carry the information convert with repr
        else:
            line = repr(attribute)
        return line
        
        
    def _make_long_string(self, attribute, memo_set, curr_depth, 
                           left_margin_elem, line_width, name=None):
        '''Convert one object to a string, use tree maker for the conversion'''
        duplicate = id(attribute) in memo_set
        #make very short
        if name in self.xshort_set or duplicate \
           or isinstance(attribute, self.short_types) \
           or not hasattr(attribute, self.tree_maker_name):
            tree = left_margin_elem * (curr_depth + 1) \
                   + self._make_short_string(attribute, memo_set, name) + '; \n'
        #create a subtree
        else:
            #memo_set.add(id(attribute)) #against infinite recursion
            tree_maker = getattr(attribute, self.tree_maker_name)
            tree = tree_maker.make_tree(attribute, curr_depth + 1, memo_set, 
                                        left_margin_elem, line_width)
        return tree
        
        

def aa_make_tree(in_obj):       
    '''
    Create ASCII-art tree of an object, and of all data attributes it 
    contains recursively. Output can be configured by putting AATreeMaker
    instances in the tree of objects.
    
    ARGUMENT
    --------
    in_obj: any object
        Object that should be displayed as ASCII-art tree.
        
    RETURNS
    ------_
    string
        ASCII-art tree representing in_obj.
    '''
    #handle some special cases
    if isinstance(in_obj, (list, dict)):
        class ListOrDictDummy(object): pass
        d = ListOrDictDummy()
        d.list_or_dict = in_obj #pylint:disable-msg=W0201
        return AATreeMaker().make_tree(d)
    else:         
        tree_maker = getattr(in_obj, AATreeMaker.tree_maker_name, AATreeMaker())
        return tree_maker.make_tree(in_obj)   



class UserException(Exception):
    '''Exception that transports user visible error messages.'''
    def __init__(self, message, loc=None, errno=None):
        Exception.__init__(self)
        self.msg = message
        self.loc = loc
        self.errno = errno

    def __str__(self):
        if self.errno is None:
            num_str = ''
        else:
            num_str = '(#%s) ' % str(self.errno) 
        return 'Error! ' + num_str + self.msg + '\n' + str(self.loc) + '\n'

    def __repr__(self):
        return self.__class__.__name__ + repr((self.msg, self.loc, self.errno))



def assert_raises(exc_type, errno, func, *args, **kwargs): #pylint:disable-msg=W0621
    '''
    Test if a function raises the expected exception. Can test error number of 
    UserException.
    
    ARGUMENTS
    ---------
    exc_type: Exception
        The type of the expected exception.
    errno: int, None
        The error number of the expected exception. The exception must have 
        an attribute "errno" which is equal to this argument. 
        Useful for UserException.
        If errno is None it is ignored
    func: Python function
        The tested function which must raise an exception.
    args: 
    kwargs: 
        Further positional and keyword arguments are supplied to the tested 
        function (argument func).
    '''
    assert issubclass(exc_type, BaseException), \
           'Argument exc_type must be an exception type.'
    assert callable(func), 'Argument func must be call-able.'
    
    try:
        func(*args, **kwargs) 
    except exc_type, e:
        #print e
        if errno is not None:
            assert hasattr(e, 'errno'), 'Exception has no attribute "errno"!'
            assert e.errno == errno, 'Wrong errno: %s. \n' \
                                     'Expecting errno: %s \n' \
                                     'Caught exception: \n%s' \
                                     % (e.errno, errno, e)
        print 'Correct exception was raised:'
        print e
    except BaseException, e:
        print >>sys.stderr, 'Wrong exception was raised! Type: %s \n' \
                            'Expected exception type: %s' \
                            % (type(e).__name__, exc_type.__name__)
        raise
    else:
        assert False, 'An exception should have been raised. \n' \
                      'Expecting exception of type: %s' % exc_type.__name__
    
    
    
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



class TextLocation(object):
    '''
    Store the location of a part of a program. Can be converted to meaningful
    string for error messages. 

    Contains file name, information to compute the line number, and program 
    text.
    '''
    def __init__(self, at_char=None, text_string=None, file_name=None, 
                        line_no=None):
        super(TextLocation, self).__init__()
        self.at_char = at_char
        self.text_string = text_string
        self.file_name = file_name
        self._line_no = line_no

    def is_valid(self):
        '''
        Return True if a meaningful line number can be computed.
        Return False otherwise.
        '''
        if self.at_char is not None and self.text_string:
            return True
        elif self._line_no is not None:
            return True
        else:
            return False

    def line_no(self):
        '''Compute the line number of the stored location.'''
        if self.at_char is not None and self.text_string:
            return pyparsing.lineno(self.at_char, self.text_string)
        elif self._line_no is not None:
            return self._line_no
        else:
            return 0

#    def col(self):
#        '''Compute the column of the stored location.'''
#        if self.atChar and self.str:
#            return pyparsing.col(self.atChar, self.str)
#        else:
#            return 0

#    def get_file_name(self):
#        '''Return the filename.'''
#        return str(self.file_name)

    def __str__(self):
        '''Return meaningful string'''
        #Including the column is not useful because it is often wrong
        #for higher level errors. Preserving the text of the original
        #Pyparsing error is transporting the column information for parsing
        #errors. Only parsing errors have useful column information.
        return '  File "' + str(self.file_name) + '", line ' + str(self.line_no())



def make_unique_dotname(base_name, existing_names):
    '''
    Make a unique name that is not in existing_names.

    If base_name is already contained in existing_names a number is appended
    to base_name to make it unique.

    Arguments:
    base_name: DotName, str
        The name that should become unique.
    existing_names: container that supports the 'in' operation
        Container with the existing names. Names are expected to be
        DotName objects.

    Returns: DotName
        Unique name; base_name with number appended if necessary
    '''
    base_name = DotName(base_name)
    for number in range(1, 100000):
        if base_name not in existing_names:
            return  base_name
        #append number to last component of DotName
        base_name = base_name[0:-1] + DotName(base_name[-1] + str(number))
    raise Exception('Too many similar names')



def debug_print(*args, **kwargs):
    '''
    Print the positional arguments to the standard output
    
    The function supports a number of keyword arguments:
    area='general' : str
        Only produce output when area is in global set DEBUG_AREAS.
    sep='' : str
        This string is inserted between the printed arguments.
    end='\n': str
        This string is appended at the end of the printed output.
    '''
    #process keyword arguments
    area = str(kwargs.get('area', 'general'))
    if area not in DEBUG_AREAS:
        return
    end = str(kwargs.get('end', '\n'))
    sep = str(kwargs.get('sep', ' '))

    #test for illegal keyword arguments
    legal_kwargs = set(['area', 'sep','end'])
    real_kwargs = set(kwargs.keys())
    if not(real_kwargs <= legal_kwargs):
        err_kwargs = real_kwargs - legal_kwargs
        print 'WARNING: "debug_print" got unexpected keyword argument(s): %s' \
              % ', '.join(err_kwargs)
        print '         Legal keyword arguments are: %s' % ', '.join(legal_kwargs)
    
    #print the positional arguments
    for arg in args:
        sys.stdout.write(str(arg) + sep)
    sys.stdout.write(end)


# ----- Testing program output -------------------------------------------------
class LineTemplate(object):
    '''
    Represents a line that is expected in the output of a program.
    
    The line has the pattern:
        head string: value1 value2 ....
        
    Currently well supported types for values are: int, float, str 
    
    The head string must be separated from the values with a colon ':' 
    character.
    '''
    def __init__(self, head, vals, tols=1e-3, convs=None): 
        '''
        ARGUMENTS
        ---------
        
        head: str
            The leading string that identifies the line. It is separated from
            the rest of the line by a colon ':'
            
        vals: [str | float]
            The items that are expected in the line. These items are not 
            converted.
            
        tols: float | [float]
            A tolerance for comparing found floating point values with expected 
            values, or a list of tolerances
            
        converter: call-able object or None
            This function is called with each of the detected values as its argument.
            The function's result is compared to the values of the template. 
            If convertes is None no conversion takes place
        '''
        object.__init__(self)
        
        #care for head: remove leading whitespace and trailing ':'
        assert isinstance(head, str)
        head = head.lstrip()
        head = head.rstrip(':')
        self.head = head
        
        assert isinstance(vals, list)
        self.vals = vals
        
        #care for the tolerances
        if isinstance(tols, list):
            #A list of tolerances is given: store it
            assert len(tols) == len(self.vals)
            self.tols = tols
        elif isinstance(tols, float):
            #The same tolerances for all examples
            self.tols = [tols] * len(self.vals)
        else:
            raise TypeError('Argument "tols" must be a list or a float number.')
        
        #care for the conversion functions
        if isinstance(convs, list):
            #A list of conversion functions is given: store it
            assert len(convs) == len(self.vals)
            self.convs = convs
        elif convs is None:
            #Use the constructors of each value as conversion functions
            self.convs = [type(v) for v in self.vals]
        else:
            raise TypeError('Argument "convs" must be None or a list of functions.')
            
        #Create *the* list of matching functions; 
        #float is matched with tolerance, everything else is matched with ==
        def match_float(tol, a, b):
            return abs(a - b) < tol
        def match_default(a, b):    
            return a == b
        matchers = []
        for val, tol in zip(self.vals, self.tols):
            if isinstance(val, float):
                m_fun = functools.partial(match_float, tol)
            else:
                m_fun = match_default
            matchers.append(m_fun)
        self.matchers = matchers
            
        #The line has off course not been matched.
        self.is_matched = False
    
    
    def to_str(self):
        'Create the line that the template describes.'
        return self.head + ': ' + ' '.join(map(str,self.vals))


    @staticmethod
    def split_head(line_str):
        '''
        Cut the line into two parts: "head: tail"
        
        Leading and trailing whitespace are removed, and the line is
        split at the first colon ':'. 

        When the line cant't be usefully split, the function returns None.
        
        ARGUMENTS
        ---------
        
        line_str: str
            The line that is split.
            
        RETURNS
        -------
        tuple(head, tail)
        '''
        s_line = line_str.strip()
        head_tail = s_line.split(':', 1)
        if len(head_tail) == 2:
            return tuple(head_tail)
        else:
            return None
        
    
    @staticmethod
    def from_str(line_str):
        '''
        Create a LineTemplate instance from a string that looks like it.
        
        The line has the pattern:
            head string: value1 value2 ....
            
        The types of the values are guessed. This function tries to convert 
        them from strings with the following constructors: 
            int, float, str 
            
        The first constructor that does not raise ValueError determines the 
        type.
        
        All other details are the default values from LineTemplate.__init__
        
        ARGUMENTS
        ---------
        
        line_str: str
            The line that should be matched by the new object
        
        RETURNS
        -------
        
        LineTemplate
        '''
        #See if first argument line_str is already a LineTemplate
        if isinstance(line_str, LineTemplate):
            return line_str
        
        #Get head
        head_tail = LineTemplate.split_head(line_str)
        if head_tail is None:
            raise ValueError('LineTemplate: Could not identify a head in: ' 
                             + line_str)
        head, tail = head_tail
        
#        #Possible extension: Argument conv_order:
#        conv_order: [call-able object]
#            The converters for the fields. They are tried in the order
#            given by the list. 
#            
#            The first converter that runs without raising an exception
#            is stored as the converter for the field, the value that it 
#            returns is stored as the value that must be matched.
#        
#        #always have conversion to string as the last possibility. 
#        #Conversion to string always works.
#        if conv_order[-1] is not str:
#            conv_order.append(str)
        
        conv_order = [int, float, str]
        
        #convert the values
        raw_vals = tail.split()
        vals = []
        for val_str in raw_vals:
            val = None
            #Try the conversion functions, the first function that works determines
            #the type of the matched value
            for conv in conv_order:
                try:
                    val = conv(val_str)
                except ValueError:
                    continue
                break
            vals.append(val)
         
        return LineTemplate(head, vals)
    

    def match_tail(self, tail_str):
        '''
        Test if tail_str matches the values.
        '''
        test_vals = tail_str.split()
        #There must be the expected number of values in the string 
        if len(test_vals) != len(self.vals):
            return False
        #values from tail_str -> convert to desired type -> test if correct
        for test_val, val, conv, match_fun in zip(test_vals, self.vals, 
                                            self.convs, self.matchers):
            #Convert with stored conversion function
            try:
                test_val_conv = conv(test_val)
            except ValueError:
                return False
            #Match with stored matching function
            if not match_fun(test_val_conv, val):
                return False
        #All tests passed
        return True
        
        
        
def search_result_lines(text, templates_list):
    '''
    Test if a number of special lines can be found in a text.
    
    The lines which are expected in the text are given by a list of Line 
    objects. Each line has the pattern:
        head string: value1 value2 value3 ....
        
    Supported values are currently float and str. Other types may work if 
    LineTemplate is used explicitly.
    Spaces at the start and end of each line are ignored (stripped).
    
    The *head string* at the beginning identifies the line, the values following 
    the string must match, for floats within the given tolerance. 
    All lines must occur in the text. 
    
    If any mismatch is detected an AssertionError is raised.
    
    ARGUMENTS
    ---------
    
    text: str
        The text which is scanned
        
    templates_list: [str | LineTemplate]
        Description of the lines that must appear in the text.
        
        Each entry of type str is converted to a LineTemplate with function
        LineTemplate.from_str(...). When more details need to be specified
        a LineTemplate should be used instead of a str.
    '''      
    #Make dictionary {head: line_template} for fast template lookup.
    #and also create LineTemplate from strings if necessary.
    line_templates = {}
    for raw_template in templates_list:
        line_tmpl = LineTemplate.from_str(raw_template)
        line_templates[line_tmpl.head] = line_tmpl
      
    for line in text.split('\n'): 
        s_line = line.strip()
        #See if line contains a head of a test line
        head_tail = LineTemplate.split_head(s_line)
        if head_tail is None:
            continue
        
        #See if the head belongs to a template that we want to match
        head, tail = head_tail
        template = line_templates.get(head, None)
        if template is None:
            continue
        
        #See if the values in the line's tail match the template
        if template.match_tail(tail):
            template.is_matched = True
        else:
            raise AssertionError(
            'Error: text template was violated! \n' +
            'Expected line: "%s" \n' % template.to_str() +
            'Got line     : "%s" \n' % line)
        
    #Test if all templates are matched        
    for tmpl in line_templates.values():
        if tmpl.is_matched == False:
            raise AssertionError('Not all templates were matched! \n' +
                                 'Missing line: "%s" \n' % tmpl.to_str())



def compile_run(in_name, test_suffix='_testprog', 
                  extra_args='', run_sims='all', no_graphs=True, clean_up=True):
    '''
    Compile and run a simulation. 
    
    Returns the simulation's text output (stdout). The created files are removed
    after the simulation has been run.
    
    Arguments
    ---------
    in_name: str
        Name of the Siml program which is tested. 
    test_suffix: str
        Prefix for all generated files. Every test should have a different 
        prefix so that there is no interference between them in the file system.
    extra_args: str
        Additional arguments for the compiler. Appended to the command string.
    run_sims: str
        Specify the which simulation should be run. Can be a string containing 
        a mumber (for example '1'), or the special value 'all' which chooses all 
        simulations. 
    no_graphs: bool
        If True: Do not show any graphs even if the simulation contains "graph"
        commands. (Passes "--no-graphs" to the simulation") 
    clean_up: bool
        If True: delete the Python program that is created by the compiler. 
        (And also the *.pyc file.)
    '''
    #test and create the filenames
    extension = in_name.split('.',)[-1]
    assert extension.lower() == 'siml', \
           'The input file must have the extension *.siml'
    out_base = in_name[:-5] + test_suffix
    
    #create the bash command
    outname_args = ' -o %s ' % (out_base + '.py')
    run_args = '-r %s ' % run_sims
    graph_args = '--no-graphs ' if no_graphs else ''
    cmd_str = 'python simlc ' + in_name + outname_args + run_args + graph_args \
              + extra_args
    debug_print('cmd_str: ', cmd_str, area='compile_run')
    
    #Run compiler and simulation(s); catch the output
    sim = Popen(cmd_str, shell=True, stdout=PIPE)
    res_txt, _ = sim.communicate()
    debug_print('Program output: \n', res_txt, sep='')
    debug_print('Return code: ', sim.returncode)
    assert sim.returncode == 0, 'Siml compiler exited with error.'
    
    #Clean up
    if clean_up:
        os.remove(out_base+'.py')
    return res_txt
