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
Test the module units.py
'''

from __future__ import division
from __future__ import absolute_import              


from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import raises            # pylint: disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises



# -------- Test parse_prefix_symbol ----------------------------------------------------------------------
def test_parse_prefix_symbol_1(): #IGNORE:C01111
    msg = 'Test parse_prefix_symbol: a few simple cases.'
    #skip_test(msg)
    print msg
    
    from freeode.units import parse_prefix_symbol
    
    prefi, symi = parse_prefix_symbol('A')
    assert prefi is None
    assert symi.symbol == 'A'
    prefi, symi = parse_prefix_symbol('pF')
    assert prefi.symbol == 'p'
    assert symi.symbol == 'F'
    prefi, symi = parse_prefix_symbol('ms')
    assert prefi.symbol == 'm'
    assert symi.symbol == 's'
    prefi, symi = parse_prefix_symbol('mmol')
    assert prefi.symbol == 'm'
    assert symi.symbol == 'mol'
#    prefi, symi = parse_prefix_symbol('   mmol     ')
#    assert prefi.symbol == 'm'
#    assert symi.symbol == 'mol'
    assert_raises(ValueError, None, parse_prefix_symbol, '') 
    assert_raises(ValueError, None, parse_prefix_symbol, 'X') 
    assert_raises(ValueError, None, parse_prefix_symbol, 'Xm') 
    


def test_parse_prefix_symbol_2(): #IGNORE:C01111
    msg = 'Test parse_prefix_symbol: Try to parse all units.'
    #skip_test(msg)
    print msg
    
    from freeode.units import parse_prefix_symbol, symbol_infos
    
    for curr_symi in symbol_infos:
        sym_str = curr_symi.symbol
        #print 'Testing unit:', sym_str
        prefi, symi = parse_prefix_symbol(sym_str)
        #print 'Recognized unit:', symi.symbol
        assert prefi is None
        assert symi is curr_symi



def test_parse_prefix_symbol_3(): #IGNORE:C01111
    msg = 'Test parse_prefix_symbol: ' \
          'Prefix all units with all prefixes and try to parse them.'
    #skip_test(msg)
    print msg
    
    from freeode.units import parse_prefix_symbol, symbol_infos, prefix_infos
    
    for curr_symi in symbol_infos:
        #Units for hour ('h') minute ('min') and day ('d') should not have prefixes
        if curr_symi.symbol in ['h', 'min', 'd']:
            continue
        for curr_prefi in prefix_infos:
            prefsym = curr_prefi.symbol + curr_symi.symbol
            print 'Testing prefixed unit:', prefsym, ' ~~ ', curr_prefi.name, curr_symi.name
            prefi, symi = parse_prefix_symbol(prefsym)
            print 'Recognized prefix:', prefi.symbol, '; unit:', symi.symbol
            assert prefi is curr_prefi
            assert symi is curr_symi



# ---------- call function for debugging here ---------------------------------
if __name__ == '__main__':
    # Debugging code may go here.
    test_parse_prefix_symbol_3()
    pass #pylint:disable-msg=W0107
