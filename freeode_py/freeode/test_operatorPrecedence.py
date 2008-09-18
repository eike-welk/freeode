#Test script to develop a nice and extendable parser for expressions,
# using the latest features from Pyparsing.

from pyparsing import *
ParserElement.enablePackrat()

S = Suppress
L = Literal
kw = Keyword

# TODO: Enter Pyparsing whish:
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
#    print "call: ",  toks
    toklist = toks.asList()[0]
    return [toklist]

def action_slicing(s, loc, toks):
#    print "slice: ",  toks
    toklist = toks.asList()[0]
    return [toklist]

print 'syntax definition start'
#The leaf nodes of the parse tree: numbers and variable names ------------------------
smartInteger = Word(nums).setParseAction(lambda t:int(t[0]))
uInteger = Word(nums)
#Floating point number (unsigned).
eE = CaselessLiteral( 'E' )
uFloat = Group( Combine(
            uInteger +
            Optional('.' + Optional(uInteger)) +
            Optional(eE + Word('+-'+nums, nums))))

literal = smartInteger | uFloat | sglQuotedString

identifier = (NotAny(kw('not') | kw('and') | kw('or')) +
              Word(alphas+'_', alphanums+'_'))


#The expression is defined recursively. Therefor it needs a forward declaration ----------
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
keyword_argument = Group(identifier + '=' + expression)
positional_argument = Group(expression)
argument = keyword_argument | positional_argument
argument_list = Group(delimitedList(argument)) + Optional(',')
#argument_list = delimitedList(keyword_argument | expression) + Optional(S(','))
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
print 'syntax definition before operatorPrecedence'
expression << operatorPrecedence(atom,
    [(L('.'),       2, opAssoc.LEFT,                action_op_infix_left), #access to an object's attributes
     (L('$'),       1, opAssoc.RIGHT,               action_op_prefix), #time differential
     (call,         1, opAssoc.LEFT,                action_call), #function/method call: f(23)
     (slicing,      1, opAssoc.LEFT,                action_slicing), #slicing/subscription: a[23]
     #Power and unary operations are intertwined to get correct operator precedence:
     #   -a**-b == -(a ** (-b))
     # TODO: TEST: -a**-b**-c is not parsed correctly???
     (oneOf('+ -'), 1, opAssoc.RIGHT,               action_op_prefix), #sign (+, -)
     (L('**'),      2, opAssoc.RIGHT,               action_op_infix), #power
     (oneOf('+ -'), 1, opAssoc.RIGHT,               action_op_prefix), #sign (+, -)
     (oneOf('* /'), 2, opAssoc.LEFT,                action_op_infix_left),
     (oneOf('+ -'), 2, opAssoc.LEFT,                action_op_infix_left),
     (oneOf('< > <= >= == !='), 2, opAssoc.LEFT,    action_op_infix_left),
     (kw('not'),    1, opAssoc.RIGHT,               action_op_prefix),
     (kw('and'),    2, opAssoc.LEFT,                action_op_infix_left),
     (kw('or'),     2, opAssoc.LEFT,                action_op_infix_left),
     ]).setName('expression')
print 'syntax definition after operatorPrecedence'

#----------    this is the code that takes so long ----------------------------
print 'syntax definition 1'
dummy0 = delimitedList(expression) #this statement seems to use 500 MiB
# this goes much faster
print 'syntax definition 2'
dummy1 = expression + ZeroOrMore(Suppress(',') + expression)

print 'syntax definition end'

test = [
        "aa.ba.c",
        "$a.b * $a.c[2] + 3",
        "1 + a(2, 3*a) + b()",
        "a(1, b=2,)",
        "a[2] + b[1, 2]",
        "a[1:2] + b[1:] + c[:] + d[:1]",
        "a[::] - a[::1] - a[0, 1:1:1, 2]",
#        "1 and 2 or not a and b",
#        "not a <= a and c > d",
#        "1*2+3",
        "-2**-3 == -(2**(-3))",
        "a(1,b=2)",
#        "1**-2**3",
#        "1**2**3",
#        "1+2+3",
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
#         **+3*4**-2*+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4-2+3*4+1-2-3------4",
         ]

print
for t in test:
    print t
    print expression.parseString(t)
    print

