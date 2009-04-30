# -*- coding: utf-8 -*-
#Try if parsing in Unicode works
#Tested on x86_64 GNU/Linux (Suse Linux 11.0)

from pyparsing import *

#creating the parser
start_kw = Keyword('ABC')
end_kw = Keyword('XYZ')
the_parser = (start_kw + '|' + CharsNotIn('|') + '|' + end_kw)

#some test texts
text1 = 'ABC | マルチ | XYZ'
text2 = 'ABC | チディ | XYZ'
text3 = 'ABC | 图形等 | XYZ'
text4 = 'ABC | 应用程 | XYZ'
text5 = 'ABC | Äöü | XYZ'
text6 = 'ABC | iöü | XYZ'
bad_1 = 'ABC  应用程 | XYZ'
bad_2 = 'ABC | 应用程  XYZ'

#function to present input output and errors in a nice way
def parse_text(text):
    print 
    print 'Trying to parse: ', text
    try: 
        print 'Result: ', the_parser.parseString(text) 
    except ParseException, error:
        print '\nParse error!'
        print error

#do some parsing 
parse_text(text1)
parse_text(text2)
parse_text(text3)
parse_text(text4)
parse_text(text5)
parse_text(text6)
parse_text(bad_1)
parse_text(bad_2)


