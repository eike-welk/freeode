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


class PyGenException(Exception):
    '''Exception thrown by the pytrhon code generator classes'''
    def __init__(self, *params):
        Exception.__init__(self, *params)
        
        
class ProcessGenerator(object):
    '''create python class that simulates a process'''
    
    def __init__(self):
        super(ProcessGenerator, self).__init__()
        
        self.iltProcess = NodeClassDef('dummy')
        '''The input: an IL-tree of the process. It has no external dependencies.'''
        self.outPy = ''
        '''The process in the python programming language.'''
        self.processPyName = ''
        '''Python name of the process'''
        self.parameters = {}
        '''The parameters: dict: {('a','b'):NodeAttrDef]'''
        self.algebraicVariables = {}
        '''The algebraic variables: dict: {('a','b'):NodeAttrDef]'''
        self.stateVariables = {}
        '''The state variables: dict: {('a','b'):NodeAttrDef]'''
        #self.pyNames = {}
        
        
    def findAttributes(self):
        '''
        Loop over the attribute definitions and classify the attributes into 
        parameters, slgebraic varianles, state variables.
        Results:
        self.parameters, self.algebraicVariables, self.stateVariables 
        '''
        for attrDef in self.iltProcess:
            if not isinstance(attrDef, NodeAttrDef):
                continue
            if attrDef.role == 'par':
                self.parameters[attrDef.attrName] = attrDef
            elif attrDef.role == 'var' and not attrDef.isStateVariable:
                self.algebraicVariables[attrDef.attrName] = attrDef
            elif attrDef.role == 'var' and attrDef.isStateVariable:
                self.stateVariables[attrDef.attrName] = attrDef
            else:
                raise PyGenException('Unknown attribute definition:\n'+ str(attrDef))
 
            
    def createAttrPyNames(self):
        '''
        Create python names for all attributes
        The python names are stored in the data attribute:
        self.targetName of NodeAttrDef and NodeAttrAccess
        '''
        paramPrefix = 'self.p'
        varPrefix = 'v'
        pyNames = {} #mapping between attribute name and python name: {('a','b'):'v_a_b'}
        
        #loop over all attribute definitions and create an unique python name 
        #for each attribute
        for attrDef in self.iltProcess:
            if not isinstance(attrDef, NodeAttrDef):
                continue
            #create underline separated name string
            pyName1 = ''
            for namePart in attrDef.attrName:
                pyName1 += '_' + namePart
            #prepend variables and parameters with differnt additional strings
            if attrDef.attrName in self.parameters:
                pyName1 = paramPrefix + pyName1
            else:
                pyName1 = varPrefix + pyName1
            #see if python name is unique; append number to make it unique
            num, numStr = 0, ''
            while pyName1 + numStr in pyNames:
                num += 1
                numStr = str(num)
            pyName1 = pyName1 + numStr
            #store python name 
            pyNames[attrDef.attrName] = pyName1
            
        #loop over all attribute definitions and attribute accesses 
        #and put python name there
        for node in self.iltProcess.iterDepthFirst():
            if   isinstance(node, NodeAttrDef):
                node.targetName = pyNames[node.attrName]
            elif isinstance(node, NodeAttrAccess):
                node.targetName = pyNames[node.attrName]
            
            
    def writeClassDefStart(self):
        '''Write first few lines of class definition.'''
        self.outPy += 'class %s(SimulatorBase): \n' % self.processPyName
        self.outPy += '    \'\'\' \n'
        self.outPy += '    Object to simulate process %s \n' % self.iltProcess.className
        self.outPy += '    Definition in file: \'%s\' line: %s \n' % ('???', '???')
        self.outPy += '    \'\'\' \n'
        self.outPy += '    \n'

        
    def write__init__func(self):
        '''Generate the __init__ function.'''
        ind8 = ' '*8
        self.outPy += '    def __init__(self): \n'
        self.outPy += '        super(%s, self).__init__() \n' % self.processPyName
        
        self.outPy += ind8 + '#create all parameters with value 0 \n'
        line1 = ind8
        for paramDef in self.parameters.values():
            line1 += '%s = 0; ' % paramDef.targetName
            if len(line1) > 75:
                self.outPy += line1 + '\n'
                line1 = ind8
        self.outPy += line1 + '\n'
        
        
    def createProcess(self, iltProcess):
        '''
        Take part of ILT tree that defines one procedure and ouput definition 
        of python class as string
        '''
        self.__init__()
        self.iltProcess = iltProcess.copy()
        
        #collect information about the process
        self.processPyName = self.iltProcess.className
        self.findAttributes()    
        self.createAttrPyNames()
        
        self.writeClassDefStart()
        self.write__init__func()
        
        print self.iltProcess
        return self.outPy
        
        
        
class ProgramGenerator(object):
    '''Create a program from an ILT-tree'''
    
    def __init__(self):
        super(ProgramGenerator,self).__init__(self)
    
    def createProgram(self, astRoot):
        '''Take an ILT and retun a python program as a string'''
        program = ''
        
        program += 'from scipy import * \n'
        program += 'from simulatorbase import SimulatorBase \n'
        program += '\n'
        
        procGen = ProcessGenerator()
        for procedure in astRoot:
            if not isinstance(procedure, NodeClassDef):
                continue
            #create procedure
            program += procGen.createProcess(procedure)
            
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
    
    pyFile = open('/home/eike/codedir/freeode/trunk/freeode_py/test.py','w')
    pyFile.write(progStr)
    pyFile.close()
    
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
