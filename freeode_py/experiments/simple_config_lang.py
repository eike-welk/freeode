# -*- coding: utf-8 -*-
'''
Copyright (C) 2010, Eike Welk
License GPL

Much nicer semantics are described in:
Can Programming Be Liberated from the von Neuman Style

Define simple shell-like language:
%Comment 
%Call function apt-get with multiple arguments
apt-get ibus-pinyin ibus-table-wubi language-pack-zh-hans
%Call the functions run, unpack, wget as a pipeline: 
%the function wget is called with the arguments:foo bar baz "hello word"
%unpack is called with the results of wget 
%and run is called with the results of unpack
run|unpack|wget foo bar baz "hello word"
'''

import sys
import itertools
from types import FunctionType

from pyparsing import (ParserElement, Forward, quotedString, Word, alphas, 
                       alphanums, Literal, restOfLine, ZeroOrMore, LineEnd, 
                       StringEnd, ParseSyntaxException, ParseException, lineno)

#If true True the parse actions do nothing
DEBUG_GRAMMAR = False


#The functions that do the work -----------------------------------
def print_func(*args):
    for arg in args:
        print arg, 
    print
    return tuple()
    
def nop_func(*args):
    return args
    
def cat_func(*args):
    #print 'cat_func:' , args,
    flat_tuple = tuple(itertools.chain.from_iterable(args))
    return ''.join(flat_tuple)

def map_func(opr_name, sequence):
    assert opr_name in ENVIRONMENT, 'Undefined operator ' + opr_name
    opr = ENVIRONMENT[opr_name]
    assert isinstance(opr, FunctionType), 'Not an operator ' + opr_name
    #perform the map oeration
    res = tuple([opr(elem) for elem in sequence])
    return res

def apt_get_func(*args):
    #TODO: implement this function
    print "The apt-get function is unimplented"
    print "Aguments: ", args
    return tuple()


#Storage of all global variables, stores only functions currently
ENVIRONMENT = {'print':print_func, 'nop':nop_func, 'cat':cat_func, 
               'map':map_func, 'apt-get':apt_get_func}


#These functions are called by the parser when a pattern in the program text is 
#recognized. These functions then perform program's actions. (There is no AST)       
def action_symbol(s, loc, toks):
    '''Parse action for a symbol. Returns: str''' 
    if DEBUG_GRAMMAR: return
    #print "action_symbol: ", toks
    return toks[0]

def action_q_symbol(s, loc, toks):
    '''Throw away quotes, return contained string. Returns: str''' 
    if DEBUG_GRAMMAR: return
    #print "action_q_symbol: ", toks
    return toks[0][1:-1] 
    
def action_pipeline(s, loc, toks):
    '''Return tuple of function names''' 
    if DEBUG_GRAMMAR: return
    #print "action_pipeline: ", toks
    return tuple(toks[::2])

def action_func_call(s, loc, toks):
    '''Execute the function call''' 
    if DEBUG_GRAMMAR: return
    #print "action_func_call: ", toks
    operators = toks[0]
    operands = tuple(toks[1::])
    try:
        #check if all operators exist
        for opr_name in operators:
            assert opr_name in ENVIRONMENT, 'Undefined operator ' + opr_name
            opr = ENVIRONMENT[opr_name]
            assert isinstance(opr, FunctionType), 'Not an operator ' + opr_name
        #call the operators from right to left
        for opr_name in operators[-1::-1]:
            opr = ENVIRONMENT[opr_name]
            operands = opr(*operands)
    except AssertionError, err:
        print 'Line: ' + str(lineno(loc, s))
        print err
        sys.exit()
    except TypeError, err:
        print 'Line: ' + str(lineno(loc, s))
        print err
        sys.exit(1)
    return operands
        
        
def defineParsers():
    #Enable a fast parsing mode with caching.
    ParserElement.enablePackrat()
    #end of line terminates statements, so it is not regular whitespace
    ParserElement.setDefaultWhitespaceChars('\t ')

    func_call = Forward() #forward declaration because this is a recursive rule   

    #The "terminal" rules
    symbol = Word(alphas+'_-', alphanums+'_-') .setParseAction(action_symbol)
    q_symbol = quotedString                    .setParseAction(action_q_symbol)
    bracket_term = Literal("(").suppress() - func_call \
                   + Literal(")").suppress()
    word = symbol | q_symbol | bracket_term
    
    #The function call
    #Parse: "foo | bar | baz" or "foo"
    pipeline = (word + ZeroOrMore("|" - word)) .setParseAction(action_pipeline) 
    #Parse "foo|bar op1 op2 op3"
    func_call << (pipeline - ZeroOrMore(word)) .setParseAction(action_func_call)
    
    #High level structure of program
    line = LineEnd() | func_call - LineEnd() #empty line or function call
    program = ZeroOrMore(line) + StringEnd() #multiple lines are a program
    
    #define the comments
    program.ignore('%' + restOfLine)
    #no tab expansion
    program.parseWithTabs()   
    #return additional func_call parser to make testing more easy
    return program, func_call
