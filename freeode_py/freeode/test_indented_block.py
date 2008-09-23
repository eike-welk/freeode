#try the indentedBlock helper function

from pyparsing import *

#-------------------------------------------------------
#enable packrat parsing and the parser won't work
#ParserElement.enablePackrat()
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
suite << indentedBlock(statement, stack)


program = indentedBlock(statement, stack, False) + stringEnd
#program = ZeroOrMore(ZeroOrMore(newline)+statement)+ZeroOrMore(newline) + stringEnd


prog1 = \
'''
foo aaa
print bar ooo
'''
print program.parseString(prog1)

prog2 = \
'''
print start
if test:
    print aaa
if test:
    print bbb
print end
'''
print program.parseString(prog2)

prog2 = \
'''
print start
if test:
    print aaa
    if test:
        print bbb
    print ccc
print end
'''
print program.parseString(prog2)


