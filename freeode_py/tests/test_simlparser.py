# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
#    eike.welk@gmx.net                                                     *
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
from __future__ import absolute_import              

from py.test import skip as skip_test  #pylint:disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test  #pylint:disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises #pylint:disable-msg=W0611



def test_parser_construction(): #IGNORE:C01111
    msg = 'Test construction of the parser. Tests constructing the Pyparsing grammar.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p
    
    parser = p.Parser()

    print 'Keywords:'
    print parser.keywords
    print
    print 'Built in variables:'
    print parser.builtInVars



def test_number_1(): #IGNORE:C01111
    msg = 'Parse a floating point number.'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeFloat
    from freeode.util import aa_make_tree
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1
    
    def test_number(num_str):
        ast = parser.parseExpressionStr(num_str)
#        print aa_make_tree(ast)
        assert isinstance(ast, NodeFloat)
        assert ast.value == num_str
    
    test_number("2")
    test_number("2.")
    test_number(".2")
    test_number("2.5")
    test_number("2E2")
    test_number("2.5E2")
    test_number("2.5E-2")
    test_number("2.5E+2")
    
    

def test_identifier_1(): #IGNORE:C01111
    msg = 'Parse an identifier.'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeIdentifier
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_expression = 'a'
    print 'expression: ', test_expression
    
    ast = parser.parseExpressionStr(test_expression)
    print 'AST:'
    print ast 
    
    node_id = ast
    assert isinstance(node_id, NodeIdentifier)
    assert isinstance(node_id.name, str)
    assert node_id.name == 'a'
        


# ---------- data statement -----------------------------------------------------
def check_single_data_statement(data_stmt, name, class_name, role):
    '''Check the validity of a single data statement, which comes from the parser.'''
    from freeode.ast import NodeDataDef, NodeIdentifier
    
    assert isinstance(data_stmt, NodeDataDef)
    #name
    assert isinstance(data_stmt.name, str)
    assert data_stmt.name == name
    #type
    assert isinstance(data_stmt.class_spec, NodeIdentifier)
    assert data_stmt.class_spec.name == class_name
    #role
    assert data_stmt.role == role
    

def test_data_def_1(): #IGNORE:C01111
    msg = 'Parse data definition for single attribute.'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import RoleConstant
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_prog = (
'''
data a: Float const
''' )
    print 'statement: --------------------------'
    print test_prog

    ast = parser.parseModuleStr(test_prog)
    print 'AST: --------------------------------'
    print ast 
    
    data_stmt = ast.statements[0]
    check_single_data_statement(data_stmt, 'a', 'Float', RoleConstant)
    
    
    
def test_data_def_2(): #IGNORE:C01111
    msg = 'Parse data definition for multiple attributes.'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeDataDef, NodeStmtList, RoleConstant
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_prog = (
'''
data a, b, c: Float const
''' )
    print 'statement: --------------------------'
    print test_prog

    ast = parser.parseModuleStr(test_prog)
    print 'AST: --------------------------------'
    print ast 
    
    #A data statement with multiple attributes is parsed into a list of 
    #data statements for one attribute
    data_stmt_list = ast.statements[0]
    assert isinstance(data_stmt_list, NodeStmtList)
    #test each data statement in the list
    for data_stmt, name in zip(data_stmt_list.statements, ['a', 'b', 'c']):
        assert isinstance(data_stmt, NodeDataDef)
        check_single_data_statement(data_stmt, name, 'Float', RoleConstant)
    


