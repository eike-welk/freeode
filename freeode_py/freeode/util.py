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
                  left_margin_elem=' |', line_width=160):
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
        '''
        self.top_names = top_names
        self.xshort_names = xshort_names
        self.short_names = short_names
        self.long_names = long_names 
        self.bottom_names = bottom_names
        self.short_types = short_types
        #self.long_types = long_types #??????????????
        self.tree_maker_name = tree_maker_name
        self.left_margin_elem = left_margin_elem
        self.line_width = line_width
        self.max_depth = 100
        
        
    def make_tree(self, in_obj, curr_depth=0, memo_set=None, 
                   left_margin_elem=None, line_width=None):
        '''Convert in_obj to a ASCII art tree, recursively.'''
        if curr_depth > self.max_depth:
            return 'Max depth exceeded!\n'
        #create the left margin
        left_margin_elem = left_margin_elem if left_margin_elem \
                             else self.left_margin_elem
        left_margin = left_margin_elem * curr_depth
        #protect against wrapping
        line_width = line_width if line_width else self.line_width
        if len(left_margin) > line_width - 10:
            return left_margin + '~ snip\n'
        #prepare memo_set 
        memo_set = memo_set if memo_set else set()
        
        #put attributes into different lists
        top_attr, short_attr, long_attr, bottom_attr = self.make_attr_lists(in_obj)
        #create the text
        tree = ''
        tree += self.make_header_block(in_obj, left_margin, line_width)
        tree += self.make_short_block(in_obj, top_attr, left_margin, memo_set, line_width)
        tree += self.make_short_block(in_obj, short_attr, left_margin, memo_set, line_width)
        tree += self.make_long_block(in_obj, long_attr, curr_depth, left_margin, memo_set, line_width)
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
        
        #get the attributes that are printed first. they are not sorted
        top_attr = []
        for name in self.top_names:
            if name in attr_names:
                top_attr.append(name)
                attr_names.remove(name)
        #get the attributes that are printed last. they are not sorted
        bottom_attr = []
        for name in self.bottom_names:
            if name in attr_names:
                bottom_attr.append(name)
                attr_names.remove(name)
        
        #get attributes that the user wants to be converted by str
        #specified by name
        short_attr = [] 
        for name in self.short_names + self.xshort_names:
            if name in attr_names:
                short_attr.append(name)
                attr_names.remove(name)
        #specified by type
        short_types = tuple(self.short_types)
        for name, attr in attr_dict.iteritems():
            if isinstance(attr, short_types) and name in attr_names:
                short_attr.append(name)
                attr_names.remove(name)
        
        #get attributes that the user wants to be converted to trees
        #specified by name
        long_attr = []
        for name in self.long_names:
            if name in attr_names:
                long_attr.append(name)
                attr_names.remove(name)
        #attributes that contain a tree maker are converted to trees
        for name, attr in attr_dict.iteritems():
            if name not in attr_names:
                continue
            #Attributes that contain a tree maker
            if hasattr(attr, self.tree_maker_name):
                long_attr.append(name)
                attr_names.remove(name)
            #Lists and tuples where the first element contains a tree maker
            elif isinstance(attr, (list, tuple)):
                elem0 = attr[0]
                if hasattr(elem0, self.tree_maker_name):
                    long_attr.append(name)
                    attr_names.remove(name)
            #dicts where the first element we see contains a tree maker
            elif isinstance(attr, dict):
                elem0 = attr.values()[0]
                if hasattr(elem0, self.tree_maker_name):
                    long_attr.append(name)
                    attr_names.remove(name)
        long_attr.sort()
        
        #all remaining attributes are considered no tree
        for name in attr_names:
            short_attr.append(name)
        short_attr.sort()
            
        #print top_attr, short_attr, long_attr, bottom_attr
        return top_attr, short_attr, long_attr, bottom_attr
        
        
    def make_header_block(self, in_obj, left_margin, line_width):
        '''Create text block, use str to convert attributes'''
        return 'head\n'
    
    def make_short_block(self, in_obj, attr_list, left_margin, memo_set, line_width):
        '''Create text block, use str to convert attributes'''
        return 'foo\n'
    
    def make_long_block(self, in_obj, attr_list, curr_depth, left_margin, memo_set, line_width):
        '''Create text block, use str to convert attributes'''
        return 'bar\n'
    
    