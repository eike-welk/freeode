# -*- coding: utf-8 -*-
'''
Design PyParsing parsers for Python style indented grammars, that work with 
packrat parsing. 

The Parsers should be a pair of "Indent", "Outdent" parsers, that can
be used like curly brackets "{ }". A "Nodent" parser that replaces the regular
LineEnd parser will be necessary too.

The difficulty lies in the Outdent, "}" parser, because one newline can be 
equivalent to several matches of the Outdent, "}" parser. This interferes with
packrat parsing (cashing of partial parse results). For example look at 
the end of a class definition in the Python language. There the indent usually 
decreases by two levels: 
1. end of "def" statement; 2. end of "class" statement. 

A possible idea to make packrat parsing compatible with the outdent parser is
to use floating point values for the current location of the parser.
'''


import re


class IndentScanner(object):
    def __init__(self):
        pass
    
    def computeIndentLineEndList(self, input_text):
        '''
        Scan through text and compute indent width and position of newline,
        for each line that contains text. 
        
        Argument:
        ---------
        input_text:
            Text for which indent widths are computed
            
        Return:
        -------
        list(tuple(ini, int)):
            Each tuple is: (indent width, position of newline)   
        '''
        black_finder = re.compile(r'[\S]') #matches any non-whitespace char
        indent_line_end = [] #function result
        line_start, line_end = 0, None
        while line_start < len(input_text):
            #find end of current line - search for next newline character
            #if no newline is found, current line extends until end of text
            line_end = input_text.find('\n', line_start)
            if line_end == -1:
                line_end = len(input_text)
            #find position of first black character in current line
            #compute indent width from this position 
            black = black_finder.search(input_text, line_start, line_end)
            if black:
                indent_width = black.start() - line_start
                indent_line_end.append((indent_width, line_end))
            #advance to next line
            line_start = line_end + 1
        return indent_line_end
    
    
    def findIndentOutdentTags(self, indent_line_end):
        '''
        Iterate through the list of indent width and line-end positions
        and generate indent and outdent tags.
        '''
        indent_tags, outdent_tags = {}, {}
        indent_stack = [0]
        for indent_width, line_end_pos in indent_line_end:
            #no change of indent
            if indent_width == indent_stack[-1]:
                continue
            #indent increases, generate indent tag
            elif indent_width > indent_stack[-1]:
                indent_stack.append(indent_width)
                indent_tags[line_end_pos] = indent_width
            #indent decreases, generate outdent tag
            #the outdent can cover multiple steps
            elif indent_width < indent_stack[-1]:
                while indent_width < indent_stack[-1]:
                    indent_stack.pop()
                if indent_stack[-1] != indent_width:
                    raise Exception("inconsistent indent!")
                outdent_tags[line_end_pos] = indent_width
            #data is corrupted
            else:
                raise Exception('Scanner internal error.')
            
        return indent_tags, outdent_tags    
            
                         

if __name__ == '__main__':
    #correct example
    input_text = """\
0
 1
  2
 1
  2
0
"""
    scan = IndentScanner()
    il = scan.computeIndentLineEndList(input_text)
    print il
    intags, outtags = scan.findIndentOutdentTags(il)
    print intags
    print outtags
    
    #erroneous example
    input_text = """\
0
0
 1
   3
  2
 1
0
"""































