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
    
    def __init__(self, 
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
        if name in self.xshort_set or duplicate:
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
        
        
    