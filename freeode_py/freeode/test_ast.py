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
Test code for the ast module
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#The py library is not standard. Preserve ability to use some test functions
# for debugging when the py library, and the py.test testing framework, are 
# not installed. 
try:                      
    import py                                       
except:
    print 'No py library, many tests may fail!'

import unittest
#tell the py.test framework to recognize traditional unittest tests
pytest_plugins = "pytest_unittest"


#import library which we want to test
from freeode.ast import * 


class TestAST(unittest.TestCase):

    def setUp(self):
        '''Node: perform common setup tasks for each test'''
        #create a tree
        n5 = Node(name='n5', type='leaf',   kids=[])       
        n4 = Node(name='n4', type='leaf',   kids=[])       
        n3 = Node(name='n3', type='leaf',   kids=[])       
        n2 = Node(name='n2', type='branch', kids=[n3, n4])
        n1 = Node(name='n1', type='trunk',  kids=[n2, n5]) 
        self.tree1 = n1
#        print n1
        n1 = Node(name='n1', type='leaf',   kids={}) 
        n2 = Node(name='n2', type='leaf',   kids={}) 
        n3 = Node(name='n3', type='trunk',  kids={'n1':n1, 'n2':n2}) 
        self.tree2 = n3

    def test__init__(self):
        '''Node: Test the __init__ method'''
        #The init method creates one attribute for each named argument.
        #There are no default attributes.
        n1 = Node()
        self.assertTrue(len(n1.__dict__) == 0)
        n2 = Node(loc=1, dat='test')
        self.assertTrue(n2.loc == 1)       #IGNORE:E1101  
        self.assertTrue(n2.dat == 'test')  #IGNORE:E1101
        self.assertRaises(TypeError, self.raise__init__1)
    def raise__init__1(self):
        '''Node: Positional arguments raise exceptions'''
        Node('test')

    def test__str__(self):
        '''Node: Test printing and line wraping (it must not crash)'''
        #TODO: Make this smarter, printing and copying are the only 
        #      genuine functions of Node
        #Test wrapping and lists
        #create additional node with many big attributes
        n_big = Node(  name='n_big', 
                        test1 = 'qworieoqwiruuqrw',
                        test2 = 'qworieoqwiruuqrw',
                        test3 = 'qworieoqwiruuqrw',
                        test4 = 'qworieoqwiruuqrw',
                        test5 = 'qworieoqwiruuqrw',
                        test6 = 'qworieoqwiruuqrw',
                        test7 = 'qworieoqwiruuqrw',
                        test8 = 'qworieoqwiruuqrw',
                        test9 = 'qworieoqwiruuqrw',
                        test10 = 'qworieoqwiruuqrw')
        self.tree1.kids[0].big = n_big                #IGNORE:E1101
        _str1 = str(self.tree1)
#        print
#        print self.tree1
        #Test dicts
        _str2 = str(self.tree2)
#        print
#        print self.tree2

#    def testIterDepthFirst(self):
#        #TODO: Reenable when new iterator exists
#        #iteration, all child nodes recursive
#        l = []
#        for node1 in self.tree1.iterDepthFirst():
#            l.append(node1.loc)
#        self.assertEqual(l, [1, 2, 3, 4, 5])
#        #iteration, all child nodes recursive also depth is returned
#        l = []
#        for node1, depth in self.tree1.iterDepthFirst(returnDepth=True):
#            line = 'dat: %s, depth; %d' % (node1.dat, depth)
#            l.append(line)
#        self.assertEqual(l, ['dat: root, depth; 0',
#                             'dat: branch, depth; 1',
#                             'dat: leaf, depth; 2',
#                             'dat: leaf, depth; 2',
#                             'dat: leaf, depth; 1'])

    def testCopy(self):
        '''Node: Test copy function'''
        #create additional weak attributes
        n1 = Node(name='weak1')
        n2 = Node(name='weak2')
        pr = weakref.proxy(n1)
