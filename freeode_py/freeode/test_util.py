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



# -------- Test AATreeMaker class ----------------------------------------------------------------------
def test_AATreeMaker(): #IGNORE:C01111
    msg = 'AATreeMaker.make_attr_lists: select attributes for the different \n' \
          'groups for string conversion.'
    #skip_test(msg)
    print msg
    
    from freeode.util import AATreeMaker
    
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
        
    t1 = Test1()
    
    top_attr, short_attr, long_attr, bottom_attr \
        = t1.__siml_aa_tree_maker__.make_attr_lists(t1)
    print top_attr, short_attr, long_attr, bottom_attr  
    
    assert top_attr == ['name', 'top'] 
    assert short_attr == ['bar', 'two', 'want_short1', 'want_short2', 'want_xshort'] 
    assert long_attr == ['want_long1', 'want_long2', 'want_long3', 'want_long4'] 
    assert bottom_attr == ['bottom']


if __name__ == '__main__':
    # Debugging code may go here.
    #test_expression_evaluation_1()
    test_AATreeMaker()
    pass
