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
*******************************
Units of Measurement.
*******************************

Numerical simulations are mainly concerned with physical quantities. The Siml
language is therefore able to express units natively to reduce the need
for tedious and error prone unit conversions.



Terms
-----

Dimensions
    * Basic physical effects that are useful to describe the world. 
    * For example: length, time, mass
    
Unit of measurement
    * A standardized quantity in one or more dimensions
    * For example: meter, second, kilogram, Newton

Physical quantities 
    * A value in some dimension, compared to a unit.
    * A unit multiplied with a numerical value
    * http://en.wikipedia.org/wiki/Physical_quantity
    
Numerical value
    * The number part of the physical quantity 
     
Quantity calculus
    * The rules for computing with units
 
A unit in Siml consists of basic units, their powers, and a scaling factor.
'''

from __future__ import division
from __future__ import absolute_import          


#TODO: Unit parser, that converts one unit symbol into prefix, unit-symbol
#      * Problem ambiguity m (meter) - m (mili), 
#      * Leading 'm' in mol, min
#      * Additional ambiguity: min (milliinch) - min (minute)
# 
#    Possible solution:
#        Cross product of all units with all prefixes, and identify them
#        directly instead of parsing.
#   
#    Possible solution:
#        Parse from end. First recognize unit, then prefix. The longest possible 
#        sequence matches.
#
#    Tests:
#        * Try all unit symbols. They must be only matched by themselves.
#        * Prepend all units by all prefixes. Assert that the correct prefixes 
#          and units are matched.

#TODO: For defining private units the parser should do some consistency checks
#      There might be clashes between units, prefixes and prefixed units.

class SymbolInfo(object):
    '''Contains information about unit symbols.'''
    def __init__(self, name, symbol, comment, expression=None):
        assert name != '' and symbol != ''
        self.name = name
        self.symbol = symbol 
        self.comment = comment 
        self.expression = expression 
        
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return '{cls}({name}, {symbol}, {comment}, {expression})' \
               .format(cls=type(self).__name__, 
                       name = self.name,
                       symbol = self.symbol,
                       comment = self.comment,
                       expression = self.expression)

    
class PrefixInfo(object):
    '''Contains information about unit prefixes.'''
    def __init__(self, name, symbol, factor):
        assert name != '' and symbol != ''
        self.name = name
        self.symbol = symbol
        self.factor = factor
        
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return '{cls}({name}, {symbol}, {factor})' \
               .format(cls=type(self).__name__, 
                       name = self.name,
                       symbol = self.symbol,
                       factor = self.factor)
        
        
#--- Generated code - start ---------------------------------------------------        
symbol_infos = [ 
    #SI Base Units 
    #Generated from lines 69 - 77 
    SymbolInfo('metre', 'm', 'Length', ''), 
    SymbolInfo('second', 's', 'Time', ''), 
    #SymbolInfo('kilogram', 'kg', 'Mass', ''), 
    SymbolInfo('gram', 'g', 'Mass additional unit to simplify parser', ''), 
    SymbolInfo('ampere', 'A', 'Electric current', ''), 
    SymbolInfo('kelvin', 'K', 'Thermodynamic temperature', ''), 
    SymbolInfo('mole', 'mol', 'Amount of substance', ''), 
    SymbolInfo('candela', 'cd', 'Luminous intensity', ''), 
    #SI Derived Units 
    #Generated from lines 87 - 114 
    SymbolInfo('hertz', 'Hz', 'frequency', 's-1'), 
    SymbolInfo('radian', 'rad', 'angle', 'dimensionless'), 
    SymbolInfo('steradian', 'sr', 'solid angle', 'dimensionless'), 
    SymbolInfo('newton', 'N', 'force, weight', 'kg·m·s^−2'), 
    SymbolInfo('pascal', 'Pa', 'pressure, stress', 'm^−1·kg·s^−2'), 
    SymbolInfo('joule', 'J', 'energy, work, heat', 'm^2·kg·s^−2'), 
    SymbolInfo('watt', 'W', 'power, radiant flux', 'm^2·kg·s^−3'), 
    SymbolInfo('coulomb', 'C', 'electric charge', 's·A'), 
    SymbolInfo('volt', 'V', 'voltage', 'm^2·kg·s^−3·A^−1'), 
    SymbolInfo('farad', 'F', 'electric capacitance', 'm^−2·kg^−1·s^4·A^2'), 
    SymbolInfo('ohm', 'Ohm', 'electric resistance', 'm^2·kg·s^−3·A^−2'), 
    SymbolInfo('siemens', 'S', 'electrical conductance', 'm^−2·kg^−1·s^3·A^2'), 
    SymbolInfo('weber', 'Wb', 'magnetic flux', 'm^2·kg·s^−2·A^−1'), 
    SymbolInfo('tesla', 'T', 'magnetic field strength', 'kg·s^−2·A^−1'), 
    SymbolInfo('henry', 'H', 'inductance', 'm^2·kg·s^−2·A^−2'), 
    SymbolInfo('celsius', 'degC', 'temperature', 'K − 273.15'), 
    SymbolInfo('lumen', 'lm', 'luminous flux', 'cd·sr'), 
    SymbolInfo('lux', 'lx', 'illuminance', 'm^−2·cd·sr'), 
    SymbolInfo('becquerel', 'Bq', 'radioactivity', 's^−1'), 
    SymbolInfo('gray', 'Gy', 'absorbed dose', 'm^2·s^−2'), 
    SymbolInfo('sievert', 'Sv', 'equivalent dose', 'm^2·s^−2'), 
    SymbolInfo('katal', 'kat', 'catalytic activity', 's^−1·mol'), 
    #Additional Units  
    #Generated from lines 124 - 141 
    SymbolInfo('minute', 'min', 'time', '60·s'), 
    SymbolInfo('hour', 'h', 'time', '3600·s'), 
    SymbolInfo('day', 'd', 'time', '24*3600·s'), 
    SymbolInfo('litre', 'l', 'volume', '10^-3·m^3'), 
    SymbolInfo('tonne', 't', 'weight', '1000·kg'), 
    SymbolInfo('degree arc', 'degA', 'angle', '(π/180)·rad'), 
    SymbolInfo('minute arc', 'minA', 'angle', '(π/10800)·rad'), 
    SymbolInfo('second arc', 'sA', 'angle', '(π/648000)·rad'), 
    SymbolInfo('electronvolt', 'eV', 'energy', '1.60217653(14)×10−19·J'), 
    SymbolInfo('atomic mass unit', 'u', 'mass', '1.66053886(28)×10−27·kg'), 
    SymbolInfo('astronomical unit', 'AU', 'length', '1.49597870691(6)×1011·m'), 
    SymbolInfo('nautical mile', 'M', 'length', '1852·m'), 
    SymbolInfo('knot', 'kn', 'speed', '(1852/3600)·m/s'), 
    SymbolInfo('bar', 'bar', 'pressure', '10^5·Pa'), 
    SymbolInfo('poise', 'P', 'dynamic viscosity', '0.1·Pa·s'), 
    SymbolInfo('stokes', 'St', 'kinematic viscosity', '10^–4·m^2·s^–1'), ] 

#SI Prefixes  
prefix_infos = [ 
    #Generated from lines 150 - 170 
    PrefixInfo('yotta', 'Y', 10**24), 
    PrefixInfo('zetta', 'Z', 10**21), 
    PrefixInfo('exa', 'E', 10**18), 
    PrefixInfo('peta', 'P', 10**15), 
    PrefixInfo('tera', 'T', 10**12), 
    PrefixInfo('giga', 'G', 10**9), 
    PrefixInfo('mega', 'M', 10**6), 
    PrefixInfo('kilo', 'k', 10**3), 
    PrefixInfo('hecto', 'h', 10**2), 
    PrefixInfo('deca', 'da', 10**1), 
    PrefixInfo('deci', 'd', 10**-1), 
    PrefixInfo('centi', 'c', 10**-2), 
    PrefixInfo('milli', 'm', 10**-3), 
    PrefixInfo('micro', 'μ', 10**-6), 
    PrefixInfo('nano', 'n', 10**-9), 
    PrefixInfo('pico', 'p', 10**-12), 
    PrefixInfo('femto', 'f', 10**-15), 
    PrefixInfo('atto', 'a', 10**-18), 
    PrefixInfo('zepto', 'z', 10**-21), 
    PrefixInfo('yocto', 'y', 10**-24), ] 

#--- Generated code - end --------------------------------------------------- 


#Put the longest unit symbols first.
symbol_infos_sorted = sorted(symbol_infos, key=lambda s: len(s.symbol), 
                             reverse=True)
prefix_finder = dict([(p.symbol, p) for p in prefix_infos])
#print [s.symbol for s in symbol_infos_sorted]
#print prefix_finder

def parse_prefix_symbol(prefsym_str):
    '''
    Recognizes unit symbols with optional prefixes.
    
    ARGUMENTS
    ---------
    
    prefsym_str: str
        The possibly prefixed unit symbol as a string. 
        For example 'km', 'm', 'pF', 's'
        
    RETURNS
    -------
    
    tuple(prefix, symbol)
        prefix: PrefixInfo
        symbol: SymbolInfo
    '''
    #prefsym_str = prefsym_str.strip()
    #search the symbol --
    symi = None
    for symi in symbol_infos_sorted:
        if prefsym_str.endswith(symi.symbol):
            #print "found symbol: %s in %s" % (symi.symbol, prefsym_str)
            break
    else:
        raise ValueError("Unknown unit: '%s'" % prefsym_str)
    #search the prefix --
    prefi = None
    #Cut off the symbol from the end of the string
    pref_str = prefsym_str[:-len(symi.symbol)]
    if pref_str:
        prefi = prefix_finder.get(pref_str, None)
        if prefi is None:
            raise ValueError("Unknown prefix: '%s'. Unit string: '%s'" 
                             % (pref_str, prefsym_str))
    return (prefi, symi)


#TODO: Unit implementation
#        * Unit symbols and powers 
#            * encoded as dict: {'m':1, 's':-1} {'kg':1, 'm':1, 's':-2}
#        * Scale factor: float
#        * ?Offset for temperature: float?
#TODO: Some quantities should not be reduced to base units, because they are
#      useful as is. Probably only important for:
#      * __str__
#      * __mul__ keep the unit intact. Does this have any relevance here? 

