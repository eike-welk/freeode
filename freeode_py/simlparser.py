#***************************************************************************
#    Copyright (C) 2006 by Eike Welk                                       *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration came from:                                                *
#    "fourFn.py", an example program, by Paul McGuire                      *
#    and the "Spark" library by John Aycock                                *
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
"""
Parser for the SIML simulation language.
"""
#TODO: usage (above)

import pprint #pretty printer
import pdb    #debuber

from pyparsing import Literal,CaselessLiteral,Keyword,Word,Combine,Group,Optional, \
    ZeroOrMore,OneOrMore,Forward,nums,alphas,restOfLine,ParseResults, ParseException, \
    ParseFatalException


pp = pprint.PrettyPrinter(indent=4)


class ParseStage(object):
    """
    The syntax definition (BNF) resides here.
    Mainly a wrapper for the Pyparsing library and therefore combines lexer
    and parser. The Pyparsing library generates a ParseResult object which is
    modfied through parse actions by this class.

    The program is entered as a string.
    ParseResult objects can be converted to nested lists: ["1", "+", ["2", "*", "3"]]

    Usage:
    parser = ParseStage()
    result = parser.parseProgram("0+1+2+3+4")
    """


    debugSyntax = 0
    """
    Define how much the parse result is modified, for easier debuging.
    0: normal operation. Compilaton does not work otherwise.
    1: No additional information and no reordering, but copy ParseResult;
    2: Do not modify parse result (from pyParsing library).
    """

    keywords = set([])
    """
    List of all keywords (filled by defineLanguageSyntax() and defineKeyword).
    """

    nodeTypes = set([])
    """
    List of all type strings, that identify the nodes in the parse result.
    Filled by defineNodeType() in the semantic actions; or by the AddMetaDict
    object.
    """


    def __init__(self):
        object.__init__(self)
        self._parser = self.defineLanguageSyntax() #Create parser object
        """The parser object from pyParsing"""


    def defineKeyword(self, inString):
        """
        Store keyword (in ParseStage.keywords) and create parser for it.
        Use this function (in defineLanguageSyntax(...)) instead of using the
        Keyword class directly.
        """
        ParseStage.keywords.add(inString)
        return Keyword(inString)


    def defineNodeType(self, inString):
        """Store type string (in ParseStage.nodeTypes) and return it."""
        ParseStage.nodeTypes.add(inString)
        return inString


#------------- Parse Actions -------------------------------------------------*
    def actionDebug(self, str, loc, toks):
        """Parse action for debuging."""
        print "------debug action"
        print str
        print loc
        print toks
        print "-------------------"
        return toks


    #def actionInfixBinOp(self, str, loc, toks):
        #"""
        #Parse action for binary mathematical operations: + - * / ^
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ## toks is structured like this [["2","+","5"]]
        #typeStr = self.defineNodeType("m_i2")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    #def actionPrefixUnaryOp(self, str, loc, toks):
        #"""
        #Parse action for mathematical unary operations: -5 .
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ## toks is structured like this [["-","5"]]
        #typeStr = self.defineNodeType("m_p1")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    #def actionValAccess(self, str, loc, toks):
        #"""
        #Parse action for memory access: aa.bb.cc
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ## toks is structured like this [["aa","bb","cc"]]
        #typeStr = self.defineNodeType("valA")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    #def actionFuncCall(self, str, loc, toks):
        #"""
        #Parse action for function call: sin(2.1)
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ## toks is structured like this [['sin','(',['2.1'],')']]
        #typeStr = self.defineNodeType("funcCall")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    #def actionParentheses(self, str, loc, toks):
        #"""
        #Parse action for pair of parentheses: ( 1+2 ).
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ##toks is structured like this [['(', ['1', '+', '2'], ')']]
        #typeStr = self.defineNodeType("paren")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    #def actionNumber(self, str, loc, toks):
        #"""
        #Parse action for a real number: 5.23 .
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ##toks is structured like this [['5.23']]
        #typeStr = self.defineNodeType("num")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    #def actionbuiltInValue(self, str, loc, toks):
        #"""
        #Parse action for a built in value: pi .
        #Put additional information into parse result, that would
        #be lost otherwise. The information is stored in a dict, and put before
        #the original parse result.
        #"""
        ##debug code-----------------
        #if   self.debugSyntax == 2:
            #return None
        #elif self.debugSyntax == 1:
            #return toks.copy()

        ##toks is structured like this [['pi']]
        #typeStr = self.defineNodeType("builtInVal")
        #newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        #newToks += toks[0].copy() #add original contents
        #return ParseResults([newToks]) #wrap in []; return.


    def actionCheckIdentifier(self, str, loc, toks):
        """
        Parse action to check an identifier.
        Tries to see wether it is equal to a keyword.
        Does not change any parse results
        """
