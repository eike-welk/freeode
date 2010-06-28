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
from subprocess import Popen, PIPE
from types import NoneType
import freeode.third_party.pyparsing as pyparsing

#version of the Siml compiler.
PROGRAM_VERSION = '0.4.0a3'
#How much debug information is printed
# 0: No debug information; 1: some; ....
DEBUG_LEVEL = 1



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



def assert_raises(exc_type, errno, func, args=(), kwargs={}): #pylint:disable-msg=W0102
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
    args: tuple
        Positional arguments for tested function.
    kwargs: dict
        Keyword arguments for tested function.
    '''
    assert issubclass(exc_type, BaseException), \
           'Argument exc_type must be an exception type.'
    assert callable(func), 'Argument func must be call-able.'
    
    try:
        func(*args, **kwargs) #pylint:disable-msg=W0142
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
        #TODO: also print one line of program text
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
    lev=0 : int
        Only produce output when the program's debug level is greater or equal 
        this value.
    sep='' : str
        This string is inserted between the printed arguments.
    end='\n': str
        This string is appended at the end of the printed output.
    '''
    #TODO: change debug level to debug area: a set of strings
    #process keyword arguments
    lev = kwargs.get('lev', 0)
    if int(lev) < DEBUG_LEVEL:
        return
    end = str(kwargs.get('end', '\n'))
    sep = str(kwargs.get('sep', ' '))

    #test for illegal keyword arguments
    legal_kwargs = set(['lev', 'sep','end'])
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
class Line(object):
    '''
    Represents a line that is expected in the output of a program.
    
    The line has the pattern:
        string float float float ....
    '''
    def __init__(self, item_list=['foo:', 1., 2.], tol=1e-3, converter=float):
        '''
        item_list : [str, float, float, ...] or str
            The items that are expected in the line.
            - If item_list is a string it is split into a list; elements [1:] 
              are then converted to float with the converter function.
        tol : float
            Tolerance for comparing the found values with the expected values.
        converter: call-able object or None
            This function is called with each of the detected values as its argument.
            The function's result is compared to the values of the template. 
            If convertes is None no conversion takes place
        '''
        object.__init__(self)
        if isinstance(item_list, str):
            item_list = item_list.split()
            self.vals = map(converter, item_list[1:])
        else:
            #item_list is list
            self.vals = item_list[1:]
        self.start = str(item_list[0])
        self.tol = tol
        self.converter = converter
        self.is_matched = False
    
    def make_line(self):
        'Create the line that the template describes.'
        return self.start + ' ' + ' '.join(map(str,self.vals))
         

        
        
def search_result_lines(text, line_templates):
    '''
    Test if a number of special lines can be found in a text.
    
    The lines which are expected in the text are given by a list of Line 
    objects. Each line has the pattern:
        string float float float ....
        
    Spaces at the start and end of each line are ignored (stripped).
    
    The string at the beginning identifies the line, the numbers following 
    the string must match within the given tolerance. All lines must occur in 
    the text. 
    
    If any mismatch is detected an AssertionError is raised.
    
    ARGUMENTS
    ---------
    text: str
        The text which is scanned
    line_templates: list(Line)
        Description of the lines that must appear in the text
    '''        
    for line in text.split('\n'): 
        s_line = line.strip()
        #see if the line is one of the interesting lines
        for tmpl in line_templates:
            #The line is one of the interesting lines -> extract the values
            if s_line.startswith(tmpl.start):
                try:
                    val_line = s_line[len(tmpl.start):] #remove tmpl.start
                    s_vals = val_line.split()
                    #Convert the values with the conversion function
                    if tmpl.converter:
                        vals = map(tmpl.converter, s_vals)
                    else:
                        vals = s_vals
                    #Test the assertions
                    if len(vals) != len(tmpl.vals):
                        raise AssertionError()
                    def compare((a, b)):
                        return abs(a - b) < tmpl.tol
                    if not all(map(compare, zip(vals, tmpl.vals))):
                        raise AssertionError()
                    tmpl.is_matched = True
                    break #Assume each line is matched by only one template
                except AssertionError, _err:
                    raise AssertionError(
                    'Error: text template was violated! \n' +
                    'Expected line: "%s" \n' % tmpl.make_line() +
                    'Got line     : "%s" \n' % line)
                    
    #Test if all templates are matched        
    for tmpl in line_templates:
        if tmpl.is_matched == False:
            raise AssertionError('Not all templates were matched! \n' +
                                 'Missing line: "%s" \n' % tmpl.make_line())



def compile_run(in_name, out_name, extra_args='', run_sims='all', clean_up=True):
    '''Compile and run a simulation.'''
    #Run compiler and simulation(s); catch the output
    cmd_str = 'python simlc %s -o %s -r %s %s' % (in_name, out_name, 
                                                  run_sims, extra_args)
    sim = Popen(cmd_str, shell=True, stdout=PIPE)
    res_txt, _ = sim.communicate()
    debug_print('Program output: ', res_txt, lev=3)
    debug_print('Return code: ', sim.returncode, lev=2)
    #Clean up
    if clean_up:
        os.remove(out_name)
    #Program must say that it terminated successfully 
    assert sim.returncode == 0, 'Program exited with error.'
    return res_txt
