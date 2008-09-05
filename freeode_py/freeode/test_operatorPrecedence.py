#
# simpleArith.py
#
# Example of defining an arithmetic expression parser using
# the operatorGrammar helper method in pyparsing.
#
# Copyright 2006, by Paul McGuire
#

from pyparsing import *
#ParserElement.enablePackrat()


# To use the operatorGrammar helper:
#   1.  Define the "atom" operand term of the grammar.
#       For this simple grammar, the smallest operand is either
#       and integer or a variable.  This will be the first argument
#       to the operatorGrammar method.
#   2.  Define a list of tuples for each level of operator
#       precendence.  Each tuple is of the form
#       (opExpr, numTerms, rightLeftAssoc, parseAction), where
#       - opExpr is the pyparsing expression for the operator;
#          may also be a string, which will be converted to a Literal
#       - numTerms is the number of terms for this operator (must
#          be 1 or 2)
#       - rightLeftAssoc is the indicator whether the operator is
#          right or left associative, using the pyparsing-defined
#          constants opAssoc.RIGHT and opAssoc.LEFT.
#       - parseAction is the parse action to be associated with
#          expressions matching this operator expression (the
#          parse action tuple member may be omitted)
#   3.  Call operatorGrammar passing the operand expression and
#       the operator precedence list, and save the returned value
#       as the generated pyparsing expression.  You can then use
#       this expression to parse input strings, or incorporate it
#       into a larger, more complex grammar.
#


# TODO: Enter Pyparsing bug:
#       Inconsistent behavior of operatorPrecedence
#       operators with two terms:
#       opAssoc.RIGHT: "1**2**3" -> [1 ** [2 ** 3]] (recursive list)
#       opAssoc.LEFT:  "1+2+3"   -> [1 + 2 + 3]     (flat list)

def action_op_prefix(s, loc, toks):
    toklist = toks.asList()[0]
#    print "pre: ",  toklist
    return [toklist]

def action_op_infix(s, loc, toks):
    if isinstance(toks,  ParseResults):
        toklist = toks.asList()[0]
    else:
        toklist = toks
#    print "in : ",  toklist
    return [toklist]

def action_op_infix_left(s, loc, toks):
    toks0 = toks[0]
#    print "inL: ",  toks0
    processedToks = action_op_infix(s,  loc, toks0[0:3])
    for i in range(3, len(toks0),  2):
        processedToks = action_op_infix(s,  loc,  [processedToks,  toks0[i],  toks0[i+1]])
    return processedToks

integer = Word(nums).setParseAction(lambda t:int(t[0]))
#variable = Word(alphas,exact=1)
primary = integer #| variable

#Power and unary operations are intertwined to get correct binding:
#   -a**-b == -(a ** (-b))
power,  u_expr = Forward(), Forward()
#Exponentiation: a**b;
#Strongest binding on left side, weaker than unary operations (-a) on right side.
power1 = Group(primary + '**' + u_expr)             .setParseAction(action_op_infix)
power << (power1 | primary)
#Unary arithmetic operations: -a; +a
u_expr1 = Group(oneOf('- +') + u_expr)              .setParseAction(action_op_prefix)
u_expr << (u_expr1 | power)

expr = operatorPrecedence( u_expr,
    [(oneOf('* /'), 2, opAssoc.LEFT, action_op_infix_left),
     (oneOf('+ -'), 2, opAssoc.LEFT, action_op_infix_left),
     (oneOf('< > <= >= == !='), 2, opAssoc.LEFT, action_op_infix_left),
     (Literal('not'), 1, opAssoc.RIGHT, action_op_infix_left),
     (oneOf('and or'), 2, opAssoc.LEFT, action_op_infix_left),
     ])

test = [
        "1 and 2",
        "not 1 <= 2 and 2 > 3",
        "1*2+3"
#        "2**3**4**5",
#        "2** 3",
#        "9 + 2 - 3 + 4",
#        "9 + 2",
#        "3----++- 2",
#        "-2**-3**4",
#        "-2**-2",
#        "2**-2",
#        "-2**2",
#        "9 + 2 - 3",
#        "9 + 2 * 4",
#        "(9 + 2) * 3",
#        "(9 + -2) * 3",
#        "(9 + -2) * 3**-4**5",
#        "1**2**3",
#        "(1**2)**3",       #TODO: parentheses don't work here!
#        "M*X + B",
#        "M*(X + B)",
#        "1+2*-3^4*5+-+-6",
#        "2+3*4-2+3*4-2+3*4**-2**+3*4-2+3*4-2+3*4-2+3*4-2+3*4**-2**+3*4**-2*+3*4\
#         -2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4*2+3*4-2+3*4-2+3*4**-2**+3*4\
#         -2+3*4-2+3*4-2+3*4-2+3*4**-2**+3*4**-2*+3*4-2+3*4-2+3*4-2+3*4-2+3*4-+3\
#         *4-2+3*4-2+3*4*2+3*4-2+3*4-2+3*4**-2**+3*4-2+3*4-2+3*4-2+3*4-2+3*4**-2\
#         **+3*4**-2*+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4+1-2-3------4"
         ]
for t in test:
    print t
    print expr.parseString(t)
#    print power.parseString(t)
    print

