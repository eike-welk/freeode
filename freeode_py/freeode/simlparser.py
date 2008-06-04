# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration came from:                                                *
#    'fourFn.py', an example program, by Paul McGuire,                     *
#    and the 'Spark' library by John Aycock.                               *
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

'''
Parser for the SIML simulation language.
'''

#TODO: write unit tests that exercise every error message of simlparser.py

from __future__ import division


#import debugger
#import pdb
#import operation system stuff
#import sys
import os
#import parser library
import pyparsing
from pyparsing import ( _ustr, Literal, CaselessLiteral, Keyword, Word,
    ZeroOrMore, OneOrMore, Forward, nums, alphas, alphanums, restOfLine,
    delimitedList, QuotedString,
    StringEnd, sglQuotedString, MatchFirst, Combine, Group, Optional,
    ParseException, ParseFatalException, ParseElementEnhance )
#import our own syntax tree classes
from freeode.ast import *

 

#Enable a fast parsing mode with caching. May not always work.
pyparsing.ParserElement.enablePackrat()



#Took code from pyparsing.Optional as a template
class ErrStop(ParseElementEnhance):
    """Parser that prevents backtracking.
       The parser tries to match the given expression (which consists of other
       parsers). If this expression does not match the parser raises a
       ParseFatalException and parsing stops.
       Otherwise, if the given expression matches, its parse results are returned
       and the ErrStop has no effect on the parse results.
       
       TODO: usage
    """

    def __init__(self, expr):
        super(ErrStop, self).__init__(expr, savelist=False)
        self.mayReturnEmpty = True
        #Additional string, that will be put in front of the error message.
        self.errMsgStart = ''

    def parseImpl(self, instring, loc, doActions=True):
        try:
            loc, tokens = self.expr._parse(instring, loc, doActions, callPreParse=False)
        except IndexError:
            raise ParseFatalException(instring, loc, 'Index error: ', self.expr)
        except ParseException, theError:
            errMsg = self.errMsgStart + theError.msg
            raise ParseFatalException(instring, theError.loc, errMsg, self.expr)
        return loc, tokens

    def setErrMsgStart(self, msg):
        """Set additional error message.
           This string will be put in front of the error message of the given
           parser.
        """
        self.errMsgStart = msg
        return self

    def __str__(self):
        if hasattr(self,"name"):
            return self.name

        if self.strRepr is None:
            self.strRepr = "[" + _ustr(self.expr) + "]"

        return self.strRepr



class ParseActionException(Exception):
    '''Exception raised by the parse actions of the parser'''
    pass



class ParseStage(object):
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
    parser = ParseStage()
    ast1 = parser.parseExpressionStr('0+1+2+3+4')
    ast2 = parser.parseModuleFile('foo-bar.siml')
    '''

    noTreeModification = 0
    '''
    Define how much the parse result is modified, for easier debuging.
    0: normal operation. Compilation does not work otherwise.
    1: Do not modify parse result (from pyParsing library).

    ParseResult objects are printed as nested lists: ['1', '+', ['2', '*', '3']]
    '''

    keywords = set()
    '''
    List of all keywords (filled by _defineLanguageSyntax() and defineKeyword(...)).
    '''
    #Special variables, that are built into the language (filled by _defineLanguageSyntax())
    builtInVars = set()


    def __init__(self):
        object.__init__(self)
        self._parser = None
        '''The parser object for the whole program (from pyParsing).'''
        self._expressionParser = None
        '''The parser for expressions'''
        self.progFileName = None
        '''Name of SIML program file, that will be parsed'''
        #name, that will be given to the root node of a module
        #usually part of the filename
        self.moduleName = None
        self.inputString = None
        '''String that will be parsed'''
        #Create parser objects
        self._defineLanguageSyntax()


    def defineKeyword(self, inString):
        '''
        Store keyword (in ParseStage.keywords) and create parser for it.
        Use this function (in _defineLanguageSyntax(...)) instead of using the
        Keyword class directly.
        '''
        ParseStage.keywords.add(inString)
        return Keyword(inString)


    def createTextLocation(self, atChar):
        '''Create a text location object at the given char'''
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
        identier = tokList[0]
        if identier in ParseStage.keywords:
            #print 'found keyword', toks[0], 'at loc: ', loc
            errMsg = 'Keyword can not be used as an identifier: ' + identier
            raise ParseException(s, loc, errMsg)


#    def _actionStoreStmtLoc(self, str, loc, toks):
#        '''
#        Remember location of last parsed statement. Useful for error
#        error message creation, since the locations of pyparsing's
#        syntax errors are frequently quite off.
#        '''
#        self._locLastStmt = self.createTextLocation(loc)


