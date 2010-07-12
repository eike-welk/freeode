# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2010 - 2010 by Eike Welk                                #
#    eike.welk@gmx.net                                                     #
#                                                                          #
#    License: GPL                                                          #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

'''
Test the module util.py
'''

from __future__ import division
from __future__ import absolute_import              


from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import raises            # pylint: disable-msg=F0401,E0611,W0611



# -------- Test AATreeMaker class ----------------------------------------------------------------------
def test_AATreeMaker_make_attr_lists(): #IGNORE:C01111
    msg = 'AATreeMaker._group_attributes: select attributes for the different \n' \
          'groups for string conversion.'
    #skip_test(msg)
    print msg
    
    from freeode.util import AATreeMaker
    
    #create some classes for the tree
    #some smaller leaves and branches
    class TestWantLong(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self):
            self.name = 'print me long'
    
    class TestWantShort1(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self):
            self.name = 'print me short 1'
    
    class TestWantShort2(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self):
            self.name = 'print me short 2'
    
    #the tree trunk
    class Test1(object):
        __siml_aa_tree_maker__ = AATreeMaker(top_names=['name', 'top'], 
                                             xshort_names=['want_xshort'], 
                                             short_names=['want_short1'], 
                                             long_names=['want_long2'], 
                                             bottom_names=['bottom'], 
                                             short_types=[TestWantShort2])
        
        def __init__(self):
            self.name = 'contain multiple cases'
            self.top = 'also want to top'
            self.bottom = 'my bottom'
            self.bar = 'my bar'
            self.two = 2
            self.want_short1 = TestWantShort1()
            self.want_xshort = TestWantShort1()
            self.want_short2 = TestWantShort2()
            self.want_long1 = TestWantLong()
            self.want_long2 = 'also want long'
            self.want_long3 = [TestWantLong()]
            self.want_long4 = {'foo':TestWantLong()}
        
    #create the tree
    t1 = Test1()
    
    #group the attributes into four groups
    top_attr, short_attr, long_attr, bottom_attr \
        = t1.__siml_aa_tree_maker__._group_attributes(t1) #pylint: disable-msg=W0212
        
    #print top_attr, short_attr, long_attr, bottom_attr  
    
    assert top_attr == ['name', 'top'] 
    assert short_attr == ['bar', 'two', 'want_short1', 'want_short2', 'want_xshort'] 
    assert long_attr == ['want_long1', 'want_long2', 'want_long3', 'want_long4'] 
    assert bottom_attr == ['bottom']



def test_AATreeMaker_make_tree(): #IGNORE:C01111
    msg = 'AATreeMaker.make_tree: test string conversion.'
    #skip_test(msg)
    print msg
    
    from freeode.util import AATreeMaker
    
    #create some classes for the tree
    #some smaller leaves and branches
    class TestWantLong(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self):
            self.name = 'print me long'
    
    class TestWantShort1(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self):
            self.name = 'print me short 1'
    
    class TestWantShort2(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self):
            self.name = 'print me short 2'
    
    #the tree trunk
    class Test1(object):
        __siml_aa_tree_maker__ = AATreeMaker(top_names=['name', 'top'], 
                                             xshort_names=['want_xshort'], 
                                             short_names=['want_short1'], 
                                             long_names=['want_long2'], 
                                             bottom_names=['bottom'], 
                                             short_types=[TestWantShort2])
        
        def __init__(self):
            self.name = 'contain multiple cases'
            self.top = 'also want to top'
            self.bottom = 'my bottom'
            self.bar = 'my bar'
            self.two = 2
            self.want_short1 = TestWantShort1()
            self.want_xshort = TestWantShort1()
            self.want_short2 = TestWantShort2()
            self.want_long1 = TestWantLong()
            self.want_long2 = 'also want long'
            self.want_long3 = [TestWantLong(), TestWantLong(), 'hello']
            self.want_long4 = {'foo':TestWantLong(), 'bar':1}
        
    #create the tree
    t1 = Test1()
    
    _tree_str = t1.__siml_aa_tree_maker__.make_tree(t1)
    #print tree_str
    
    
    
def test_AATreeMaker_infinite_recursion(): #IGNORE:C01111
    msg = 'AATreeMaker.make_tree: test protection against infinite_recursion.'
    #skip_test(msg)
    print msg
    
    from freeode.util import AATreeMaker

    class Test1(object):
        __siml_aa_tree_maker__ = AATreeMaker()
        def __init__(self, name, foo=None, bar=None):
            self.name = name
            self.foo = foo
            self.bar = bar
            
    tree = Test1('root', 
                 Test1('branch1', Test1('branch2', 23, 42), 13), 
                 Test1('branch3', 'hello', 'world'))
    tree.foo.bar = tree
    
    _tree_str = tree.__siml_aa_tree_maker__.make_tree(tree)
    #print tree_str
    
    
    
