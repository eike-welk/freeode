# -*- coding: utf-8 -*-

from pyparsing import *


#this class should replace the parse results.
#The __getitem__ method sometimes confuses Pyparsing
class Node(object):
    def __init__(self):
        self.kids = []
    #This is the method which confuses Pyparsing
    def __getitem__(self, i):
        return self.kids[i]

#replace ParseResult with Node
def action_Node(s, loc, toks): 
    return Node()


#--- Example 1 ---
#This combination raises a parse exception where it should not:
identifier = Word(alphas+'_', alphanums+'_').setParseAction(action_Node)
  
keyword_argument = Group(identifier         .setResultsName('keyword')
                         + '=')  
print        
print 'trying example 1'      
try:
    print keyword_argument.parseString('b=')
    print 'Oh my golly! Example 1 worked !!! (The bug is fixed.)'
except:
    print 'exception happened in example 1. (This is the bug.)'


#--- Example 2 ---
#This combination raises no exception (don't use setResultsName):
identifier = Word(alphas+'_', alphanums+'_').setParseAction(action_Node)
  
keyword_argument = Group(identifier         #.setResultsName('keyword')
                         + '=')  
print
print 'trying example 2'  
print keyword_argument.parseString('b=')
print 'Example 2 worked.'


#--- Example 3 ---
#This combination raises no exception (don't use setParseAction):
identifier = Word(alphas+'_', alphanums+'_')#.setParseAction(action_Node)
  
keyword_argument = Group(identifier         .setResultsName('keyword')
                         + '=')  
print
print 'trying example 3'  
print keyword_argument.parseString('b=')
print 'Example 3 worked.'


#--- Example 4 ---
#This combination does not raise an exception (different class for storing 
# results):
#replace ParseResult with string
def action_string(s, loc, toks): 
    return 'identifier'
    
identifier = Word(alphas+'_', alphanums+'_').setParseAction(action_string)
  
keyword_argument = Group(identifier         .setResultsName('keyword')
                         + '=')  
print        
print 'trying example 4'   
print keyword_argument.parseString('b=')
print 'Example 4 worked.'


