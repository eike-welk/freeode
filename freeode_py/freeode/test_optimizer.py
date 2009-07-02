# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    License: GPL                                                          *
#                                                                          *
#    This program is free software; you can redistribute it and/or modify  *
#    it under the terms of the GNU General Public License as published by  *
#    the Free Software Foundation; either version 2 of the License, or     *
#    (at your option) any later version.                                   *
#                                                                          *
#    This program is distributed in the hope that it will be useful,       *
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#    GNU General Public License for more details.                          *
#                                                                          *
#    You should have received a copy of the GNU General Public License     *
#    along with this program; if not, write to the                         *
#    Free Software Foundation, Inc.,                                       *
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#***************************************************************************

"""
Test code for the "optimizer.py" module
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#The py library is not standard. Preserve ability to use some test functions
# for debugging when the py library, and the py.test testing framework, are 
# not installed. 
try:                      
    import py
except ImportError:
    print 'No py library, many tests may fail!'



def test_optimizer_1(): #IGNORE:C01111
    msg = '''
    Simple test
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import (Interpreter, IFloat)
    from freeode.ast import DotName, NodeAssignment

    prog_text = \
'''
class A:
    data a,b,c: Float
    
    func dynamic(this):       
        a = 1
        b = a * 2
        c = a * b + 1

compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    #mod = intp.modules['test']
    #print mod
    
    sim = intp.get_compiled_objects()[0]
    #print sim
    #look at variables
    a = sim.get_attribute(DotName('a'))
    b = sim.get_attribute(DotName('b'))
    c = sim.get_attribute(DotName('c'))
    #look at the generated function
    dyn = sim.get_attribute(DotName('dynamic'))




