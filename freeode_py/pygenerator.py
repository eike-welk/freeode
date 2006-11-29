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

from ast import *


class ProcedureGenerator(object):
    '''create python class that simulates a process'''
    
    def __init__(self):
        super(ProcedureGenerator, self).__init__()
        
    def createProcedure(self, iltProcedure):
        '''
        Take part of ILT tree that defines one procedure and ouput definition 
        of python class as string
        '''
        return 'test\n'
        
        
        
class ProgramGenerator(object):
    '''Create a program from an ILT-tree'''
    
    def __init__(self):
        super(ProgramGenerator,self).__init__(self)
    
    def createProgram(self, astRoot):
        '''Take an ILT and retun a python program as a string'''
        program = ''
        procGen = ProcedureGenerator()
        
        for procedure in astRoot:
            if not isinstance(procedure, NodeClassDef):
                continue
            #create procedure
            program += procGen.createProcedure(procedure)
            
        return program
    
    
    

if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #TODO: add doctest tests. 
    
    
    from simlparser import ParseStage, ASTGenerator, ILTGenerator
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
        A_bott := 1; A_o := 0.02; mu := 0.55;
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

#------------ testProg2 -----------------------
    testProg2 = (
'''
model Test
    var a;

    block run
        $a := 0.5;
    end
    block init
        a := 1;
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

    parser = ParseStage()
    astGen = ASTGenerator()
    iltGen = ILTGenerator()
    progGen = ProgramGenerator()
    
    pres = parser.parseProgram(testProg1)
    print 'parse result:'
    #print pres
    astTree = astGen.createSyntaxTree(pres)
    #print 'AST tree:'
    print astTree
 
    iltTree = iltGen.createIntermediateTree(astTree)
    print 'ILT tree:'
    print iltTree

    progStr = progGen.createProgram(iltTree)
    print 'python program:'
    print progStr
    
    
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
