#!/usr/bin/env python
############################################################################
#    Copyright (C) 2006 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
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
import pygenerator
import simlparser


#import pdb
import simlparser
import pygenerator

#------------ testProg1 -----------------------
testProg1 = (
'''
model Test
    var V; var h;
    par A_bott; par A_o; par mu;
    par q; par g;
    
    block run
        h := V/A_bott;
        $V := q - mu*A_o*sqrt(2*g*h);
    end
    
    block init
        V := 0;
        A_bott := 1; 
        A_o := 0.02; mu := 0.55;
        q := 0.05;
    end
end

process RunTest
    sub test as Test;
    
    block run
        run test;
    end
    block init
        init test;
    end
end
''' )

#-------- the code -----------------------------------------------------
parser = simlparser.ParseStage()
astGen = simlparser.ASTGenerator()
iltGen = simlparser.ILTGenerator()
progGen = pygenerator.ProgramGenerator()

pres = parser.parseProgram(testProg1)
#print 'parse result:'
#print pres

astTree = astGen.createSyntaxTree(pres)
#print 'AST tree:'
#print astTree

iltTree = iltGen.createIntermediateTree(astTree)
print 'ILT tree:'
print iltTree

progGen.createProgram(iltTree)
progStr = progGen.buffer()
#print 'python program:'
#print progStr

pyFile = open('/home/eike/codedir/freeode/trunk/freeode_py/test.py','w')
pyFile.write(progStr)
pyFile.close()

from test import RunTest
sim = RunTest()
sim.simulateDynamic()
#sim.graph('test.V')

a=1