##        #debug code-----------------
##        if   self.debugSyntax == 2:
##            return
        #toks is structured like this: ['a1']
        if toks[0] in self.keywords:
            #print "found keyword", toks[0], "at loc: ", loc
            #raise ParseException(str, loc, "Identifier same as keyword: %s" % toks[0])
            raise ParseFatalException(
                str, loc, "Identifier same as keyword: '%s'" % toks[0] )


#------------------- BNF --------------------------------------------------------*
    def defineLanguageSyntax(self):
        """
        Here is Siml's BNF
        Creates the objects of the pyParsing library,
        that do all the work.
        """
        #define short alias so they don't clutter the text
        kw = self.defineKeyword # Usage: test = kw("variable")
        L = Literal # Usage: L("+")

        #Values that are built into the language
        #TODO: this should be a for loop and a list (attribute)!
        builtInValue = Group( kw("e") | kw("pi") | kw("time"))      .setParseAction(AddMetaDict('builtInVal'))\
                                                                    .setName("builtInValue")#.setDebug(True)

        #Functions that are built into the language
        #TODO: this should be a for loop and a list (attribute)!
        builtInFuncName = (  kw("sin") | kw("cos") | kw("tan") |
                             kw("sqrt") | kw("ln")               )  .setName("builtInFuncName")#.setDebug(True)

        #Integer (unsigned).
        uInteger = Word(nums)                                       .setName("uInteger")#.setDebug(True)
        #Floating point number (unsigned).
        eE = CaselessLiteral( "E" )
        uNumber = Group( Combine(
                    uInteger +
                    Optional("." + Optional(uInteger)) +
                    Optional(eE + Word("+-"+nums, nums))))          .setParseAction(AddMetaDict('num'))\
                                                                    .setName("uNumber")#.setDebug(True)

        # .............. Mathematical expression .............................................................
        #"Forward declarations" for recursive rules
        expression = Forward()
        term =  Forward()
        factor = Forward()
        signedAtom = Forward()
        valAccess = Forward() #For PDE: may also contain expressions for slices: a.b.c(2.5:3.5)

        #Basic building blocks of mathematical expressions e.g.: (1, x, e,
        #sin(2*a), (a+2), a.b.c(2.5:3.5))
        #Function call, parenthesis and memory access can however contain
        #expressions.
        funcCall = Group( builtInFuncName + "(" + expression + ")") .setParseAction(AddMetaDict('funcCall')) \
                                                                    .setName("funcCall")#.setDebug(True)
        parentheses = Group("(" + expression + ")")                 .setParseAction(AddMetaDict('paren')) \
                                                                    .setName("parentheses")#.setDebug(True)
        atom = (    uNumber | builtInValue | funcCall |
                    valAccess | parentheses               )         .setName("atom")#.setDebug(True)

        #The basic mathematical operations: -a+b*c^d.
        #All operations have right-to-left associativity; althoug this is only
        #required for exponentiation. Precedence decreases towards the bottom.
        #Unary minus: -a, not a;
        negop = "-" | kw("not")
        unaryMinus = Group(negop + signedAtom)          .setParseAction(AddMetaDict('m_p1')) \
                                                        .setName("unaryMinus")#.setDebug(True)
        signedAtom << (atom | unaryMinus)               .setName("signedAtom")#.setDebug(True)

        #Exponentiation: a^b;
        factor1 = signedAtom                            .setName("factor1")#.setDebug(True)
        factor2 = Group(signedAtom + "^" + factor)      .setParseAction(AddMetaDict('m_i2')) \
                                                        .setName("factor2")#.setDebug(True)
        factor << (factor2 | factor1)                   .setName("factor")#.setDebug(True)

        #multiplicative operations: a*b; a/b
        multop = L("*") | L("/")
        term1 = factor                                  .setName("term1")#.setDebug(True)
        term2 = Group(factor + multop + term)           .setParseAction(AddMetaDict('m_i2')) \
                                                        .setName("term2")#.setDebug(True)
        term << (term2 | term1)                         .setName("term")#.setDebug(True)

        #additive operations: a+b; a-b
        addop  = L("+") | L("-")
        expression1 = term                              .setName("expression1")#.setDebug(True)
        expression2 = Group(term + addop + expression)  .setParseAction(AddMetaDict('m_i2')) \
                                                        .setName("expression2")#.setDebug(True)
        expression << (expression2 | expression1)       .setName("expression")#.setDebug(True)

        #Relational operators : <, >, ==, ...
        #TODO: missing are: or, and, not
        relop = L('<') | L('>') | L('<=') | L('>=') | L('==')
        boolExpression = Group(expression + relop + expression) .setParseAction(AddMetaDict('m_i2')) \
                                                                .setName("expression2")#.setDebug(True)
        #................ End mathematical expression ................................................---

        #................ Identifiers ...................................................................
        #TODO: check for keywods -  .setParseAction(self.actionCheckIdentifier) \
        identifier = Word(alphas, alphas+nums+"_")              .setName("identifier")#.setDebug(True)

        #Compound identifiers for variables or parameters "aaa.bbb".
        #TODO: add slices: aaa.bbb(2:3)
        dotSup = Literal(".").suppress()
        valAccess << Group( Optional("$") +
                            identifier +
                            ZeroOrMore(dotSup  + identifier) )  .setParseAction(AddMetaDict('valA')) \
                                                                .setName("valAccess")#.setDebug(True)

        #..................... Statements ..............................................................
        statementList = Forward()
        #Flow control - if then else
        ifStatement = Group(
                        kw('if') + boolExpression + kw('then') +
                        statementList +
                        Optional(kw('else') + statementList) +
                        kw('end'))                                  .setParseAction(AddMetaDict('ifStmt'))\
                                                                    .setName("ifStatement")#.setDebug(True)
        #compute expression and assign to value
        assignment = Group(valAccess + ':=' + expression + ';')     .setParseAction(AddMetaDict('assign'))\
                                                                    .setName("assignment")#.setDebug(True)
        #execute a block - insert code of a child model
        blockName = kw('run') | kw('init') #| kw('insert')
        blockExecute = Group(blockName + identifier + ';')          .setParseAction(AddMetaDict('blockExecute'))\
                                                                    .setName("blockExecute")#.setDebug(True)

        statement = (blockExecute | ifStatement | assignment)       .setName("statement")#.setDebug(True)
        statementList << Group(OneOrMore(statement))                .setParseAction(AddMetaDict('stmtList'))\
                                                                    .setName("statementList")#.setDebug(True)

        #..................... Class ........................................................................
        #define parameters, variables and submodels
        defRole = kw('par') | kw('var') | kw('sub') | kw('submodel')
        dedinitionStatement = Group(defRole + identifier + ';')     .setParseAction(AddMetaDict('defStmt'))\
                                                                    .setName("dedinitionStatement")#.setDebug(True)
        definitionList = Group(OneOrMore(dedinitionStatement))      .setParseAction(AddMetaDict('defList'))\
                                                                    .setName("definitionList")#.setDebug(True)

        #The statements (equations) that determine the system dynamics go here
        runBlock = Group(   kw('block') + kw('run') +
                            statementList +
                            kw('end'))                              .setParseAction(AddMetaDict('runBlock'))\
                                                                    .setName("runBlock")#.setDebug(True)

        #The initialization code goes here
        initBlock = Group(  kw('block') + kw('init') +
                            statementList +
                            kw('end'))                              .setParseAction(AddMetaDict('initBlock'))\
                                                                    .setName("initBlock")#.setDebug(True)

        classRole = kw('procedure') | kw('model') #| kw('paramset')
        classDef = Group(   classRole + identifier +
                            Optional(definitionList) +
                            Optional(runBlock) +
                            Optional(initBlock)  +
                            kw('end'))                              .setParseAction(AddMetaDict('classDef'))\
                                                                    .setName("classDef")#.setDebug(True)

        program = Group(OneOrMore(classDef))                        .setParseAction(AddMetaDict('program'))\
                                                                    .setName("program")#.setDebug(True)
        #................ End of language definition ..................................................

        #determine start symbol
        startSymbol = program
        #set up comments
        singleLineCommentCpp = "//" + restOfLine
        singleLineCommentPy = "#" + restOfLine
        startSymbol.ignore(singleLineCommentCpp)
        startSymbol.ignore(singleLineCommentPy)

        return startSymbol


    #TODO: Maybe write: parseExpression, parseMemAccess, ...
    def parseProgram(self, inString):
        """Parse a whole program. The program is entered as a string."""
        result = self._parser.parseString(inString)
        return result



