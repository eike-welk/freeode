# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
#    eike.welk@gmx.net                                                     *
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
    Provoke errors, mainly high level by writing small Siml Programs.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611
#from py.test import raises            # pylint: disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises


def test_argument_list_1(): #IGNORE:C01111
    msg = 'Test error in argument list - too many arguments.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    prog_text = \
'''
func foo(a):
    return a

data a, b: Float    
foo(a, b)
'''
    #create the interpreter
    intp = Interpreter()
    
    assert_raises(UserException, 3200250, 
                  intp.interpret_module_string, prog_text, None, 'test')
    
#    print 'module after interpreter run: ---------------------------------'
#    print aa_make_tree(intp.modules['test'])
    
  
  
def test_argument_list_2(): #IGNORE:C01111
    msg = 'Test error in argument list - unknown argument.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a):
    return a

data a: Float    
foo(b=a)
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 3200260
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  
  
def test_argument_list_3(): #IGNORE:C01111
    msg = 'Test error in argument list - Duplicate argument.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a, b):
    return a

data a, b: Float    
foo(a, a=b)
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 3200270
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  
  
def test_argument_list_4(): #IGNORE:C01111
    msg = 'Test error in argument list - too few arguments.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a, b):
    return a

data a: Float    
foo(a)
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 3200280
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  

def test_argument_list_5(): #IGNORE:C01111
    msg = 'Test error in argument list - wrong types.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a: String):
    return a

data a: Float    
foo(a)
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 3200310
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  

def test_argument_list_6(): #IGNORE:C01111
    msg = 'Test error in argument list - keyword arguments must come first, function definition.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a=1, b):
    return a
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 3200110
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  

def test_argument_list_7(): #IGNORE:C01111
    msg = 'Test error in argument list - duplicate argument names, function definition.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a, a):
    return a
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 3200120
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  

def test_argument_list_8(): #IGNORE:C01111
    msg = 'Test error in argument list - keyword arguments must come first, function call.'
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
func foo(a, b):
    return a

foo(a=1, 2)
'''
    #create the interpreter
    intp = Interpreter()
    
    try:
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print e
        assert e.errno == 2140010
        print 'Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised.'
    
#    print 'module after interpreter run: ---------------------------------'
#    print intp.modules['test']
    
  

def test_argument_list_compile_statement_1(): #IGNORE:C01111
    msg = '''
    Good error messages when argument 'this' is missing in definition of 
    any main function. ("dynamic()" instead of "dynamic(this)")
    
    This is a reminder for an error (now fixed) where empty argument lists
    did not receive the correct location of their definition.
    
    - The error message should point to line 3 as the line where the function 
    is defined.
    - It should also point to line 6 where the call to dynamic(...) is made 
    implicitly. 
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 


    prog_text = \
'''
class A:
    func dynamic():
        pass
    
compile A
'''

    #interpret the program
    intp = Interpreter()
    try:
        intp.interpret_module_string(prog_text, None, 'test')
    except UserException, e:
        print 'Exception is OK'
        print e
        assert e.errno == 3200250
        print 'Correct exception was raised.'
        #Judge the quality of the error message:
        #Try to find the text 'line 3', which is the line where the function 
        #is defined
        err_str = str(e)
        index = err_str.find('line 3')
        assert index != -1, 'Line of function definition is not mentioned ' \
                            'correctly in error message.'
    else:
        assert False, 'No exception is raised.'



def test_Interpreter_statement_dispatch_1(): #IGNORE:C01111
    msg = \
    '''Test errors generated by StatementVisitor.dispatch: 
    - Duplicate attribute.'''
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
data a: Float const
data a: Float const
'''
    #create the interpreter
    intp = Interpreter()
    
#    print 'module after interpreter run: ---------------------------------'
#    print aa_make_tree(intp.modules['test'])

    def raise_1():
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3800910, raise_1)

    

def test_Interpreter_statement_dispatch_2(): #IGNORE:C01111
    msg = \
    '''Test errors generated by StatementVisitor.dispatch: 
    - Undefined attribute.'''
    #py.test.skip(msg)
    print msg
    from freeode.interpreter import Interpreter
    from freeode.util import UserException    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    
    prog_text = \
