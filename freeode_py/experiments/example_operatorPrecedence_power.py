# Grammar for mathematical expressions, that to parses
# the power (**) and sign (-) operators correctly.
#
# operatorPrecedence (of Pyparsing 1.5.0) can not parse power and sign 
# correctly, because it has a purely hierarchical model for the precedence 
# of operators.
#
# See also:
# http://docs.python.org/ref/power.html


from pyparsing import *
ParserElement.enablePackrat() #comment this out once for comparison


#dummy parse actions
def action_op_prefix(s, loc, toks):
#    print "pre: ",  toks
    return

def action_op_infix(s, loc, toks):
#    print "in : ",  toks
    return

def action_op_infix_left(s, loc, toks):
#    print "inL: ",  toks
    return


#The leaf nodes of the parse tree: integer numbers and variable names
integer = Word(nums).setParseAction(lambda t:int(t[0]))
variable = (NotAny(Keyword('not') | Keyword('and') | Keyword('or')) +
            Word(alphas,exact=1))

#Let parentheses work with power and unary '-' too
expression = Forward()
primary = integer | variable | Suppress('(') + expression + Suppress(')')

#Power and unary operations are intertwined to get correct operator precedence:
#   -a**-b == -(a ** (-b))
power,  u_expr = Forward(), Forward()
#Exponentiation: a**b;
#Strongest binding on left side, weaker than unary operations (-a) on right side.
power1 = Group(primary + '**' + u_expr)          .setParseAction(action_op_infix)
power << (power1 | primary)
#Unary arithmetic operations: -a; +a
u_expr1 = Group(oneOf('- +') + u_expr)           .setParseAction(action_op_prefix)
u_expr << (u_expr1 | power)

#All other operators are defined here. Those with the strongest binding come first.
expression << operatorPrecedence( u_expr,
    [(oneOf('* /'),   2, opAssoc.LEFT,           action_op_infix_left),
     (oneOf('+ -'),   2, opAssoc.LEFT,           action_op_infix_left),
     (oneOf('< > <= >= == !='), 2, opAssoc.LEFT, action_op_infix_left),
     (Keyword('not'), 1, opAssoc.RIGHT,          action_op_prefix),
     (Keyword('and'), 2, opAssoc.LEFT,           action_op_infix_left),
     (Keyword('or'),  2, opAssoc.LEFT,           action_op_infix_left),
     ])

test = [
        "1**2**3**4",
        "-2**-3 == -(2**(-3))", #why does this expression take so long?
        "3----++-2",
        "1 and 2 or not a and b",
        "not a <= a and c > d",
        "9 + 2 - 3 + 4",
        "9 + 2 * 4",
        "(9 + 2) * 3",
        "(9 + -2) * 3**-4**5",
        "M*X + B",
        "M*(X + B)",
#        "2+3*4-2+3*4-2+3*4**-2**+3*4-2+3*4 and -2+3*4-2+3*4 or -2+3*4**-2**+3*4**-2**+3*4\
#         -2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2 or 3*4-2 and not 3*4*2+3*4-2+3*4-2+3*4**-2**3*4\
#         -2+3*4-2+3*(4-2+3)*4*-2+3*4**-2**+3**4**-2**+3**(4-(2+3)*4-2+3*4-2+3*4-2)+3*4-+3\
#         *4-2+3*4-2+3*4*2+3*4-2+3*4-2+3*4**-2**+3**4**-2 < +3*4-2 or 3**4-2+3*4-2+3*4**-2\
#         **+3**-4**-2*+3*4-2+3*4-2==+3*4 or -2+3*4<-2+3*4-2+3*4-2+3*4-2+3*4+1-2-3-------4"
         ]

#test the parser
print
for t in test:
    print t
    print expression.parseString(t)
#    print power.parseString(t)
    print