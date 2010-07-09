# -*- coding: utf-8 -*-
# Code is put to:
#          http://pastebin.com/f762576c5

#-----------------------------------------------------------------------------------------
#
#       Example implementation for better error reporting.
#
#-----------------------------------------------------------------------------------------

from freeode.third_party.pyparsing import \
    ParseElementEnhance, Keyword, Word, Group, ZeroOrMore, \
    OneOrMore, StringEnd, alphas, alphanums, ParseException, \
    ParseFatalException, _ustr


##-------------------------------------------------------------------------------------
##                    The ErrStop as it was used in the SIML parser
##-------------------------------------------------------------------------------------
#class ErrStop(ParseElementEnhance):
#    """Parser that prevents backtracking.
#       The parser tries to match the given expression (which consists of other
#       parsers). If this expression does not match the parser raises a
#       ParseFatalException and parsing stops.
#       Otherwise, if the given expression matches, its parse results are returned
#       and the ErrStop has no effect on the parse results.
#
#    """
#
#    def __init__(self, expr):
#        super(ErrStop, self).__init__(expr, savelist=False)
#        self.mayReturnEmpty = True
#        #Additional string, that will be put in front of the error message.
#        self.errMsgStart = ''
#
#    def parseImpl(self, instring, loc, doActions=True):
#        try:
#            loc, tokens = self.expr._parse(instring, loc, doActions, callPreParse=False)
#        except IndexError:
#            raise ParseFatalException(instring, loc, 'Index error: ', self.expr)
#        except ParseException, theError:
#            errMsg = self.errMsgStart + theError.msg
#            raise ParseFatalException(instring, theError.loc, errMsg, self.expr)
#        return loc, tokens
#
#    def setErrMsgStart(self, msg):
#        """Set additional error message.
#           This string will be put in front of the error message of the given
#           parser.
#        """
#        self.errMsgStart = msg
#        return self
#
#    def __str__(self):
#        if hasattr(self,"name"):
#            return self.name
#
#        if self.strRepr is None:
#            self.strRepr = "[" + _ustr(self.expr) + "]"
#
#        return self.strRepr



#Took code from pyparsing.Optional as a template
class ErrStop(ParseElementEnhance):
    """Parser that prevents backtracking.
       The parser tries to match the given expression. If this expression does not match
       the parser raises a ParseFatalException and parsing stops.
       Otherwise, if the given expression matches, its parse results are returned and
       the ErrStop has no effect on the parse results.
    """
    def __init__( self, expr ):
        super(ErrStop,self).__init__( expr, savelist=False )
        self.mayReturnEmpty = True

    def parseImpl( self, instring, loc, doActions=True ):
        try:
            loc, tokens = self.expr._parse( instring, loc, doActions, callPreParse=False )
        except IndexError:
            raise ParseFatalException(instring, loc, 'Index error: ', self.expr)
        except ParseException, theError:
            raise ParseFatalException(instring, theError.loc, theError.msg, self.expr)
        return loc, tokens

    def __str__( self ):
        if hasattr(self,"name"):
            return self.name

        if self.strRepr is None:
            self.strRepr = "[" + _ustr(self.expr) + "]"

        return self.strRepr


#------- Define the language -----------------------------------------------------
# Some Basics
identifier = Word(alphas+'_', alphanums+'_')
attrNameList = Group(identifier + ZeroOrMore(',' + identifier))
# The statements
dataDef1 = Group(Keyword('data') + attrNameList + ':' + identifier + ';')
dataDef2 = Group(Keyword('data') + ErrStop(attrNameList + ':' + identifier + ';'))
foo1 = Group(Keyword('foo1') + ';')
foo2 = Group(Keyword('foo2') + ';')
# The top level parsers
programPs1 = OneOrMore(dataDef1 | foo1 | foo2) + StringEnd()
programPs2 = OneOrMore(dataDef2 | foo1 | foo2) + StringEnd()


#------------ Test the parsers -----------------------------------------------------
# example "programs"
progGood = \
'foo1; data a, a1, b: Real; foo1;'
progBad = \
'foo1; data a, a1 b: Real; foo1;' # missing ',' after char 15

print 'Correct program: ', progGood
print 'Faulty program : ', progBad

print
print 'Test regular parser:'
print programPs1.parseString(progGood)
try:
    print programPs1.parseString(progBad)
except ParseException, theError:
    print theError

print
print 'Test parser with backtracking stop:'
print programPs2.parseString(progGood)
try:
    print programPs2.parseString(progBad)
except (ParseException, ParseFatalException), theError:
    print theError


# --------- The program should print the following lines: --------------------------
#Correct program:  foo1; data a, a1, b: Real; foo1;
#Faulty program :  foo1; data a, a1 b: Real; foo1;
#
#Test regular parser:
#[['foo1', ';'], ['data', ['a', ',', 'a1', ',', 'b'], ':', 'Real', ';'], ['foo1', ';']]
#Expected end of text (at char 6), (line:1, col:7)
#
#Test parser with backtracking stop:
#[['foo1', ';'], ['data', ['a', ',', 'a1', ',', 'b'], ':', 'Real', ';'], ['foo1', ';']]
#Expected ":" (at char 17), (line:1, col:18)
