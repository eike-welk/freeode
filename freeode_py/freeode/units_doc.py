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
*******************************************************************
Documentation and Code Generators for Units of Measurement Module
*******************************************************************

This module contains code generator scripts, and documentation for the 
units module.

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



SI Units
-------------

============= ================ ========================== 
SI Base Units
http://en.wikipedia.org/wiki/SI_base_unit                 
----------------------------------------------------------
Name          Symbol           Quantity                   
============= ================ ======================================= = 
metre         m                Length                     
second        s                Time                       
kilogram      kg               Mass  
gram          g                Mass additional unit to simplify parser  
ampere        A                Electric current           
kelvin        K                Thermodynamic temperature  
mole          mol              Amount of substance        
candela       cd               Luminous intensity         
============= ================ ========================== 
                               
                               
========== ====== ======================= =================== =================== 
SI Derived Units 
http://en.wikipedia.org/wiki/SI_derived_unit
---------------------------------------------------------------------------------
Name       Symbol Quantity                Expression in terms Expression in terms 
                                          of other units      of SI base units
========== ====== ======================= =================== ===================
hertz      Hz     frequency               1/s                 s-1
radian     rad    angle                   m·m^-1              dimensionless
steradian  sr     solid angle             m2·m^-2             dimensionless
newton     N      force, weight           kg·m/s^2            kg·m·s^−2
pascal     Pa     pressure, stress        N/m^2               m^−1·kg·s^−2
joule      J      energy, work, heat      N·m = C·V = W·s     m^2·kg·s^−2
watt       W      power, radiant flux     J/s = V·A           m^2·kg·s^−3
coulomb    C      electric charge         s·A                 s·A
volt       V      voltage                 W/A = J/C           m^2·kg·s^−3·A^−1
farad      F      electric capacitance    C/V                 m^−2·kg^−1·s^4·A^2
ohm        Ω      electric resistance     V/A                 m^2·kg·s^−3·A^−2
siemens    S      electrical conductance  1/Ω                 m^−2·kg^−1·s^3·A^2
weber      Wb     magnetic flux           J/A                 m^2·kg·s^−2·A^−1
tesla      T      magnetic field strength V·s/m^2 = Wb/m^2    kg·s^−2·A^−1
                                           = N/(A·m)
henry      H      inductance              V·s/A = Wb/A        m^2·kg·s^−2·A^−2
celsius    °C     temperature             K − 273.15          K − 273.15
           degC
lumen      lm     luminous flux           lx·m^2              cd·sr
lux        lx     illuminance             lm/m^2              m^−2·cd·sr
becquerel  Bq     radioactivity           1/s                 s^−1
                  (decays per unit time)  
gray       Gy     absorbed dose           J/kg                m^2·s^−2
                  (of ionizing radiation) 
sievert    Sv     equivalent dose         J/kg                m^2·s^−2
                  (of ionizing radiation) 
katal      kat    catalytic activity      mol/s               s^−1·mol
========== ====== ======================= =================== ===================


================== ====== ======================= =================== ===================
Additional Units 
http://en.wikipedia.org/wiki/Non-SI_units_accepted_for_use_with_SI
---------------------------------------------------------------------------------
Name               Symbol Quantity                Expression in terms Expression in terms 
                                          of other units      of SI base units
================== ====== ======================= =================== ===================
minute             min    time                    -                   60·s
hour               h      time                    -                   3600·s
day                d      time                    -                   24*3600·s
litre              l      volume                  -                   10^-3·m^3
tonne              t      weight                  -                   1000·kg
degree arc         °      angle                   -                   (π/180)·rad
minute arc         ′      angle                   (1/60)°             (π/10800)·rad
second arc         ″      angle                   (1/60)              (π/648000)·rad
electronvolt       eV     energy                  -                   1.60217653(14)×10−19·J
atomic mass unit   u      mass                    -                   1.66053886(28)×10−27·kg
astronomical unit  AU     length                  -                   1.49597870691(6)×1011·m
nautical mile      M      length                                      1852·m
knot               kn     speed                   "nautical mile"/h   (1852/3600)·m/s
bar                bar    pressure                                    10^5·Pa
poise              P      dynamic viscosity                           0.1·Pa·s
stokes             St     kinematic viscosity                         10^–4·m^2·s^–1
================== ====== ======================= =================== ===================