# ---------- if statement -----------------------------------------------------
def test_ifc_stmt_1(): #IGNORE:C01111
    msg = 'Test to parse a ifc statement. The ifc statement is executed at compile time,'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeIfStmt, NodeClause, NodeFloat
    #from freeode.util import aa_make_tree
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_prog = (
'''
ifc a==1:
    b = 1
    c = 1
elif a==2:
    b = 2
else:
    b = 3
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print aa_make_tree(ast) 
    
    if_stmt = ast.statements[0]
    assert isinstance(if_stmt, NodeIfStmt)
    assert if_stmt.runtime_if == False
    assert len(if_stmt.clauses) == 3 
    if_clause = if_stmt.clauses[0]
    assert isinstance(if_clause, NodeClause)
    assert len(if_clause.statements) == 2
    elif_clause = if_stmt.clauses[1]
    assert isinstance(elif_clause, NodeClause)
    assert len(elif_clause.statements) == 1
    else_clause = if_stmt.clauses[2]
    assert isinstance(else_clause, NodeClause)
    assert len(else_clause.statements) == 1
    assert isinstance(else_clause.condition, NodeFloat)
    


def test_if_stmt_1(): #IGNORE:C01111
    msg = 'Test to parse an if statement. The if statement is executed at run time,'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeIfStmt, NodeClause, NodeFloat
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_prog = (
'''
if a==1:
    b = 1
    c = 1
elif a==2:
    b = 2
else:
    b = 3
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast 
    
    if_stmt = ast.statements[0]
    assert isinstance(if_stmt, NodeIfStmt)
    assert if_stmt.runtime_if == True
    assert len(if_stmt.clauses) == 3 
    if_clause = if_stmt.clauses[0]
    assert isinstance(if_clause, NodeClause)
    assert len(if_clause.statements) == 2
    elif_clause = if_stmt.clauses[1]
    assert isinstance(elif_clause, NodeClause)
    assert len(elif_clause.statements) == 1
    else_clause = if_stmt.clauses[2]
    assert isinstance(else_clause, NodeClause)
    assert len(else_clause.statements) == 1
    assert isinstance(else_clause.condition, NodeFloat)
    


def test_if_stmt_2(): #IGNORE:C01111
    msg = 'Test to parse an if statement. - Corner case, most simple if statement.'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeIfStmt, NodeClause
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_prog = (
'''
if a: b
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast 
    
    if_stmt = ast.statements[0]
    assert isinstance(if_stmt, NodeIfStmt)
    assert len(if_stmt.clauses) == 1 
    if_clause = if_stmt.clauses[0]
    assert isinstance(if_clause, NodeClause)
    assert len(if_clause.statements) == 1
    
    
    
# ---------- class definition -----------------------------------------------------
def test_class_def_1(): #IGNORE:C01111
    msg = 'Parse data definition for multiple attributes.'
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser   
    from freeode.ast import NodeClassDef, NodePassStmt
    
    parser = Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
    #Parser.noTreeModification = 1

    test_prog = (
'''
class A:
    pass
''' )
    print 'statement: --------------------------'
    print test_prog

    ast = parser.parseModuleStr(test_prog)
    print 'AST: --------------------------------'
    print ast 
    
    class_stmt = ast.statements[0]
    assert isinstance(class_stmt, NodeClassDef)    
    assert class_stmt.name == 'A'
    #the single statement in the class body
    assert len(class_stmt.statements) == 1
    assert isinstance(class_stmt.statements[0], NodePassStmt)



# ---------- function definition -----------------------------------------------------
def test_parse_function_definition_1(): #IGNORE:C01111
    msg = 'Test to parse a function definition without arguments.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p    
    from freeode.ast import NodeFuncDef
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1():
    return
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast 
    
    func = ast.statements[0]
    assert isinstance(func, NodeFuncDef)
    assert len(func.signature.arguments) == 0
    assert len(func.statements) == 1
    assert func.signature.return_type is None

    
    
def test_parse_function_definition_2(): #IGNORE:C01111
    msg = 'Test to parse a function definition with positional arguments.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p 
    from freeode.ast import NodeFuncDef
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a, b, c):
    return
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast    

    func = ast.statements[0]
    assert isinstance(func, NodeFuncDef)
    assert len(func.signature.arguments) == 3
    assert len(func.statements) == 1
    assert func.signature.return_type is None
    


def test_parse_function_definition_3(): #IGNORE:C01111
    msg = 'Test to parse a function definition with default values.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p 
    from freeode.ast import NodeFuncDef, NodeFuncArg, NodeFloat
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a=0, b=2, c=5):
    return
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast       
    
    #Test some general properties of the function node
    func = ast.statements[0]
    assert isinstance(func, NodeFuncDef)
    assert len(func.signature.arguments) == 3
    assert len(func.statements) == 1
    assert func.signature.return_type is None

    #See if the default values are really there.
    a, b, c = func.signature.arguments
    assert isinstance(a, NodeFuncArg)
    assert isinstance(a.default_value, NodeFloat)
    assert isinstance(b.default_value, NodeFloat)
    assert isinstance(c.default_value, NodeFloat)
     


def test_parse_function_definition_4(): #IGNORE:C01111
    msg = 'Test to parse a function definition with argument type speifcications.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p
    from freeode.ast import NodeFuncDef, NodeFuncArg, NodeIdentifier
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a:Float, b:String, c:Float):
    return
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast   

    #Test some general properties of the function node
    func = ast.statements[0]
    assert isinstance(func, NodeFuncDef)
    assert len(func.signature.arguments) == 3
    assert len(func.statements) == 1
    assert func.signature.return_type is None

    #See if the type annotations  are really there.
    a, b, c = func.signature.arguments
    assert isinstance(a, NodeFuncArg)
    assert isinstance(a.type, NodeIdentifier)
    assert isinstance(b.type, NodeIdentifier)
    assert isinstance(c.type, NodeIdentifier)



def test_parse_function_definition_5(): #IGNORE:C01111
    msg = 'Test to parse a fully featured function definition.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p
    from freeode.ast import NodeFuncDef
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1(a:String, b, c:Float, d:Float=2, e=3, f:Float=4) -> Float:
    return
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast   
    #assert False, 'Test'
    
    #Test some general properties of the function node
    func = ast.statements[0]
    assert isinstance(func, NodeFuncDef)
    assert len(func.signature.arguments) == 6
    assert len(func.statements) == 1
    assert func.signature.return_type is not None


    
def test_parse_function_definition_6(): #IGNORE:C01111
    msg = 'Test to parse a function definition with return type specification.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p
    from freeode.ast import NodeFuncDef, NodeIdentifier
    
    parser = p.Parser()
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    test_prog = (
'''
func test_1() -> Float:
    return 1
''' )
    #print test_prog
    print
    ast = parser.parseModuleStr(test_prog)
    #print ast 
#    assert False, 'Test'
    
    #Test some general properties of the function node
    func = ast.statements[0]
    assert isinstance(func, NodeFuncDef)
    assert len(func.signature.arguments) == 0
    assert len(func.statements) == 1
    assert func.signature.return_type is not None
    
    assert isinstance(func.signature.return_type, NodeIdentifier)
    
    
    
# ---------- complete program -----------------------------------------------------
def test_parse_complete_program_1(): #IGNORE:C01111
    msg = 'Test to parse a complete program.'
    #py.test.skip(msg)
    print msg
    
    import freeode.simlparser as p
    
    test_prog = (
'''
class Test:
    data V, h: Float
    data A_bott, A_o, mu, q, g: Float param
                                               #5 
    func dynamic():
        h = V/A_bott
        $V = q - mu*A_o*sqrt(2*g*h)
        print('h: ', h)
                                               #10
    func init():
        V = 0;
        A_bott = 1E0; A_o = 0.02; mu = 0.55;
        q = 0.05
 
 
class RunTest:
    data g: Float param
    data test: Test

    func dynamic():
        test.dynamic()

    func init():
        g = 9.81
        test.init()
        solution_parameters(100, 1)

    func final():
        graph(test.V, test.h)
        print('Simulation finished successfully.')
        

compile RunTest
''' )
    
    parser = p.Parser()
    
    #For debugging: keep Pyparsing's  original parse results.
    # Exit immediately from all action functions
#   Parser.noTreeModification = 1

    _ast = parser.parseModuleStr(test_prog)
    #print _ast
    #assert False, 'Test'



# ---------- errors -----------------------------------------------------------
def test_parser_stack_overflow_bug(): #IGNORE:C01111
    msg = '''
    Some relatively short input made the the parser crash because of stack 
    exhaustion.
    
    This test is for fixed bug: #389924
        https://bugs.launchpad.net/freeode/+bug/389924
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.simlparser import Parser
    from freeode.util import UserException
    
    #--- first example ------------------------------------------------------
    #http://launchpadlibrarian.net/28144614/crash_parser3.siml
    prog_text = \
'''
#This file causes a compiler internal error which is difficult to debug:
#RuntimeError: maximum recursion depth exceeded
#Now trying illegal syntax

#func a():
#func a():
func a():

if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:  #There must be an if statement at the end for the error to happen
    a()
'''
    parser = Parser()
    assert_raises(UserException, None, 
                  parser.parseModuleStr, prog_text)
    
    #--- second example --------------------------------------------------
    #Modified version of:
    #http://launchpadlibrarian.net/28144614/crash_parser3.siml
    prog_text = \
'''
func a():
    pass

if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:
    a()
if a:  #There must be an if statement at the end for the error to happen
    a()
'''
    parser = Parser()
    _ast = parser.parseModuleStr(prog_text)
    
    #--- third example ------------------------------------------------------
    #http://launchpadlibrarian.net/28144624/crash_parser4.siml
    prog_text = \
'''
#This file causes a compiler internal error which is difficult to debug:
#RuntimeError: maximum recursion depth exceeded
#Now trying illegal syntax

func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():
func a():

'''
    
    parser = Parser()
    assert_raises(UserException, None, 
                  parser.parseModuleStr, prog_text)
    
    #--- fourth example ------------------------------------------------------
    #http://launchpadlibrarian.net/28144635/crash_parser5.siml
    prog_text = \
'''
#This file causes a compiler internal error which is difficult to debug:
#RuntimeError: maximum recursion depth exceeded
#Now trying illegal syntax

if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
if a:
'''
    
    parser = Parser()
    assert_raises(UserException, None, 
                  parser.parseModuleStr, prog_text)
       
    
    
# ---------- call function for debugging here ---------------------------------
if __name__ == '__main__':
    # Debugging code may go here.
    test_number_1()
    pass #pylint:disable-msg=W0107
