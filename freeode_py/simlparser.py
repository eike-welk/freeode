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

from pyparsing import Literal,Keyword,CaselessLiteral,Word,Combine,Group,Optional, \
    ZeroOrMore,Forward,nums,alphas,restOfLine,ParseResults, ParseException, \
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

    keywords = []
    """
    List of all keywords (filled by defineLanguageSyntax() and defineKeyword).
    TODO: change to set.
    """

    nodeTypes = []
    """
    List of all type strings, that identify the nodes in the parse result.
    (filled by defineNodeType() in the semantic actions).
    TODO: change to set.
    """


    def __init__(self):
        object.__init__(self)
        self._parser = self.defineLanguageSyntax() #Create parser object
        """The parser object from pyParsing"""


    def defineKeyword(self, inString):
        """
        Store keyword (in self.keywords) and create parser for it.
        Use this function (in defineLanguageSyntax(...)) instead of using the
        Keyword class directly.
        """
        if not (inString in self.keywords):
            self.keywords.append(inString)
        return Keyword(inString)


    def defineNodeType(self, inString):
        """Store type string (in self.nodeTypes) and return it."""
        #TODO create faster solution! Don't call this function in parse actions.
        if not (inString in self.nodeTypes):
            self.nodeTypes.append(inString)
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


    def actionInfixBinOp(self, str, loc, toks):
        """
        Parse action for binary mathematical operations: + - * / ^
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        # toks is structured like this [["2","+","5"]]
        typeStr = self.defineNodeType("m_i2")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.


    def actionPrefixUnaryOp(self, str, loc, toks):
        """
        Parse action for mathematical unary operations: -5 .
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        # toks is structured like this [["-","5"]]
        typeStr = self.defineNodeType("m_p1")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.


    def actionMemAccess(self, str, loc, toks):
        """
        Parse action for memory access: aa.bb.cc
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        # toks is structured like this [["aa","bb","cc"]]
        typeStr = self.defineNodeType("memA")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.


    def actionFuncCall(self, str, loc, toks):
        """
        Parse action for function call: sin(2.1)
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        # toks is structured like this [['sin','(',['2.1'],')']]
        typeStr = self.defineNodeType("funcCall")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.


    def actionParentheses(self, str, loc, toks):
        """
        Parse action for pair of parentheses: ( 1+2 ).
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        #toks is structured like this [['(', ['1', '+', '2'], ')']]
        typeStr = self.defineNodeType("paren")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.


    def actionNumber(self, str, loc, toks):
        """
        Parse action for a real number: 5.23 .
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        #toks is structured like this [['5.23']]
        typeStr = self.defineNodeType("num")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.


    def actionbuiltInConstant(self, str, loc, toks):
        """
        Parse action for a built in constant: pi .
        Put additional information into parse result, that would
        be lost otherwise. The information is stored in a dict, and put before
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()

        #toks is structured like this [['pi']]
        typeStr = self.defineNodeType("buildInVal")
        newToks = ParseResults([{"typ":typeStr, "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.




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

        #Constants that are built into the language
        #TODO: come up with better name: time is no constant
        builtInConstant = Group( kw("e") | kw("pi") | kw("time"))   .setParseAction(self.actionbuiltInConstant)\
                                                                    .setName("builtInConstant")#.setDebug(True)

        #Functions that are built into the language
        builtInFuncName = (  kw("sin") | kw("cos") | kw("tan") |
                             kw("sqrt") | kw("ln")               )  .setName("builtInFuncName")#.setDebug(True)

        #Integer (unsigned).
        uInteger = Word(nums)                                       .setName("uInteger")#.setDebug(True)
        #Floating point number (unsigned).
        eE = CaselessLiteral( "E" )
        uNumber = Group( Combine(
                    uInteger +
                    Optional("." + Optional(uInteger)) +
                    Optional(eE + Word("+-"+nums, nums))))          .setParseAction(self.actionNumber)\
                                                                    .setName("uNumber")#.setDebug(True)

        # .............. Mathematical expression .............................................................
        #"Forward declarations" for recursive rules
        expression = Forward()
        term =  Forward()
        factor = Forward()
        signedAtom = Forward()
        memAccess = Forward() #For PDE: may also contain expressions for slices: a.b.c(2.5:3.5)

        #Basic building blocks of mathematical expressions e.g.: (1, x, e,
        #sin(2*a), (a+2), a.b.c(2.5:3.5))
        #Function call, parenthesis and memory access can however contain
        #independent expressions.
        funcCall = Group( builtInFuncName + "(" + expression + ")") .setParseAction(self.actionFuncCall) \
                                                                    .setName("funcCall")#.setDebug(True)
        parentheses = Group("(" + expression + ")")                 .setParseAction(self.actionParentheses) \
                                                                    .setName("parentheses")#.setDebug(True)
        atom = (    uNumber | builtInConstant | funcCall |
                    memAccess | parentheses               )         .setName("atom")#.setDebug(True)

        #The basic mathematical operations: -a+b*c^d.
        #All operations have right-to-left associativity; althoug this is only
        #required for exponentiation. Precedence decreases towards the bottom.
        #Unary minus: -a;
        unaryMinus = Group("-" + signedAtom)            .setParseAction(self.actionPrefixUnaryOp) \
                                                        .setName("unaryMinus")#.setDebug(True)
        signedAtom << (atom | unaryMinus)               .setName("signedAtom")#.setDebug(True)

        #Exponentiation: a^b;
        factor1 = signedAtom                            .setName("factor1")#.setDebug(True)
        factor2 = Group(signedAtom + "^" + factor)      .setParseAction(self.actionInfixBinOp) \
                                                        .setName("factor2")#.setDebug(True)
        factor << (factor2 | factor1)                   .setName("factor")#.setDebug(True)

        #multiplicative operations: a*b; a/b
        multop = L("*") | L("/")
        term1 = factor                                  .setName("term1")#.setDebug(True)
        term2 = Group(factor + multop + term)           .setParseAction(self.actionInfixBinOp) \
                                                        .setName("term2")#.setDebug(True)
        term << (term2 | term1)                         .setName("term")#.setDebug(True)

        #additive operations: a+b; a-b
        addop  = L("+") | L("-")
        expression1 = term                              .setName("expression1")#.setDebug(True)
        expression2 = Group(term + addop + expression)  .setParseAction(self.actionInfixBinOp) \
                                                        .setName("expression2")#.setDebug(True)
        expression << (expression2 | expression1)       .setName("expression")#.setDebug(True)

        #TODO: missing are relational operators (<, >, ==, ...).
        #They have the lowest precedence and would be placed here

        #................ End mathematical expression ................................................---

        #Identifiers
        #TODO: check for keywods -  .setParseAction(self.actionCheckIdentifier) \
        identifier = Word(alphas, alphas+nums+"_")              .setName("identifier")#.setDebug(True)

        #Compound identifiers for variables or parameters "aaa.bbb".
        #TODO: add slices: aaa.bbb(2:3)
        dotSup = Literal(".").suppress()
        memAccess << Group( Optional("$") +
                            identifier +
                            ZeroOrMore(dotSup  + identifier) )  .setParseAction(self.actionMemAccess) \
                                                                .setName("memAccess")#.setDebug(True)

        #................ End of language definition ..................................................

        #determine start symbol
        startSymbol = expression
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
        childStr = repr(self.kids)
        #if location and contents have their default value, don't print them
        if self.loc == None:
            locStr = ''
        else:
            locStr = ', ' + repr(self.loc)
        if self.dat == None:
            datStr =''
        else:
            datStr = ', ' + repr(self.dat)

        reprStr = className  + "(" + typeStr + "," + childStr + locStr + datStr + ")"
        return reprStr


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



class SyntaxTreeGenerator(object):
    """Create a syntax tree from the parsers output"""

    def __init__(self):
        object.__init__(self)
        pass


    def createSyntaxTree(self, parseResult):
        """Create the syntax tree from a ParseResult."""
        toklist = parseResult.asList()[0]
        #pdb.set_trace()
        tree = self._createSubTree(toklist)
        return tree


    def _createSubTree(self, tokList):
        """Central dispatcher function for recursive tree construction."""

        try:
            #First item is a dict with meta information. Get node type from there.
            nType = tokList[0]["typ"]

            if nType == "m_i2":
                return self._createInfixOp(tokList)
            elif nType == "num":
                return self._createNumber(tokList)
            else:
                print "Warning unknown node type discovered: " + nType
                return None
        except:
            print "Warning node without node type or meta dict discovered!"
            raise
    #TODO: "m_p1", "memA", "funcCall", "paren", "buildInVal", --- "m_i2", "num"

    def _createInfixOp(self, tokList):
        """
        Create node for math infix operators: + - * / ^
        The item has the followin structure:
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


    def _createNumber(self, tokList):
        """
        Create node for a number: 5.23
        The item has the followin structure:
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


    #def createGenericNode(self, tokList):
        #"""
        #Create a generic node.
        #Parse result is a list of lists: [{"loc":0}"1", "+", [{"loc":2}"2", "*", "3"]]
        #1. For every list item create a child node.
        #2. Put everything else into the dat attribute.
        #"""
        #nodeNew = Node("gen")
        #nodeNew.dat = []

        ##pdb.set_trace()
        ##The first item can be a dict with meta information
        #if isinstance(tokList[0], type({})):
            #metaDict = tokList[0]
            #startItem = 1
        #else:
            #metaDict = {}
            #startItem = 0
        ##Create an attribute for each key value pair
        #for attrName, attrVal in metaDict.iteritems():
            #setattr(nodeNew, attrName, attrVal)

        ##For all other items create either a child or put them into dat
        #print 'enter function with: ', tokList
        ##pdb.set_trace()
        #for i in range(startItem, len(tokList)):
            #currItem = tokList[i]
            #if isinstance(currItem, type([])):
                #print 'currItem: ', currItem
                #childNew = self.createSubTree(currItem)
                #print 'childNew: ', childNew
                #nodeNew.kids.append(childNew)
            #else:
                #nodeNew.dat.append(currItem)

        #print 'exit function with: ', nodeNew
        #return nodeNew