'''
data a: Float const
a = 2 * b
'''
    #create the interpreter
    intp = Interpreter()
    
#    print 'module after interpreter run: ---------------------------------'
#    print aa_make_tree(intp.modules['test'])

    def raise_1():
        #run mini program
        intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3250100, raise_1)
        
  
  
def test_if_statement_error_1(): #IGNORE:C01111
    msg = '''
    Test the if statement. Code is generated and condition involves variables.
    There is no catch all (else) statement. The interpreter must complain about it.
    '''
    #py.test.skip(msg)
    print msg
    
    from freeode.interpreter import Interpreter
    from freeode.util import UserException
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 

    prog_text = \
'''
class A:
    data a,b: Float
    data c: Float const
    
    func dynamic(this):       
        if a == 1:
            b = 1
        elif a == 2:
            b = 2
        elif a == 3:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    def raise_1():
        intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3700630, raise_1)



def test_if_statement_error_2(): #IGNORE:C01111
    msg = '''
    Test the if statement. There is a return statement in the body of the "if"
    statement. The interpreter must detect the error.
    '''
    #skip_test(msg)
    print msg
    
    from freeode.util import UserException
    from freeode.interpreter import Interpreter    
    #from freeode.util import aa_make_tree  #pylint:disable-msg=W0612 


    prog_text = \
'''
class A:
    data a,b: Float
    data c: Float const
    
    func dynamic(this):       
        if a == 1:
            b = 1
        elif a == 2:
            b = 2
            return
        else:
            b = 3

compile A
'''

    #interpret the program
    intp = Interpreter()
    def raise_1():
        intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3700640, raise_1)


def test_unknown_const_1(): #IGNORE:C01111
    msg = '''The interpreter must find any illegal use of unknown constants.
    Reading unknown constants in anything that generates code is illegal.
    '''
    #skip_test(msg)
    print msg
    
    from freeode.interpreter import Interpreter
    from freeode.util import UserException

    # --- operator and unknown constant ----------------------
    prog_text = \
'''
class A:
    data c: Float const
    
    func initialize(this):
        c + 2
              
compile A
'''
    #interpret the program
    intp = Interpreter()
    #intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3190110, 
                  intp.interpret_module_string, prog_text, '-dummy-', 'test')
    #return
    
    # --- built in function and unknown constant ----------------------
    prog_text = \
'''
class A:
    data c: Float const
    
    func initialize(this):
        sqrt(c)
              
compile A
'''
    #interpret the program
    intp = Interpreter()
    #intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3190110, 
                  intp.interpret_module_string, prog_text, '-dummy-', 'test')
    #return

    # --- print function and unknown constant ----------------------
    prog_text = \
'''
class A:
    data c: Float const
    
    func initialize(this):
        print(c)
              
compile A
'''
    #interpret the program
    intp = Interpreter()
    #intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3190110, 
                  intp.interpret_module_string, prog_text, '-dummy-', 'test')
    #return

    # --- printc function must work, it does never generate code. -------------
    prog_text = \
'''
class A:
    data c: Float const
    
    func initialize(this):
        printc(c)
              
compile A
'''
    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')
    #return

    # --- assignment and unknown constant ----------------------
    prog_text = \
'''
class A:
    data p: Float param
    data c: Float const
    
    func initialize(this):
        p = c
              
compile A
'''
    #interpret the program
    intp = Interpreter()
    #intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3190110, 
                  intp.interpret_module_string, prog_text, '-dummy-', 'test')

    # --- assignment and unknown constant ----------------------
    prog_text = \
'''
class A:
    data c1, c2: Float const
    
    func initialize(this):
        c1 = c2
              
compile A
'''
    #interpret the program
    intp = Interpreter()
    #intp.interpret_module_string(prog_text, None, 'test')
    assert_raises(UserException, 3190110, 
                  intp.interpret_module_string, prog_text, '-dummy-', 'test')



if __name__ == '__main__':
    # Debugging code may go here.
    test_unknown_const_1()
    pass #pylint: disable-msg=W0107
