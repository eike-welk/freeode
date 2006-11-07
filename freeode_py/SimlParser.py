"""
Parser for the SIML simulation language.

Inspiration came from: 
    "fourFn.py" an example program by Paul McGuire
    and the "Spark" library by John Aycock

Copyright (C) 2006 Eike Welk
"""

from pyparsing import Literal,Keyword,CaselessLiteral,Word,Combine,Group,Optional, \
    ZeroOrMore,Forward,nums,alphas,restOfLine,ParseResults


class ParseStage(object):
    """
    The syntax definition (BNF) resides here.
    Mainly a wrapper for the Pyparsing library and therefore combines lexer 
    and parser. It returns a ParseResult object. The ParseResult object is 
    generated by the Pyparsing library and modfied through parse actions.
    The program is entered as a string.
    
    Usage:
    parser = ParseStage()
    result = parser.parseString("0+1+2+3+4");
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
    """
    
    def __init__(self):
        self._parser = self.defineLanguageSyntax() #Create parser object
        """The parser object from pyParsing"""
    
    def defineKeyword(self, inString):
        """
        Store keyword (in self.keywords) and create parser for it.
        Use this function (in defineLanguageSyntax(...)) instead of using the 
        Keyword class directly. 
        """
        if not inString in self.keywords:
            self.keywords.append(inString)
        return Keyword(inString)
    
##    ------------------------------ Parse Actions ------------------------------------
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
        Parse action: Put additional information into parse result, that would 
        be lost otherwise. The information is stored in a dict, and put before 
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()
        
        # toks is nested like this [["2","+","5"]]
        newToks = ParseResults([{"type":"mopI2", "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.
    
    def actionPrefixUnaryOp(self, str, loc, toks):
        """
        Parse action: Put additional information into parse result, that would 
        be lost otherwise. The information is stored in a dict, and put before 
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()
        
        # toks is nested like this [["-","5"]]
        newToks = ParseResults([{"type":"mopP1", "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.    
    
    def actionMemAccess(self, str, loc, toks):
        """
        Parse action: Put additional information into parse result, that would 
        be lost otherwise. The information is stored in a dict, and put before 
        the original parse result.
        """
        #debug code-----------------
        if   self.debugSyntax == 2:
            return None
        elif self.debugSyntax == 1:
            return toks.copy()
        
        # toks is nested like this [["-","5"]]
        newToks = ParseResults([{"type":"memA", "loc":loc}]) #create dict
        newToks += toks[0].copy() #add original contents
        return ParseResults([newToks]) #wrap in []; return.    
    
##    ------------------------------ BNF ------------------------------------
    def defineLanguageSyntax(self):
        """
        Here is Siml's BNF
        Creates the objects of the pyParsing library, 
        that do all the work.
        """
        #define short alias for defineKeyword(...) function. 
        #Usage: test = kw("test")
        kw = self.defineKeyword
        
        #Constants that are built into the language
        #TODO come up with better name: time is no constant
        builtInConstant = ( kw("e") | kw("pi") | kw("time"))        .setName("builtInConstant")#.setDebug(True)
        
        #Functions that are built into the language
        builtInFuntion = (  kw("sin") | kw("cos") | kw("tan") |
                            kw("sqrt") | kw("ln")               )   .setName("builtInFuntion")#.setDebug(True)
        
        #Floating point number.
        e = CaselessLiteral( "E" )
        number = ( Combine( 
                    Word(nums) + 
                    Optional("." + Optional(Word(nums))) +
                    Optional(e + Word("+-"+nums, nums))     )
                 )                                                  .setName("builtInConstant")#.setDebug(True)
        
        #Mathematical expressions ----------------------------------------------------------------------------
        #"Forward declarations" for recursive rules
        expression = Forward()
        term =  Forward()
        factor = Forward()
        signedAtom = Forward()
        memAccess = Forward()
        
        #Basic building blocks of mathematical expressions (1, x, e, sin(2*a), (a+2))
        #Function call, parenthesis and memory access can however contain 
        #independent expressions.
        funcCall = Group( builtInFuntion + "(" + expression + ")") .setName("funcCall")#.setDebug(True)
        parenthesis = Group("(" + expression + ")")                .setName("parenthesis")#.setDebug(True)
        atom = (    number | builtInConstant | funcCall | 
                    memAccess | parenthesis               )        .setName("atom")#.setDebug(True)
        
        #The basic mathematical operations (-a+b*c^d):
        #All operations have right-to-left associativity; althoug this is only 
        #required for exponentiation. Precedence decreases towards the bottom.
        addop  = Literal("+") | Literal("-")
        multop = Literal("*") | Literal("/")
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
        term1 = factor                                  .setName("term1")#.setDebug(True)
        term2 = Group(factor + multop + term)           .setParseAction(self.actionInfixBinOp) \
                                                        .setName("term2")#.setDebug(True)
        term << (term2 | term1)                         .setName("term")#.setDebug(True)
        
        #additive operations: a+b; a-b 
        expression1 = term                              .setName("expression1")#.setDebug(True)
        expression2 = Group(term + addop + expression)  .setParseAction(self.actionInfixBinOp) \
                                                        .setName("expression2")#.setDebug(True)
        expression << (expression2 | expression1)       .setName("expression")#.setDebug(True)
        
        #TODO missing are relational operators (<, >, ==, ...).
        #They have the lowest precedence and would be placed here
        #End mathematical expressions ------------------------------------------------------------------------
        
        #Identifiers
        #TODO: check for keywods
        identifier = Word(alphas, alphas+nums+"_")              .setName("identifier")#.setDebug(True)
        
        #Compound identifiers for variables or parameters "aaa.bbb". 
        #TODO: add slices: aaa.bbb(2:3)
        dotSup = Literal(".").suppress()
        memAccess << Group( Optional("$") +
                            identifier + 
                            ZeroOrMore(dotSup  + identifier) )  .setParseAction(self.actionMemAccess) \
                                                                .setName("memAccess")#.setDebug(True)
        
        #End of language definition --------------------------------------------------------------------------
        #determine start symbol 
        startSymbol = expression
        #set up comments
        singleLineCommentCpp = "//" + restOfLine
        singleLineCommentPy = "#" + restOfLine
        startSymbol.ignore(singleLineCommentCpp)
        startSymbol.ignore(singleLineCommentPy)
        
        return startSymbol
        
    def parseString(self, inString):
        """Parse a whole program. The program is entered as a string."""
        result = self._parser.parseString(inString)
        return result
    

if __name__ == '__main__':
    # Self-testing code goes here.
    
    #TODO: add unit tests
    parser = ParseStage()
##    parser.debugSyntax = 1
##    parser.debugSyntax = 2
    
    print parser.parseString("0+1+2+3+4");
    print parser.parseString("0*1*2*3*4");
    print parser.parseString("0^1^2^3^4");
    print parser.parseString("0+1*2+3+4");
    print parser.parseString("0*1^2*3*4");
    print parser.parseString("0+(1+2)+3+4");
    print parser.parseString("-0+1+--2*-3--4");
    print parser.parseString("-aa.a+bb.b+--cc.c*-dd.d--ee.e");
    print parser.parseString("0+sin(2+3*4)+5");
    print parser.parseString("0+a1.a2+bb.b1.b2+3+4 #comment");
    print parser.parseString("0.123+1.2e3");
    #parser.parseString("0+1*2^3^4+5+6*7+8+9");
    
    
    print "keywords:"
    print parser.keywords

else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
