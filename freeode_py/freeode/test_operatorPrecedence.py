#
# simpleArith.py
#
# Example of defining an arithmetic expression parser using
# the operatorGrammar helper method in pyparsing.
#
# Copyright 2006, by Paul McGuire
#

from pyparsing import *
ParserElement.enablePackrat()

S = Suppress
L = Literal
kw = Keyword

#TODO: write parser 2nd parser for expression that implemets
#      paul's way of dealing with the power operator.
#      Compare both operators!

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

def action_call(s, loc, toks):
    print "call: ",  toks
    toklist = toks.asList()[0]
    return [toklist]

def action_slicing(s, loc, toks):
    print "slice: ",  toks
    toklist = toks.asList()[0]
    return [toklist]

#The leaf nodes of the parse tree: integer numbers and variable names
integer = Word(nums).setParseAction(lambda t:int(t[0]))
literal = integer
identifier = (NotAny(kw('not') | kw('and') | kw('or')) +
              Word(alphas,exact=1))

expression = Forward()

#Atoms are the most basic elements of expressions.
##Brackets or braces are also categorized syntactically as atoms.
#TODO: enclosures can also create tuples
#enclosure = S('(') + expression + S(')')
atom = identifier | literal #| enclosure

#Function/method call: everything within the round brackets is parsed here;
# the function name is parsed in 'expression'
#The error message "Keyword arguments must come after positional arguments."
# will be generated in the parse action.
keyword_argument = Group(identifier + S('=') + expression)
argument_list = delimitedList(keyword_argument | expression) + Optional(S(','))
call = Group(S('(') - Optional(argument_list) + S(')'))

#Slicing/subscription: everything within the rectangular brackets is parsed here;
# the variable name is parsed in 'expression'
proper_slice = Group(Optional(expression) + L(':') + Optional(expression) #Look at Python documentation
                     + Optional(L(':') + Optional(expression))) #for possibly better parser.
ellipsis = L('...')
slice_item = ellipsis | proper_slice | expression
slice_list = delimitedList(slice_item) + Optional(S(','))
slicing = Group(S('[') - slice_list + S(']'))

#Expression: mathematical, logtical, and comparison operators;
# together with attribute access, function call, and slicing.
# The operators with the strongest binding come first.
expression << operatorPrecedence(atom,
    [(L('.'),       2,  opAssoc.LEFT,               action_op_infix_left), #access to an object's attributes
     (call,         1,  opAssoc.LEFT,               action_call), #function/method call: f(23)
     (slicing,      1,  opAssoc.LEFT,               action_slicing), #slicing/subscription: a[23]
     #Power and unary operations are intertwined to get correct operator precedence:
     #   -a**-b == -(a ** (-b))
     # TODO: TEST: -a**-b**-c is not parsed correctly???
     (oneOf('+ -'), 1, opAssoc.RIGHT,               action_op_prefix),
     (L('**'),      2, opAssoc.RIGHT,               action_op_infix),
     (oneOf('+ -'), 1, opAssoc.RIGHT,               action_op_prefix),
     (oneOf('* /'), 2, opAssoc.LEFT,                action_op_infix_left),
     (oneOf('+ -'), 2, opAssoc.LEFT,                action_op_infix_left),
     (oneOf('< > <= >= == !='), 2, opAssoc.LEFT,    action_op_infix_left),
     (kw('not'),    1, opAssoc.RIGHT,               action_op_prefix),
     (kw('and'),    2, opAssoc.LEFT,                action_op_infix_left),
     (kw('or'),     2, opAssoc.LEFT,                action_op_infix_left),
     ])

test = [
        "a.b.c",
        "1 + a(2, 3*a) + b()",
        "a(1, b=2,)",
        "a[2] + b[1, 2]",
        "a[1:2] + b[1:] + c[:] + d[:1]",
        "a[::] - a[::1] - a[0, 1:1:1, 2]",
#        "1 and 2 or not a and b",
#        "not a <= a and c > d",
#        "1*2+3",
        "-2**-3 == -(2**(-3))",
#        "1*-2**3",
#        "-1**-2**-3",
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
#        "(1**2)**3",
#        "1**-2**3",
#        "1**(-2)**3",
#        "M*X + B",
#        "M*(X + B)",
#        "1+2*-3^4*5+-+-6",
#        "2+3*4-2+3*4-2+3*4**-2**+3*4-2+3*4-2+3*4-2+3*4-2+3*4**-2**+3*4**-2*+3*4\
#         -2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4*2+3*4-2+3*4-2+3*4**-2**+3*4\
#         -2+3*4-2+3*4-2+3*4-2+3*4**-2**+3*4**-2*+3*4-2+3*4-2+3*4-2+3*4-2+3*4-+3\
#         *4-2+3*4-2+3*4*2+3*4-2+3*4-2+3*4**-2**+3*4-2+3*4-2+3*4-2+3*4-2+3*4**-2\
#         **+3*4**-2*+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4+1-2-3------4"
         ]

print
for t in test:
    print t
    print expression.parseString(t)
#    print power.parseString(t)
    print

