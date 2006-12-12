#***************************************************************************
#    Copyright (C) 2006 by Eike Welk                                       *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration came from:                                                *
#    'fourFn.py', an example program, by Paul McGuire                      *
#    and the 'Spark' library by John Aycock                                *
#                                                                          *
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

__doc__ = \
'''
Parser for the SIML simulation language.
'''
#TODO: usage (above)


#import pprint #pretty printer
#import pdb    #debuber

from pyparsing import Literal,CaselessLiteral,Keyword,Word,Combine,Group,Optional, \
    ZeroOrMore,OneOrMore,Forward,nums,alphas,restOfLine,ParseResults, ParseException, \
    ParseFatalException

from ast import *


#pp = pprint.PrettyPrinter(indent=4) 


class ParseStage(object):
    '''
    The syntax definition (BNF) resides here.
    Mainly a wrapper for the Pyparsing library and therefore combines lexer
    and parser. The Pyparsing library generates a ParseResult object which is
    modfied through parse actions by this class.

    The program is entered as a string.
    ParseResult objects can be converted to nested lists: ['1', '+', ['2', '*', '3']]

    Usage:
    parser = ParseStage()
    result = parser.parseProgram('0+1+2+3+4')
    '''


    debugSyntax = 0
    '''
    Define how much the parse result is modified, for easier debuging.
    0: normal operation. Compilaton does not work otherwise.
    1: No additional information and no reordering, but copy ParseResult;
    2: Do not modify parse result (from pyParsing library).
    '''

    keywords = set([])
    '''
    List of all keywords (filled by _defineLanguageSyntax() and defineKeyword).
    '''

    nodeTypes = set([])
    '''
    List of all type strings, that identify the nodes in the parse result.
    Filled by defineNodeType() in the semantic actions; or by the AddMetaDict
    object.
    '''


    def __init__(self):
        object.__init__(self)
        self._parser = self._defineLanguageSyntax() #Create parser object
        '''The parser object from pyParsing'''


    def defineKeyword(self, inString):
        '''
        Store keyword (in ParseStage.keywords) and create parser for it.
        Use this function (in _defineLanguageSyntax(...)) instead of using the
        Keyword class directly.
        '''
        ParseStage.keywords.add(inString)
        return Keyword(inString)


    def defineNodeType(self, inString):
        '''Store type string (in ParseStage.nodeTypes) and return it.'''
        ParseStage.nodeTypes.add(inString)
        return inString


#------------- Parse Actions -------------------------------------------------*
    def _actionDebug(self, str, loc, toks):
        '''Parse action for debuging.'''
        print '------debug action'
        print str
        print loc
        print toks
        print '-------------------'
        return toks


    def _actionCheckIdentifier(self, str, loc, toks):
        '''
        Parse action to check an identifier.
        Tries to see wether it is equal to a keyword.
        Does not change any parse results
        '''
##        #debug code-----------------
##        if   self.debugSyntax == 2:
##            return
        #toks is structured like this: ['a1']
        if toks[0] in self.keywords:
            #print 'found keyword', toks[0], 'at loc: ', loc
            #raise ParseException(str, loc, 'Identifier same as keyword: %s' % toks[0])
            raise ParseFatalException(
                str, loc, 'Identifier same as keyword: %s' % toks[0] )