#    def _actionBuiltInValue(self, str, loc, toks):
#        '''
#        Create AST node for a built in value: pi, time
#        tokList has the following structure:
#        [<identifier>]
#        '''
#        if ParseStage.noTreeModification:
#            return None #No parse result modifications for debugging
#        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
#        #create AST node
#        nCurr = NodeBuiltInVal()
#        nCurr.loc = self.createTextLocation(loc) #Store position
#        nCurr.dat = tokList #Store the built in value's name
#        return nCurr


    def _actionNumber(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for a number: 5.23
        tokList has the following structure:
        [<number>]
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeNum()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.dat = tokList[0] #Store the number
        return nCurr


    def _actionString(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for a string: 'qwert'
        tokList has the following structure:
        [<string>]
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeString()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #nCurr.dat = tokList #Store the string
        nCurr.dat = tokList[1:-1] #Store the string; remove quotes
        return nCurr


    def _actionParenthesesPair(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for a pair of parentheses that enclose an expression: (...)
        tokList has the following structure:
        ['(', <expression>, ')']
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeParentheses()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.kids = [tokList[1]] #store child expression
        return nCurr


    def _actionPrefixOp(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for math prefix operators: -
        tokList has the following structure:
        [<operator>, <expression_l>]
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeOpPrefix1()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.operator = tokList[0]  #Store operator
        nCurr.kids=[tokList[1]] #Store child tree
        return nCurr


    def _actionInfixOp(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for math infix operators: + - * / ^
        tokList has the following structure:
        [<expression_l>, <operator>, <expression_r>]
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeOpInfix2()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #create children and store operator
        lhsTree = tokList[0]   #child lhs
        nCurr.operator = tokList[1] #operator
        rhsTree = tokList[2]   #child rhs
        nCurr.kids=[lhsTree, rhsTree]
        return nCurr


    def _actionAttributeAccess(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for access to a variable or parameter: bb.ccc.dd
        tokList has the following structure:
        [<part1>, <part2>, <part3>, ...]
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeAttrAccess()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #Look if there is a '$' that indicates time derivatives
        if tokList[0] == '$':
            nCurr.deriv = ('time',)
            del tokList[0]
        #The remaining tokens are the dot separated name
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
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeIfStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #there must be the correct number of tokens
        if len(tokList) < 7 or (len(tokList)-7) % 4: 
            raise ParseActionException('Broken "if" statement! loc: ' 
                                       + str(nCurr.loc))
        #extract the interesting tokens 
        for i in range(1, len(tokList)-4, 4):
            condition = tokList[i]
            condStmts = tokList[i+2]
            nCurr.kids.append(condition)
            nCurr.kids.append(condStmts)
        elseStmts = tokList[-1]
        nCurr.kids.append(elseStmts)
        return nCurr


    def _actionAssignment(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for assignment: a = 2*b
        BNF:
        assignment = Group(valAccess + '=' + expression + ';')
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeAssignment()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #create children and store operator
        lhsTree = tokList[0]   #child lhs
        nCurr.operator = tokList[1] #operator
        rhsTree = tokList[2]   #child rhs
        nCurr.kids=[lhsTree, rhsTree]
        return nCurr


    def _actionPrintStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for print statement:
            print 'hello', foo.x
        BNF:
        printStmt = Group(kw('print') + exprList  .setResultsName('argList')
                          + Optional(',')         .setResultsName('trailComma')
                          + ';')                  .setParseAction(self._actionPrintStmt)\
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodePrintStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.kids = toks.argList.asList()[0]
        if toks.trailComma:
            nCurr.newline = False
        return nCurr


    def _actionGraphStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for graph statement:
            graph foo.x, foo.p
        BNF:
        graphStmt = Group(kw('graph') + exprList  .setResultsName('argList')
                          + ';')                  .setParseAction(self._actionDebug)\
        '''
        if ParseStage.noTreeModification:
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
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeStoreStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.kids = toks.argList.asList()
        return nCurr


    def _actionReturnStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for return statement:
            return 2*a;
        BNF:
        returnStmt = (kw('return') + ES(Optional(expression          .setResultsName('retVal')) 
                                        + stmtEnd)                   .setErrMsgStart('Return statement: ')
                      )                                              .setParseAction(self._actionReturnStmt)
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        nCurr = NodeReturnStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        if isinstance(toks.retVal, Node):
            nCurr.appendChild(toks.retVal)
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
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        nCurr = NodePragmaStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        for i in range(1, len(toks)):
            nCurr.options.append(toks[i])
        return nCurr


    def _actionForeignCodeStmt(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for foreign_code statement:
            foreign_code python replace_call ::{{ sin(x) }}:: ;
        BNF:
        foreignCodeStmt = (kw('foreign_code') 
                           + ES(Word(alphanums+'_')                  .setResultsName('language')
                                                                     .setName('language specification')
                                + Word(alphanums+'_')                .setResultsName('method')
                                                                     .setName('code insertion method')
                                + QuotedString(quoteChar='::{{', 
                                               endQuoteChar='}}::')  .setResultsName('code')
                                                                     .setName('code to insert')
                                + stmtEnd)                           .setErrMsgStart('Foreign code statement: ')
                           )                                         .setParseAction(self._actionForeignCodeStmt)
         '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        nCurr = NodeForeignCodeStmt()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.language = toks.language
        nCurr.method = toks.method
        nCurr.code = toks.code
        return nCurr

    
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
        if ParseStage.noTreeModification:
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
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeStmtList()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #create children - each child is a statement
        for tok in tokList:
            nCurr.kids.append(tok)
        return nCurr


    def _actionDataDef(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for defining parameter, variable or submodel:
            'data foo, bar: baz.boo parameter;
        One such statement can define multiple parmeters; and an individual
        NodeDataDef is created for each. They are returned together inside a
        list node of type NodeStmtList.
        BNF:
        newAttrList = Group( identifier +
                                ZeroOrMore(',' + identifier))
        attrRole = kw('state_variable') |kw('variable') | kw('param') | kw('const')
        #parse 'data foo, bar: baz.boo param;
        attributeDef = Group(kw('data')
                             + ES(newAttrList                        .setResultsName('attrNameList')
                                  + ':' + dotIdentifier              .setResultsName('className')
                                  + Optional(attrRole)               .setResultsName('attrRole')
                                  + Optional('=' + ES(expression     .setResultsName('value')
                                                      )              .setErrMsgStart('default value: ') )
                                  + stmtEnd)                         .setErrMsgStart('data definition: ')
                             )                                       .setParseAction(self._actionDataDef)\
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        #multiple attributes can be defined in a single statement
        #Create a node for each of them and put them into a statement list
        attrDefList = NodeDataDefList(loc=self.createTextLocation(loc))
        nameList = toks.attrNameList.asList()
        for name in nameList:
            if name in ParseStage.keywords:
                if name in ParseStage.builtInVars:
                    errMsg = 'Special name can not be redefined: ' + name
                else:
                    errMsg = 'Keyword can not be used as an identifier: ' + name
                raise ParseFatalException(str, loc, errMsg)
            attrDef = NodeDataDef(loc=self.createTextLocation(loc))
            attrDef.name = DotName(name) #store attribute name
            attrDef.className = DotName(toks.className.asList())  #store class name
            #map role string to role object, and store the role
            #If role is not specified RoleVariable is assumed. 
            #Submodels will be labled variables even though these categories don't apply to them.
            roleDict = {'const':RoleConstant, 'param':RoleParameter, 'variable':RoleVariable,
                        'algebraic_variable':RoleAlgebraicVariable, 
                        'state_variable':RoleStateVariable}
            attrDef.role = roleDict.get(toks.attrRole, None)
            #store the default value
            if isinstance(toks.defaultValue, Node):
                attrDef.setValue(toks.defaultValue)
            #store the attribute definition in the statement list
            attrDefList.appendChild(attrDef)
        #Special case: only one attribute defined
        if len(attrDefList) == 1:
            return attrDefList[0] #take it out of the list and return it
        else:
            return attrDefList #return list with multiple definitions


    def _actionFuncArgCall(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for one argument of a function call. 
            x=2.5  ,  x*2+sin(a)
        Node types are: either a mathematical expression, or an assignment. 
        BNF:
        funcArgCall = (  Group(identifier                            .setResultsName('argName')
                               + '=' + expression                    .setResultsName('value')
                               )                                     .setResultsName('namedArg') 
                       | Group(expression)                           .setResultsName('positionalArg') 
                       )                                             .setParseAction(self._actionFuncArgCall)
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debuging
        #named argument: x=2.5  
        if toks.namedArg:
            #TODO:Should a new node NodeNamedArg be introduced? A named argument is 
            # not really an assignment. Making it an assignment may break the 
            # attribute renaming algorithm.
            raise UserException('Named arguments are currently unsupported!',
                                self.createTextLocation(loc))
#            nCurr = NodeAssignment()
#            nCurr.loc = self.createTextLocation(loc) #Store position
#            nArgName = NodeAttrAccess()
#            nArgName.name = DotName(toks.namedArg.argName)
#            nCurr.lhs = nArgName
#            nCurr.rhs = toks.namedArg.value
        #positional argument: 2.5
        elif toks.positionalArg:
            nCurr = toks.positionalArg[0]
        else:
            raise ParseActionException('Broken function argument. ' +
                                        str(self.createTextLocation(loc)) + ' ' +
                                        str(toks))
        return nCurr
    
    def _actionFuncCall(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for calling a function or method.
            bar.doFoo(10, x, a=2.5)
        BNF:
        funcCall << Group(dotIdentifier                              .setResultsName('funcName')
                         + '(' + ES(funcArgListCall                  .setResultsName('argList')
                                    + ')' ))                         .setParseAction(self._actionFuncCall)
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeFuncExecute()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store function name
        nCurr.name = DotName(toks.funcName)
        #store function arguments: 
        thereWasNamedArgument = False
        for arg in toks.argList:
            nCurr.appendChild(arg)
            #check argument list - positional arguments must come before named arguments
            if isinstance(arg, NodeAssignment):
                thereWasNamedArgument = True
            elif thereWasNamedArgument:
                raise UserException('Positional arguments must come before named arguments!',
                                    nCurr.loc)  
        return nCurr
    
    
    def _actionFuncArgDef(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for one function argument of a function definition. 
        A NodeDataDef is created; therefore this method is quite similar 
        to _actionDataDef.
        BNF:
        funcArgDefault = Group(identifier                            .setResultsName('name')
                               + Optional(':' + ES(dotIdentifier     .setResultsName('className')
                                                   )                 .setErrMsgStart('type specifier: '))
                               + Optional('=' + ES(expression        .setResultsName('defaultValue')
                                                   )                 .setErrMsgStart('default value: '))
                               )                                     .setParseAction(self._actionFuncArgument)
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeDataDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store argument name
        nCurr.name = DotName(toks.name)
        #store optional type of argument
        if toks.className:
            nCurr.className = DotName(toks.className.asList())
        #store optional default value
        if isinstance(toks.defaultValue, Node):
            nCurr.setValue(toks.defaultValue)
        #store role
        nCurr.role = RoleFuncArgument
        return nCurr
        
    
    def _actionFuncDef(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for definition of a function or method.
            func doFoo(a:Real=2.5, b) -> Real: {... }
        BNF:
        funcDef = Group(kw('func') + ES(
                        newIdentifier                                .setResultsName('funcName')
                        + '(' + ES(Group(funcArgList)                .setResultsName('argList')
                                   )                                 .setErrMsgStart('argument List: ')
                        + ')'                                    
                        + Optional('->' + ES(dotIdentifier           .setResultsName('returnType')
                                             )                       .setErrMsgStart('return type: '))
                        + ':' 
                        + Group(suite)                               .setResultsName('funcBody')
                        )                                            .setErrMsgStart('function definition: ')
                        )                                            .setParseAction(self._actionFuncDefinition)\
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeFuncDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store function name
        nCurr.name = DotName(toks.funcName)
        #store function arguments: statement list of 'data' statements
        nCurr.argList = toks.argList[0]
        #check argument list - arguments without default values must come first!
        thereWasDefaultArgument = False
        for arg in nCurr.argList:
            if arg.value is not None:
                thereWasDefaultArgument = True
            elif thereWasDefaultArgument:
                raise UserException('Arguments without defaut values must come first!',
                                    nCurr.loc)  
        #store return type
        if toks.returnType:
            nCurr.returnType = DotName(toks.returnType)
        #store function body: statement list
        nCurr.funcBody = toks.funcBody[0]
        return nCurr


    def _actionClassDef(self, s, loc, toks): #IGNORE:W0613
        '''
        Create node for definition of a class:
            class foo(Model):{ }
        BNF:
        classBodyStmts = pragmaStmt | attributeDef | funcDef | assignment
        classDef = Group(kw('class')
                         + ES(newIdentifier                          .setResultsName('className')
                              + '(' + ES(dotIdentifier               .setResultsName('superName')
                                         + ')')                      .setErrMsgStart('Definition of base class: ')
                              + ':' + blockBegin
                              + ZeroOrMore(classBodyStmts)            .setResultsName('classBodyStmts')
                              + blockEnd)                            .setErrMsgStart('class definition: ')
                         )                                           .setParseAction(self._actionClassDef)\
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeClassDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store class name and name of super class
        nCurr.name = DotName(toks.className)
        nCurr.baseName = DotName(toks.superName)
        #create children (may or may not be present):  data, functions
        if len(toks.classBodyStmts) > 0:
            for stmt in toks.classBodyStmts:
                nCurr.appendChild(stmt)
        return nCurr


    def _actionModule(self, s, loc, toks): #IGNORE:W0613
        '''
        Create the root node of a module.
        BNF:
        program = Group(OneOrMore(classDef))
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeModule()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.name = self.moduleName
        #create children - each child is a Node
        for tok in tokList:
            nCurr.kids.append(tok)
        return nCurr


#------------------- BNF --------------------------------------------------------
    def _defineLanguageSyntax(self):
        '''
        Here is Siml's BNF
        Creates the objects of the pyParsing library,
        that do all the work.
        '''
        #define short alias so they don't clutter the text
        kw = self.defineKeyword # Usage: test = kw('variable')
        L = Literal # Usage: L('+')
        ES = ErrStop

        #Values that are built into the language
        #Integer (unsigned).
        uInteger = Word(nums)                                       .setName('uInteger')#.setDebug(True)
        #Floating point number (unsigned).
        eE = CaselessLiteral( 'E' )
        uNumber = Group( Combine(
                    uInteger +
                    Optional('.' + Optional(uInteger)) +
                    Optional(eE + Word('+-'+nums, nums))))          .setParseAction(self._actionNumber)\
                                                                    .setName('uNumber')#.setDebug(True)
        #string
        stringConst = sglQuotedString                               .setParseAction(self._actionString)\
                                                                    .setName('string')#.setDebug(True)

#------------------ Mathematical expression .............................................................
        #Forward declarations for recursive top level rules
        expression = Forward() #mathematical expression (incuding bool logic)
        valAccess = Forward()  #Refer to data: a.b.c[2.5:3.5]
        funcCall = Forward()   #Call a function: a.b.c(2, d)

        #Basic building blocks of mathematical expressions e.g.: (1, x, e,
        #sin(2*a), (a+2), a.b.c(2.5:3.5))
        #Function call, parenthesis and memory access can however contain
        #expressions.
        parentheses = Group('(' + expression + ')')                 .setParseAction(self._actionParenthesesPair) \
                                                                    .setName('parentheses')#.setDebug(True)
        atom = ( uNumber | stringConst | 
                 funcCall | valAccess | parentheses     )           .setName('atom')#.setDebug(True)

        #The basic mathematical operations: -a+b*c^d.
        #All operations have right-to-left associativity; although this is only
        #required for exponentiation. Precedence decreases towards the bottom.
        #Unary minus: -a, not a;
        negop = '-' | kw('not')
        signedAtom = Forward()
        unaryMinus = Group(negop + signedAtom)          .setParseAction(self._actionPrefixOp) \
                                                        .setName('unaryMinus')#.setDebug(True)
        signedAtom << (atom | unaryMinus)               .setName('signedAtom')  #IGNORE:W0104

        #Exponentiation: a^b;
        factor = Forward()
        factor1 = signedAtom                            .setName('factor1')#.setDebug(True)
        factor2 = Group(signedAtom + '**' + factor)     .setParseAction(self._actionInfixOp) \
                                                        .setName('factor2')#.setDebug(True)
        factor << (factor2 | factor1)                   .setName('factor')  #IGNORE:W0104

        #multiplicative operations: a*b; a/b
        multop = L('*') | L('/') | L('and')  
        term =  Forward()
        term1 = factor                                  .setName('term1')#.setDebug(True)
        term2 = Group(factor + multop + term)           .setParseAction(self._actionInfixOp) \
                                                        .setName('term2')#.setDebug(True)
        term << (term2 | term1)                         .setName('term')  #IGNORE:W0104

        #additive operations: a+b; a-b
        addop  = L('+') | L('-') | L('or')
        algExpr = Forward()
        algExpr1 = term                                 .setName('expression1')#.setDebug(True)
        algExpr2 = Group(term + addop + algExpr)        .setParseAction(self._actionInfixOp) \
                                                        .setName('expression2')#.setDebug(True)
        algExpr << (algExpr2 | algExpr1)                .setName('algExpr')  #IGNORE:W0104

        #TODO: 'and', 'or' should have less precedence than comparison operators
        #       otherwise one has to always write: (a < b) and (b < c)
        #Relational operators : <, >, ==, ...
        relop = L('<') | L('>') | L('<=') | L('>=') | L('==') | L('!=')
        expression1 = algExpr
        expression2 = Group(algExpr + relop + expression).setParseAction(self._actionInfixOp) \
                                                         .setName('boolExpr2')#.setDebug(True)
        expression << (expression2 | expression1)        .setName('expression')  #IGNORE:W0104

        #................ End mathematical expression ................................................---

#------------------ Identifiers .................................................................
        #Built in variables, handled specially at attribute access. (also keywords)
        kw('time'); kw('this')
        ParseStage.builtInVars = set(['time', 'this'])   
        #identifiers   
        #TODO: change to: identifier = Word(alphas, alphanums+'_') for code that the user writes
        #      internal symbols could then be written like: "__init_constants__"
        identifier = Word(alphas+'_', alphanums+'_')            .setName('identifier')#.setDebug(True)
        #Use this when defining new objects. The new identifier is checked if it is not a keyword
        newIdentifier = identifier.copy()                       .setParseAction(self._actionCheckIdentifier)
        #Compound identifiers for variables or parameters 'aaa.bbb'.
        dotSup = Literal('.').suppress()
        dotIdentifier = Group(identifier +
                              ZeroOrMore(dotSup + identifier))  .setName('dotIdentifier')#.setDebug(True)
        #Method to access a stored value: dotted name ('a.b.c'),
        # with optional differentiation operator ('$a.b.c'),
        # and optional partial access ('a.b.c[2:5]'). (partial access is currently not implemented)
        valAccess << Group( Optional('$') +                                            #IGNORE:W0104
                            identifier +
                            ZeroOrMore(dotSup + identifier) )   .setParseAction(self._actionAttributeAccess) \
                                                                .setName('valAccess')

#------------------- Statements ..................................................................
        blockBegin = Literal('{').suppress()
        blockEnd = Literal('}').suppress()
        stmtEnd = Literal(';').suppress()
        
        #Statement and list of statements - for compund statements and function bodies
        statement = Forward()
        block = blockBegin + ES(ZeroOrMore(statement) + blockEnd)    .setErrMsgStart('Block: ')
        suite = Group(block | statement)                             .setParseAction(self._actionStatementList)\
                                                                     #.setName('statementList')#.setDebug(True)
        #Flow control - if then else
        ifStatement = \
            Group(kw('if') + ES(expression + ':' + suite
                  + ZeroOrMore(kw('elif') + ES(expression + ':' + suite) .setErrMsgStart('elif: '))
                  + kw('else') + ES(':' + suite)                         .setErrMsgStart('else: ')
                  )                                                      .setErrMsgStart('if: ')
                  )                                                      .setParseAction(self._actionIfStatement)\
                                                                         .setName('ifStatement')#.setDebug(True)
        #compute expression and assign to value
        assignment = Group(valAccess + '='
                           + ES(expression + stmtEnd)                .setErrMsgStart('Assignment statement: ')
                           )                                         .setParseAction(self._actionAssignment)\
                                                                     .setName('assignment')#.setDebug(True)
        #execute a class method (or a function) - 
        #usually inserts the function bodie's code into the current method. 
        #This code insertion (inlinig) is done recursively and leaves only 
        #a few big top level methods
        funcCallStmt = funcCall + ES(stmtEnd)                        .setErrMsgStart('Call statement: ')

        #Return values from a function
        returnStmt = (kw('return') + ES(Optional(expression          .setResultsName('retVal')) 
                                        + stmtEnd)                   .setErrMsgStart('Return statement: ')
                      )                                              .setParseAction(self._actionReturnStmt)
        
        #pragma statement: tell any kind of options to the compiler
        pragmaStmt = (kw('pragma') 
                      + ES(OneOrMore(Word(alphanums+'_')             .setName('pragma option')
                                     ) + stmtEnd)                    .setErrMsgStart('Pragma statement: ')
                      )                                              .setParseAction(self._actionPragmaStmt)
        
        #foreign code statement: specify code in the target language that is
        #inserted into the compiled module
        #    foreign_code python replace_call ::{{ sin(x) }}:: ;
        foreignCodeStmt = (kw('foreign_code') 
                           + ES(Word(alphanums+'_')                  .setResultsName('language')
                                                                     .setName('language specification')
                                + Word(alphanums+'_')                .setResultsName('method')
                                                                     .setName('code insertion method')
                                + QuotedString(quoteChar='::{{', 
                                               endQuoteChar='}}::')  .setResultsName('code')
                                                                     .setName('code to insert')
                                + stmtEnd)                           .setErrMsgStart('Foreign code statement: ')
                           )                                         .setParseAction(self._actionForeignCodeStmt)
        
        #expression list - parse: 2, foo.bar, 3*sin(baz)
        commaSup = Literal(',').suppress()
        expressionList = Group(expression
                                + ZeroOrMore(commaSup + expression)).setName('exprList')
        #print something to stdout
        printStmt = Group(kw('print')
                          + ES(expressionList                        .setResultsName('argList')
                                    + Optional(',')                  .setResultsName('trailComma')
                                    + stmtEnd)                       .setErrMsgStart('Print statement: ')
                          )                                          .setParseAction(self._actionPrintStmt)\
                                                                     .setName('printStmt')#.setDebug(True)
        #show graphs
        graphStmt = Group(kw('graph')
                          + ES(expressionList                        .setResultsName('argList')
                                    + stmtEnd)                       .setErrMsgStart('Graph statement: ')
                          )                                          .setParseAction(self._actionGraphStmt)\
                                                                     .setName('graphStmt')#.setDebug(True)
        #store to disk
        storeStmt = Group(kw('save')
                          + ES(Group(Optional(stringConst))          .setResultsName('argList')
                                    + stmtEnd)                       .setErrMsgStart('Save statement: ')
                          )                                          .setParseAction(self._actionStoreStmt)\
                                                                     .setName('storeStmt')#.setDebug(True)
        #compile a class
        compileStmt = (kw('compile') + ES(
                          (dotIdentifier                             .setResultsName('className')
                           + stmtEnd
                           ) |
                          (identifier                                .setResultsName('name')
                           + ':' + dotIdentifier                     .setResultsName('className')
                           + stmtEnd) 
                          )                                          .setErrMsgStart('compile statement: ')
                       )                                             .setParseAction(self._actionCompileStmt)\
        
        statement << (storeStmt | graphStmt | printStmt |                                   #IGNORE:W0104
                      returnStmt | pragmaStmt | foreignCodeStmt |
                      ifStatement | assignment | funcCallStmt)       .setName('statement')

#------------- Function ............................................................................
        #Function call 
        #one argument at the call site: x=2.5  ,  x  ,  2.5
        funcArgCall = (  Group(identifier                            .setResultsName('argName')
                               + '=' + expression                    .setResultsName('value')
                               )                                     .setResultsName('namedArg') 
                       | Group(expression)                           .setResultsName('positionalArg') 
                       )                                             .setParseAction(self._actionFuncArgCall)
        funcArgListCall = \
                Group(Optional(delimitedList(funcArgCall, ',')))     #.setParseAction(self._actionStatementList)
        #the function call
        #The funcCall parser is is forward decdlared, because it is used in 
        #the (mathematical) expression and in the function call statement.
        funcCall << Group(dotIdentifier                              .setResultsName('funcName')  #IGNORE:W0104
                         + '(' + ES(funcArgListCall                  .setResultsName('argList')
                                    + ')' ))                         .setParseAction(self._actionFuncCall)

        #Function definition (class method or global function)
        #one argument of the definition: inX:Real=2.5
        funcArgDef = Group(identifier                                .setResultsName('name')
                           + Optional(':' + ES(dotIdentifier         .setResultsName('className')
                                               )                     .setErrMsgStart('type specifier: '))
                           + Optional('=' + ES(expression            .setResultsName('defaultValue')
                                               )                     .setErrMsgStart('default value: '))
                           )                                         .setParseAction(self._actionFuncArgDef)
        funcArgListDef = \
                Group(Optional(delimitedList(funcArgDef, ',')))      .setParseAction(self._actionStatementList)
        #the function: func doFoo(a:Real=2.5, b) -> Real {...}
        funcDef = Group(kw('func') + ES(
                        newIdentifier                                .setResultsName('funcName')
                        + '(' + ES(Group(funcArgListDef)             .setResultsName('argList')
                                   + ')' )                           .setErrMsgStart('argument List: ')            
                        + Optional('->' + ES(dotIdentifier           .setResultsName('returnType')
                                             )                       .setErrMsgStart('return type: '))
                        + ':' 
                        + Group(suite)                               .setResultsName('funcBody')
                        )                                            .setErrMsgStart('function definition: ')
                        )                                            .setParseAction(self._actionFuncDef)\
                                                                     #.setName('memberFuncDef')#.setDebug(True)

#---------- Define new objects ......................................................................
        #define parameters, variables, constants and submodels
        #commaSup = Literal(',').suppress()
        #parse: 'foo, bar, baz
        #Identifiers must not be keywords, check is done in _actionDataDef
        newAttrList = Group(identifier
                            + ZeroOrMore(commaSup + identifier))     .setName('attrNameList')
        #The roles of data (maybe call it storage class?):
        #variable:    changes during the simulation 
        #parameter:   constant during a (dynamic?) simulation, can change beween simulations,
        #             can be computed in the init function.
        #constant:    must be known at compile time, may be optimized away, 
        #             the compiler may generate special code depending on the value.
        attrRole = kw('state_variable') | kw('algebraic_variable') | \
                   kw('variable') | kw('param') | kw('const')
        #parse 'data foo, bar: baz.boo parameter;
        attributeDef = Group(kw('data')
                             + ES(newAttrList                        .setResultsName('attrNameList')
                                  + ':' + dotIdentifier              .setResultsName('className')
                                  + Optional(attrRole)               .setResultsName('attrRole')
                                  + Optional('=' + ES(expression     .setResultsName('defaultValue')
                                                      )              .setErrMsgStart('default value: ') )
                                  + stmtEnd)                         .setErrMsgStart('data definition: ')
                             )                                       .setParseAction(self._actionDataDef)\

        #definition of a class (process, model, type?)
        classBodyStmts = pragmaStmt | attributeDef | funcDef | assignment
        classDef = Group(kw('class')
                         + ES(newIdentifier                          .setResultsName('className')
                              + '(' + ES(dotIdentifier               .setResultsName('superName')
                                         + ')')                      .setErrMsgStart('Definition of base class: ')
                              + ':' + blockBegin
                              + ZeroOrMore(classBodyStmts)           .setResultsName('classBodyStmts')
                              + blockEnd)                            .setErrMsgStart('class definition: ')
                         )                                           .setParseAction(self._actionClassDef)\

        topLevelStms = classDef | funcDef | attributeDef | \
                       compileStmt | assignment
        module = (Group(ZeroOrMore(topLevelStms)) + StringEnd())    .setParseAction(self._actionModule)\
                                                                     .setName('module')#.setDebug(True)

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
    flagTestParser = True
    #flagTestParser = False
    if flagTestParser:
        parser = ParseStage()
        #ParseStage.noTreeModification = 1

        print parser.parseModuleStr(testProg1)
        #print parser.parseModuleStr(testProg2)
        
        #print parser.parseProgram('if a==0 then b=-1; else b=2+3+4; a=1; end')
        #print parser.parseExpression('0*1*2*3*4').asList()[0]
        #print parser.parseExpression('0^1^2^3^4')
        #print parser.parseExpression('0+1*2+3+4').asList()[0]
        #print parser.parseExpression('0*1^2*3*4')
        #print parser.parseExpression('0+(1+2)+3+4')
        #print parser.parseExpression('-0+1+--2*-3--4')
        #print parser.parseExpression('-aa.a+bb.b+--cc.c*-dd.d--ee.e+f').asList()[0]
        #print parser.parseExpression('time+0+sin(2+3*4)+5').asList()[0]
        #print parser.parseExpression('0+a1.a2+bb.b1.b2+3+4 #comment')
        #print parser.parseExpression('0.123+1.2e3')
        #parser.parseExpression('0+1*2^3^4+5+6*7+8+9')

        print 'keywords:'
        print parser.keywords



if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #TODO: add doctest tests. With doctest tests are embedded in the documentation

    doTests()
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
