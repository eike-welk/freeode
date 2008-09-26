#create new node class


class NodeNg(object):
    '''
    Base class for all elements of the AST.
    
    Features:
    __str__(), aa_tree(...): 
        create an Ascii-art tree representation of the node and its 
        attributes.
    copy():
        Return deep copy of the node and of all attributes that are 'owned'
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
            0: not a NodeNg
            1: not owned
            2: NodeNg
            3: list(NodeNg)
            4: list(list(NodeNg))
        '''
        #get attribute
        if attr_name in self.__dict__:
            attr = self.__dict__[attr_name]
        else:
            return -1 # attribute does not exist
        #categorize attribute
        if isinstance(attr, NodeNg):
            return 2 # NodeNg
        elif isinstance(attr, list) and isinstance(attr[0], NodeNg):
            return 3 # list(NodeNg)
        elif isinstance(attr, list) and isinstance(attr[0], list) and\
             isinstance(attr[0][0], NodeNg):
            return 4 # list(list(NodeNg))
        else:
            #TODO: return 1 for not owned attributes too!
            return 0 #not a NodeNg
            
    def aa_make_str_any(self, attr_name_list, indent_str, nesting_level):
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
                raise Exception('Feature unimplemented!')
            #Attribute is Node
            elif cat == 2:
                if line != indent_str: tree += line  + '\n'
                line = indent_str
                tree += indent_str + name + ' = \n'
                tree += self.__dict__[name].aa_make_tree(nesting_level +1)
            #Attribute is list(NodeNg)
            elif cat == 3:
                if line != indent_str: tree += line  + '\n'
                line = indent_str   
                tree += indent_str + name + ' = list :: \n'     
                for item in self.__dict__[name]:
                    tree += item.aa_make_tree(nesting_level +1)  
            #Attribute is list(list(NodeNg))
            elif cat == 4:
                raise Exception('Feature unimplemented!')
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
            Attribute names are in NodeNg.aa_top, or in self.aa_top.
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
            Attribute names are in NodeNg.aa_bottom, or in self.aa_bottom.
        '''
        #init buffer
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
            tree_buffer += ' ID: ' + str(id(self))
        tree_buffer += ' ---------------------------------\n'
        
        #convert the attributes to string
        tree_buffer += self.aa_make_str_any(attr_top,    indent_str, nesting_level)
        tree_buffer += self.aa_make_str_any(attr_small,  indent_str, nesting_level)
        tree_buffer += self.aa_make_str_any(attr_big,    indent_str, nesting_level)
        tree_buffer += self.aa_make_str_any(attr_bottom, indent_str, nesting_level)
        
        return tree_buffer
    
        
    #TODO: implement!       
#    def copy(self):
#        '''
#        Return a (recursive) deep copy of the node.
#    
#        Only objects owned by this object are copied deeply.
#        TODO: how is ownership established? Weak references??
#        '''
#        return copy.deepcopy(self)
#
#
#    def __deepcopy__(self, memoDict):
#        '''Hook that does the copying.
#        Called by the function copy.deepcopy()'''
#        #create empty instance of self.__class__
#        newObj = NodeNg.__new__(self.__class__)
#        for name, name in self.__dict__.iteritems():
#            if name == 'kids':
#                #kids: make deep copy
#                newObj.kids = copy.deepcopy(self.kids, memoDict)
#            else:
#                #normal attribute: no copy, only reference.
#                setattr(newObj, name, name)
#        return newObj

            
            
NodeNg.aa_show_ID = True

n1 = NodeNg(a=1, b=2, c='*'*150, d=4, name='n1')
print n1

n2 = NodeNg(a=1, b=NodeNg(a=11, b=22), c=3, d=NodeNg(a=11, b=22), loc='test-loc', name='n2')
print n2

n3 = NodeNg(a=1, b=[NodeNg(a=10, b=20), NodeNg(a=11, b=21)], d=4, loc='test-loc', name='n3')
print n3

n4 = NodeNg(a=1, b=n3, d=4, loc='test-loc', name='n4')
print n4


