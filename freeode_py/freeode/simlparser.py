# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration and little bits of text and code came from:               *
#     'fourFn.py', 'simpleArith.py' example programs, by Paul McGuire,     *
#     the 'Spark' library by John Aycock,                                  *
#     and the Python Reference Manual by Guido van Rossum.                 *
#    Many thanks for their excellent contributions to publicly available   *
#    knowledge.                                                            *
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
Parser for the SIML simulation language.
"""

#TODO: write unit tests that exercise every error message of simlparser.py

from __future__ import division

__version__ = "$Revision: $"
# $Source$

#import debugger
#import pdb
import os
#import parser library
from pyparsing import ( Literal, CaselessLiteral, Keyword, Word,
    ZeroOrMore, OneOrMore, Forward, nums, alphas, alphanums, restOfLine,
    oneOf, LineEnd, indentedBlock, 
    delimitedList, Suppress, operatorPrecedence, opAssoc,
    StringEnd, quotedString, Combine, Group, Optional,
    ParseException, ParseFatalException, ParserElement, )
#import our own syntax tree classes
from freeode.ast import *



#Enable a fast parsing mode with caching. May not always work.
pyparsing.ParserElement.enablePackrat()


class ChMsg(object):
    '''
    Change a parser's error message.
    
    Attach to parser with setFailAction
    '''
    def __init__(self, prepend=None, append=None):
        object.__init__(self)
        self.prepend_str = prepend
        self.append_str = append
        
    def __call__(self, s,loc,expr,err):
        '''Change error message. Called by parser when it fails.
        
        Arguments:
            - s = string being parsed
            - loc = location where expression match was attempted and failed
            - expr = the parse expression that failed
            - err = the exception thrown
            
        Return:
           The function returns no value.  It may throw ParseFatalException
           if it is desired to stop parsing immediately.
        '''
        #TODO: Does this class need to react to regular ParseExceptions too? (ParseSyntaxException)
        #Work only with fatal errors from Pyparsing
        if isinstance(err, ParseFatalException):
            if self.prepend_str is not None:
                err.msg = self.prepend_str + err.msg
            if self.append_str is not None:
                err.msg = err.msg + self.append_str
            raise err
        
        
#TODO: remove?
#
#class ParseActionException(Exception):
#    '''Exception raised by the parse actions of the parser.'''
#    pass



class Parser(object):
    '''
    Parse the Siml program. Generate a parse tree.

    The syntax definition (BNF) resides here.

    The parsing is done by the pyparsing library which combines
    lexer and parser. The Pyparsing library generates a tree of
    ParseResult objects. These objects are replaced by objects inheriting
    from ast.Node in the parse actions (_action* functions) of this class.

    Normally a file name is given to the class, and a tree of ast.Node objects is
    returned. The program can also be entered as a string.
    Additionally the class can parse parts of a program: expressions.

    The parse* methods return a tree of ast.Node objects; the parse tree.

    Usage:
    parser = Parser()
    ast1 = parser.parseExpressionStr('0+1+2+3+4')
    ast2 = parser.parseModuleFile('foo-bar.siml')
    '''

    noTreeModification = 0
    '''
    Define how much the parse result is modified, for easier debuging.
    0: normal operation. Compilation does not work otherwise.
    1: Do not modify parse result from the Pyparsing library.

    ParseResult objects (which come from the Pyparsing library) are printed
    as nested lists: ['1', '+', ['2', '*', '3']]
    '''

    keywords = set()
    '''
    Set of all keywords (filled by _defineLanguageSyntax() and defineKeyword(...)).
    '''
    #Special variables, that are built into the language (filled by _defineLanguageSyntax())
    builtInVars = set()


    def __init__(self):
        object.__init__(self)
        #The parser object for the whole program (from pyParsing).
        self._parser = None
        #The parser for expressions
        self._expressionParser = None
        #Name of SIML program file, that will be parsed
        self.progFileName = None
        #name, that will be given to the root node of a module
        #usually part of the filename
        self.moduleName = None
        #String that will be parsed
        self.inputString = None
        #indent stack for indentedBlock helper from Pyparsing
        self.indentStack = [1]

        #Create parser objects
        self._defineLanguageSyntax()


    def defineKeyword(self, inString):
        '''
        Store keyword (in Parser.keywords) and create parser for it.
        Use this function (in _defineLanguageSyntax(...)) instead of using the
        Keyword class directly.
        '''
        Parser.keywords.add(inString)
        return Keyword(inString)

    def createTextLocation(self, atChar):
        '''Create a text location object at the given char.'''
        return TextLocation(atChar, self.inputString, self.progFileName)


#------------- Parse Actions -------------------------------------------------*
    def _actionDebug(self, s, loc, toks):
        '''Parse action for debugging.'''
        print '------debug action'
        print s
        print loc
        print toks
        print '-------------------'
        return None

    def _actionCheckIdentifier(self, s, loc, toks):
        '''
        Tests wether an identifier is legal.
        If the identifier is equal to any keyword the parse action raises
        an exception.
        Does not change any parse results

        tokList is structured like this: ['a1']
        '''
        tokList = toks.asList() #asList() this time ads *no* extra pair of brackets
        identifier = tokList[0]
        if identifier in Parser.keywords:
            #print 'found keyword', toks[0], 'at loc: ', loc
            errMsg = 'Keyword can not be used as an identifier: ' + identifier
            raise ParseException(s, loc, errMsg)
        return

    def _actionCheckIdentifierFatal(self, s, loc, toks):
        '''
        Tests whether an identifier is legal.
        If the identifier is equal to any keyword the parse action raises
        an user visible exception. This will usually stop the compiler.
        Does not change any parse results

        tokList is structured like this: ['a1']
        '''
        tokList = toks.asList() #asList() this time ads *no* extra pair of brackets
        identifier = tokList[0]
        if identifier in Parser.keywords:
            #print 'found keyword', toks[0], 'at loc: ', loc
            errMsg = 'Keyword can not be used as an identifier: ' + identifier
#            txtLoc = self.createTextLocation(loc)
            raise ParseFatalException(s, loc, errMsg)
        if identifier in Parser.builtInVars:
            errMsg = 'Built in variables can not be redefined: ' + identifier
#            txtLoc = self.createTextLocation(loc)
            raise ParseFatalException(s, loc, errMsg)
        return

#    def _actionBuiltInValue(self, str, loc, toks):
#        '''
#        Create AST node for a built in value: pi, time
#        tokList has the following structure:
#        [<identifier>]
#        '''
#        if Parser.noTreeModification:
#            return None #No parse result modifications for debugging
#        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
#        #create AST node
#        nCurr = NodeBuiltInVal()
#        nCurr.loc = self.createTextLocation(loc) #Store position
#        nCurr.dat = tokList #Store the built in value's name
#        return nCurr


    def _action_number(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for a number: 5.23
        tokList has the following structure:
        [<number>]
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeFloat()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.value = tokList[0] #Store the number
        return nCurr

    def _action_string(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for a string: 'qwert'
        tokList has the following structure:
        [<string>]
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeString()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.value = tokList[1:-1] #Store the string; remove quotes
        return nCurr

    def _action_parentheses_pair(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for a pair of parentheses that enclose an expression: (...)
        tokList has the following structure:
        ['(', <expression>, ')']

        The information about parentheses is necessary to be able to output
        correct Python code, without the need for complicated algorithms.
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeParentheses()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.arguments = [tokList[1]] #store child expression
        return nCurr

    def _action_op_prefix(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for math prefix operators: -
        tokList has the following structure:
        [<operator>, <expression>]
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #Group() ads an extra pair of brackets
        nCurr = NodeOpPrefix1()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.operator = tokList[0]  #Store operator
        nCurr.arguments = [tokList[1]] #Store expression 
        return nCurr

    def _action_op_infix_left(self, s, loc, toks): #IGNORE:W0613
        '''
        Build tree of infix operators from list of operators and operands.

        operatorPrecedence returns such a list for left assocative operaators.
        tokList has the following structure:
        [<expression_1>, <operator_1>, <expression_2>, <operator_2>, ... 
         <expression_n+1>]
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0]
        tree = self._action_op_infix(s,  loc, tokList[0:3])
        for i in range(3, len(tokList),  2):
            tree = self._action_op_infix(s,  loc,  [tree,  tokList[i],  tokList[i+1]])
        return tree

    def _action_op_infix(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for math infix operators: + - * / **
        tokList has the following structure:
        [<expression_l>, <operator>, <expression_r>]
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        if not isinstance(toks,  list):
            #Convert parse result to list, remove extra pair of brackets
            tokList = toks.asList()[0] 
        else:
            #function was called by _action_op_infix_left(...) toks is already
            #a list.
            tokList = toks
        nCurr = NodeOpInfix2()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #Store both expressions and operator
        exprLhs = tokList[0]        #expression left hand side
        nCurr.operator = tokList[1] #operator
        exprRhs = tokList[2]        #rhs
        nCurr.arguments = [exprLhs, exprRhs]
        return nCurr

    def _action_identifier(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for an identifier. 
        
        An identifier always means access to data. Identifiers closely work
        together with the dot operator. 
        tokList has the following structure:
        [<string>]
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeIdentifier()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #The flattened system will require the use of multicomponent DotNames;
        # therefore the DotName class is used already here.
        nCurr.name = DotName(tokList)
        return nCurr


    def _actionIfStatement(self, s, loc, toks): #IGNORE:W0613 
        '''
        Create node for if ... : ... else: ... statement.
        BNF:
        ifStatement = Group(kw('if') + boolExpression + ':'
                            + statementList
                            + Optional(kw('else') +':' + statementList)
                            + kw('end'))
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeIfStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #there must be the correct number of tokens
        if len(tokList) < 7 or (len(tokList)-7) % 4:
            raise Exception('Broken "if" statement! loc: '
                                       + str(nCurr.loc))
        #extract the interesting tokens
        for i in range(1, len(tokList)-4, 4):
            condition = tokList[i]
            condStmts = tokList[i+2]
            nCurr.kids.append(condition)
            nCurr.kids.append(condStmts)
        #else: last condition is always true
        elseCond = NodeFloat(None, nCurr.loc, '1')
        elseStmts = tokList[-1]
        nCurr.kids.append(elseCond)
        nCurr.kids.append(elseStmts)
        return nCurr


    def _actionAssignment(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for assignment: a = 2*b
        BNF:
        assignment = Group(valAccess + '=' + expression + ';')
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeAssignment()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #create children and store operator
        lhsTree = tokList[0]   #child lhs
#        nCurr.operator = '=' #operator
        rhsTree = tokList[2]   #child rhs
        nCurr.arguments = [lhsTree, rhsTree]
        return nCurr

    def _action_print_stmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for print statement:
            print 'hello', foo.x
        BNF:
        expression_list = delimitedList(expression, ',')            .setName('exprList')
        print_stmt = Group(kw('print')
                          - Optional(expression_list)               .setResultsName('arg_list')
                          + Optional(',')                           .setResultsName('trail_comma')                       
                          )                                         .setParseAction(self._action_print_stmt)\
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #Group adds 
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodePrintStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.arguments = toks.arg_list.asList()
        if toks.trailComma:
            nCurr.newline = False
        else:
            nCurr.newline = True
        return nCurr

    def _actionGraphStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for graph statement:
            graph foo.x, foo.p
        BNF:
        graphStmt = Group(kw('graph') + exprList  .setResultsName('argList')
                          + ';')                  .setParseAction(self._actionDebug)\
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeGraphStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.kids = toks.argList.asList()[0]
        return nCurr

    def _actionStoreStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for graph statement:
            graph foo.x, foo.p
        BNF:
        graphStmt = Group(kw('graph') + exprList  .setResultsName('argList')
                          + ';')                  .setParseAction(self._actionDebug)\
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeStoreStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.kids = toks.argList.asList()
        return nCurr

    def _action_return_stmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for return statement:
            return 2*a;
        BNF:
        return_stmt = (kw('return') - Optional(expression           .setResultsName('ret_val'))
                      )                                             .setParseAction(self._action_return_stmt) \
                                                                    .setFailAction(ChMsg(prepend='return statement: '))
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        nCurr = NodeReturnStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        if isinstance(toks.ret_val, Node):
            nCurr.arguments.append(toks.ret_val)
        return nCurr

    def _actionPragmaStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for pragma statement:
            pragma no flatten;
        BNF:
        pragmaStmt = (kw('pragma')
                      + ES(OneOrMore(Word(alphanums+'_')) + stmtEnd) .setErrMsgStart('Pragma statement: ')
                      )                                              #.setParseAction(self._actionPragmaStmt)
         '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        nCurr = NodePragmaStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        for i in range(1, len(toks)):
            nCurr.options.append(toks[i])
        return nCurr

#    def _actionForeignCodeStmt(self, s, loc, toks): #IGNORE:W0613
#        '''
#        Create node for foreign_code statement:
#            foreign_code python replace_call ::{{ sin(x) }}:: ;
#        BNF:
#        foreignCodeStmt = (kw('foreign_code')
#                           + ES(Word(alphanums+'_')                  .setResultsName('language')
#                                                                     .setName('language specification')
#                                + Word(alphanums+'_')                .setResultsName('method')
#                                                                     .setName('code insertion method')
#                                + QuotedString(quoteChar='::{{',
#                                               endQuoteChar='}}::')  .setResultsName('code')
#                                                                     .setName('code to insert')
#                                + stmtEnd)                           .setErrMsgStart('Foreign code statement: ')
#                           )                                         .setParseAction(self._actionForeignCodeStmt)
#         '''
#        if Parser.noTreeModification:
#            return None #No parse result modifications for debugging
#        nCurr = NodeForeignCodeStmt()
#        nCurr.loc = self.createTextLocation(loc) #Store position
#        nCurr.language = toks.language
#        nCurr.method = toks.method
#        nCurr.code = toks.code
#        return nCurr

    def _actionCompileStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for foreign_code statement:
            foreign_code python replace_call ::{{ sin(x) }}:: ;
        BNF:
        compileStmt = (kw('compile') + ES(
                          (dotIdentifier                             .setResultsName('className')
                           + stmtEnd
                           ) |
                          (identifier                                .setResultsName('name')
                           + ':' + dotIdentifier                     .setResultsName('className')
                           + stmtEnd)
                          )                                          .setErrMsgStart('compile statement: ')
                       )                                             .setParseAction(self._actionCompileStmt)\
         '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        nCurr = NodeCompileStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.className = DotName(toks.className)
        if toks.name:
            nCurr.name = toks.name
        return nCurr

    def _actionStatementList(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for list of statements: a=1; b=2; ...
        BNF:
        statementList << Group(OneOrMore(statement))
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeStmtList()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #create children - each child is a statement
        for tok in tokList:
            nCurr.kids.append(tok)
        return nCurr


    def _action_data_def(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for defining parameter, variable or submodel:
            'data foo, bar: baz.boo parameter;
        One such statement can define multiple parmeters; and an individual
        NodeDataDef is created for each. They are returned together inside a
        list node of type NodeStmtList.
        BNF:
        newAttrList = delimitedList(newIdentifier)   
        data_stmt = Group(kw('data')
                          - newAttrList                             .setResultsName('attr_name_list')
                          + ':' + expression                        .setResultsName('class_name')
                          + Optional(attrRole)                      .setResultsName('attr_role')
                          + Optional('=' - expression               .setResultsName('default_value')
                                     )                              .setFailAction(ChMsg(prepend='default value: '))
                          )                                         .setParseAction(self._action_data_def)\
         '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        #multiple attributes can be defined in a single statement
        #Create a node for each of them and put them into a special statement list
        attrDefList = NodeDataDefList()
        attrDefList.loc = self.createTextLocation(loc)
        nameList = toks.attr_name_list.asList()
        for name in nameList:
            attrDef = NodeDataDef()
            attrDef.loc = self.createTextLocation(loc)
            attrDef.name = DotName(name) #store attribute name
            attrDef.class_name = toks.class_name #.name #toks.class_name is NodeIdenifier
            #map role string to role object, and store the role
            #If role is not specified RoleVariable is assumed.
            #Submodels will be labeled variables even though these categories don't apply to them.
            roleDict = {'const':RoleConstant, 'param':RoleParameter, 'variable':RoleVariable,
                        'algebraic_variable':RoleAlgebraicVariable,
                        'state_variable':RoleStateVariable}
            attrDef.role = roleDict.get(toks.attr_role, None)
            #store the default value
            if isinstance(toks.default_value, Node):
                attrDef.default_value = toks.default_value
                raise UserException('Default values are currently unsupported!',
                                    self.createTextLocation(loc))
            #store the attribute definition in the list
            attrDefList.statements.append(attrDef)
        #Special case: only one attribute defined
        if len(attrDefList.statements) == 1:
            return attrDefList.statements[0] #take it out of the list and return it
        else:
            return attrDefList #return list with multiple definitions


    def _action_slicing(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for slicing operation.
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debuging
        raise UserException('Slicing is currently unsupported!',
                            self.createTextLocation(loc))


#    def _action_func_call_arg(self, s, loc, toks): #IGNORE:W0613
#        '''
#        Create node for one argument of a function call.
#            x=2.5  ,  x*2+sin(a)
#        Node types are: either a mathematical expression, or an assignment.
#        BNF:
#        call_argument = ( Group(identifier                         .setResultsName('keyword')
#                                + '=' + expression                 .setResultsName('value')
#                                )                                  .setResultsName('keyword_argument')
#                        | Group(expression)                        .setResultsName('positional_argument')
#                        )                                          .setParseAction(self._action_func_call_arg)
#        '''
#        if Parser.noTreeModification:
#            return None #No parse result modifications for debuging
#        #named argument: x=2.5
#        if toks.keyword_argument:
#            #TODO:Should a new node NodeNamedArg be introduced? A named argument is
#            # not really an assignment. Making it an assignment may break the
#            # attribute renaming algorithm.
#            raise UserException('Keyword arguments are currently unsupported!',
#                                self.createTextLocation(loc))
#        #positional argument: 2.5
#        elif toks.positional_argument:
#            nCurr = toks.positionalArg[0]
#        else:
#            raise ParseActionException('Broken function argument. ' +
#                                        str(self.createTextLocation(loc)) + ' ' +
#                                        str(toks))
#        return nCurr

    def _action_func_call(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for calling a function or method.
            bar.doFoo(10, x, a=2.5)
        BNF:
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debuging
        toks = toks[0] #remove extra bracket of group
        nCurr = NodeFuncCall() 
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store function name
        nCurr.name = toks[0]
        #check argument list - positional arguments must come before keyword arguments
        there_was_keyword_argument = False
        #store function arguments:
        for arg in toks[1].argument_list:
            if arg.positional_argument:
                if there_was_keyword_argument:
                    raise UserException('Positional arguments must come before keyword arguments!',
                                        nCurr.loc)
                nCurr.arguments.append(arg.positional_argument[0][0])
            elif arg.keyword_argument:
                there_was_keyword_argument = True
#                print 'arg.keyword_argument: ', arg.keyword_argument
                #TODO: store keyword arguments too
                raise UserException('Keyword arguments are currently unimplemented!',
                                     nCurr.loc)
        return nCurr


    def _action_func_def_arg(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for one function argument of a function definition.
        A NodeDataDef is created; therefore this method is quite similar
        to _action_data_def.
        BNF:
        func_def_arg = Group(identifier                             .setResultsName('name')
                           + Optional(':' - expression              .setResultsName('type')
                                      )                             .setFailAction(ChMsg(prepend='type specifier: '))
                           + Optional('=' - expression              .setResultsName('default_value')
                                      )                             .setFailAction(ChMsg(prepend='default value: '))
                           )                                        .setParseAction(self._action_func_def_arg)
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeFuncArg()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store argument name
        nCurr.name = DotName(toks.name.name)
        #store optional type of argument
        if toks.type:
            nCurr.type = toks.type
            raise UserException('Type specifications are not yet supported!', 
                                nCurr.loc)
        #store optional default value
        if toks.default_value:
            nCurr.default_value = toks.default_value
            raise UserException('Default values are not yet supported!', 
                                nCurr.loc)
        return nCurr


    def _action_func_def(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for definition of a function or method.
            func doFoo(a:Real=2.5, b) -> Real: {... }
        BNF:
        func_def_arg_list = (delimitedList(func_def_arg, ',')
                             + Optional(','))                
        #the function: func doFoo(a:Real=2.5, b) -> Real {...}
        func_def_stmt = Group(kw('func') - newIdentifier            .setResultsName('func_name')
                        + ('(' - Optional(func_def_arg_list         .setResultsName('arg_list'))
                           + ')' )                                  .setFailAction(ChMsg(prepend='argument list: '))
                        + Optional('->' - expression                .setResultsName('return_type')
                                   )                                .setFailAction(ChMsg(prepend='return type: : '))
                        + ':'
                        + suite                                     .setResultsName('func_body')
                        )                                           .setParseAction(self._action_func_def) \
                                                                    .setFailAction(ChMsg(prepend='function definition: ')) \
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #Group adds
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeFuncDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store function name
        nCurr.name = DotName(toks.func_name)
        #store function arguments: statement list of 'data' statements
        nCurr.arguments = toks.arg_list.asList()
        #check argument list - arguments with default values must come last!
        #TODO: put keyword arguments into keyword_argument list
        #TODO: put complete algorithm into separate function: it is used in _action_class_def too!
        thereWasKeywordArgument = False
        for arg in nCurr.arguments:
            if arg.default_value is not None:
                thereWasKeywordArgument = True
            elif thereWasKeywordArgument:
                raise UserException('Positional arguments must come first!',
                                    nCurr.loc)
        #store return type
        if toks.return_type:
            nCurr.return_type = toks.return_type
        #store function body; take each statement out of its sublist
        for sublist in toks.func_body:
            nCurr.statements.append(sublist[0])
        return nCurr


    def _action_class_def(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for definition of a class:
            class foo(a):
                inherit Model
                data myA: Real = a
            
        BNF:
        class_stmt = Group(kw('class')
                         - newIdentifier                            .setResultsName('classname')
                         + Optional('(' - argument_list + ')' )     .setFailAction(ChMsg(prepend='constructor arguments: '))
                         + ':' + suite                              .setResultsName('class_body_stmts')
                         )                                          .setParseAction(self._action_class_def)\
                                                                    .setFailAction(ChMsg(prepend='class definition: '))
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #the Group creates
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeClassDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store class name and name of super class
        nCurr.name = DotName(toks.classname)
        #store function arguments: statement list of 'data' statements
        if toks.arg_list:
            nCurr.arguments = toks.arg_list.asList()
        #store class body; take each statement out of its sublist 
        for sublist in toks.class_body_stmts:
            nCurr.statements.append(sublist[0])
        return nCurr


    def _action_module(self, s, loc, toks): #IGNORE:W0613
        '''
        Create the root node of a module.
        BNF:
        module = (indentedBlock(statement, self.indentStack, indent=False) 
                  + StringEnd())                                      .setParseAction(self._action_module)
        '''
        if Parser.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] 
        nCurr = NodeModule()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.name = self.moduleName
        #take the sublists out of the nested lists that indentedBlock produces
        statements = []
        for sublist in tokList:
            statements.append(sublist[0])
        nCurr.statements = statements
        return nCurr 


#------------------- BNF ------------------------------------------------------------------------*
    def _defineLanguageSyntax(self):
        '''
        Here is Siml's BNF
        Creates the objects of the pyParsing library,
        that do all the work.
        '''
        #define short alias so they don't clutter the text
        kw = self.defineKeyword # Usage: test = kw('variable')
        L = Literal # Usage: L('+')
        S = Suppress

        #end of line terminates statements, so it is not regular whitespace
        ParserElement.setDefaultWhitespaceChars('\t ')
        #the matching end of line token 
        newline = LineEnd().suppress()
        
#------------------ Literals .................................................................

        #Integer (unsigned).
        uInteger = Word(nums)                                       .setName('uInteger')#.setDebug(True)
        #Floating point number (unsigned).
        eE = CaselessLiteral( 'E' )
        uFloat = Group( Combine(
                    uInteger +
                    Optional('.' + Optional(uInteger)) +
                    Optional(eE + Word('+-'+nums, nums))))          .setParseAction(self._action_number)\
                                                                    .setName('uFloat')#.setDebug(True)
        #string
        #TODO: good error message for missing 2nd quote in single line string
        stringLiteral = quotedString                                .setParseAction(self._action_string)\
                                                                    .setName('string')#.setDebug(True)
        literal = uFloat | stringLiteral

#------------------ Identifiers .................................................................

        #Built in variables, handled specially at attribute access.
        #kw('time'); kw('this')
        Parser.builtInVars = set(['time', 'this', 'diff', 'Unit'])
        #identifiers
        identifierBase = Word(alphas+'_', alphanums+'_')            .setName('identifier')#.setDebug(True)
        # identifier:    Should be used in expressions. If a keyword is used an ordinary parse error is
        #                raised. This is needed to parse expressions containing the operators 'and', 'or', 'not'.
        identifier  = Group(identifierBase.copy()                   .setParseAction(self._actionCheckIdentifier)
                            )                                       .setParseAction(self._action_identifier)
        # newIdentifier: Should be used in definition of new objects (data, class, function).
        #                If a keyword is used as a identifier a fatal, user visible error is raised.
        newIdentifier = identifierBase.copy()                       .setParseAction(self._actionCheckIdentifierFatal)

#------------------ Mathematical expression .............................................................
        #Expression: mathematical, logtical, and comparison operators;
        # together with attribute access, function call, and slicing.
        #Forward declaration for recursive top level rule 
        expression = Forward()

        #Atoms are the most basic elements of expressions.
        #Brackets or braces are also categorized syntactically as atoms.
        #TODO: future extension: enclosures can also create tuples
        enclosure = S('(') + expression + S(')')                    .setParseAction(self._action_parentheses_pair)
        atom = identifier | literal | enclosure
      
        #Function/method call: everything within the round brackets is parsed here;
        # the function name is parsed in 'expression'. This parser is quite general;
        # more syntax checks are done in parse action to generate better error messages.
        #
        #one argument at the call site: x=2.5  ,  x  ,  2.5
        keyword_argument = Group(identifier                         #.setResultsName('keyword')
                                 + '=' - expression                 #.setResultsName('value')
                                 )                                  .setResultsName('keyword_argument', listAllMatches=True)
        positional_argument = Group(expression)                     .setResultsName('positional_argument', listAllMatches=True)
        call_argument = Group(keyword_argument | positional_argument) #extra group to make setResultsName work
        argument_list = ( delimitedList(call_argument)              .setResultsName('argument_list')
                          + Optional(',') )
        call = Group('(' - Optional(argument_list) + ')') #TODO: Error message 'Function arguments: '

        #Slicing/subscription: everything within the rectangular brackets is parsed here;
        # the variable name is parsed in 'expression'
        #Look at Python documentation for possibly better parser.
        proper_slice = Group(Optional(expression) + L(':') + Optional(expression)
                             + Optional(L(':') + Optional(expression)))
        ellipsis = L('...')
        slice_item = ellipsis | proper_slice | expression
        slice_list = delimitedList(slice_item) + Optional(S(','))
        slicing = Group(S('[') - slice_list + S(']'))

        #attribute access, function call, and slicing. (operators with the strongest binding come first.)
        expression_ex = operatorPrecedence(atom,
             #TODO: special node and parse action for attribute lookup
            [(L('.'),       2, opAssoc.LEFT,             self._action_op_infix_left), #access to an object's attributes
             #TODO: special node and parse action for differential operator
             (L('$'),       1, opAssoc.RIGHT,            self._action_op_prefix), #time differential
             (call,         1, opAssoc.LEFT,             self._action_func_call), #function/method call: f(23)
             (slicing,      1, opAssoc.LEFT,             self._action_slicing), #slicing/subscription: a[23]
             ])                                                     .setName('expression_ex')

        #Power and unary (sign) operators are intertwined, to get correct operator precedence:
        #   -a**-b == -(a ** (-b))
        # This can currently (of Pyparsing 1.5.0) not be expressed by operatorPrecedence
        power,  u_expr = Forward(), Forward()
        #Exponentiation: a**b;
        #Strongest binding on left side, weaker than unary operations (-a) on right side.
        power1 = Group(expression_ex + '**' + u_expr)               .setParseAction(self._action_op_infix)
        power << (power1 | expression_ex)
        #Unary arithmetic operations: -a; +a
        u_expr1 = Group(oneOf('- +') + u_expr)                      .setParseAction(self._action_op_prefix)
        u_expr << (u_expr1 | power)             
             
        #arithmetic, logtical, and comparison operators; the top level parser
        expression << operatorPrecedence(u_expr, 
            [(oneOf('* /'), 2, opAssoc.LEFT,             self._action_op_infix_left),
             (oneOf('+ -'), 2, opAssoc.LEFT,             self._action_op_infix_left),
             (oneOf('< > <= >= == !='), 2, opAssoc.LEFT, self._action_op_infix_left),
             (kw('not'),    1, opAssoc.RIGHT,            self._action_op_prefix),
             (kw('and'),    2, opAssoc.LEFT,             self._action_op_infix_left),
             (kw('or'),     2, opAssoc.LEFT,             self._action_op_infix_left),
             ])                                                     .setName('expression')

#------------------- STATEMEMTS -------------------------------------------------------------------------*
#------------------- Simple statements ..................................................................

#        #execute a class method (or a function) -
#        #usually inserts the function bodie's code into the current method.
#        #This code insertion (inlinig) is done recursively and leaves only
#        #a few big top level methods
#        funcCall = Forward() #TODO: REMOVE!!!
#        funcCallStmt = funcCall + ES(stmtEnd)                        .setErrMsgStart('call statement: ')

        #Return values from a function 
        return_stmt = (kw('return') - Optional(expression           .setResultsName('ret_val'))
                      )                                             .setParseAction(self._action_return_stmt) \
                                                                    .setFailAction(ChMsg(prepend='return statement: '))

        #pragma statement: tell any kind of options to the compiler
        pragma_stmt = (kw('pragma') 
                       - OneOrMore(Word(alphanums+'_')))            .setParseAction(self._actionPragmaStmt) \
                                                                    .setFailAction(ChMsg(prepend='pragma statement: '))

#        #foreign code statement: specify code in the target language that is
#        #inserted into the compiled module
#        #    foreign_code python replace_call ::{{ sin(x) }}:: ;
#        foreignCodeStmt = (kw('foreign_code')
#                           + ES(Word(alphanums+'_')                  .setResultsName('language')
#                                                                     .setName('language specification')
#                                + Word(alphanums+'_')                .setResultsName('method')
#                                                                     .setName('code insertion method')
#                                + QuotedString(quoteChar='::{{',
#                                               endQuoteChar='}}::')  .setResultsName('code')
#                                                                     .setName('code to insert')
#                                + stmtEnd)                           .setErrMsgStart('Foreign code statement: ')
#                           )                                         .setParseAction(self._actionForeignCodeStmt)

        #expression list - parse: 2, foo.bar, 3*sin(baz)
        expression_list = delimitedList(expression, ',')            .setName('exprList')
        #print something to stdout
        print_stmt = Group(kw('print')
                          - Optional(expression_list)               .setResultsName('arg_list')
                          + Optional(',')                           .setResultsName('trail_comma')                       
                          )                                         .setParseAction(self._action_print_stmt)\
                                                                    .setFailAction(ChMsg(prepend='print statement: '))
        #show graphs
        graph_stmt = Group(kw('graph') - expression_list            .setResultsName('arg_list')
                           - Optional(','))                         .setParseAction(self._actionGraphStmt)\
                                                                    .setFailAction(ChMsg(prepend='graph statement: '))
        #store to disk
        store_stmt = Group(kw('save') - expression_list             .setResultsName('arg_list')
                          - Optional(','))                          .setParseAction(self._actionStoreStmt)\
                                                                    .setFailAction(ChMsg(prepend='save statement: '))

        #compile a class
        compile_stmt = (kw('compile') 
                        - Optional(identifier                       .setResultsName('name')
                                   + ':') 
                        + expression                                .setResultsName('class_name')
                        )                                           .setParseAction(self._actionCompileStmt)\
                                                                    .setFailAction(ChMsg(prepend='compile statement: '))

        #compute expression and assign to value
        assign_stmt = Group(expression_ex + '=' - expression)       .setParseAction(self._actionAssignment)\
                                                                    .setFailAction(ChMsg(prepend='assignment statement: '))

        #------------ data statemnt -------------------------------------------------------------------------
        #define parameters, variables, constants and submodels
        #TODO: add 'save' - 'no_save' keywords 
        #The roles of data (maybe call it storage class?):
        #variable:    changes during the simulation
        #parameter:   constant during a (dynamic?) simulation, can change beween simulations,
        #             can be computed in the init function.
        #constant:    must be known at compile time, may be optimized away,
        #             the compiler may generate special code depending on the value.
        #TODO: maybe add role for automatically created variables
        attrRole = (  kw('state_variable') | kw('algebraic_variable') 
                    | kw('variable') | kw('param') | kw('const')      )
        #parse: 'foo, bar, baz
        newAttrList = delimitedList(newIdentifier)         
        #parse 'data foo, bar: baz.boo parameter;
        data_stmt = Group(kw('data')
                          - newAttrList                             .setResultsName('attr_name_list')
                          + ':' + expression                        .setResultsName('class_name')
                          + Optional(attrRole)                      .setResultsName('attr_role')
                          + Optional('=' - expression               .setResultsName('default_value')
                                     )                              .setFailAction(ChMsg(prepend='default value: '))
                          )                                         .setParseAction(self._action_data_def)\
                                                                    .setFailAction(ChMsg(prepend='data definition: '))
                                                                   
        simple_stmt = (data_stmt| print_stmt | return_stmt |
                       pragma_stmt |store_stmt | graph_stmt |                                    #IGNORE:W0104
                       compile_stmt | assign_stmt )                 .setName('simple statement')

#------------- Compound statements ............................................................................
        #body of compound statements
        suite = Forward()
        
        #------------- if ...........................................................................................
        #Flow control - if then else
        if_stmt = \
            Group(kw('if') - expression + ':' + suite
                  + ZeroOrMore(kw('elif') - expression + ':' + suite) .setFailAction(ChMsg(prepend='elif: '))
                  + Optional(  kw('else') - ':' + suite)            .setFailAction(ChMsg(prepend='else: '))
                  )                                                 .setParseAction(self._actionIfStatement) \
                                                                    .setFailAction(ChMsg(prepend='if statement: ')) \
                                                                    .setName('if statement')
        
        #------------- Function / Method ............................................................................
        #Function definition (class method or global function)
        #one argument of the definition: inX:Real=2.5
        func_def_arg = Group(identifier                             .setResultsName('name')
                           + Optional(':' - expression              .setResultsName('type')
                                      )                             .setFailAction(ChMsg(prepend='type specifier: '))
                           + Optional('=' - expression              .setResultsName('default_value')
                                      )                             .setFailAction(ChMsg(prepend='default value: '))
                           )                                        .setParseAction(self._action_func_def_arg)
        func_def_arg_list = (delimitedList(func_def_arg, ',')
                             + Optional(','))
        #the function: func doFoo(a:Real=2.5, b) -> Real {...}
        func_def_stmt = Group(kw('func') - newIdentifier            .setResultsName('func_name')
                        + ('(' - Optional(func_def_arg_list         .setResultsName('arg_list'))
                           + ')' )                                  .setFailAction(ChMsg(prepend='argument list: '))
                        + Optional('->' - expression                .setResultsName('return_type')
                                   )                                .setFailAction(ChMsg(prepend='return type: : '))
                        + ':'
                        + suite                                     .setResultsName('func_body')
                        )                                           .setParseAction(self._action_func_def) \
                                                                    .setFailAction(ChMsg(prepend='function definition: ')) \
                                                                    .setName('function definition')#.setDebug(True)

        #---------- class  ......................................................................
        #definition of a class 
        #TODO: "inherit" statement
        class_stmt = Group(kw('class')
                           - newIdentifier                          .setResultsName('classname')
                           + Optional('(' - func_def_arg_list       .setResultsName('arg_list')
                                      + ')' )                       .setFailAction(ChMsg(prepend='constructor arguments: '))
                           + ':' + suite                            .setResultsName('class_body_stmts')
                           )                                        .setParseAction(self._action_class_def)\
                                                                    .setFailAction(ChMsg(prepend='class definition: '))
                                      
        
        compound_stmt = (class_stmt | func_def_stmt | if_stmt)
        
        
        #------ Statement, Suite -------------------------------------------------------------------------
        # See: http://docs.python.org/ref/compound.html
        #list of simple statements, separated by semicolon: a=1; b=2; print a, b
        stmt_list = Group(delimitedList(Group(simple_stmt), ';') 
                     + Optional(Suppress(";")) )                    #.setParseAction(self._actionStatementList)
        #Statement: one line of code, or a compound (if, class, func) statement
        statement = (  simple_stmt + newline 
                     | stmt_list + newline 
                     | compound_stmt         )
        #And indented block of statements
        stmt_block = indentedBlock(statement, self.indentStack)     #.setParseAction(self._actionStatementList)
        #Body of class or function; the dependent code of 'if'
        # Statement list and indented block of statements lead to the same AST
        suite << ( stmt_list + newline | newline + stmt_block )                                                
        
#        #simple definition for debuging
#        #simple statements are terminated by newline
#        #while the indented block eats all newlines after the compound statement
#        statement = simple_stmt + newline | compound_stmt 
#        #a suite is an indented block of statements
#        suite << indentedBlock(statement, self.indentStack)
        
#---------- module ------------------------------------------------------------------------------------#
        module = (indentedBlock(statement, self.indentStack, indent=False) 
                  + StringEnd())                                      .setParseAction(self._action_module)
        
        #workaround for pyparsing bug ???         
#        module = (ZeroOrMore(newline) 
#                  + ZeroOrMore(Group(statement) + ZeroOrMore(newline)) 
#                  + StringEnd())
        #................ End of language definition ..................................................

        #determine start symbol
        startSymbol = module
        #set up comments
        singleLineCommentCpp = '//' + restOfLine
        singleLineCommentPy = '#' + restOfLine
        startSymbol.ignore(singleLineCommentCpp)
        startSymbol.ignore(singleLineCommentPy)
        #no tab expansion
        startSymbol.parseWithTabs()
        #store parsers
        self._parser = startSymbol
        self._expressionParser = expression


    def parseExpressionStr(self, inString):
        '''Parse a single expression. Example: 2*a+b'''
        self.inputString = inString
        return self._expressionParser.parseString(inString).asList()[0]


    def parseModuleStr(self, inProgram, fileName=None, moduleName=None):
        '''
        Parse a whole program. The program is entered as a string.

        Parameters
        ----------
        inProgram : str
            A program in the Siml language. This might also be a module.
        fileName : str
            File name, so that good error messages can be generated.

        Returns
        -------
        parse tree : ast.Node
            The parse tree of the program.
        '''
        self.inputString = inProgram
        if fileName is not None:
            self.progFileName = fileName
        if moduleName is not None:
            self.moduleName = moduleName
        #initialize the indentation stack (just to be sure)
        self.indentStack = [1]
        #parse the program
        try:
            astTree = self._parser.parseString(inProgram).asList()[0]
        except (ParseException, ParseFatalException), theError:
            #make UserException that will be visible to the user
            msgPyParsing = str(theError)
            loc =  TextLocation(theError.loc, theError.pstr, self.progFileName)
            raise UserException(msgPyParsing, loc)
        return astTree


    def parseModuleFile(self, fileName, moduleName=None):
        '''Parse a whole program. The program's file name is supplied.'''
        self.progFileName = os.path.abspath(fileName)
        #TODO: deduce from file name?
        self.moduleName = moduleName
        #open and read the file
        try:
            inputFile = open(self.progFileName, 'r')
            inputFileContents = inputFile.read()
            inputFile.close()
        except IOError, theError:
            message = 'Could not read input file.\n' + str(theError)
            raise UserException(message, None)
        #parse the program
        return self.parseModuleStr(inputFileContents)



def doTests():
    '''Perform various tests.'''

    print 'doing tests ...'
    #t1 = Node('root', [Node('child1',[]),Node('child2',[])])
    #print t1

#------------ testProg1 -----------------------
    testProg1 = (
'''
class Test(Model):
{
    data V, h: Real;
    data A_bott, A_o, mu, q, g: Real param;

    func dynamic():
    {
        h = V/A_bott;
        $V = q - mu*A_o*sqrt(2*g*h);
        print 'h: ', h,;
    }

    func init():
    {
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
        q = 0.05;
    }
}

class RunTest(Process):
{
    data g: Real param;
    data test: Test;

    func dynamic():
    {
        test.dynamic();
    }

    func init():
    {
        g = 9.81;
        test.init();
        solutionParameters.simulationTime = 100;
        solutionParameters.reportingInterval = 1;
    }

    func final():
    {
        #store;
        graph test.V, test.h;
        print 'Simulation finished successfully.';
    }
}

compile RunTest;
compile run1: RunTest;
''' )

#------------ testProg2 -----------------------
    testProg2 = (
'''
class RunTest(Process):
{
    data test: Real;
    data a,b: Real const = sin(3*pi);

    func foo(a:real, b:Real=2):
    {
        foo.bar(2, x );
        a=foo.bar(2)+time;
        return 2;
        pragma no_flatten;
        foreign_code python replace_call
        ::{{ sin(x) }}:: ;
    }
}
''')

    #test the parser ----------------------------------------------------------------------
    do_test = True
    do_test = False
    if do_test:
        parser = Parser()
        Parser.noTreeModification = 1

        print 'keywords:'
        print parser.keywords

        print parser.parseModuleStr(testProg1)
        #print parser.parseModuleStr(testProg2)

    do_test = True
    do_test = False
    if do_test:
        parser = Parser()
        #Parser.noTreeModification = 1

        print 'keywords:'
        print parser.keywords

#        print parser.parseExpressionStr('qwert99')
#        print parser.parseExpressionStr('\'qwert99\'')
#        print parser.parseExpressionStr('99')
#        print parser.parseExpressionStr('0.123e99')
#        print parser.parseExpressionStr('0*1*2*3*4*99')
#        print parser.parseExpressionStr('0**1**2**3**4**99')
#        print parser.parseExpressionStr('a.b.c')
        print parser.parseExpressionStr('0+1*2+3+4-99')
#        print parser.parseExpressionStr('-0+1+--2*-3--4')
#        print parser.parseExpressionStr('0+a1.a2+b1.b2.b3*3+99 #comment')
#        print parser.parseExpressionStr('a(1, 3, )')
#        print parser.parseExpressionStr('a.b.c(1, d.e)')
#        print parser.parseExpressionStr('0.123+1.2e3')

    do_test = True
#    do_test = False
# ---------- test -------------
    if do_test:
        parser = Parser()
#        Parser.noTreeModification = 1

        print 'keywords:'
        print parser.keywords


        prog = \
'''
print 'start'
print 'end'
'''
        print prog
        print parser.parseModuleStr(prog)
        print 
        
        prog = \
"""
print 'start'

func foo(a, b):
    print a, b
    
class A(a, b):
    data a1: Float
    data a2: Float

data a: A(1)
data b: A

print 'end'
"""
        print prog
        print parser.parseModuleStr(prog)
        print 

    print 'tests finished'


if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #TODO: add doctest tests. With doctest tests are embedded in the documentation
        
    #profile the tests
#    import cProfile
#    cProfile.run('doTests()')
    
    #run tests normally
    doTests()
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