#Create the parser(s)
parse_program, parse_call = defineParsers() 


#Execute the program; this is the main function
def execute_program_str(prog_text):
    try:
        parse_program.parseString(prog_text)
    except ParseException, err:
        print err
        sys.exit(1)
        


def test_program():
    '''Execute some programs to see if the language works'''
    prog_text = \
"""
% The built in operators:
print ---------- print ------------
% The print operator prints its arguments and returns an empty list
print foo bar baz

print ---------- nop -----------
% The nop operator returns its arguments unchanged
% it can be considered as a constructor for nested lists.
print | nop foo bar baz
print | nop a b (nop c d e) (nop f g) h

print ---------- cat ----------
% cat concatenates its arguments
print | cat foo bar baz

print ---------- map -----------
%The map operator has two arguments: an operator and a list.
%It calls the operator which each element of the list as it's argument:
print foo bar baz
map print (nop foo bar baz)

print ---------- apt-get ----------
% The apt-get function needs to be implemented, 
% it currently only prints its arguments
apt-get foo bar baz
"""
    execute_program_str(prog_text)
    
    prog_text = \
"""
% The syntax:
% Comments start with a "%" character. They extend until the end of the line.

% Every line is one application (function call) of an operator.
% The first word is the name of the operator all other words are arguments.
print
print These are the arguments of the print operator

%Operators can be chained into a pipeline with the "|" character:
print | nop | cat foo bar baz

% Brackets "()" work similarly to brackets in Python. The expression in between
% the brackets is evaluated first. The first word (or pipeline) between the 
% brackets is the operator, and is executed.
print first (cat foo bar baz) boo boum

% There are quoted stings
print "Hello World!" foo "bar: E = mc² baz!"

print
"""
    execute_program_str(prog_text)
    
    
    
def test_func_call():
    '''Test the functions and the calling mechanism'''
    #test call mechanism --- 
    #Single operator 
    prog_text = "nop foo bar baz"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == ('foo', 'bar', 'baz')
    #pipeline operator 
    prog_text = "nop | nop foo bar baz"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == ('foo', 'bar', 'baz')
    #brackets  
    prog_text = "nop (nop foo bar) baz"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == (('foo', 'bar'), 'baz')
    
    #test built in functions
    #print  
    prog_text = "print foo bar baz"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == tuple()
    #nop was already tested
    #cat
    prog_text = "cat foo bar baz"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == 'foobarbaz'
    #cat 
    prog_text = "nop (cat foo bar baz)  (cat foo bar baz)"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == ('foobarbaz', 'foobarbaz')
    #map
    prog_text = "map cat (nop (nop foo bar baz) (nop foo bar baz))"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == ('foobarbaz', 'foobarbaz')
    #apt-get
    prog_text = "apt-get ibus-pinyin ibus-table-wubi language-pack-zh-hans"
    res = parse_call.parseString(prog_text)
    #print res
    assert res[0] == tuple()
    
    
    
def test_language_grammar():
    '''Test the grammar, the following programs must be parsed without error'''
    #switch the parse actions off
    global DEBUG_GRAMMAR
    DEBUG_GRAMMAR = True
    
    #test that comments are ignored ------
    prog_text = "%Only comment"
    res = parse_program.parseString(prog_text)
    #print res
    assert len(res) == 0
    
    #test call --- 
    #Single operator and operand
    prog_text = "foo bar" 
    res = parse_call.parseString(prog_text)
    #print res
    assert len(res) == 2 and res[0] == 'foo' and res[1] == 'bar'
    #Single operator, multiple operands 
    prog_text = "foo bar1 bar2 bar3" 
    res = parse_call.parseString(prog_text)
    #print res
    assert len(res) == 4 and res[0] == 'foo' and res[1] == 'bar1'  and \
           res[2] == 'bar2'  and res[3] == 'bar3'
    #Pipeline operator, multiple operands 
    prog_text = "foo1|foo2|foo3 bar1 bar2 bar3" 
    res = parse_call.parseString(prog_text)
    #print res
    assert len(res) == 8 and res[0] == 'foo1' and res[2] == 'foo2'  and \
           res[4] == 'foo3'
    
    #Test program ---------
    #correct program
    prog_text = \
"""
foo bar1 bar2 bar3
%comment
foo1|foo2|foo3 bar1 bar2 bar3
""" 
    res = parse_program.parseString(prog_text)
    #print res
    #this one must raise syntax error
    try:
        prog_text = "foo1 foo2|foo3 bar1 bar2 bar3" 
        res = parse_program.parseString(prog_text)
    except ParseSyntaxException:
        pass
    else:
        assert False, "Syntax error was not detected!" 
    
    #test bracket "(foo bar)" syntax
    prog_text = "foo (bar baz) boom" 
    res = parse_call.parseString(prog_text)
    #print res
    assert len(res) == 4
    
    #switch parse actions on again
    DEBUG_GRAMMAR = False
    
    
if __name__ == '__main__':
    test_program()
    test_func_call()
    test_language_grammar()
    pass