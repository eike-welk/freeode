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
    Create an ASCII string to visualize arbitrary Python objects.
    
    Default behavior:
    Objects that contain an object named '__siml_aa_tree_maker__' are converted
    to ASCII art trees; all other objects are converted to strings with the 
    built in function str.
    '''
    
    def __init__(self, top_names=['name'], xshort_names=[], short_names=[], 
                  long_names=[], 
                  bottom_names=[], short_types=[], 
                  #long_types=[], 
                  tree_maker_name='__siml_aa_tree_maker__', 
                  left_margin_elem='| ', line_width=80, max_depth=50, 
                  show_ID=True):
        '''
        Many parameters to customize the behavior can be specified here.
        
        PARAMETER
        ---------
        top_names: [str]
            Attributes with these names are at the top. The short 
            representation is used.
        xshort_names: [str] 
        short_names: [str]
        long_names: [str] 
            Important for lists.
        bottom_names: [str]
        short_types: [type] 
        long_types: [type]  #??????????????
        tree_maker_name: str
        left_margin_elem: str
        max_depth: int        
        show_ID: bool
        '''
        self.top_names = top_names
        self.xshort_names = xshort_names
        self.xshort_set = set(xshort_names)
        self.short_names = short_names
        self.long_names = long_names 
        self.bottom_names = bottom_names
        self.short_types = tuple(short_types)
        #self.long_types = long_types #??????????????
        self.tree_maker_name = tree_maker_name
        self.left_margin_elem = left_margin_elem
        self.line_width = line_width
        self.max_depth = max_depth
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
        top_attr, short_attr, long_attr, bottom_attr = self.make_attr_lists(in_obj)
        
        #create the text
        tree = ''
        tree += self.make_header_block(in_obj, left_margin_1, line_width)
        left_margin = left_margin_1 + left_margin_elem
        tree += self.make_short_block(in_obj, top_attr, left_margin, memo_set, line_width)
        tree += self.make_short_block(in_obj, short_attr, left_margin, memo_set, line_width)
        tree += self.make_long_block(in_obj, long_attr, curr_depth, left_margin, 
                                     memo_set, line_width, left_margin_elem)
        tree += self.make_short_block(in_obj, bottom_attr, left_margin, memo_set, line_width)
        
        return tree
    
    
    def make_attr_lists(self, in_obj):
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
        
        
    def make_header_block(self, in_obj, left_margin, _line_width):
        '''Create header with type information'''
        tree = left_margin + in_obj.__class__.__name__ 
        if self.show_ID:
            tree += ' at ' + hex(id(in_obj))
        tree += '\n'
        return tree
    
    
    def make_short_block(self, in_obj, attr_list, left_margin, memo_set, line_width):
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
                    + self.make_short_string(attribute, memo_set, name) + '; '
            #do line wrapping
            if len(line) > line_width:
                tree += line + '\n'
                line = left_margin

        if line != left_margin:
            tree += line + '\n'
        return  tree
    
    
    def make_long_block(self, in_obj, attr_list, curr_depth, left_margin, 
                          memo_set, line_width, left_margin_elem):
        '''Create text block for sub trees.'''
        tree = ''
        for name in attr_list:
            attribute = getattr(in_obj, name)
            

            #Attribute is list or tuple
            if isinstance(attribute, (list, tuple)):
                tree += left_margin + name + ' = [ \n'     
                for item in attribute:
                    tree += self.make_long_string(item, memo_set, curr_depth + 1, 
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
                    tree += self.make_long_string(item, memo_set, curr_depth + 1, 
                                                  left_margin_elem, line_width, 
                                                  name)
                tree += left_margin + '} \n'
            #Simple ttribute with tree maker
            else:
                tree += left_margin + name + ' = \n' \
                        + self.make_long_string(attribute, memo_set, curr_depth,  
                                                left_margin_elem, line_width, 
                                                name)
        return  tree
    

    def make_short_string(self, attribute, memo_set, name=None):
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
        
        
    def make_long_string(self, attribute, memo_set, curr_depth, 
                           left_margin_elem, line_width, name=None):
        '''Convert one object to a string, use tree maker for the conversion'''
        duplicate = id(attribute) in memo_set
        #make very short
        if name in self.xshort_set or duplicate \
           or isinstance(attribute, self.short_types) \
           or not hasattr(attribute, self.tree_maker_name):
            tree = left_margin_elem * (curr_depth + 1) \
                   + self.make_short_string(attribute, memo_set, name) + '; \n'
        #create a subtree
        else:
            #memo_set.add(id(attribute)) #against infinite recursion
            tree_maker = getattr(attribute, self.tree_maker_name)
            tree = tree_maker.make_tree(attribute, curr_depth + 1, memo_set, 
                                        left_margin_elem, line_width)
        return tree
        
        
    