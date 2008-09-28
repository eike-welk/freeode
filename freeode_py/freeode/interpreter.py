# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2006 - 2008 by Eike Welk                                *
#    eike.welk@post.rwth-aachen.de                                         *
#                                                                          *
#    Inspiration and little bits of text and code came from:               *
#     'fourFn.py', 'simpleArith.py' example programs, by Paul McGuire,     *
#     the 'Spark' library by John Aycock,                                  *
#     and the Python Reference Manual by Guido van Rossum.                 *
#    Many thanks for their excellent contributions to publicly available   *
#    knowledge.                                                            *
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
Interpreter, that is run at compile time, for the SIML language.

The interpreter reads the AST from the parser. It generates constant 
objects (the symbol table) and changes (simplifies) the code.
"""

from ast import *


class Instance(Node):
    '''
    Base class of all objects that the interpreter operates on.
    
    It inherits from Node only to get Ascii-art tree and copying.
    '''