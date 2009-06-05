# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2009 by Eike Welk                                *
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
Test code for the "interpreter.py" module
    Test basic functionality.
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



def test_ExpressionGenerator_1(): #IGNORE:C01111
    msg = 'Test creation of expression strings. Check all operators'
    #py.test.skip(msg)
    print msg
    from freeode.pygenerator import ExpressionGenerator, IFloat
    from freeode.ast import (DotName, RoleConstant,
                             NodeOpInfix2, NodeOpPrefix1, NodeParentheses)

    e_gen = ExpressionGenerator()
    #create some variables and numbers
    a = IFloat()
    a.target_name = 'a'
    b = IFloat()
    b.target_name = 'b'
    c = IFloat(2)
    c.role = RoleConstant
    
    #expression a + b * 2
    expr = NodeOpInfix2('+', (a, NodeOpInfix2('*', (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2}) == 5

    #expression a - b / 2
    expr = NodeOpInfix2('-', (a, NodeOpInfix2('/', (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2}) == 0

    #expression a ** b % 2
    expr = NodeOpInfix2('**', (a, NodeOpInfix2('%', (b, c))))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':2, 'b':3}) == 0

    #expression - 2
    expr = NodeOpPrefix1('-', (c,))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {}) == -2

    #expression (a + b) * 2
    expr = NodeOpInfix2('*', (NodeParentheses((NodeOpInfix2('+', (a, b)),)
                                              ), 
                              c)
                        )
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':1, 'b':2}) == 6



def test_ExpressionGenerator_2(): #IGNORE:C01111
    msg = 'Test creation of expression strings. Check function calls'
    #py.test.skip(msg)
    print msg
    from math import sin
    from freeode.pygenerator import ExpressionGenerator, IFloat
    from freeode.ast import (RoleConstant, NodeFuncCall)

    e_gen = ExpressionGenerator()
    #create some variables and numbers
    a = IFloat()
    a.target_name = 'a'
    b = IFloat()
    b.target_name = 'b'
    c = IFloat(2)
    c.role = RoleConstant
    
    #expression a + b * 2
    expr = NodeFuncCall('sin', (a,))
    expr_str = e_gen.create_expression(expr)
    print expr_str
    assert eval(expr_str, {'a':0, 'sin':sin}) == 0


    
if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_locals_update()
    pass
