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
Test code for the ast module
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611

import unittest
#tell the py.test framework to recognize traditional unittest tests
pytest_plugins = "pytest_unittest"


#import weakref


class TestAST(unittest.TestCase): #IGNORE:C01111

    def setUp(self):
        '''Node: perform common setup tasks for each test'''
        from freeode.ast import Node
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
        from freeode.ast import Node
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
        from freeode.ast import Node
        Node('test')

    def test__str__(self):
        '''Node: Test printing and line wraping (it must not crash)'''
        from freeode.ast import Node
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
        _str1 = self.tree1.aa_make_tree()
#        print
#        print self.tree1
        #Test dicts
        _str2 = self.tree2.aa_make_tree()
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

#    def testCopy(self):
#        '''Node: Test copy function'''
#        from freeode.ast import Node
#        #create additional weak attributes
#        n1 = Node(name='weak1')
#        n2 = Node(name='weak2')
#        pr = weakref.proxy(n1)
##        pr = n1    #to make test fail
#        wr = weakref.ref(n2)
#        self.tree1.pr = pr                                                   #IGNORE:W0201
#        self.tree1.kids[0].wr = wr                                           #IGNORE:E1101
#        #create (mostly) deep copy
#        tree1_c = self.tree1.copy() 
#        #assert that values are equal
#        self.assertTrue(len(tree1_c.__dict__) == len(self.tree1.__dict__))
#        self.assertTrue(tree1_c.name == self.tree1.name)                     #IGNORE:E1101
#        self.assertTrue(tree1_c.kids[0].name == self.tree1.kids[0].name)     #IGNORE:E1101
#        self.assertTrue(   tree1_c.kids[0].kids[0].name == 
#                        self.tree1.kids[0].kids[0].name    )                 #IGNORE:E1101
#        #assert that copy created new objects
#        self.assertFalse(id(tree1_c) == id(self.tree1))
#        self.assertFalse(id(tree1_c.kids[0]) == id(self.tree1.kids[0]))      #IGNORE:E1101
#        self.assertFalse(id(   tree1_c.kids[0].kids[0]) == 
#                         id(self.tree1.kids[0].kids[0])    )                 #IGNORE:E1101
#        #test copying of not owned (weak, shared) attributes
#        #assert that values are equal
#        self.assertTrue(tree1_c.pr.name == self.tree1.pr.name)               #IGNORE:E1101
#        self.assertTrue(   tree1_c.kids[0].wr().name == 
#                        self.tree1.kids[0].wr().name    )                    #IGNORE:E1101
#        #assert no new objects were created
#        self.assertTrue(id(tree1_c.pr) == id(self.tree1.pr))                 #IGNORE:E1101
#        self.assertTrue(id(   tree1_c.kids[0].wr()) == 
#                        id(self.tree1.kids[0].wr())    )                     #IGNORE:E1101
#        # this assertion is an implementation detail
#        self.assertTrue(id(   tree1_c.kids[0].wr) == 
#                        id(self.tree1.kids[0].wr)    )                       #IGNORE:E1101
    
    

if __name__ == '__main__':
    # Debugging code may go here.
#    t1 = TestVisitor('test__dispatch')
#    t1.run()
    #test_UserException()
    pass