# -------- Test DotName --------------------------------------------------------  
def test_DotName__new__():
    msg =  'DotName: Test constructor.'
    #skip_test(msg)
    print msg

    from freeode.util import DotName
    
    #create DotName object from string
    abc = DotName('a.b.c')
    assert(abc == ('a', 'b', 'c'))
    assert(tuple(abc) == ('a', 'b', 'c'))
    #create DotName from other iterable
    abc1 = DotName(('a', 'b', 'c'))
    assert(abc1 == ('a', 'b', 'c'))


def test_DotName__str__():
    msg =  '''DotName: Test conversion to string.'''
    #skip_test(msg)
    print msg

    from freeode.util import DotName
    
    abc = DotName('a.b.c')
    assert(str(abc) == 'a.b.c')


def test_DotName__repr__():
    msg =  '''DotName: Test repr method.'''
    #skip_test(msg)
    print msg

    from freeode.util import DotName
    
    abc = DotName('a.b.c')
    assert(repr(abc) == "DotName('a.b.c')")


def test_DotName__add__():
    msg =  '''DotName: Test addition (concatenating).'''
    #skip_test(msg)
    print msg

    from freeode.util import DotName
    
    #addition of two DotNames
    abc = DotName('a.b.c')
    efg = DotName('e.f.g')
    abcefg = abc + efg
    assert(abcefg == DotName('a.b.c.e.f.g'))
    assert(isinstance(abcefg, DotName))
    #mixed addition with tuple 1
    abcefg = abc + ('e', 'f', 'g')
    assert(abcefg == DotName('a.b.c.e.f.g'))
    assert(isinstance(abcefg, DotName))
    #mixed addition with tuple 2
    abcefg = ('a', 'b', 'c') + efg
    assert(abcefg == DotName('a.b.c.e.f.g'))
    assert(isinstance(abcefg, DotName))


def test_DotName__getitem__():
    msg =  '''DotName: Test access to parts of the object (foo[1], foo[0:4]).'''
    #skip_test(msg)
    print msg

    from freeode.util import DotName
    
    a_g = DotName('a.b.c.d.e.f.g')
    #subscription
    b = a_g[1]
    assert(b == 'b')
    assert(isinstance(b, str))
    e = a_g[4]
    assert(e == 'e')
    assert(isinstance(e, str))
    #simple slicing
    abc = a_g[0:3]
    assert(abc == DotName('a.b.c'))
    assert(isinstance(abc, DotName))
    c_c = a_g[2:3]
    assert(c_c == DotName('c'))
    assert(isinstance(c_c, DotName))
    empty = a_g[3:3]
    assert(empty == DotName())
    assert(isinstance(empty, DotName))
    #extendet slicing
    a_g2 = a_g[0:7:2]
    assert(a_g2 == DotName('a.c.e.g'))
    assert(isinstance(a_g2, DotName))
    
    #test boundary checking
    def raise__getitem__1():
        '''Subscription out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[9]
    def raise__getitem__2():
        '''Simple slice out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[0:9]
    def raise__getitem__3():
        '''Extended slice out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[0:9:2]
    raises(IndexError, raise__getitem__1)
    #The next tests unexpectedly work, because the tuple implementation thinks 
    #it's OK.
    #raises(IndexError, raise__getitem__2)
    raise__getitem__2()
    #raises(IndexError, raise__getitem__3)
    raise__getitem__3()
    return 



# -------- Test UserException --------------------------------------------------------  
def test_UserException():
    msg = "Test the class for user visible exceptions"
    #skip_test(msg)
    print msg
    
    from freeode.util import UserException, TextLocation
    
    #test the __repr__ function
    err = UserException("Foo", None, None)
    #print repr(err)
    assert repr(err) == "UserException('Foo', None, None)"
    
    #test __str__ function; it must not crash
    err = UserException("Foo", None, None)
    print err
    err = UserException("Foo", TextLocation(3, "Foo bar", "baz.txt"), 42)
    print err



# -------- Testing aids --------------------------------------------------------  
def test_assert_raises():
    msg = "Test function for checking that the correct exceptions are raised."
    #skip_test(msg)
    print msg
    
    from freeode.util import UserException, assert_raises
    
    class DummyException(Exception):
        pass

    #--- Correct behavior -----------------------------------------------
    #Test case: correct exception is raised with errno
    #Also test parameter passing
    def raise_errno_001(a, b, c, d):
        assert a == 1 and b == 2 and c == 3 and d == 4
        raise UserException('Test message', None, 1)
    assert_raises(UserException, 1, raise_errno_001, (1, 2), {'c':3, 'd':4})
    
    #Test case: correct exception is raised no errno
    def raise_DummyException_1():
        raise DummyException('Test message')
    assert_raises(DummyException, None, raise_DummyException_1)
    
    #--- Errors -----------------------------------------------------------
    #Test case: wrong errno
    try:
        def raise_errno_002():
            raise UserException('Test message', None, 2)
        assert_raises(UserException, 1, raise_errno_002)
    except AssertionError:
        print '--- Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised!'
        
    #Test case: Wrong exception is raised
    try:
        def raise_DummyException_2():
            raise DummyException('Test message')
        assert_raises(UserException, 1, raise_DummyException_2)
    except DummyException:
        print '--- Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised!'

    #Test case: No exception is raised
    try:
        def raise_nothing():
            pass
        assert_raises(UserException, 1, raise_nothing)
    except AssertionError:
        print '--- Correct exception was raised.'
    else:
        assert False, 'An exception should have been raised!'



def test_debug_print():
    msg = """Test debug printing function. 
          The output must be viewed to check correct operation.
          """
    #skip_test(msg)
    print msg
    
    from freeode.util import debug_print
    import freeode.util
    
    freeode.util.DEBUG_AREAS.add('test')
    
    #Testing debug levels
    print 'freeode.util.DEBUG_AREAS: ', freeode.util.DEBUG_AREAS
    print 'Two lines should be printed with debug area "test":'
    debug_print('This text should appear. area="test"', area="test")
    debug_print('This text should appear too. area="test"', area="test")
    debug_print('This text should NOT appear. area="foo"', area="foo")
    print
    #test a few other data types
    debug_print('String, int, float, function:', 1, 2.0, debug_print, 
                sep=" ", area="test")
    #test all legal keyword arguments
    debug_print('Print', 'with', 'big', 'spaces', 'between', 'words,', 
                sep='      ', end='\n\n\n\n', area="test")
    debug_print('and also with many newlines at the end.', end='\n\n', 
                area="test")
    #Test illegal keyword arguments
    debug_print('Some illegal keyword arguments.', foo=2, bar='hello', 
                area="test")
        
        
    
def test_search_result_lines(): #IGNORE:C01111
    msg = '''Test function test_search_result_lines'''
#    skip_test(msg)
    print msg
    
    from freeode.util import assert_raises, search_result_lines, Line
    
    in_text = '''