def doTests():
    """Perform various tests."""

    #t1 = Node("root", [Node("child1",[]),Node("child2",[])])
    #print t1

    #test the AST generator
    flagTestASTGenerator = True
    #flagTestASTGenerator = False
    if flagTestASTGenerator:
        parser = ParseStage()
        treeGen = SyntaxTreeGenerator()

        pres = parser.parseProgram("0+1+2")
        print pres
        tree = treeGen.createSyntaxTree(pres)
        print tree
        #pres = [['0'],['1'],['2']]
        #print pr
        #tree = treeGen.createSubTree(pr)
        ##pp.pprint(tree)
        #print tree

    #test the parser
    #flagTestParser = True
    flagTestParser = False
    if flagTestParser:
        parser = ParseStage()
        #parser.debugSyntax = 1
        #parser.debugSyntax = 2
        print parser.parseProgram("0+1+2+3+4")
        print parser.parseProgram("0*1*2*3*4")
        print parser.parseProgram("0^1^2^3^4")
        print parser.parseProgram("0+1*2+3+4")
        print parser.parseProgram("0*1^2*3*4")
        print parser.parseProgram("0+(1+2)+3+4")
        print parser.parseProgram("-0+1+--2*-3--4")
        print parser.parseProgram("-aa.a+bb.b+--cc.c*-dd.d--ee.e+f")
        print parser.parseProgram("0+sin(2+3*4)+5")
        print parser.parseProgram("0+a1.a2+bb.b1.b2+3+4 #comment")
        print parser.parseProgram("0.123+1.2e3")
        #parser.parseProgram("0+1*2^3^4+5+6*7+8+9")

        print "keywords:"
        print parser.keywords
        print "node types"
        print parser.nodeTypes

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
