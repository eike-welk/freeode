# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2008 by Eike Welk                                       *
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

#TODO: Implement namespaces. Usefull would be:
#       - Global namespace for: classes, global functions.
#       - Class namespace for class attributes
#       - Function local namespace for: data attributes, function attributes


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
    """
    #TODO: implement setErrorAction( callableObject )
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
    The syntax definition (BNF) resides here.

    The parsing is done by the pyparsing library which combines
    lexer and parser. The Pyparsing library generates a tree of
    ParseResult objects. These objects
    are replaced by objects inheriting from ast.Node
    in the parse actions of this class.

    Normally a file name is given to the class, and a tree of ast.Node objects is
    returned. The program can also be entered as a string.
    Additionally the class can parse parts of a program: expressions.

    The parse* methods return a tree of Node objects; the abstract syntax
    tree (AST)

    Usage:
    parser = ParseStage()
    ast1 = parser.parseExpressionStr('0+1+2+3+4')
    ast2 = parser.parseProgramFile('foo-bar.siml')
    '''

    noTreeModification = 0
    '''
    Define how much the parse result is modified, for easier debuging.
    0: normal operation. Compilation does not work otherwise.
    1: Do not modify parse result (from pyParsing library).

    ParseResult objects are printed as nested lists: ['1', '+', ['2', '*', '3']]
    '''

    keywords = set([])
    '''
    List of all keywords (filled by _defineLanguageSyntax() and defineKeyword).
    '''


    def __init__(self):
        object.__init__(self)
        self._parser = None
        '''The parser object for the whole program (from pyParsing).'''
        self._expressionParser = None
        '''The parser for expressions'''
        #self._lastStmtLocator = StoreLoc(self)
        self._locLastStmt = TextLocation()
        '''Object to remember location of last parsed statement; for
           error message creation.'''
        self.progFileName = None
        '''Name of SIML program file, that will be parsed'''
        self.inputString = None
        '''String that will be parsed'''
        self._builtInFunc = {}
        '''Names of built in functions and some info about them.
           Format: {'function_name':number_of_function_arguments}
           Example: {'sin':1, 'max':2}'''
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
    def _actionDebug(self, str, loc, toks):
        '''Parse action for debugging.'''
        print '------debug action'
        print str
        print loc
        print toks
        print '-------------------'
        return None


    def _actionCheckIdentifier(self, str, loc, toks):
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
            raise ParseException(str, loc, errMsg)
            #raise ParseFatalException(
            #    str, loc, 'Identifier same as keyword: %s' % toks[0] )
#            raise UserException(
#                'Keyword can not be used as an identifier: ' + identier,
#                 self.createTextLocation(loc))


    def _actionStoreStmtLoc(self, str, loc, toks):
        '''
        Remember location of last parsed statement. Useful for error
        error message creation, since the locations of pyparsing's
        syntax errors are frequently quite off.
        '''
        self._locLastStmt = self.createTextLocation(loc)


    def _actionBuiltInValue(self, str, loc, toks):
        '''
        Create AST node for a built in value: pi, time
        tokList has the following structure:
        [<identifier>]
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        #create AST node
        nCurr = NodeBuiltInVal()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.dat = tokList #Store the built in value's name
        return nCurr


    def _actionNumber(self, str, loc, toks):
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


    def _actionString(self, str, loc, toks):
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


    def _actionBuiltInFunction(self, str, loc, toks):
        '''
        Create node for function call: sin(2.1)

        Definition:
        funcCall = Group(builtInFuncName         .setResultsName('funcName')
                         + '(' + expressionList  .setResultsName('arguments')
                         + ')' )                 .setParseAction(self._actionBuiltInFunction) \
                                                 .setName('funcCall')#.setDebug(True)
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeBuiltInFuncCall()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.dat = toks.funcName #function dentifier
        nCurr.kids = toks.arguments.asList() #child expression(s)
        #check if number of function arguments is correct
        if len(nCurr.kids) != self._builtInFunc[nCurr.dat]:
            msg = ('Illegal number of function arguments. \n' +
                   'Function: %s, required number of arguments: %d, ' +
                   'given arguments: %d.') % \
                  (nCurr.dat, self._builtInFunc[nCurr.dat], len(nCurr.kids))
            raise UserException(msg, self.createTextLocation(loc))
        return nCurr


    def _actionParenthesesPair(self, str, loc, toks):
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


    def _actionPrefixOp(self, str, loc, toks):
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


    def _actionInfixOp(self, str, loc, toks):
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


    def _actionAttributeAccess(self, str, loc, toks):
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
        nCurr.attrName = DotName(tokList)
        return nCurr


    def _actionIfStatement(self, str, loc, toks):
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
        #if ... then ... end
        if len(tokList) == 5:
            condition = tokList[1]
            thenStmts = tokList[3]
            nCurr.kids=[condition, thenStmts]
        #if ... then ... else ... end
        elif len(tokList) == 8:
            condition = tokList[1]
            thenStmts = tokList[3]
            elseStmts = tokList[6]
            nCurr.kids=[condition, thenStmts, elseStmts]
        else:
            raise ParseActionException('Broken >if< statement! loc: ' + str(nCurr.loc))
        return nCurr


    def _actionAssignment(self, str, loc, toks):
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


    def _actionFuncExecute(self, str, loc, toks):
        '''
        Create node for execution of a function (insertion of the code):
            call foo.init()
        BNF:
        funcExecute = Group(kw('call')
                             + dotIdentifier    .setResultsName('funcName')
                             + '(' + ')'
                             + ';')             .setParseAction(self._createBlockExecute)\
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeFuncExecute()
        nCurr.loc = self.createTextLocation(loc) #Store position
        nCurr.funcName = DotName(toks.funcName)    #full (dotted) function name
        return nCurr


    def _actionPrintStmt(self, str, loc, toks):
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


    def _actionGraphStmt(self, str, loc, toks):
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


    def _actionStoreStmt(self, str, loc, toks):
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


    def _actionStatementList(self, str, loc, toks):
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


    def _actionAttrDefinition(self, str, loc, toks):
        '''
        Create node for defining parameter, variable or submodel:
            'data foo, bar: baz.boo parameter;
        One such statement can define multiple parmeters; and an individual
        NodeAttrDef is created for each. They are returned together inside a
        list node of type NodeStmtList.
        BNF:
        attrNameList = Group( identifier +
                                ZeroOrMore(',' + identifier))
        attrRole = kw('parameter') | kw('variable')
        #parse 'data foo, bar: baz.boo parameter;
        attributeDef = Group(kw('data')
                             + attrNameList                          .setResultsName('attrNameList')
                             + ':' + dotIdentifier                   .setResultsName('className')
                             + Optional(attrRole)                    .setResultsName('attrRole')
                             + ';')
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        #multiple attributes can be defined in a single statement
        #Create a node for each of them and put them into a statement list
        attrDefList = NodeStmtList(loc=self.createTextLocation(loc))
        nameList = toks.attrNameList.asList()
        for name in nameList:
            if name in self.keywords:
                errMsg = 'Keyword can not be used as an identifier: ' + name
                raise ParseFatalException(str, loc, errMsg)
            attrDef = NodeAttrDef(loc=self.createTextLocation(loc))
            attrDef.attrName = DotName(name) #store attribute name
            attrDef.className = DotName(toks.className.asList())  #store class name
            #store the role
            if toks.attrRole == 'parameter':
                attrDef.role = RoleParameter
            else:
                #we do not know if variable or parameter; submodels will be
                #labled variables even though these categories don't apply
                #to them.
                attrDef.role = RoleVariable
            attrDefList.appendChild(attrDef)
        #Special case: only one attribute defined
        if len(attrDefList) == 1:
            return attrDefList[0] #take it out of the list and return it
        else:
            return attrDefList #return list with multiple definitions


    def _actionFuncDefinition(self, str, loc, toks):
        '''
        Create node for definition of a (member) function:
            func init(): a=1; end
        BNF:
        memberFuncDef = Group(kw('func')
                              + identifier                           .setResultsName('funcName')
                              + '(' + ')' + ':'
                              + ZeroOrMore(statement)                .setResultsName('funcBody', True)
                              + kw('end'))        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debuging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeFuncDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store name of block
        nCurr.name = DotName(toks.funcName)
        #create children - each child is a statement
        statements = []
        if len(toks.funcBody) > 0:
            statements = toks.funcBody.asList()[0]
        for stmt1 in statements:
            nCurr.appendChild(stmt1)
        return nCurr


    def _actionClassDef(self, str, loc, toks):
        '''
        Create node for definition of a class:
            class foo(Model): ... end
        BNF:
        classDef = Group(kw('class')
                         + identifier                 .setResultsName('className')
                         + '(' + dotIdentifier        .setResultsName('superName')
                         + ')' + ':'
                         + OneOrMore(attributeDef)    .setResultsName('attributeDef', True)
                         + ZeroOrMore(memberFuncDef)  .setResultsName('memberFuncDef', True)
                         + kw('end'))
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        #tokList = toks.asList()[0] #there always seems to be
        toks = toks[0]             #an extra pair of brackets
        nCurr = NodeClassDef()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #store class name and name of super class
        nCurr.className = DotName(toks.className)
        nCurr.superName = DotName(toks.superName)
        #create children (may or may not be present):  data, functions
        data, funcs = [], [] #special cases for empty sections necessary
        if len(toks.attributeDef) > 0:
            data = toks.attributeDef.asList()[0]
        if len(toks.memberFuncDef) > 0:
            funcs =  toks.memberFuncDef.asList()[0]
        for stmt1 in data + funcs:
            nCurr.appendChild(stmt1)
        return nCurr


    def _actionProgram(self, str, loc, toks):
        '''
        Create the root node of a program.
        BNF:
        program = Group(OneOrMore(classDef))
        '''
        if ParseStage.noTreeModification:
            return None #No parse result modifications for debugging
        tokList = toks.asList()[0] #asList() ads an extra pair of brackets
        nCurr = NodeProgram()
        nCurr.loc = self.createTextLocation(loc) #Store position
        #create children - each child is a class
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

        #Values that are built into the language
        builtInValue = (kw('pi') | kw('time'))                      .setParseAction(self._actionBuiltInValue)\
                                                                    .setName('builtInValue')#.setDebug(True)

        #Functions that are built into the language
        #Dict: {'function_name':number_of_function_arguments}
        self._builtInFunc = {'sin':1, 'cos':1, 'tan':1,
                             'sqrt':1, 'exp':1, 'log':1,
                             'min':2, 'max':2}
        builtInFuncName = MatchFirst(
            [kw(funcName)
             for funcName in self._builtInFunc.keys()])             .setName('builtInFuncName')#.setDebug(True)

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
#        stringConst = QuotedString(quoteChar='\'', escChar='\\')    .setParseAction(self._actionString)\
#                                                                    .setName('string')#.setDebug(True)
        stringConst = sglQuotedString                               .setParseAction(self._actionString)\
                                                                    .setName('string')#.setDebug(True)

        # .............. Mathematical expression .............................................................
        #'Forward declarations' for recursive rules
        expressionList = Forward() #For built in functions TODO: this should be a list of bool expressions
        boolExpression = Forward()
        expression = Forward()
        term =  Forward()
        factor = Forward()
        signedAtom = Forward()
        valAccess = Forward() #For PDE: may also contain expressions for slices: a.b.c(2.5:3.5)

        #Basic building blocks of mathematical expressions e.g.: (1, x, e,
        #sin(2*a), (a+2), a.b.c(2.5:3.5))
        #Function call, parenthesis and memory access can however contain
        #expressions.
        #TODO: funcCall should be unified with with call to member function
        funcCall = Group(builtInFuncName                            .setResultsName('funcName')
                         + '(' + expressionList                     .setResultsName('arguments')
                         + ')' )                                    .setParseAction(self._actionBuiltInFunction) \
                                                                    .setName('funcCall')#.setDebug(True)
        parentheses = Group('(' + expression + ')')                 .setParseAction(self._actionParenthesesPair) \
                                                                    .setName('parentheses')#.setDebug(True)
        atom = ( uNumber | stringConst | builtInValue |
                 funcCall | valAccess | parentheses     )           .setName('atom')#.setDebug(True)

        #The basic mathematical operations: -a+b*c^d.
        #All operations have right-to-left associativity; although this is only
        #required for exponentiation. Precedence decreases towards the bottom.
        #Unary minus: -a, not a;
        negop = '-' | kw('not')
        unaryMinus = Group(negop + signedAtom)          .setParseAction(self._actionPrefixOp) \
                                                        .setName('unaryMinus')#.setDebug(True)
        signedAtom << (atom | unaryMinus)               .setName('signedAtom')#.setDebug(True)

        #Exponentiation: a^b;
        factor1 = signedAtom                            .setName('factor1')#.setDebug(True)
        factor2 = Group(signedAtom + '**' + factor)     .setParseAction(self._actionInfixOp) \
                                                        .setName('factor2')#.setDebug(True)
        factor << (factor2 | factor1)                   .setName('factor')#.setDebug(True)

        #multiplicative operations: a*b; a/b
        multop = L('*') | L('/') | L('and')
        term1 = factor                                  .setName('term1')#.setDebug(True)
        term2 = Group(factor + multop + term)           .setParseAction(self._actionInfixOp) \
                                                        .setName('term2')#.setDebug(True)
        term << (term2 | term1)                         .setName('term')#.setDebug(True)

        #additive operations: a+b; a-b
        addop  = L('+') | L('-') | L('or')
        expression1 = term                              .setName('expression1')#.setDebug(True)
        expression2 = Group(term + addop + expression)  .setParseAction(self._actionInfixOp) \
                                                        .setName('expression2')#.setDebug(True)
        expression << (expression2 | expression1)       .setName('expression')#.setDebug(True)

        #Relational operators : <, >, ==, ...
        relop = L('<') | L('>') | L('<=') | L('>=') | L('==') | L('!=')
        boolExpr1 = expression
        boolExpr2 = Group(expression + relop + boolExpression)  .setParseAction(self._actionInfixOp) \
                                                                .setName('boolExpr2')#.setDebug(True)
        boolExpression << (boolExpr2 | boolExpr1)               .setName('boolExpression')#.setDebug(True)

        #expression list - sparse: 2, foo.bar, 3*sin(baz)
        commaSup = Literal(',').suppress()
        expressionList << Group(boolExpression
                                + ZeroOrMore(commaSup + boolExpression)).setName('exprList')
        #................ End mathematical expression ................................................---

        #................ Identifiers ...................................................................
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
        valAccess << Group( Optional('$') +
                            identifier +
                            ZeroOrMore(dotSup + identifier) )   .setParseAction(self._actionAttributeAccess) \
                                                                .setName('valAccess')#.setDebug(True)

#------------------- Statements ---------------------------------------------------------------
        statementList = Forward()
        #Flow control - if then else
        ifStatement = Group(kw('if')
                            + ErrStop( boolExpression + ':'
                                       + statementList
                                       + Optional(kw('else')
                                                  + ErrStop(':' + statementList))
                                       + kw('end'))
                            )                                        .setParseAction(self._actionIfStatement)\
                                                                     .setName('ifStatement')#.setDebug(True)
        #compute expression and assign to value
        assignment = Group(valAccess + '='
                           + ErrStop(boolExpression + ';')           .setErrMsgStart('Assignment statement: ')
                           )                                         .setParseAction(self._actionAssignment)\
                                                                     .setName('assignment')#.setDebug(True)
        #execute a block - insert code of a child model
        #function arguments are currently missing
        #TODO: Unify with builtin functions.
        funcExecute = Group(kw('call')
                             + ErrStop(dotIdentifier                 .setResultsName('funcName')
                                       + '(' + ')'
                                       + ';')                        .setErrMsgStart('Call statement: ')
                             )                                       .setParseAction(self._actionFuncExecute)\
                                                                     .setName('blockExecute')#.setDebug(True)
        #print something to stdout
        printStmt = Group(kw('print')
                          + ErrStop(expressionList                   .setResultsName('argList')
                                    + Optional(',')                  .setResultsName('trailComma')
                                    + ';')                           .setErrMsgStart('Print statement: ')
                          )                                          .setParseAction(self._actionPrintStmt)\
                                                                     .setName('printStmt')#.setDebug(True)
        #show graphs
        graphStmt = Group(kw('graph')
                          + ErrStop(expressionList                   .setResultsName('argList')
                                    + ';')                           .setErrMsgStart('Graph statement: ')
                          )                                          .setParseAction(self._actionGraphStmt)\
                                                                     .setName('graphStmt')#.setDebug(True)
        #store to disk
        storeStmt = Group(kw('save')
                          + ErrStop(Group(Optional(stringConst))     .setResultsName('argList')
                                    + ';')                           .setErrMsgStart('Save statement: ')
                          )                                          .setParseAction(self._actionStoreStmt)\
                                                                     .setName('storeStmt')#.setDebug(True)

        statement = (storeStmt | graphStmt | printStmt |
                     funcExecute | ifStatement | assignment)         .setParseAction(self._actionStoreStmtLoc)\
                                                                     .setName('statement')#.setDebug(True)
        statementList << Group(OneOrMore(statement))                 .setParseAction(self._actionStatementList)\
                                                                     .setName('statementList')#.setDebug(True)

#---------- Define new objects ---------------------------------------------------------------------*
        #define parameters, variables, constants and submodels
        #commaSup = Literal(',').suppress()
        #parse: 'foo, bar, baz
        #Identifiers must not be keywords, check is done in _actionAttrDefinition
        newAttrList = Group(identifier
                            + ZeroOrMore(commaSup + identifier))     .setName('attrNameList')
        #The roles of data (maybe call it storage class?):
        #variable:    changes during the simulation 
        #parameter:   constant during a (dynamic?) simulation, can change beween simulations,
        #             can be computed in the init function.
        #constant:    must be known at compile time, may be optimized away, 
        #             the compiler may generate special code depending on the value.
        attrRole = kw('variable') | kw('parameter') | kw('constant')
        #parse 'data foo, bar: baz.boo parameter;
        attributeDef = Group(kw('data')
                             + ErrStop(newAttrList                   .setResultsName('attrNameList')
                                       + ':' + dotIdentifier         .setResultsName('className')
                                       + Optional(attrRole)          .setResultsName('attrRole')
                                       + ';')                        .setErrMsgStart('Wrong syntax in data definition. ')
                             )                                       .setParseAction(self._actionAttrDefinition)\
                                                                     .setName('attributeDef')#.setDebug(True)
        #define member function (method)
        #TODO: function arguments are currently missing
        #TODO: unify with built in functions
        funcDef = Group(kw('func')
                        + ErrStop(newIdentifier                      .setResultsName('funcName')
                                  + '(' + ')' + ':'
                                  + ZeroOrMore(statement)            .setResultsName('funcBody', True)
                                  + kw('end'))                       .setErrMsgStart('Wrong syntax in function definition. ')
                        )                                            .setParseAction(self._actionFuncDefinition)\
                                                                     .setName('memberFuncDef')#.setDebug(True)
        #definition of a class (process, model, type?)
        classDef = Group(kw('class')
                         + ErrStop(newIdentifier                     .setResultsName('className')
                                   + '(' + dotIdentifier             .setResultsName('superName')
                                   + ')' + ':'
                                   + ZeroOrMore(attributeDef)        .setResultsName('attributeDef', True)
                                   + ZeroOrMore(funcDef)             .setResultsName('memberFuncDef', True)
                                   + kw('end'))                      .setErrMsgStart('Wrong syntax in class definition. ')
                         )                                           .setParseAction(self._actionClassDef)\
                                                                     .setName('classDef')#.setDebug(True)

        program = (Group(OneOrMore(classDef)) + StringEnd())         .setParseAction(self._actionProgram)\
                                                                     .setName('program')#.setDebug(True)

        #................ End of language definition ..................................................

        #determine start symbol
        startSymbol = program
        #set up comments
        singleLineCommentCpp = '//' + restOfLine
        singleLineCommentPy = '#' + restOfLine
        startSymbol.ignore(singleLineCommentCpp)
        startSymbol.ignore(singleLineCommentPy)
        #no tab expansion
        startSymbol.parseWithTabs()
        #store parsers
        self._parser = startSymbol
        self._expressionParser = boolExpression


    def parseExpressionStr(self, inString):
        '''Parse a single expression. Example: 2*a+b'''
        self.inputString = inString
        return self._expressionParser.parseString(inString).asList()[0]


    def parseProgramStr(self, inString):
        '''Parse a whole program. The program is entered as a string.'''
        self.inputString = inString
        result = self._parser.parseString(inString).asList()[0]
        return result


    def parseProgramFile(self, fileName):
        '''Parse a whole program. The program's file name is supplied.'''
        self.progFileName = os.path.abspath(fileName)
        #open and read the file
        try:
            inputFile = open(self.progFileName, 'r')
            inputFileContents = inputFile.read()
            inputFile.close()
        except IOError, theError:
            message = 'Could not read input file.\n' + str(theError)
            raise UserException(message, None)
        #parse the program
        try:
            astTree = self.parseProgramStr(inputFileContents)
        except (ParseException, ParseFatalException), theError:
            #add additional information to the pyparsing exceptions.
            msgPyParsing = str(theError) + '\n'
            #see if there is the loc of a successfully parsed statement
            if self._locLastStmt.isValid():
                msgLastStmt = 'Last parsed statement was: \n' \
                              + str(self._locLastStmt)
            else:
                msgLastStmt = ''
            #make UserException that will be visible to the user
            loc =  TextLocation(theError.loc, theError.pstr, self.progFileName)
            raise UserException(msgPyParsing + msgLastStmt, loc)
        return astTree



def doTests():
    '''Perform various tests.'''

    #t1 = Node('root', [Node('child1',[]),Node('child2',[])])
    #print t1

#------------ testProg1 -----------------------
    testProg1 = (
'''
class Test(Model):
    data V, h: Real;
    data A_bott, A_o, mu, q, g: Real parameter;

    func dynamic():
        h = V/A_bott;
        $V = q - mu*A_o*sqrt(2*g*h);
        print 'h: ', h,;
    end

    func init():
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
        q = 0.05;
    end
end

class RunTest(Process):
    data g: Real parameter;
    data test: Test;

    func dynamic():
        call test.dynamic();
    end

    func init():
        g = 9.81;
        call test.init();
        solutionParameters.simulationTime = 100;
        solutionParameters.reportingInterval = 1;
    end
    func final():
        #store;
        graph test.V, test.h;
        print 'Simulation finished successfully.';
    end
end
''' )


    #test the parser ----------------------------------------------------------------------
    flagTestParser = True
    #flagTestParser = False
    if flagTestParser:
        parser = ParseStage()
        #ParseStage.debugSyntax = 1
        #ParseStage.debugSyntax = 2
        #print parser.parseProgram('model test var a; par b; end')
        #print parser.parseProgram('model test par a; end')


        #print parser.parseProgram(testProg2)

        print parser.parseProgramStr(testProg1)
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