#        pr = n1    #to make test fail
        wr = weakref.ref(n2)
        self.tree1.pr = pr                                                   #IGNORE:W0201
        self.tree1.kids[0].wr = wr                                           #IGNORE:E1101
        #create (mostly) deep copy
        tree1_c = self.tree1.copy() 
        #assert that values are equal
        self.assertTrue(len(tree1_c.__dict__) == len(self.tree1.__dict__))
        self.assertTrue(tree1_c.name == self.tree1.name)                     #IGNORE:E1101
        self.assertTrue(tree1_c.kids[0].name == self.tree1.kids[0].name)     #IGNORE:E1101
        self.assertTrue(   tree1_c.kids[0].kids[0].name == 
                        self.tree1.kids[0].kids[0].name    )                 #IGNORE:E1101
        #assert that copy created new objects
        self.assertFalse(id(tree1_c) == id(self.tree1))
        self.assertFalse(id(tree1_c.kids[0]) == id(self.tree1.kids[0]))      #IGNORE:E1101
        self.assertFalse(id(   tree1_c.kids[0].kids[0]) == 
                         id(self.tree1.kids[0].kids[0])    )                 #IGNORE:E1101
        #test copying of not owned (weak, shared) attributes
        #assert that values are equal
        self.assertTrue(tree1_c.pr.name == self.tree1.pr.name)               #IGNORE:E1101
        self.assertTrue(   tree1_c.kids[0].wr().name == 
                        self.tree1.kids[0].wr().name    )                    #IGNORE:E1101
        #assert no new objects were created
        self.assertTrue(id(tree1_c.pr) == id(self.tree1.pr))                 #IGNORE:E1101
        self.assertTrue(id(   tree1_c.kids[0].wr()) == 
                        id(self.tree1.kids[0].wr())    )                     #IGNORE:E1101
        # this assertion is an implementation detail
        self.assertTrue(id(   tree1_c.kids[0].wr) == 
                        id(self.tree1.kids[0].wr)    )                       #IGNORE:E1101



class TestVisitor(unittest.TestCase):

    def setUp(self):
        '''perform common setup tasks for each test'''
        pass

#    def test__when_type(self):
#        #this tests implementation details
#        #define dummy class to test the decorators
#        class FooClass(Visitor):
#            @Visitor.when_type(list, 23)
#            def test(self):
#                print 'test(...) called'
#
#        #print FooClass.test._dispatchIfType
#        self.assertEqual(FooClass.test._dispatchIfType, list)
#        self.assertEqual(FooClass.test._dispatchPriority, 23)
#        fooInst = FooClass()
#        #print fooInst.test._dispatchIfType
#        #print fooInst.test._dispatchPriority
#        self.assertEqual(fooInst.test._dispatchIfType, list)
#        self.assertEqual(fooInst.test._dispatchPriority, 23)
#        #print fooInst._ruleTable
#        #fooInst.test()


    def test__dispatch(self):
        '''Visitor: Test normal operation.'''
        #define visitor class
        class FooClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            @Visitor.when_type(list)
            def visitList(self, _inObject):
                return 'list'
            @Visitor.when_type(int)
            def visitInt(self, _inObject):
                return 'int'
            @Visitor.when_type(float)
            def visitFloat(self, _inObject):
                return 'float'
            @Visitor.default
            def visitDefault(self, _inObject):
                return 'default'

        #test dispatching - dispatching multiple times also tries the cache
        fooInst = FooClass()
        #print fooInst.dispatch([])
        self.assertEqual(fooInst.dispatch([]), 'list')
        self.assertEqual(fooInst.dispatch([1,2]), 'list')
        self.assertEqual(fooInst.dispatch([]), 'list')
        #print fooInst.dispatch(1)
        self.assertEqual(fooInst.dispatch(1), 'int')
        self.assertEqual(fooInst.dispatch(2), 'int')
        self.assertEqual(fooInst.dispatch(3), 'int')
        #print fooInst.dispatch(1.0)
        self.assertEqual(fooInst.dispatch(1.0), 'float')
        #print fooInst.dispatch('qwert')
        self.assertEqual(fooInst.dispatch('qwert'), 'default')
        
        print 'test__dispatch finished successfully!'


    def test__switching_inheritance_priority(self):
        '''Visitor: Test switching based on inheritance and priority.'''
        #Define class hierarchy
        class Base(object):
            pass
        class Derived1(Base):
            pass
        class Derived2(Base):
            pass

        #define visitor class
        class TestVisitorClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            #Can handle all Base objects but has low priority
            @Visitor.when_type(Base, 1)
            def visitBase(self, _inObject):
                return 'Base'
            #Specialized method for Derived1 with high priority
            @Visitor.when_type(Derived1, 5)
            def visitDerived1(self, _inObject):
                return 'Derived1'
            @Visitor.when_type(int)
            def visitInt(self, _inObject):
                return 'int'

        #create some objects that the visitor should handle
        baseInst = Base()
        derived1Inst = Derived1()
        derived2Inst = Derived2()
        intInst = 2
        #create the visitor
        visitor = TestVisitorClass()

        #try the visitor
        self.assertEqual(visitor.dispatch(baseInst), 'Base')
        self.assertEqual(visitor.dispatch(derived1Inst), 'Derived1')
        self.assertEqual(visitor.dispatch(derived2Inst), 'Base')
        self.assertEqual(visitor.dispatch(intInst), 'int')


    def test_priority_2(self):
        '''Visitor: Test priority 2.'''

        class A(Node):
            pass
        class B(Node):
            pass
        
        class NodeVisitor(Visitor):
            def __init__(self):
                Visitor.__init__(self)

            #Handlers for derived classes - specialized
            #- should have high priority
            @Visitor.when_type(A, 2)
            def visitA(self, a_inst):                         #IGNORE:W0613