lkasdf kldfj ladkfj 
test1: 4 5 6
klasdf asdf 
foo test2: 1 2 3
klajfd 
'''
    search_result_lines(in_text, [Line(['test1:', 4, 5, 6]),
                                  Line(['foo test2:', 1, 2, 3])])
    
    def raise1():
        search_result_lines(in_text, [Line(['test1:', 4, 5, 7]),
                                      Line(['foo test2:', 1, 2, 3])])
    assert_raises(AssertionError, None, raise1)
    
    def raise2():
        search_result_lines(in_text, [Line(['test1:', 4, 5, 6, 7]),
                                      Line(['foo test2:', 1, 2, 3])])
    assert_raises(AssertionError, None, raise2)
    
    def raise3():
        search_result_lines(in_text, [Line(['test0:', 0, 0, 0, 0]),
                                      Line(['test1:', 4, 5, 6]),
                                      Line(['foo test2:', 1, 2, 3])])
    assert_raises(AssertionError, None, raise3)
    
    
 
def test_compile_run_lines(): #IGNORE:C01111
    msg = '''Test function compile_run'''
#    skip_test(msg)
    print msg
    
    from freeode.util import assert_raises, compile_run, DEBUG_AREAS
    import os
    
    DEBUG_AREAS.add('compile_run')
    
    prog_text = \
'''
class Foo:
    data x: Float
    
    func initialize(this):
        x = 0
        solution_parameters(100, 1)
        print('in initialize')
        
    func dynamic(this):
        $x = 1
        
    func final(this):
        print('final x:', x)
    

compile Foo
'''
    base_name = ('compile_run_output')
    test_prefix = 'testprefix_'
    out_file = open(base_name + '.siml', 'w')
    out_file.write(prog_text)
    out_file.close()
    
#    os.system('pwd')
#    os.system('ls')

    compile_run(base_name + '.siml', test_prefix)
    assert_raises(AssertionError, None, compile_run, 
                  (base_name + '.siml', test_prefix, '--foo'))
    
    #compile_run(base_name + '.siml', test_prefix, '--foo', run_sims, no_graphs, clean_up)
    #assert_raises(exc_type, errno, func, args, kwargs)
    #TODO: clean up junk
    
    #remove the siml file
    os.remove(base_name + '.siml')
    


if __name__ == '__main__':
    # Debugging code may go here.
    test_compile_run_lines()
    pass #pylint: disable-msg=W0107