#------------------- BNF --------------------------------------------------------*
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
        #TODO: this should be a for loop and a list (attribute)!
        builtInValue = Group( kw('pi') | kw('time'))                .setParseAction(AddMetaDict('builtInVal'))\
                                                                    .setName('builtInValue')#.setDebug(True)

        #Functions that are built into the language
        #TODO: this should be a for loop and a list (attribute)!
        builtInFuncName = (  kw('sin') | kw('cos') | kw('tan') |
                             kw('sqrt') | kw('exp') | kw('ln')   )  .setName('builtInFuncName')#.setDebug(True)

        #Integer (unsigned).
        uInteger = Word(nums)                                       .setName('uInteger')#.setDebug(True)
        #Floating point number (unsigned).
        eE = CaselessLiteral( 'E' )
        uNumber = Group( Combine(
                    uInteger +
                    Optional('.' + Optional(uInteger)) +
                    Optional(eE + Word('+-'+nums, nums))))          .setParseAction(AddMetaDict('num'))\
                                                                    .setName('uNumber')#.setDebug(True)

        # .............. Mathematical expression .............................................................
        #'Forward declarations' for recursive rules
        expression = Forward()
        term =  Forward()
        factor = Forward()
        signedAtom = Forward()
        valAccess = Forward() #For PDE: may also contain expressions for slices: a.b.c(2.5:3.5)

        #Basic building blocks of mathematical expressions e.g.: (1, x, e,
        #sin(2*a), (a+2), a.b.c(2.5:3.5))
        #Function call, parenthesis and memory access can however contain
        #expressions.
        funcCall = Group( builtInFuncName + '(' + expression + ')') .setParseAction(AddMetaDict('funcCall')) \
                                                                    .setName('funcCall')#.setDebug(True)
        parentheses = Group('(' + expression + ')')                 .setParseAction(AddMetaDict('paren')) \
                                                                    .setName('parentheses')#.setDebug(True)
        atom = (    uNumber | builtInValue | funcCall |
                    valAccess | parentheses               )         .setName('atom')#.setDebug(True)

        #The basic mathematical operations: -a+b*c^d.
        #All operations have right-to-left associativity; althoug this is only
        #required for exponentiation. Precedence decreases towards the bottom.
        #Unary minus: -a, not a;
        negop = '-' | kw('not')
        unaryMinus = Group(negop + signedAtom)          .setParseAction(AddMetaDict('m_p1')) \
                                                        .setName('unaryMinus')#.setDebug(True)
        signedAtom << (atom | unaryMinus)               .setName('signedAtom')#.setDebug(True)

        #Exponentiation: a^b;
        factor1 = signedAtom                            .setName('factor1')#.setDebug(True)
        factor2 = Group(signedAtom + '**' + factor)     .setParseAction(AddMetaDict('m_i2')) \
                                                        .setName('factor2')#.setDebug(True)
        factor << (factor2 | factor1)                   .setName('factor')#.setDebug(True)

        #multiplicative operations: a*b; a/b
        multop = L('*') | L('/') | L('and')
        term1 = factor                                  .setName('term1')#.setDebug(True)
        term2 = Group(factor + multop + term)           .setParseAction(AddMetaDict('m_i2')) \
                                                        .setName('term2')#.setDebug(True)
        term << (term2 | term1)                         .setName('term')#.setDebug(True)

        #additive operations: a+b; a-b
        addop  = L('+') | L('-') | L('or')
        expression1 = term                              .setName('expression1')#.setDebug(True)
        expression2 = Group(term + addop + expression)  .setParseAction(AddMetaDict('m_i2')) \
                                                        .setName('expression2')#.setDebug(True)
        expression << (expression2 | expression1)       .setName('expression')#.setDebug(True)

        #Relational operators : <, >, ==, ...
        relop = L('<') | L('>') | L('<=') | L('>=') | L('==')
        boolExpression = Group(expression + relop + expression) .setParseAction(AddMetaDict('m_i2')) \
                                                                .setName('expression2')#.setDebug(True)
        #................ End mathematical expression ................................................---

        #................ Identifiers ...................................................................
        #TODO: check for keywods -  .setParseAction(self.actionCheckIdentifier) \
        identifier = Word(alphas, alphas+nums+'_')              .setName('identifier')#.setDebug(True)

        #Compound identifiers for variables or parameters 'aaa.bbb'.
        #TODO: add slices: aaa.bbb(2:3)
        dotSup = Literal('.').suppress()
        valAccess << Group( Optional('$') +
                            identifier +
                            ZeroOrMore(dotSup  + identifier) )  .setParseAction(AddMetaDict('valA')) \
                                                                .setName('valAccess')#.setDebug(True)

        #..................... Statements ..............................................................
        statementList = Forward()
        #Flow control - if then else
        ifStatement = Group(
                        kw('if') + boolExpression + kw('then') +
                        statementList +
                        Optional(kw('else') + statementList) +
                        kw('end'))                                  .setParseAction(AddMetaDict('ifStmt'))\
                                                                    .setName('ifStatement')#.setDebug(True)
        #compute expression and assign to value
        assignment = Group(valAccess + ':=' + expression + ';')     .setParseAction(AddMetaDict('assign'))\
                                                                    .setName('assignment')#.setDebug(True)
        #execute a block - insert code of a child model
        blockName = kw('run') | kw('init') #| kw('insert')
        blockExecute = Group(blockName + identifier + ';')          .setParseAction(AddMetaDict('blockExecute'))\
                                                                    .setName('blockExecute')#.setDebug(True)

        statement = (blockExecute | ifStatement | assignment)       .setName('statement')#.setDebug(True)
        statementList << Group(OneOrMore(statement))                .setParseAction(AddMetaDict('stmtList'))\
                                                                    .setName('statementList')#.setDebug(True)

#---------- Class Def ---------------------------------------------------------------------*
        #define parameters, variables and submodels
        defRole = kw('par') | kw('var') | kw('sub') 
        attributeDef = Group(defRole + identifier + 
                             Optional(kw('as') + identifier) + ';') .setParseAction(AddMetaDict('defAttr'))\
                                                                    .setName('attributeDef')#.setDebug(True)
        #Note: For the AST this is also a statementList-'stmtList'
