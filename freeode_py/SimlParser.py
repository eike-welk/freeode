"""
Parser for the SIML simulation language.
"""

from pyparsing import Literal,Keyword,CaselessLiteral,Word,Combine,Group,Optional, \
    ZeroOrMore,Forward,nums,alphas

class ParseMain(object):
    
    def __init__(self):
        self.keywords = [] #list of used keywords (filled by createParseObject())
        self.parser = self.createParseObject() #the parseer object from pyParsing
        
    def defineKeyword(self, inString):
        """
        1. Put a keyword into the list of keywords.
        2. Create a parser for the keyword and return it.
        """
        if not inString in self.keywords:
            self.keywords.append(inString)
        return Keyword(inString)
    
    def createParseObject(self):
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
        builtInConstant = (kw("e") | kw("pi") | kw("time"))    .setName("builtInConstant")#.setDebug(True)
        
        #Floating point number.
        e = CaselessLiteral( "E" )
        number = ( Combine( 
                    Word("+-"+nums, nums) + 
                    Optional("." + Optional(Word(nums))) +
                    Optional(e + Word("+-"+nums, nums))     )
                 )                                             .setName("builtInConstant")#.setDebug(True)
        
        #Mathematical expressions ----------------------------------------------------------------------------
        #"Forward declarations" for recursive rules
        expression = Forward()
        term =  Forward()
        factor = Forward()
        signedAtom = Forward()
        memAccess = Forward()
        
        #Basic building blocks of mathematical expressions (1, x, e, sin(2*a), (a+2))
        #Function call, parenthesis and memory access can contain independent
        #expressions.
        #TODO: funcCall: implement built in functions 
        funcCall = Group( kw("testfn") + "(" + expression + ")")   .setName("funcCall")#.setDebug(True)
        parenthesis = Group("(" + expression + ")")                .setName("parenthesis")#.setDebug(True)
        atom = (    number | builtInConstant | funcCall | 
                    memAccess | parenthesis               )        .setName("atom")#.setDebug(True)
        
        #The basic mathematical operations (-a+b*c^d):
        #All operations have right-to-left associativity; althoug this is only 
        #required for exponentiation. Precedence decreases towards the bottom.
        addop  = Literal("+") | Literal("-")
        multop = Literal("*") | Literal("/")
        #Unary minus: -a;
        unaryMinus = Group("-" + signedAtom)           .setName("unaryMinus")#.setDebug(True)
        signedAtom << (atom | unaryMinus)              .setName("signedAtom")#.setDebug(True)
        
        #Exponentiation: a^b; 
        factor1 = signedAtom                           .setName("factor1")#.setDebug(True)
        factor2 = Group(signedAtom + "^" + factor)     .setName("factor2")#.setDebug(True)
        factor << (factor2 | factor1)                  .setName("factor")#.setDebug(True)
        
        #multiplicative operations: a*b; a/b 
        term1 = factor                                 .setName("term1")#.setDebug(True)
        term2 = Group(factor + multop + term)          .setName("term2")#.setDebug(True)
        term << (term2 | term1)                        .setName("term")#.setDebug(True)
        
        #additive operations: a+b; a-b 
        expression1 = term                             .setName("expression1")#.setDebug(True)
        expression2 = Group(term + addop + expression) .setName("expression2")#.setDebug(True)
        expression << (expression2 | expression1)      .setName("expression")#.setDebug(True)
        
        #TODO missing are relational operators (<, >, ==, ...).
        #They have the lowest precedence and would be placed here
        #End mathematical expressions ------------------------------------------------------------------------
        
        #Identifiers
        #TODO: check for keywods
        identifier = Word(alphas, alphas+nums+"_")             .setName("identifier")#.setDebug(True)
        #Compound identifiers for variables or parameters "aaa.bbb". 
        #TODO: slices: aaa.bbb(2:3)
        memAccess << Group( identifier + 
                            ZeroOrMore("." + identifier) )      .setName("memAccess")#.setDebug(True)
        
        startSymbol = expression
        return startSymbol
    
    def doParse(self, inString):
        result = self.parser.parseString(inString)
        print result
    

parser = ParseMain()
parser.doParse("0+1+2+3+4");
parser.doParse("0*1*2*3*4");
parser.doParse("0^1^2^3^4");
parser.doParse("0+1*2+3+4");
parser.doParse("0*1^2*3*4");
parser.doParse("0+(1+2)+3+4");
parser.doParse("-0+1+--2+3+4");
parser.doParse("0+aa+2+3--bb");
parser.doParse("0+testfn(2+3*4)+5");
parser.doParse("0+a1.a2+bb.b1.b2+3+4");
parser.doParse("0.123+1.2e3");

print "keywords:"
print parser.keywords

#parser.doParse("0+1*2^3^4+5+6*7+8+9");
