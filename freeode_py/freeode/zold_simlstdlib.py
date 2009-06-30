# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2008 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
#                                                                          #
#    License: GPL                                                          #
#    TODO: GPL exception for generated code!
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
============================================================================
THIS MODULE IS NO LONGER USED, IT IS ONLY KEPT FOR REFERENCE!
============================================================================

Standard library of the SIML language

The standard library is mostly written in Siml, and resides in a text string 
in this module. Some parts can non be expressed in the language, but as AST 
nodes. These nodes are created in Python code and added to the parse tree 
after parsing the text string.

As the Siml language is highly specialized, it can not express low level 
concepts. Therefore most of the standard library constists of empty 
declarations, that are treated specially by the compiler.  
'''

#TODO: Rename to simlbuiltinlib! This lib is comparable to the built in symbols of Python.
#      Python's standard library is much larger, and it is also not automatically included 
#      like this lib.

from __future__ import division

import os
import unittest
#import our own syntax tree classes
import freeode.ast as ast
#import the parser
import freeode.simlparser as simlparser



#The built in library as a string
builtInLibraryStr = \
'''
#------------- base objects -----------------------------------------
#class Object():{}

class Numeric(Object):{}

class Real(Numeric):
{
    pragma no_flatten;
    pragma built_in_type;
    #TODO: Add special functions for the mathematical operators (__add__) to
    #      define the resulting types of mathematical expressions.        
}

class Model(Object):{}

class SolutionParameterClass(Object):
{
    data simulationTime: Real param; 
    data reportingInterval: Real param; 
}

class Process(Model):
{
    pragma compile_main_function init;
    pragma compile_main_function dynamic;
    pragma compile_main_function final;
    data solutionParameters: SolutionParameterClass;
}


#------------- mathematical functions -------------------------------
func sin(x):{
    #TODO: how should the built in functions be handled?
    #foreign_code python replace_call ::{{ sin(x) }}:: ;
    pragma built_in_func;
}
func cos(x):{ pragma built_in_func; }

func tan(x):{ pragma built_in_func; }

func sqrt(x):{ pragma built_in_func; }

func exp(x):{ pragma built_in_func; }

func log(x):{ pragma built_in_func; }

func min(a, b):{ pragma built_in_func; }

func max(a, b):{ pragma built_in_func; }


#------------- constants --------------------------------------------
data pi:Real const = 3.141592653589793;
#pi = 3.141592653589793; 
'''


def createParseTree():
    '''Create a complete parse ast of the standard library'''
    #Add newline chars to the library, so that the line numbers of error  
    #messages match the line numbers in this file. Use filename of this file.
    stdLibExt = '\n'*54 + builtInLibraryStr
    fileName = os.path.abspath(__file__)
    #remove 'c' from 'pyc'
    if fileName[-3:] == 'pyc':
        fileName = fileName[0:-1]
    #parse the library
    parser = simlparser.ParseStage()
    parseTree = parser.parseModuleStr(stdLibExt, fileName, 'builtin')
    #Create the 'object' class, the parent class of all classes
    objectClass = ast.NodeClassDef(name='Object', baseName=None) 
    parseTree.insertChild(0, objectClass)
    return parseTree



class TestStdLib(unittest.TestCase):

    def setUp(self):
        '''perform common setup tasks for each test'''
        pass

    def test__new__(self):
        '''Standard Library: Test if library can be parsed.'''
        #parse the library (and attach some nodes by hand)
        tree = createParseTree()
        self.assertTrue(isinstance(tree, ast.NodeModule))

    
    
def doTests():
    '''Perform various tests.'''
    #test the library ------------------------------------------------------------------
    flagTestTheLib = False
    flagTestTheLib = True
    if flagTestTheLib:
        astTree = createParseTree()
        print 'AST tree:'
        print astTree

if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add doctest tests. With doctest tests are embedded in the documentation

    #doTests()
    
    #perform the unit tests
    #unittest.main() #exits interpreter
    testSuite = unittest.TestSuite()
    testSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStdLib))
    unittest.TextTestRunner(verbosity=2).run(testSuite)
    
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