======= ====== ========================
SI prefixes 
http://en.wikipedia.org/wiki/SI_prefix
---------------------------------------
Prefix  Symbol 10^n     
======= ====== ========================
yotta   Y      10^24
zetta   Z      10^21
exa     E      10^18
peta    P      10^15
tera    T      10^12
giga    G      10^9
mega    M      10^6
kilo    k      10^3
hecto   h      10^2
deca    da     10^1
deci    d      10^-1
centi   c      10^-2
milli   m      10^-3
micro   μ      10^-6
nano    n      10^-9
pico    p      10^-12
femto   f      10^-15
atto    a      10^-18
zepto   z      10^-21
yocto   y      10^-24
======= ====== ========================


Other Units Packages
--------------------

units
    http://pypi.python.org/pypi/units/
    
quantities
    http://pypi.python.org/pypi/quantities/
    
Unum
    License: LGPL
    http://home.scarlet.be/be052320/Unum.html

PhysicalQuantities
    Can really parse unit prefixes.
    http://dirac.cnrs-orleans.fr/ScientificPython/ScientificPythonManual/Scientific.Physics.PhysicalQuantities-module.html

simtk.physical.Quantity
    https://simtk.org/home/python_units
'''

from __future__ import division
from __future__ import absolute_import          


#Create the lists of SymbolInfo and PrefixInfo objects --------------------
def create_symbol_list(lines_start, lines_stop, lines, out_file):
    '''Create list of calls to SymbolInfo constructor.'''
    out_file.write('    #Generated from lines %s - %s \n' % (lines_start, lines_stop))
    #find the positions of the field boundaries from the "======= ======== ======"
    header_line = lines[lines_start-1]
    sep1 = header_line.find(' ')
    sep2 = header_line.find(' ', sep1+1)
    sep3 = header_line.find(' ', sep2+1)
    sep4 = header_line.find(' ', sep3+1)
    print header_line
    print 'sep1: ', sep1, 'sep2: ', sep2, 'sep3: ', sep3, 'sep4: ', sep4
    #parse content
    content_lines = lines[lines_start:lines_stop]
    for line in content_lines:
        #print line
        name       = line[:sep1]      .strip()
        symbol     = line[sep1+1:sep2].strip()
        comment    = line[sep2+1:sep3].strip()
        _expr1     = line[sep3+1:sep4].strip()
        expression = line[sep4+1:]    .strip()
        #print name, symbol, comment, expression
        out_file.write("    SymbolInfo('%s', '%s', '%s', '%s'), \n" % 
                       (name, symbol, comment, expression))
    
def create_prefix_list(lines_start, lines_stop, lines, out_file):
    '''Create list of calls to PrefixInfo constructor.'''
    out_file.write('    #Generated from lines %s - %s \n' % (lines_start, lines_stop))
    #find the positions of the field boundaries from the "======= ======== ======"
    header_line = lines[lines_start-1]
    sep1 = header_line.find(' ')
    sep2 = header_line.find(' ', sep1+1)
    print header_line
    print 'sep1: ', sep1, 'sep2: ', sep2
    #parse content
    content_lines = lines[lines_start:lines_stop]
    for line in content_lines:
        #print line
        name       = line[:sep1]      .strip()
        symbol     = line[sep1+1:sep2].strip()
        factor    = line[sep2+1:].strip()
        factor = factor.replace('^', '**')
        factor = factor.encode('ascii', 'replace')
        #print name, symbol, factor
        out_file.write("    PrefixInfo('%s', '%s', %s), \n" % 
                       (name, symbol, factor))
        
def create_symbol_prefix_list_from_doc():
    in_file = open('units_doc.py', 'r')
    out_file = open('units_genfile.py', 'w')
    lines = in_file.readlines()
    
    out_file.write('''# -*- coding: utf-8 -*-
    
class SymbolInfo:
    pass
class PrefixInfo:
    pass
    
''')
    out_file.write('symbol_infos = [ \n')
    out_file.write('    #SI Base Units \n')
    create_symbol_list(69, 77, lines, out_file)
    out_file.write('    #SI Derived Units \n')
    create_symbol_list(87, 114, lines, out_file)
    out_file.write('    #Additional Units  \n')
    create_symbol_list(124, 141, lines, out_file)
    out_file.write('                                      ] \n')
    
    
    out_file.write('\n#SI Prefixes  \n')
    out_file.write('prefix_infos = [ \n')
    create_prefix_list(150, 170, lines, out_file)
    out_file.write('                                      ] \n')
    
    in_file.close()
    out_file.close()
    
create_symbol_prefix_list_from_doc()
    