#        definitionList = Group(OneOrMore(attributeDef))             .setParseAction(AddMetaDict('stmtList'))\
#                                                                    .setName('definitionList')#.setDebug(True)

        #The statements (equations) that determine the system dynamics go here
        runBlock = Group(   kw('block') + kw('run') +
                            #statementList +
                            OneOrMore(statement) + 
                            kw('end'))                              .setParseAction(AddMetaDict('blockDef'))\
                                                                    .setName('runBlock')#.setDebug(True)

        #The initialization code goes here
        initBlock = Group(  kw('block') + kw('init') +
                            #statementList +
                            OneOrMore(statement) + 
                            kw('end'))                              .setParseAction(AddMetaDict('blockDef'))\
                                                                    .setName('initBlock')#.setDebug(True)

        classRole = kw('process') | kw('model') #| kw('paramset')
        classDef = Group(   classRole + identifier +
                            #Optional(definitionList) +
                            OneOrMore(attributeDef) +
                            Optional(runBlock) +
                            Optional(initBlock)  +
                            kw('end'))                              .setParseAction(AddMetaDict('classDef'))\
                                                                    .setName('classDef')#.setDebug(True)

        program = Group(OneOrMore(classDef))                        .setParseAction(AddMetaDict('program'))\
                                                                    .setName('program')#.setDebug(True)
        #................ End of language definition ..................................................

        #determine start symbol
        startSymbol = program
        #set up comments
        singleLineCommentCpp = '//' + restOfLine
        singleLineCommentPy = '#' + restOfLine
        startSymbol.ignore(singleLineCommentCpp)
        startSymbol.ignore(singleLineCommentPy)

        return startSymbol


    #TODO: Maybe write: parseExpression, parseMemAccess, ...
    def parseProgram(self, inString):
        '''Parse a whole program. The program is entered as a string.'''
        result = self._parser.parseString(inString)
        #TODO: test if input string is consumed completely
        #TODO: store loc of last parsed statement; for error message generation.
        #TODO: catch ParseExceptions, generate UserExceptions
        return result