class AddMetaDict(object):
    """
    Functor class to add a dict to a ParseResults object in a semantic action.
    The meta dict contains (at least) the result's type and the location in the
    input string:
    {'typ':'foo', 'loc':23}

    Additionally adds type string to a central list
    (ParseStage.nodeTypes - really a set) for checking the consistency

    TODO: a dict, that is added to the standard meta dict.
    """
    def __init__(self, typeString):
        """typeString : string to identify the node."""
        object.__init__(self)
        self.typeString = typeString
        ParseStage.nodeTypes.add(typeString) #add to set


    def __call__(self,str, loc, toks):
        """The parse action that adds the dict."""
        #debug code-----------------
        if   ParseStage.debugSyntax == 2:
            return None
        elif ParseStage.debugSyntax == 1:
            return toks.copy()

        #toks is structured like this [['pi']]
        newToks = ParseResults([{"typ":self.typeString, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.



class Node(object):
    """Building block of a n-ary tree structure."""

    def __init__(self, typ, kids=[], loc=None, dat=None):
        #TODO: write an init function that can accept any number of named arguments
        #Variabe number of arguments:
        #*args    : is a list of all normal arguments
        #**kwargs : is a dict of keyword arguments
        #Code for derived classes: super(A, self).__init__(*args, **kwds)
        object.__init__(self)
        self.typ = typ   # type string
        #self.parent = None
        self.kids = kids[:] # list of children
        self.loc  = loc     # the location in the program
        self.dat = dat      # whatever is appropriate


    def __repr__(self):
        className = self.__class__.__name__
        typeStr = repr(self.typ)
        childStr = "," + repr(self.kids)
        #if location and contents have their default value, don't print them
        if self.loc == None:
            locStr = ''
        else:
            locStr = ', ' + repr(self.loc)
        if self.dat == None:
            datStr =''
        else:
            datStr = ', ' + repr(self.dat)
        #treat all other attributes as named attributes
        standardAttributes = set(['typ', 'kids', 'loc', 'dat'])
        for key, attr in self.__dict__.iteritems():
            if key in standardAttributes:
                continue
            extraAttrStr += ', ' + key + '=' + repr(attr)

        reprStr = className  + "(" + typeStr + childStr + locStr + datStr + \
                                    extraAttrStr + ")"
        return reprStr

    #TODO: __str__() that prints the tree in a neat way

    #Acces to childern throug []
    def __getitem__(self, i):
        return self.kids[i]
    def __len__(self):
        return len(self.kids)
    #def __getslice__(self, low, high):
        #return self.kids[low:high]
    #def __setslice__(self, low, high, childList):
        #self.kids[low:high] = seq
##    def __cmp__(self, o):
##        return cmp(self.type, o)


##    def copy(self):
##        """
##        TODO: use built in copy module
##          import copy
##          x = copy.copy(y)        # make a shallow copy of y
##          x = copy.deepcopy(y)    # make a deep copy of y
##
##        Make a (recursive) deep copy of the object.
##        This will (currently) not work with attributes that are lists or
##        dictionaries!
##        See: http://www.python.org/search/hypermail/python-1993/0267.html
##        """
##        newObject = self.__class__()     #Create new object with same class
##        #duplicate attributes
##        for key in self.__dict__.keys(): #key is a string
##            oldAttr = getattr(self, key)
##            if hasattr(oldAttr, "copy"): #If attribute has a copy function then
##                newAttr = oldAttr.copy() #use the copy function to duplicate it
##            else:
##                newAttr = oldAttr #else shallow copy - attribute is believed to
##                                  #be immutable e.g.: number.
##            setattr(newObject, key, newAttr) #Put duplicated attribute into
##                                             #new object
##        return newObject




class NodeValAccess(Node):
    """
    AST node for access to a variable or parameter.
    Has additional attribute deriv.
        typ: type string, usually: 'valA'
        kids: slice?
        loc: location in input string
        dat: list of identifiers; the dot separated name, from left to right.
        deriv: [],['time'] or list of distibution domains
    """

    def __init__(self, typ='valA', kids=[], loc=None, dat=None, deriv=[]):
        """
        deriv: [],['time'] or list of distibution domains. Shows that
        derivative of variable is accessed.
        """
        Node.__init__(self, typ, kids, loc, dat)
        self.deriv = deriv[:]




class ASTGeneratorException(Exception):
    """Exception raised by the ASTGenerator class"""
    pass


class ASTGenerator(object):
    """Create a syntax tree from the parsers output"""

    def __init__(self):
        object.__init__(self)
        pass


    def _createPrefixOp(self, tokList):
        """
        Create node for math prefix operators: -
        Parameter tokList has the following structure:
        [<meta dictionary>, <operator>, <expression_l>]
        """
        nCurr = Node("m_p1")
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
        """
        Create node for math infix operators: + - * / ^
        Parameter tokList has the following structure:
        [<meta dictionary>, <expression_l>, <operator>, <expression_r>]
        """
        nCurr = Node("m_i2")
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
        """
        Create node for function call: sin(2.1)
        Parameter tokList has the following structure:
        [<meta dictionary>, <function dentifier>, "(", <expression>, ")"]
        """
        nCurr = Node("funcCall")
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #store child expession and function name
        nCurr.dat = tokList[1]                       #function dentifier
        nCurr.kids=[self._createSubTree(tokList[3])] #child expression
        return nCurr


    def _createParenthesePair(self, tokList):
        """
        Create node for a pair of parentheses that enclose an expression: (...)
        Parameter tokList has the following structure:
        [<meta dictionary>, "(", <expression>, ")"]
        """
        nCurr = Node("paren")
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Create and store child expression
        nCurr.kids = [self._createSubTree(tokList[2])]
        return nCurr


    def _createNumber(self, tokList):
        """
        Create node for a number: 5.23
        Parameter tokList has the following structure:
        [<meta dictionary>, <number>]
        """
        nCurr = Node("num")
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Store the number
        nCurr.dat = tokList[1]
        return nCurr


    def _createBuiltInValue(self, tokList):
        """
        Create node for a built in value: pi, time
        Parameter tokList has the following structure:
        [<meta dictionary>, <identifier>]
        """
        nCurr = Node("builtInVal")
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Store the built in value's name
        nCurr.dat = tokList[1]
        return nCurr


    def _createValueAccess(self, tokList):
        """
        Create node for acces to a variable or parameter: bb.ccc.dd
        Parameter tokList has the following structure:
        [<meta dictionary>, <part1>, <part2>, <part3>, ...]
        """
        nCurr = NodeValAccess("valA")
        #Create an attribute for each key value pair in the meta dictionary
        metaDict = tokList[0]
        for attrName, attrVal in metaDict.iteritems():
            setattr(nCurr, attrName, attrVal)
        #Look if there is a '$' that indicates time derivatives
        tok1 = 1
        if tokList[1] == '$':
            nCurr.deriv = ['time']
            tok1 = 2
        #The remaining tokens are the dot separated name
        nCurr.dat = tokList[tok1:len(tokList)]
        return nCurr


    funcDict = {"m_p1":_createPrefixOp, "m_i2":_createInfixOp,
                "funcCall":_createFunctionCall, "paren":_createParenthesePair,
                "num":_createNumber,"builtInVal":_createBuiltInValue,
                "valA":_createValueAccess}
    """Dictionary with type string and node creator function."""


    def _createSubTree(self, tokList):
        """Central dispatcher function for recursive tree construction.
        tokList is a nested list."""

        #First list item is a dict with meta information.
        metaDict = tokList[0]
        if not isinstance(metaDict, type({})):
            raise ASTGeneratorException("Node has no metadict!")

        nType = metaDict["typ"]             #Get node type.
        creatorFunc = self.funcDict[nType]  #Find matching creator function
        return creatorFunc(self, tokList)   #call ceator function


    def createSyntaxTree(self, parseResult):
        """
        Create the syntax tree from a ParseResult.
        parameter parseResult: ParseResult object, or nested list.
        """
        if isinstance(parseResult, ParseResults): #Parse result objects
            tokList = parseResult.asList()[0]     #must be converted to lists
            tokList = tokList[0]     #remove one pair of square brackets
        else:
            tokList = parseResult
        #pdb.set_trace()
        return self._createSubTree(tokList)




def doTests():
    """Perform various tests."""

    #t1 = Node("root", [Node("child1",[]),Node("child2",[])])
    #print t1

    testProgStr = (
"""
model test
var V; var h;
par A_bott; par A_o; par mu;
par q; par g;

block run
h := V/A;
$V := q - mu*A_o*sqrt(2*g*h);
end

block init
V := 0;
A_bott := 1; A_o := 0.02; mu := 0.55;
q := 0.05;
end
end
""" )

    #test the AST generator
    flagTestASTGenerator = True
    #flagTestASTGenerator = False
    if flagTestASTGenerator:
        parser = ParseStage()
        treeGen = ASTGenerator()

        pres = parser.parseProgram(testProgStr)
        print "parse result:"
        print pres
        tree = treeGen.createSyntaxTree(pres)
        print "tree:"
        print tree


    #test the parser
    #flagTestParser = True
    flagTestParser = False
    if flagTestParser:
        parser = ParseStage()
        #ParseStage.debugSyntax = 1
        #ParseStage.debugSyntax = 2
        #print parser.parseProgram('model test var a; par b; end')
        #print parser.parseProgram('model test par a; end')


        print parser.parseProgram(testProgStr)

        #print parser.parseProgram("a:=0+1;b:=2+3+4;")
        #print parser.parseProgram("if a==0 then b:=-1; else b:=2+3+4; a:=1; end")
        #print parser.parseProgram("0*1*2*3*4")
        #print parser.parseProgram("0^1^2^3^4")
        #print parser.parseProgram("0+1*2+3+4")
        #print parser.parseProgram("0*1^2*3*4")
        #print parser.parseProgram("0+(1+2)+3+4")
        #print parser.parseProgram("-0+1+--2*-3--4")
        #print parser.parseProgram("-aa.a+bb.b+--cc.c*-dd.d--ee.e+f")
        #print parser.parseProgram("0+sin(2+3*4)+5")
        #print parser.parseProgram("0+a1.a2+bb.b1.b2+3+4 #comment")
        #print parser.parseProgram("0.123+1.2e3")
        #parser.parseProgram("0+1*2^3^4+5+6*7+8+9")

        print "keywords:"
        print parser.keywords
        print "node types"
        print parser.nodeTypes

    #Check if the parser and the AST generator use the same type strings
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


    pdb.set_trace()


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
