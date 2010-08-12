# -*- coding: utf-8 -*-
"""
Experiment with inspecting the frame stack.

Getting the function itself is more work. I think one could use the __import__ 
function to import the caller's module. However the filename must be somehow 
converted to a valid module name.

Documentation:
    http://docs.python.org/library/inspect.html
"""

import inspect

def find_caller():
    caller_frame = inspect.currentframe().f_back
    func_name = caller_frame.f_code.co_name
    file_name = caller_frame.f_code.co_filename
    print "Called by function:", func_name
    print "In file           :", file_name
    #Alternative, probably more portable way to get the textual information
    #print inspect.getframeinfo(caller_frame)

def foo():
    find_caller()
    

foo()