class AddMetaDict(object):
    '''
    Functor class to add a dict to a ParseResults object in a semantic action.
    The meta dict contains (at least) the result's type and the location in the
    input string:
    {'typ':'foo', 'loc':23}

    Additionally adds type string to a central list
    (ParseStage.nodeTypes - really a set) for checking the consistency
    '''
    def __init__(self, typeString):
        '''typeString : string to identify the node.'''
        object.__init__(self)
        self.typeString = typeString
         #add to set of known type strings
        ParseStage.nodeTypes.add(typeString)


    def __call__(self,str, loc, toks):
        '''The parse action that adds the dict.'''
        #debug code-----------------
        if   ParseStage.debugSyntax == 2:
            return None
        elif ParseStage.debugSyntax == 1:
            return toks.copy()

        #toks is structured like this [['pi']]
        newToks = ParseResults([{'typ':self.typeString, 'loc':loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.



class ASTGeneratorException(Exception):
    '''Exception raised by the ASTGenerator class'''
    pass



class ASTGenerator(object):
    '''Create a syntax tree from the parsers output'''
    #TODO: integrate this class with ParseStage. 
    #TODO: Replace the ParseResults objects with Node objects in semantic actions.
    #TODO: This class' methods would become the semantic actions

    def __init__(self):
        object.__init__(self)
        pass


    def _createPrefixOp(self, tokList):
        '''
        Create node for math prefix operators: -
        Parameter tokList has the following structure:
        [<meta dictionary>, <operator>, <expression_l>]
        '''
        nCurr = NodeOpPrefix1('m_p1')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #create the child and store operator
        nCurr.dat = tokList[1]                     #operator
        childTree = self._createSubTree(tokList[2]) #child
        nCurr.kids=[childTree]
        return nCurr


    def _createInfixOp(self, tokList):
        '''
        Create node for math infix operators: + - * / ^
        Parameter tokList has the following structure:
        [<meta dictionary>, <expression_l>, <operator>, <expression_r>]
        '''
        nCurr = NodeOpInfix2('m_i2')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #create children and store operator
        lhsTree = self._createSubTree(tokList[1]) #child lhs
        nCurr.dat = tokList[2]                    #operator
        rhsTree = self._createSubTree(tokList[3]) #child rhs
        nCurr.kids=[lhsTree, rhsTree]
        return nCurr


    def _createFunctionCall(self, tokList):
        '''
        Create node for function call: sin(2.1)
        Parameter tokList has the following structure:
        [<meta dictionary>, <function dentifier>, '(', <expression>, ')']
        '''
        nCurr = NodeBuiltInFuncCall('funcCall')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #store child expession and function name
        nCurr.dat = tokList[1]                       #function dentifier
        nCurr.kids=[self._createSubTree(tokList[3])] #child expression
        return nCurr


    def _createParenthesePair(self, tokList):
        '''
        Create node for a pair of parentheses that enclose an expression: (...)
        Parameter tokList has the following structure:
        [<meta dictionary>, '(', <expression>, ')']
        '''
        nCurr = NodeParentheses('paren')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Create and store child expression
        nCurr.kids = [self._createSubTree(tokList[2])]
        return nCurr


    def _createNumber(self, tokList):
        '''
        Create node for a number: 5.23
        Parameter tokList has the following structure:
        [<meta dictionary>, <number>]
        '''
        nCurr = NodeNum('num')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Store the number
        nCurr.dat = tokList[1]
        return nCurr


    def _createBuiltInValue(self, tokList):
        '''
        Create node for a built in value: pi, time
        Parameter tokList has the following structure:
        [<meta dictionary>, <identifier>]
        '''
        nCurr = NodeBuiltInVal('builtInVal')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Store the built in value's name
        nCurr.dat = tokList[1]
        return nCurr


    def _createValueAccess(self, tokList):
        '''
        Create node for acces to a variable or parameter: bb.ccc.dd
        Parameter tokList has the following structure:
        [<meta dictionary>, <part1>, <part2>, <part3>, ...]
        '''
        nCurr = NodeAttrAccess('valA')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Look if there is a '$' that indicates time derivatives
        tok1 = 1
        if tokList[1] == '$':
            nCurr.deriv = ('time',)
            tok1 = 2
        #The remaining tokens are the dot separated name
        nCurr.attrName = tuple(tokList[tok1:len(tokList)]) 
        return nCurr


    def _createIfStatement(self, tokList):
        '''
        Create node for if - then - else statement.
        type string: 'ifStmt'
        BNF:
        ifStatement = Group(
                    kw('if') + boolExpression + kw('then') +
                    statementList +
                    Optional(kw('else') + statementList) +
                    kw('end'))
        '''
        nCurr = Node('ifStmt')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #create children
        if len(tokList) == 5:
            condition = self._createSubTree(tokList[2])
            thenStmts = self._createSubTree(tokList[4])
            nCurr.kids=[condition, thenStmts]
        elif len(tokList) == 7:
            condition = self._createSubTree(tokList[2])
            thenStmts = self._createSubTree(tokList[4])
            elseStmts = self._createSubTree(tokList[6])
            nCurr.kids=[condition, thenStmts, elseStmts]
        else:
            raise ASTGeneratorException('Broken >if< statement! loc: ' + str(nCurr.loc))
        return nCurr


    def _createAssignment(self, tokList):
        '''
        Create node for assignment: a := 2*b
        type string: 'assign'
        BNF:
        assignment = Group(valAccess + ':=' + expression + ';')
        '''
        nCurr = NodeAssignment('assign')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #create children and store operator
        lhsTree = self._createSubTree(tokList[1]) #child lhs
        nCurr.dat = tokList[2]                    #operator
        rhsTree = self._createSubTree(tokList[3]) #child rhs
        nCurr.kids=[lhsTree, rhsTree]
        return nCurr


    def _createBlockExecute(self, tokList):
        '''
        Create node for execution of a block (insertion of the code): run foo
        type string: 'blockExecute'
        BNF:
        blockName = kw('run') | kw('init') #| kw('insert')
        blockExecute = Group(blockName + subModelName + ';')
        '''
        nCurr = NodeBlockExecute('blockExecute')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Store the data
        blockName = tokList[1]                    #block name - operator
        modelName = tokList[2]                    #Name of model from where block is taken
        nCurr.blockName = blockName
        nCurr.subModelName = modelName
        return nCurr


    def _createStatementList(self, tokList):
        '''
        Create node for list of statements: a:=1; b:=2; ...
        type string: 'stmtList'
        BNF:
        statementList << Group(OneOrMore(statement))
        '''
        nCurr = NodeStmtList('stmtList')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #create children - each child is a statement
        for tok in tokList[1:len(tokList)]:
            child = self._createSubTree(tok)
            nCurr.kids.append(child)
        return nCurr


    def _createAttrDefinition(self, tokList):
        '''
        Create node for defining parameterr, variable or submodel: var foo;
        type string: 'defAttr'
        BNF:
        defRole = kw('par') | kw('var') | kw('sub') 
        attributeDef = Group(defRole + identifier + 
                             Optional(kw('as') + identifier + ';'))
        '''
        nCurr = NodeAttrDef('defAttr')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #These are aways present
        roleStr = tokList[1]                    #var, par, sub
        #TODO: change attrName into tuple(tokList[2])
        nCurr.attrName = tokList[2] #identifier; name of the attribute
        #attribute is a submodel
        if roleStr == 'sub':
            nCurr.className = tokList[4]
            nCurr.isSubmodel = True
            nCurr.role = None
        #attribute is a variable or parameter
        else:
            nCurr.className = 'Real'
            nCurr.isSubmodel = False
            nCurr.isStateVariable = False
            nCurr.role = roleStr
        return nCurr


    def _createBlockDefinition(self, tokList):
        '''
        Create node for definition of a block: block run a:=1; end
        type string: 'blockDef'
        BNF:
        runBlock = Group(   kw('block') + blockName +
                            OneOrMore(statement) + 
                            kw('end'))
        '''
        nCurr = NodeBlockDef('blockDef')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #store name of block 
        blockName = tokList[2]
        nCurr.name = blockName     
        #create children - each child is a statement
        for tok in tokList[3:len(tokList)-1]:
            child = self._createSubTree(tok)
            nCurr.kids.append(child)
        return nCurr


    def _createClassDef(self, tokList):
        '''
        Create node for definition of a class: model foo ... end
        type string: 'classDef'
        BNF:
        classRole = kw('process') | kw('model') #| kw('paramset')
        classDef = Group(   classRole + identifier +
                            OneOrMore(attributeDef) +
                            Optional(runBlock) +
                            Optional(initBlock)  +
                            kw('end'))
        '''
        nCurr = NodeClassDef('classDef')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #store role and class name - these are always present
        role = tokList[1]
        name = tokList[2]
        nCurr.className = name
        nCurr.role = role
        #create children (may or may not be present):  definitions, run block, init block
        for tok in tokList[3:len(tokList)-1]:
            if not isinstance(tok, list):
                break
            child = self._createSubTree(tok)
            nCurr.kids.append(child)
        return nCurr


    def _createProgram(self, tokList):
        '''
        Create the root node of a program.
        type string: 'program'
        BNF:
        program = Group(OneOrMore(classDef))
        '''
        nCurr = Node('program')
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        nCurr.typ = 'AST' #make it look mor like the ILT
        #create children - each child is a class
        for tok in tokList[1:len(tokList)]:
            child = self._createSubTree(tok)
            nCurr.kids.append(child)
        return nCurr


    funcDict = {
        'm_p1':_createPrefixOp, 'm_i2':_createInfixOp,
        'funcCall':_createFunctionCall, 'paren':_createParenthesePair,
        'num':_createNumber, 'builtInVal':_createBuiltInValue,
        'valA':_createValueAccess, 'ifStmt':_createIfStatement,
        'assign':_createAssignment, 'blockExecute':_createBlockExecute,
        'stmtList':_createStatementList, 'defAttr':_createAttrDefinition,
        'blockDef':_createBlockDefinition, 'classDef':_createClassDef,
        'program':_createProgram }
    '''Dictionary with type string and node creator function.'''


    def _createSubTree(self, tokList):
        '''Central dispatcher function for recursive tree construction.
        tokList is a nested list.'''

        #First list item is a dict with meta information.
        metaDict = tokList[0]
        if not isinstance(metaDict, type({})):
            raise ASTGeneratorException('Node has no metadict!')

        nType = metaDict['typ']             #Get node type.
        creatorFunc = self.funcDict[nType]  #Find matching creator function
        return creatorFunc(self, tokList)   #call ceator function


    def createSyntaxTree(self, parseResult):
        '''
        Create the syntax tree from a ParseResult.
        parameter parseResult: ParseResult object, or nested list.
        '''
        if isinstance(parseResult, ParseResults): #Parse result objects
            tokList = parseResult.asList()        #must be converted to lists
            tokList = tokList[0]     #remove one pair of square brackets
        else:
            tokList = parseResult
        #pdb.set_trace()
        return self._createSubTree(tokList)
    


class ILTGenException(Exception):
    '''Exception thrown by the ILT-Process Generator (Compiler internal error)'''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        
        
        
class ILTProcessGenerator(object):
    '''
    Generate process for the intermediate language tree (ILT).
    
    Takes a process from the AST and generates a new process. This new process 
    contains the atributes of all submodels. The code of the submodels' blocks 
    is inserted (imlined) into the new process' blocks.
    The new process is a 'flattened' version of the original structured process.
    '''
    def __init__(self, astRoot):
        self.astRoot = astRoot
        '''The AST'''
        self.astClasses = {}
        '''dict of classes in ast: {'mod1':NodeClassDef}'''
        self.astProcess = NodeClassDef('Dummy') 
        '''the original process that is now instantiated'''
        self.astProcessAttributes = {}
        '''Atributes of the original process. Dict: {('mod1', 'var1'):NodeAttrDef}'''
        self.process = NodeClassDef('Dummy') 
        '''The new process which is currently assembled'''
        self.processAttributes = {}
        '''Attributes of the new process: {('mod1', 'var1'):NodeAttrDef}'''
        self.stateVariables = {}
        '''State variables of the new process; {('mod1', 'var1'):NodeAttrDef}'''
        
        #populate self.classes and self.processes 
        self.findClassesInAst()

    
    def findClassesInAst(self):
        '''
        Extract all class definitions from the ast and put them into self.classes.
        Additionally the process definitions go into self.processes.
        '''
        for classDef in self.astRoot:
            self.astClasses[classDef.className] = classDef
                

    def addBuiltInParameters(self):
        '''
        Some parameters exist without beeing defined; create them here.
        
        -In a later stage they could be inherited from a base class.
        -This method could be expanded into a more general mechanism for 
         built-in values, like pi.
        '''
        #Put solutionparameters as first attribute into the process
        solParAttr = NodeAttrDef(typ='built-in attribute',  loc=0,
                                 attrName='solutionParameters', 
                                 className='solutionParametersClass',
                                 isSubmodel=True)
        self.astProcess.insertChild(0, solParAttr)
        
        
    def findAttributesRecursive(self, astClass, namePrefix):
        '''
        Find all of the process' attributes (recursing into the sub-models)
        and put then into self.astProcessAttributes.
        
        Attributes are: parameters, variables, sub-models, and functions.
        The definition in the AST is searched NOT the new process.
        Output is: self.astProcessAttributes
        '''
        #each of the class' children is a definition
        for attrDef in astClass:
            #get attribute name
            if isinstance(attrDef, NodeAttrDef): #definition of data attribute or submodel
                attrName = attrDef.attrName
            elif isinstance(attrDef, NodeBlockDef): #definition of block (function)
                attrName = attrDef.name
            else:
                raise ILTGenException('Unknown Node.' + repr(attrDef))
            #prepend prefix to attribute name 
            #TODO: clean up last remains of tuple - list mess
            longAttrName = namePrefix + [attrName]
            longAttrNameTup = tuple(longAttrName)
            #Check redefinition
            if longAttrNameTup in self.astProcessAttributes:
                raise UserException('Redefinition of: ' + makeDotName(longAttrName), attrDef.loc)
            #put new attribute into dict.
            self.astProcessAttributes[longAttrNameTup] = attrDef
            
            #recurse into submodel, if definition of submodel 
            if isinstance(attrDef, NodeAttrDef) and attrDef.isSubmodel:                
                #User visible error if class does not exist
                if not attrDef.className in self.astClasses:
                    raise UserException('Undefined class: ' + attrDef.className, attrDef.loc)
                subModel = self.astClasses[attrDef.className]
                self.findAttributesRecursive(subModel, longAttrName)
        
        
    def copyDataAttributes(self):
        '''
        Copy variables and parameters from all submodels into the procedure
        Additionaly puts all attributes into self.processAttributes
        arguments:
            model      : A class definition from the AST
            namePrefix : a list of strings. prefix for the dotted name of the class' attributes.
        '''
        #Iterate over the (variable, parameter, submodel, function) definitions
        for longName, defStmt in self.astProcessAttributes.iteritems():
            #we only care for data attributes
            if (not isinstance(defStmt, NodeAttrDef)) or defStmt.isSubmodel:
                continue
            newAttr = defStmt.copy() #copy definition, 
            newAttr.attrName = longName #exchange name with long name (a.b.c)
            self.process.appendChild(newAttr) #put new attribute into ILT process
            self.processAttributes[longName] = newAttr #and into quick access dict
        return
       
       
    def copyBlockRecursive(self, block, namePrefix, newBlock, allowedBlocks):
        '''
        Copy block into newBlock recursively. 
        Copies all statements of block and all statements of blocks that are 
        executed in this block, recursively.
            block          : A block definition 
            namePrefix     : a list of strings. prefix for all variable names.
            newBlock       : the statements are copied here
            allowedBlocks  : ['run'] or ['init']
        '''
        for statement in block:
            #Block execution statement: include the called blocks variables
            if isinstance(statement, NodeBlockExecute):
                subModelName = namePrefix + [statement.subModelName]
                subBlockName = subModelName + [statement.blockName]
                #Error if submodel or method does not exist
                if not tuple(subModelName) in self.astProcessAttributes:
                    raise UserException('Undefined submodel: ' + 
                                        str(subModelName), statement.loc)
                if not tuple(subBlockName) in self.astProcessAttributes:
                    raise UserException('Undefined method: ' + 
                                        str(subBlockName), statement.loc)
                #Check if executing (inlining) this block is allowed
                if not (statement.blockName in allowedBlocks):
                    raise UserException('Method can not be executed here: ' + 
                                        str(statement.blockName), statement.loc)
                #find definition of method, and recurse into it.
                subBlockDef = self.astProcessAttributes[tuple(subBlockName)] 
                self.copyBlockRecursive(subBlockDef, subModelName, newBlock, allowedBlocks)
            #Any other statement: copy statement
            else:
                newStmt = statement.copy()
                #put prefix before all varible names in new Statement
                for var in newStmt.iterDepthFirst():
                    if not isinstance(var, NodeAttrAccess):
                        continue
                    newAttrName = tuple(namePrefix) + var.attrName
                    var.attrName = tuple(newAttrName)
                #put new statement into new block
                newBlock.appendChild(newStmt)



    def checkUndefindedReferences(self, tree):
        '''
        Look at all attribute accessors and see if the attributes exist in 
        the new process.
        '''
        #iterate over all nodes in the syntax tree
        for node in tree.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            if not (node.attrName) in self.processAttributes:
                raise UserException('Undefined reference: ' + 
                                    makeDotName(node.attrName), node.loc)



    def findStateVariables(self, block):
        '''Search for variables with a $ and put them into self.stateVariables'''
        #self.stateVariables = {}
        #iterate over all nodes in the syntax tree and search for variable accesses
        for node in block.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            #State variables are those that have time derivatives
            if node.deriv != ('time',):
                continue
            
            #get definition of variable 
            stateVarDef = self.processAttributes[node.attrName]
            #Check conceptual constraint: no $parameter allowed
            if stateVarDef.role == 'par':
                raise UserException('Parameters can not be state variables: ' +
                              makeDotName(node.attrName), node.loc)
            #remember: this is a state variable; in definition and in dict
            stateVarDef.isStateVariable = True
            self.stateVariables[node.attrName] = stateVarDef
    
    
    
    def checkRunMethodConstraints(self, block):
        '''See if the method is a valid run method.'''
        #iterate over all nodes in the syntax tree and search for assignments
        for node in block.iterDepthFirst():
            if not isinstance(node, NodeAssignment):
                continue
            lVal = node.lhs() #must be NodeValAccess
            lValDef = self.processAttributes[lVal.attrName]
            #No assignment to parameters 
            if lValDef.role == 'par':
                raise UserException('Illegal assignment to parameter: ' + 
                                    makeDotName(lVal.attrName), lVal.loc)
            #No assignment to state variables - only to their time derivatives
            if lValDef.isStateVariable and (lVal.deriv != ('time',)):
                raise UserException('Illegal assignment to state variable: ' + 
                                    makeDotName(lVal.attrName) + 
                                    '. You must however assign to its time derivative. ($' + 
                                    makeDotName(lVal.attrName) +')', lVal.loc)

    
    def checkInitMethodConstraints(self, block):
        '''See if the method is a valid init method.'''
        #iterate over all nodes in the syntax tree and search for variable accesses
        for node in block.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            #$ operators are illegal in init method
            if node.deriv == ('time',):
                raise UserException('Time derivation illegal in init: ' +
                                    str(node.attrName), node.loc) 
    
    
    def createProcess(self, inAstProc):
        '''generate ILT subtree for one process'''
        #store original process
        self.astProcess = inAstProc.copy()
        #init new process
        self.process = NodeClassDef('ILTProcess')
        self.process.className = self.astProcess.className
        self.process.role = self.astProcess.role
        #init quick reference dicts
        self.processAttributes = {}
        self.astProcessAttributes = {}
        self.stateVariables = {}
        
        #add some built in attributes to the process
        self.addBuiltInParameters()
        #discover all attributes 
        self.findAttributesRecursive(self.astProcess, [])
        #create the new process' data attributes
        self.copyDataAttributes()
        #create the new process' blocks (methods)
        runBlock, initBlock, blockCount = None, None, 0
        for block in self.astProcess:
            if not isinstance(block, NodeBlockDef):
                continue
            #create the new method (block) definition
            newBlock = NodeBlockDef('ILTBlock') 
            newBlock.name = block.name
            blockCount += 1 #count the number of blocks
            #determine which methods can be executed in this method
            if block.name == 'run':
                allowedBlocks = ['run'] #list of compatible methods
                runBlock = newBlock     #remember which block is which
            elif block.name == 'init':
                allowedBlocks = ['init']
                initBlock = newBlock
            else:
                raise UserException('Illegal method: ' + str(block.name), 
                                    block.loc)
            #copy the statements, and put new method into new procedure
            self.copyBlockRecursive(block, [], newBlock, allowedBlocks) 
            self.process.kids.append(newBlock) #put new block into process
        
        if (not runBlock) or (not initBlock) or (blockCount != 2):
            raise UserException('Process must contain exactly one run method ' + 
                                'and one init method.', self.astProcess.loc)
        self.checkUndefindedReferences(self.process) #Check undefined refference
        self.findStateVariables(runBlock) #Mark state variables
        self.checkRunMethodConstraints(runBlock)
        self.checkInitMethodConstraints(initBlock)
        
        #TODO: Check correct order of assignments (or initialization).
        #TODO: Check if all variables have been assigned; 
        #TODO: Propagate parameters - only replace those that have not been explicitly initialized.
        #TODO: Check if all parameters and state vars have been initialized.
        
        return self.process

        
    
class ILTGenerator(object):
    '''
    Generate a tree that represents the intermediate language.
    intermediate language tree (ILT)
    '''
   
    def __init__(self):
        super(ILTGenerator, self).__init__()
   
   
    def addBuiltInClasses(self, astRoot):
        '''
        Some classes exist without beeing defined; create them here.
        
        -This method could be expanded into a more general mechanism for 
         built-in values and functions, like pi, sin(x).
        '''
        #Create the solution parameters' definition
        solPars = NodeClassDef(typ='built-in class', loc=0,
                               name='solutionParametersClass', role='model')
        solPars.appendChild(NodeAttrDef(typ='built-in param',  loc=0,
                                        attrName='simulationTime', 
                                        className='Real', role='par'))
        solPars.appendChild(NodeAttrDef(typ='built-in param',  loc=0,
                                        attrName='reportingInterval', 
                                        className='Real', role='par'))
        #add solutionparameTers to AST, and update class dict
        astRoot.insertChild(0, solPars) 


    def createIntermediateTree(self, astRoot):
        '''generate ILT tree from AST tree'''
        #add built ins to AST
        self.addBuiltInClasses(astRoot)
        #create ILT root node
        iltRoot = Node('ILT')
        
        procGen = ILTProcessGenerator(astRoot)
        #searc for processes in the AST and instantiate them in the ILT
        for processDef in astRoot:
            if ((not isinstance(processDef, NodeClassDef)) or 
                (not processDef.role == 'process')):
                continue
            newProc = procGen.createProcess(processDef)
            iltRoot.appendChild(newProc)
        return iltRoot
    
    
    
def doTests():
    '''Perform various tests.'''

    #t1 = Node('root', [Node('child1',[]),Node('child2',[])])
    #print t1

#------------ testProg1 -----------------------
    testProg1 = (
'''
model Test
    var V; var h;
    par A_bott; par A_o; par mu;
    par q; par g;
    
    block run
        h := V/A_bott;
        $V := q - mu*A_o*sqrt(2*g*h);
    end
    
    block init
        V := 0;
        A_bott := 1; A_o := 0.02; mu := 0.55;
        q := 0.05;
    end
end

process RunTest
    sub test as Test;
    
    block run
        run test;
    end
    block init
        init test;
    end
end
''' )

#------------ testProg2 -----------------------
    testProg2 = (
'''
model Test
    var a;

    block run
        $a := 0.5;
    end
    block init
        a := 1;
    end
end

process RunTest
    sub test as Test;
    
    block run
        run test;
    end
    
    block init
        init test;
    end
end 
''' )
    #test the intermedite tree generator ------------------------------------------------------------------
    flagTestILTGenerator = True
    #flagTestILTGenerator = False
    if flagTestILTGenerator:
        parser = ParseStage()
        astGen = ASTGenerator()
        iltGen = ILTGenerator()
        
        pres = parser.parseProgram(testProg1)
        print 'parse result:'
        print pres
        astTree = astGen.createSyntaxTree(pres)
        print 'AST tree:'
        print astTree
 
        iltTree = iltGen.createIntermediateTree(astTree)
        print 'ILT tree:'
        print iltTree
        
        
    #test the AST generator ------------------------------------------------------------------
    #flagTestASTGenerator = True
    flagTestASTGenerator = False
    if flagTestASTGenerator:
        parser = ParseStage()
        treeGen = ASTGenerator()

        pres = parser.parseProgram(testProg1)
        print 'parse result:'
        print pres
        astTree = treeGen.createSyntaxTree(pres)
        print 'tree:'
##        print tree
        TreePrinter(astTree).printTree()

    #test the parser ----------------------------------------------------------------------
    #flagTestParser = True
    flagTestParser = False
    if flagTestParser:
        parser = ParseStage()
        #ParseStage.debugSyntax = 1
        #ParseStage.debugSyntax = 2
        #print parser.parseProgram('model test var a; par b; end')
        #print parser.parseProgram('model test par a; end')


        print parser.parseProgram(testProg2)

        #print parser.parseProgram('a:=0+1;b:=2+3+4;')
        #print parser.parseProgram('if a==0 then b:=-1; else b:=2+3+4; a:=1; end')
        #print parser.parseProgram('0*1*2*3*4')
        #print parser.parseProgram('0^1^2^3^4')
        #print parser.parseProgram('0+1*2+3+4')
        #print parser.parseProgram('0*1^2*3*4')
        #print parser.parseProgram('0+(1+2)+3+4')
        #print parser.parseProgram('-0+1+--2*-3--4')
        #print parser.parseProgram('-aa.a+bb.b+--cc.c*-dd.d--ee.e+f')
        #print parser.parseProgram('0+sin(2+3*4)+5')
        #print parser.parseProgram('0+a1.a2+bb.b1.b2+3+4 #comment')
        #print parser.parseProgram('0.123+1.2e3')
        #parser.parseProgram('0+1*2^3^4+5+6*7+8+9')

        print 'keywords:'
        print parser.keywords
        print 'node types'
        print parser.nodeTypes
    
    #Check if the parser and the AST generator use the same type strings ---------------------------------
    #to identify the nodes.
    typeStrParser = ParseStage.nodeTypes
    typeStrASTGenerator = set(ASTGenerator.funcDict.keys())
    print
    if typeStrASTGenerator == typeStrParser:
        print 'Parser and AST generator use the same type strings.'
    else:
        print 'Error: Parser and AST generator use DIFFERENT type strings!'
        print 'Type strings only in parser: '
        print typeStrParser.difference(typeStrASTGenerator)
        print 'Type strings only in AST generator: '
        print typeStrASTGenerator.difference(typeStrParser)


##    pdb.set_trace()


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