#                print 'seen class def: ' + classDef.name
                return ['A']
            @Visitor.when_type(B, 2)
            def visitB(self, b_inst):                          #IGNORE:W0613
#                print 'seen func def: ' + funcDef.name
                return ['B']

            #handler for a base class - general
            #- should have low priority
            @Visitor.when_type(Node, 1)
            def visitNode(self, node): #IGNORE:W0613
#                print 'seen Node: ' + str(node.dat)
                return ['Node']

            def mainLoop(self, tree):
                retList = []
                for node in tree.kids:
                    retList += self.dispatch(node)
                return retList

        #create a syntax tree
        tr = Node(kids=[])
        tr.kids.append(A(name='a1'))  #IGNORE:E1101
        tr.kids.append(A(name='a2'))  #IGNORE:E1101
        tr.kids.append(Node(name='n1'))           #IGNORE:E1101
        tr.kids.append(B(name='b1'))   #IGNORE:E1101
        tr.kids.append(B(name='b2'))   #IGNORE:E1101
        #visit all nodes
        nv = NodeVisitor()
        testList = nv.mainLoop(tr)
#        print testList

        expectedList = ['A', 'A', 'Node', 'B', 'B']
        self.assertEqual(testList, expectedList)


    def test__built_in_default_func(self):
        '''Visitor: Test the built in default function.'''
        #define visitor class
        class FooClass(Visitor):
            def __init__(self):
                Visitor.__init__(self)
            @Visitor.when_type(list)
            def visitList(self, _inObject):
                return 'list'
            @Visitor.when_type(int)
            def visitInt(self, _inObject):
                return 'int'

        fooInst = FooClass()
        #print fooInst.dispatch([])
        self.assertEqual(fooInst.dispatch([]), 'list')
        #print fooInst.dispatch(1)
        self.assertEqual(fooInst.dispatch(1), 'int')
        #the built in default function raises an exception.
        try:
            self.assertEqual(fooInst.dispatch(1.0), 'float')
            #if we get till here there was an error
            raise Exception('Expected exception was not raised!')
        except TypeError: #IGNORE:W0704
            #print err
            pass


    def test__decorator_errors(self):
        '''Visitor: Test errors because of wrong decorator use.'''
        self.assertRaises(TypeError, self.raise__decorator_error_1)
        self.assertRaises(TypeError, self.raise__decorator_error_2)
        self.assertRaises(TypeError, self.raise__decorator_error_3)
        self.assertRaises(TypeError, self.raise__decorator_error_4)
    def raise__decorator_error_1(self):
        '''Error: No parameters for @Visitor.when_type.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.when_type
            def visitList(self, _inObject):
                return 'list'
    def raise__decorator_error_2(self):
        '''Error: Wrong 1st parameter for @Visitor.when_type.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.when_type([])
            def visitList(self, _inObject):
                return 'list'
    def raise__decorator_error_3(self):
        '''Error: Wrong 2nd parameter for @Visitor.when_type.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.when_type(list, 'qwert')
            def visitList(self, _inObject):
                return 'list'
    def raise__decorator_error_4(self):
        '''Error: Parameters for @Visitor.default.'''
        class FooClass(Visitor): #IGNORE:W0612
            @Visitor.default(int)
            def visitDefault(self, _inObject):
                return 'default'



def test_visitor_inherited_handler_methods():
    '''
    Test if the visitor calls inherited handler methods correctly.
       - The priority values dictate what method takes precedence. 
       - Only when the priority values are the same, then the (new) method
         of the current class is called. 
       - When the current class defines a default function, then this default 
         function is used; the default function of the base class is forgotten. 
    '''
    py.test.skip('Inherited handler functions are currently not implemented.') #IGNORE:E1101
    
    #Define class hierarchy
    class Base(object):
        pass
    class Derived1(Base):
        pass
    class Derived2(Base):
        pass

    #define visitor class
    class TestVisitorClass(Visitor):
        def __init__(self):
            Visitor.__init__(self)
        #Can handle all Base objects but has low priority
        @Visitor.when_type(Base, 1)
        def visit_Base(self, _inObject):
            return 'Base'
        #Specialized method for Derived1 with high priority
        @Visitor.when_type(Derived1, 5)
        def visit_Derived1(self, _inObject):
            return 'Derived1'
        @Visitor.when_type(int)
        def visit_Int(self, _inObject):
            return 'int'
        @Visitor.default
        def default_handler(self, _inObject):
            return 'default handler'

    #create the visitor
    visitor = TestVisitorClass()
    #try the visitor
    assert visitor.dispatch(Base()) == 'Base'
    assert visitor.dispatch(Derived1()) == 'Derived1'
    assert visitor.dispatch(Derived2()) == 'Base'
    assert visitor.dispatch(2) == 'int'
    assert visitor.dispatch(2.5) == 'default handler'
    
    #define derived visitor
    class TestVisitorDerived(TestVisitorClass):
        def __init__(self):
            TestVisitorClass.__init__(self)
        #redefine handler for base class (low priority).
        @Visitor.when_type(Base, 1)
        def visit_Base(self, _inObject):
            return 'Base by derived'
        @Visitor.default
        def default_handler(self, _inObject):
            return 'default handler by derived'
        
    #create the visitor
    visitor2 = TestVisitorDerived()
    #test derived visitor
    assert visitor2.dispatch(Base()) == 'Base by derived'
    assert visitor2.dispatch(Derived1()) == 'Derived1'
    assert visitor2.dispatch(Derived2()) == 'Base'
    assert visitor2.dispatch(2) == 'int'
    assert visitor2.dispatch(2.5) == 'default handler by derived'

    
    
class TestDotName(unittest.TestCase):

    def setUp(self):
        '''perform common setup tasks for each test'''
        pass

    def test__new__(self):
        '''DotName: Test constructor.'''
        #create DotName object from string
        abc = DotName('a.b.c')
        self.assertTrue(abc == ('a','b','c'))
        self.assertTrue(tuple(abc) == ('a','b','c'))
        #create DotName from other iterable
        abc1 = DotName(('a','b','c'))
        self.assertTrue(abc1 == ('a','b','c'))

    def test__str__(self):
        '''DotName: Test conversion to string.'''
        abc = DotName('a.b.c')
        self.assertTrue(str(abc) == 'a.b.c')

    def test__repr__(self):
        '''DotName: Test repr method.'''
        abc = DotName('a.b.c')
        self.assertTrue(repr(abc) == "DotName('a.b.c')")

    def test__add__(self):
        '''DotName: Test addition (concatenating).'''
        #addition of two DotNames
        abc = DotName('a.b.c')
        efg = DotName('e.f.g')
        abcefg = abc + efg
        self.assertTrue(abcefg == DotName('a.b.c.e.f.g'))
        self.assertTrue(isinstance(abcefg, DotName))
        #mixed addition with tuple 1
        abcefg = abc + ('e', 'f', 'g')
        self.assertTrue(abcefg == DotName('a.b.c.e.f.g'))
        self.assertTrue(isinstance(abcefg, DotName))
        #mixed addition with tuple 2
        abcefg = ('a', 'b', 'c') + efg
        self.assertTrue(abcefg == DotName('a.b.c.e.f.g'))
        self.assertTrue(isinstance(abcefg, DotName))

    def test__getitem__(self):
        '''DotName: Test access to parts of the object (foo[1], foo[0:4]).'''
        a_g = DotName('a.b.c.d.e.f.g')
        #subscription
        b = a_g[1]
        self.assertTrue(b == 'b')
        self.assertTrue(isinstance(b, str))
        e = a_g[4]
        self.assertTrue(e == 'e')
        self.assertTrue(isinstance(e, str))
        #simple slicing
        abc = a_g[0:3]
        self.assertTrue(abc == DotName('a.b.c'))
        self.assertTrue(isinstance(abc, DotName))
        c_c = a_g[2:3]
        self.assertTrue(c_c == DotName('c'))
        self.assertTrue(isinstance(c_c, DotName))
        empty = a_g[3:3]
        self.assertTrue(empty == DotName())
        self.assertTrue(isinstance(empty, DotName))
        #extendet slicing
        a_g2 = a_g[0:7:2]
        self.assertTrue(a_g2 == DotName('a.c.e.g'))
        self.assertTrue(isinstance(a_g2, DotName))
        #test boundary checking
        self.assertRaises(IndexError, self.raise__getitem__1)
        #This unexpectedly works, because the tuple implementation thinks 
        #it's OK
#        self.assertRaises(IndexError, self.raise__getitem__2)
        self.raise__getitem__2()
#        self.assertRaises(IndexError, self.raise__getitem__3)
        self.raise__getitem__3()
        return 
    def raise__getitem__1(self):
        '''Subscription out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[9]
    def raise__getitem__2(self):
        '''Simple slice out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[0:9]
    def raise__getitem__3(self):
        '''Extended slice out of bounds'''
        a_g = DotName('a.b.c.d.e.f.g')
        _foo = a_g[0:9:2]



if __name__ == '__main__':
    # Debugging code may go here.
#    t1 = TestVisitor('test__dispatch')
#    t1.run()
    test_visitor_inherited_handler_methods()
    
    pass
