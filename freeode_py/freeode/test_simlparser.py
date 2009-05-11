# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    License: GPL                                                          *
#                                                                          *
#    This program is free software; you can redistribute it and/or modify  *
#    it under the terms of the GNU General Public License as published by  *
#    the Free Software Foundation; either version 2 of the License, or     *
#    (at your option) any later version.                                   *
#                                                                          *
#    This program is distributed in the hope that it will be useful,       *
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#    GNU General Public License for more details.                          *
#                                                                          *
#    You should have received a copy of the GNU General Public License     *
#    along with this program; if not, write to the                         *
#    Free Software Foundation, Inc.,                                       *
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#***************************************************************************

"""
Test code for the interpreter module
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#import for test helper functions:
# py.test.fail('bad, bad, bad'); py.test.skip('no test')
                      
import py 

#import the library that we want to test
import freeode.simlparser as p



def test_parser_construction():
    print 'Test construction of the parser. Tests constructing the Pyparsing grammar.'
    parser = p.Parser()

    print 'Keywords:'
    print parser.keywords
    print
    print 'Built in variables:'
    print parser.builtInVars



def test_parse_function_definition_1():
    print 'Test to parse a function definition without arguments.'
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1():
    return
''' )
    print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    print ast 
    
    
    
def test_parse_function_definition_2():
    print 'Test to parse a function definition with positional arguments.'
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a, b, c):
    return
''' )
    print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    print ast    



def test_parse_function_definition_3():
    py.test.skip() #IGNORE:E1101
    print 'Test to parse a function definition with default values.'
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a=0, b=2, c=5):
    return
''' )
    print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    print ast   



def test_parse_function_definition_4():
    py.test.skip() #IGNORE:E1101
    print 'Test to parse a function definition with argument type specifications.'
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a:Float, b:String, c:Float):
    return
''' )
    print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    print ast   



def test_parse_function_definition_5():
    py.test.skip() #IGNORE:E1101
    print 'Test to parse a fully featured function definition.'
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a:String, b, c:Float, d:Float=2, e=3, f:Float=4):
    return
''' )
    print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    print ast   
    #assert False, 'Test'
    
    
    
def test_parse_complete_program_1():
    print 'Test to parse a complete program.'
    
    test_prog = (
'''
class Test:
    data V, h: Float
    data A_bott, A_o, mu, q, g: Float param

    func dynamic():
        h = V/A_bott
        $V = q - mu*A_o*sqrt(2*g*h)
#        print('h: ', h)

    func init():
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
        q = 0.05
 
 
class RunTest:
    data g: Float param
    data test: Test

    func dynamic():
        test.dynamic()

    func init():
        g = 9.81
        test.init()
#        solutionParameters.simulationTime = 100
#        solutionParameters.reportingInterval = 1

    func final():
#        graph test.V, test.h
        print('Simulation finished successfully.')
        

compile RunTest
''' )
    
    parser = p.Parser()
    
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    ast = parser.parseModuleStr(test_prog)
    print ast
    #assert False, 'Test'



