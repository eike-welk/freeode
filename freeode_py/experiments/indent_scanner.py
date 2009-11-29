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

FIXME: The current implementation does not function with comments. 
'''


import re
import pyparsing


def compute_indent_line_end_list(input_text):
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


def compute_indent_outdent_maps(indents_line_ends, input_text):
    '''
    Find line endings where the indent width changes.
    
    For each newline where the indent depth changes, create 
    an entry in a map: position in text -> indent width.
    Two maps are maintained, one where the indent increases (indent)
    and an other where the indent decreases (outdent).
    '''
    indent_tags, outdent_tags = {}, {}
    indent_stack = [0]
    il_it = indents_line_ends.__iter__()
    old_width, old_pos = il_it.next() 
    if old_width != 0:
        raise Exception('Indentation width at beginning of file must be 0!')
    for indent_width, line_end_pos in il_it:
        #no change of indent
        if indent_width == indent_stack[-1]:
            pass
        #indent increases, generate indent tag
        elif indent_width > indent_stack[-1]:
            indent_stack.append(indent_width)
            indent_tags[old_pos] = indent_width
        #indent decreases, generate outdent tag
        elif indent_width < indent_stack[-1]:
            #the outdent can cover multiple steps
            while indent_width < indent_stack[-1]:
                indent_stack.pop()
            if indent_stack[-1] != indent_width:
                line_no = pyparsing.lineno(line_end_pos, input_text)
                raise Exception("Inconsistent indent! "
                                "Line: %d, offending indent width: %d"
                                % (line_no, indent_width))
            outdent_tags[old_pos] = indent_width
        #data is corrupted
        else:
            raise Exception('Scanner internal error.')
        #remember position from previous line
        old_pos = line_end_pos
    return indent_tags, outdent_tags    
            
                         
class IndentData(object):
    '''Data to coordinate the indent parsers'''
    def __init__(self):
        self.indent_map = {}
        self.outdent_map = {}
        self.indent_stack = [0]
        self.init = False
        
    def initialize_maps(self, input_text):
        """Create the maps that identify indents and outdents"""
        indent_list = compute_indent_line_end_list(input_text)
        self.indent_map, self.outdent_map = \
                    compute_indent_outdent_maps(indent_list, input_text)
        self.init = True
        

class LineEndIndent(pyparsing.LineEnd):
    '''
    Parse end of line and increasing indent (in next line).
    '''    
    def __init__(self, data):
        pyparsing.LineEnd.__init__(self)
        self.data = data
        
    def parseImpl( self, instring, loc, doActions=True ):
        '''Do the parsing work'''
        #Initialize the maps if necessary
        if not self.data.init:
            self.data.initialize_maps()
        #test if there is a newline at loc
        new_loc, char = pyparsing.LineEnd.parseImpl(self, instring, 
                                                    int(loc), doActions)
        #test if there is also an increased indent at the next line
        indent_width = self.data.indent_map.get(int(loc), None)
        if indent_width:
            self.data.indent_stack.append(indent_width)
            return new_loc, char
        else:
            raise pyparsing.ParseException(instring, loc, "Expecting increasing indent.", self)
    
    
class LineEndNodent(pyparsing.LineEnd):
    '''
    Parse end of line and constant indent.
    '''    
    def __init__(self, data):
        pyparsing.LineEnd.__init__(self)
        self.data = data
        
    def parseImpl( self, instring, loc, doActions=True ):
        '''Do the parsing work'''
        #test if there is a newline at loc
        new_loc, char = pyparsing.LineEnd.parseImpl(self, instring, 
                                                    int(loc), doActions)
        #test if indent is changing at the next line
        i_loc = int(loc)
        if not (i_loc in self.data.indent_map or 
                i_loc in self.data.outdent_map   ): 
            return new_loc, char
        else:
            raise pyparsing.ParseException(instring, loc, "Expecting constant indent.", self)
    
    
class LineEndOutdent(pyparsing.LineEnd):
    '''
    Parse end of line and decreasing indent (in next line).
    '''    
    def __init__(self, data):
        pyparsing.LineEnd.__init__(self)
        self.data = data
        
    def parseImpl( self, instring, loc, doActions=True ):
        '''Do the parsing work'''
        #test if there is a newline at loc
        new_loc, char = pyparsing.LineEnd.parseImpl(self, instring, 
                                                    int(loc), doActions)
        #test if indent is decreasing at the next line
        indent_width = self.data.outdent_map.get(int(loc), None)
        if indent_width: 
            self.data.indent_stack.pop()
            #if multiple un-indents happen at this character, 
            #don't go to the next character, but increase loc only a tiny bit
            #return a float as loc
            if self.data.indent_stack[-1] < indent_width:
                return loc + 1./indent_width, char
            else:
                return new_loc, char
        else:
            raise pyparsing.ParseException(instring, loc, "Expecting decreasing indent.", self)
    
    
    
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
    il = compute_indent_line_end_list(input_text)
    print il
    intags, outtags = compute_indent_outdent_maps(il, input_text)
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































