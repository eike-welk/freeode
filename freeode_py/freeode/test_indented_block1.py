#try the indentedBlock helper function

from freeode.third_party.pyparsing import *

#-------------------------------------------------------
#enable packrat parsing and the parser won't work
ParserElement.enablePackrat()
#-------------------------------------------------------


def indentedBlock1(blockStatementExpr, indentStack, indent=True):
    def checkPeerIndent(s, l, _t):
        print 'PeerIndent: ',
        if l >= len(s): return
        curCol = col(l, s)
        print 'line: ', lineno(l, s), ' col: ', curCol,  ' stack: ', indentStack,
        if curCol != indentStack[-1]:
            if curCol > indentStack[-1]:
                print ' fail: illegal nesting'
                raise ParseFatalException(s, l, "illegal nesting")
            print ' fail: not a peer entry'
            raise ParseException(s, l, "not a peer entry")
        print ' success'

    def checkSubIndent(s, l, _t):
        print 'SubIndent:  ',
        curCol = col(l, s)
        print 'line: ', lineno(l, s), ' col: ', curCol, ' stack: ', indentStack,
        if curCol > indentStack[-1]:
            indentStack.append( curCol )
            print 'append, stack: ', indentStack,
        else:
            print ' fail: not a subentry'
            raise ParseException(s, l, "not a subentry")
        print ' success'

    def checkUnindent(s, l, _t):
        print 'Unindent:   ',
        if l >= len(s): return
        curCol = col(l, s)
        print 'line: ', lineno(l, s), ' col: ', curCol,  ' stack: ', indentStack,
        if not(indentStack and curCol < indentStack[-1] and curCol <= indentStack[-2]):
            print ' fail: not an unindent'
            raise ParseException(s, l, "not an unindent")
        indentStack.pop()
        print 'pop, stack: ', indentStack, ' success'

    NL = OneOrMore(LineEnd().setWhitespaceChars("\t ").suppress())
    INDENT = Empty() + Empty().setParseAction(checkSubIndent)#.setNoPackrat()
    PEER   = Empty().setParseAction(checkPeerIndent).setNoPackrat()
    UNDENT = Empty().setParseAction(checkUnindent).setNoPackrat()
    if indent:
        smExpr = Group( Optional(NL) 
            + FollowedBy(blockStatementExpr) 
            + INDENT + OneOrMore( ((PEER + Group(blockStatementExpr))  .setNoPackrat() 
                                   + Optional(NL))                     .setNoPackrat() 
                                ) 
            + UNDENT )
    else:
        smExpr = Group( Optional(NL) 
            + OneOrMore( ((PEER + Group(blockStatementExpr))           .setNoPackrat() 
                           + Optional(NL))                             .setNoPackrat() 
                       ) )
    blockStatementExpr.ignore("\\" + LineEnd())
    return smExpr



#-------------------------------------------------------
stack = [1]
ParserElement.setDefaultWhitespaceChars('\t ')
newline = LineEnd().suppress()
#need to forward declare block of statements
suite = Forward()

#simple statements
print_stmt = Group(Keyword('print') - ZeroOrMore(Word(alphas)))
foo_stmt = Group(Keyword('foo') - ZeroOrMore(Word(alphas)))
#compound statements
if_stmt = Group(Keyword('if') - Word(alphas) + ':' + suite )

simple_stmt = print_stmt | foo_stmt
compound_stmt = if_stmt 
#simple statements are terminated by newline
#while the indented block eats all newlines after the compound statement
statement = simple_stmt + newline | compound_stmt 
#a suite is an indented block of statements
suite << indentedBlock1(statement, stack)


program = indentedBlock1(statement, stack, False) + stringEnd
#program = ZeroOrMore(newline) + ZeroOrMore(statement+ZeroOrMore(newline)) + stringEnd


prog1 = \
'''
foo aaa
print bar ooo
'''
#print program.parseString(prog1)

prog2 = \
'''
print start
if test:
    print aaa
if test:
    print bbb
print end
'''
#print program.parseString(prog2)

prog2 = \
'''
print start
if test:
    print aaa
    if test:
        print bbb
      
print zzz
'''
print program.parseString(prog2)


































