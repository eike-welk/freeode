#create new node class


class Node(object):
    '''
    Base class for all elements of the AST.
    '''
    #put attributes with these names at the top or bottom of ASCII-art tree
    aa_top = []
    aa_bottom = ['loc']
    #stack to coordinate tree printing
    aa_stack = []
    
    def __init__(self, **args): 
        object.__init__(self)
        for key, value in args.iteritems():
            setattr(self, key, value)
            
    def __str__(self):
        '''
        Create ASCII-art tree of this object, and of all data attributes it 
        contains recursively.
        '''
        return self.aa_tree()
    
    def aa_tree(self, ):
        '''
        Create ASCII-art tree of this object, and of all data attributes it 
        contains recursively.
        
        The algorithm only recurses into nodes owned by this node. All other 
        objects will be printed in a very limited manner.
        
        The data attributes will be printed in alphabetical order. Exceptions
        are controlled by two lists (self.aa_top, self.aa_bottom).
        Attributes that appear in these lists are printed at the top or at
        the bottom of the area covered by this node.  
        '''
#        #the node's attributes are printed in sorted order,
#        #but the special attributes are excluded
#        specialAttrs = set(['loc', 'kids', '_nameSpaceAttrs', 'name', 'mainFuncs'])
#        attrNameSet = set(node.__dict__.keys())
#        attrNames= list(attrNameSet - specialAttrs)
#        attrNames.sort()
#        #get attributes out node.__dict__
#        for name1 in attrNames:
#            #TODO:more robustness when other attributes are Nodes too
#            #TODO:more robustness against circular dependencies
#            putStr(indentStr, name1 + ': ' + safeStr(node.__dict__[name1]) + ' ')
#        #put newline after complete node
#        self.endLine()
    
    
        
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
#        newObj = Node.__new__(self.__class__)
#        for name, attr in self.__dict__.iteritems():
#            if name == 'kids':
#                #kids: make deep copy
#                newObj.kids = copy.deepcopy(self.kids, memoDict)
#            else:
#                #normal attribute: no copy, only reference.
#                setattr(newObj, name, attr)
#        return newObj

            
            
            
n1 = Node(a=1, b=2)
print n1
