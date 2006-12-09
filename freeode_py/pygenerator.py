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


__doc__ = \
'''
Generator for python code.

The highlevel wrapper class is Program generator.
It consumes a modified AST, the intermediate language tree (ILT) and 
generates some python classes that perform the simulations.
'''


from ast import *


class PyGenException(Exception):
    '''Exception thrown by the pytrhon code generator classes'''
    def __init__(self, *params):
        Exception.__init__(self, *params)
        

class LongLineWriter(object):
    '''
    Automate writing lines with a maximum length.
    
    This class is usefull for writing lines with multiple statements.
    '''
    
    def __init__(self, file=None, maxLen=80, startStr='', endStr='\\'):
        '''
        Parameters:
            file     : Object with write(string) method where the 
                       completed lines are put (most possibly a file). 
                       If file=None a buffer string is used instead, that
                       can be retrieved with the buffer() method
            maxLen   : Maximum lenght of a line.
            startStr : Lines start with this string (usually the indent)
                       unless startLine(...) 
            endStr   : Lines end with this string unless endLine(...) is called.
        '''
        self.file = file
        self.multiLineBuf = ''
        self.lineBuf = startStr
        self.maxLen = maxLen
        self.startStr = startStr
        self.endStr = endStr
    
    def _putLine(self, lineStr):
        '''Put the finished line into the file or into the buffer'''
        if not self.file:
            self.multiLineBuf += lineStr
        else:
            self.file.write(lineStr)
    
    def write(self, inStr):
        '''
        Put this string at he end of the current line. 
        If the line is too long statrt a new line.
        '''
        if len(self.lineBuf) + len(inStr) + len(self.endStr) > self.maxLen:
            self._putLine(self.lineBuf + self.endStr + '\n')
            self.lineBuf = self.startStr + inStr
        else:
            self.lineBuf += inStr
        #return self
        
    def endLine(self, finalStr):
        '''Put inStr unconditionally at the line's end and start a new line.'''
        self._putLine(self.lineBuf + finalStr + '\n')
        self.lineBuf = self.startStr
        #return self
        
    def startLine(self, beginStr):
        '''
        Begin a new line with beginStr. 
        The normal start string (self.startStr) is omitted.
        If the current line is not empty it is ended with self.endLine('').
        '''
        if self.lineBuf != self.startStr:
            self.endLine('')
        else:
            self.lineBuf = beginStr
        #return self
        
    def buffer(self):
        '''
        Return the buffer where the completed lines are.
        Only usefull when no file object is used.
        '''
        return self.multiLineBuf
    

def makeDotName(inTuple):
    '''
    Create a dotted name from a tuple of strings.
    The dotted names are parsed into (and stored as) tuples of strings.
    '''
    dotName = ''
    for namePart in inTuple:
        if dotName == '':
            dotName = namePart
        else:
            dotName += '.'+namePart
    return dotName


class StatementGenerator(object):
    '''
    Generate a statement in Python from an AST or ILT syntax tree.
    '''
    
    def __init__(self):
        super(StatementGenerator, self).__init__()
        self.outPy = ''
        '''The statement in the python programming language.'''
    
    
    def createFormula(self, iltFormula):
        '''
        Take ILT sub-tree that describes a formula and 
        convert it into a formula in the Python programming language.
        (recursive)
        
        arguments:
            iltFormula : tree of Node objects
        returns:
            string, formula in Python language
        '''
        self.outPy = ''
        #Built in value: pi, time
        if isinstance(iltFormula, NodeBuiltInVal):
            nameDict = {'pi':'pi', 'time':'time'}
            return nameDict[iltFormula.dat]
        #Built in function: sin(...) 
        elif isinstance(iltFormula, NodeBuiltInFuncCall):
            nameDict = {'sin':'sin', 'cos':'cos', 'tan':'tan', 'sqrt':'sqrt', 
                        'exp':'exp', 'ln':'ln' }
            funcName = nameDict[iltFormula.dat]
            return funcName + '(' + self.createFormula(iltFormula[0]) + ')'
        #Number: 123.5
        elif isinstance(iltFormula, NodeNum):
            return str(float(iltFormula.dat))
        #pair of prentheses: ( ... )
        elif isinstance(iltFormula, NodeParentheses):
            return '(' + self.createFormula(iltFormula[0]) + ')'
        #Infix operator: + - * / ^ and or
        elif isinstance(iltFormula, NodeOpInfix2):
            opDict = {'+':' + ', '-':' - ', '*':'*', '/':'/', '**':'**', 
                      'and':' and ', 'or':' or '}
            opStr = opDict[iltFormula.dat]
            return (self.createFormula(iltFormula[0]) + opStr + 
                    self.createFormula(iltFormula[1]))
        #Prefix operator: - not
        elif isinstance(iltFormula, NodeOpPrefix1):
            opDict = {'-':' -', 'not':' not '}
            opStr = opDict[iltFormula.dat]
            return opStr + self.createFormula(iltFormula[0])
        #variable or parameter
        elif isinstance(iltFormula, NodeAttrAccess):
            return iltFormula.targetName
        #unknown node
        else:
            raise PyGenException('Unknown node in FormulaGenerator:\n' + str(iltFormula))


    def createStatement(self, iltStmt, indent):
        '''
        Take ILT sub-tree and convert it into Python statement.
        
        arguments:
            iltStmt : tree of Node objects
            indent  : string of whitespace, put in front of each line
        returns:
            string, statement in Python language
        '''
        self.outPy = ''
        
        if isinstance(iltStmt, NodeAssignment):
            self.outPy += indent + (iltStmt.lhs().targetName + ' = ' + 
                                    self.createFormula(iltStmt.rhs()) + '\n')
        else:
            raise PyGenException('Unknown node in StatementGenerator:\n' + str(iltStmt))
         
        return self.outPy


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
        
        
    def findAttributes(self):
        '''
        Loop over the attribute definitions and classify the attributes into 
        parameters, slgebraic varianles, state variables.
        Results:
        self.parameters, self.algebraicVariables, self.stateVariables 
        '''
        #create dicts to find and classify attributes fast
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
        timeDerivSuffix = '_dt'
        for node in self.iltProcess.iterDepthFirst():
            if isinstance(node, NodeAttrDef):
                namePy = pyNames[node.attrName]
                node.targetName = {tuple():namePy}
                #variables with derivatives have multiple target names
                if node.attrName in self.stateVariables:
                    node.targetName[('time',)] = namePy + timeDerivSuffix
            elif isinstance(node, NodeAttrAccess):
                #derivatives get an additional ending
                if node.deriv == ('time',): 
                    node.targetName = pyNames[node.attrName] + timeDerivSuffix
                else:
                    node.targetName = pyNames[node.attrName]
            
            
    def writeClassDefStart(self):
        '''Write first few lines of class definition.'''
        self.outPy += 'class %s(SimulatorBase): \n' % self.processPyName
        self.outPy += '    \'\'\' \n'
        self.outPy += '    Object to simulate process %s \n' % self.iltProcess.className
        self.outPy += '    Definition in file: \'%s\' line: %s \n' % ('???', '???')
        self.outPy += '    \'\'\' \n'
        self.outPy += '    \n'

        
    def writeConstructor(self):
        '''Generate the __init__ function.'''
        ind8 = ' '*8
        self.outPy += '    def __init__(self): \n'
        self.outPy += '        super(%s, self).__init__() \n' % self.processPyName
        self.outPy += ind8 + 'self.variableNameMap = {} \n'
        #create the parameters
        self.outPy += (ind8 + '#create all parameters with value 0; ' + 
                       'to prevent runtime errors.\n')
        longW = LongLineWriter(startStr=ind8, endStr='')
        for paramDef in self.parameters.values():
            longW.write('%s = 0.0; ' % paramDef.targetName[tuple()])
        longW.endLine('')
        self.outPy += longW.buffer()
        self.outPy += '\n\n'
        
        
    def writeInitMethod(self):
        '''Generate method that initializes variables and parameters'''
        #search the process' init method 
        for initMethod in self.iltProcess:
            if isinstance(initMethod, NodeBlockDef) and \
               initMethod.name == 'init':
                break
        #write method definition
        ind8 = ' '*8
        self.outPy += '    def initialize(self): \n'
        self.outPy += ind8 + '\'\'\' \n'
        self.outPy += ind8 + 'Compute parameter values and \n'
        self.outPy += ind8 + 'compute initial values of state variables \n'
        self.outPy += ind8 + '\'\'\' \n'
        #create all variables
        self.outPy += (ind8 + '#create all variables with value 0; ' + 
                       'to prevent runtime errors.\n')      
        #create long lines with 'var_name = 0; ...'
        line1 = ind8
        for varDef in (self.algebraicVariables.values() + 
                       self.stateVariables.values()):
            line1 += '%s = 0.0; ' % varDef.targetName[tuple()]
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind8
        self.outPy += line1 + '\n'
        #print the method's statements
        self.outPy += ind8 + '#do computations \n'
        stmtGen = StatementGenerator()
        for statement in initMethod:
            self.outPy += stmtGen.createStatement(statement, ind8)
        #put initial values into array and store them
        #sequence of variables in the array is determined by self.stateVariables
        self.outPy += ind8 + '#assemble initial values to array and store them \n'
        #create long lines with 'var_ame11, var_name12, var_name13, ...'
        line1 = ind8 + 'self.initialValues = array(['
        for varDef in self.stateVariables.values():
            line1 += '%s, ' % varDef.targetName[tuple()]
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind8 + ' '*28 #indent of rectangular bracket
        self.outPy += line1 + '], \'float64\') \n'        
        self.outPy += ind8 + 'self.stateVectorLen = len(self.initialValues) \n'
        #assemble vector with algebraic variables to compute their total size
        self.outPy += ind8 + '#put algebraic variables into array, only to compute its size \n'
        algVarNames = self.algebraicVariables.values()
        line1 = ind8 + 'algVars = array(['
        for varDef, nState in zip(algVarNames, range(len(algVarNames))):
            line1 += '%s, ' % varDef.targetName[tuple()]
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind8 + ' '*18 #indent of rectangular bracket
        self.outPy += line1 + '], \'float64\') \n'
        self.outPy += ind8 + 'self.algVectorLen = len(algVars) \n'
        #TODO: compute self.variableNameMap from the actual sizes of the variables
        self.outPy += ind8 + '#TODO: compute self.variableNameMap from the actual sizes of the variables \n'
        #Create maping between variable names and array indices
        longW = LongLineWriter(startStr=' '*16)
        longW.startLine(ind8 + 'self.variableNameMap = {')
        for i, varName in zip(range(len(self.stateVariables) + 
                                    len(self.algebraicVariables)),
                              self.stateVariables.keys() + 
                              self.algebraicVariables.keys()):
            longW.write('\'%s\':%d, ' % (makeDotName(varName), i))
        longW.endLine('}')
        self.outPy += longW.buffer()
        self.outPy += '\n\n'
    
    
    def writeDynamicMethod(self):
        '''Generate the method that contains the differential equations'''
        #search the process' dynamic method 
        for dynMethod in self.iltProcess:
            if isinstance(dynMethod, NodeBlockDef) and \
               dynMethod.name == 'run':
                break
        #write method definition
        ind8 = ' '*8
        self.outPy += '    def dynamic(self, time, state): \n'
        self.outPy += ind8 + '\'\'\' \n'
        self.outPy += ind8 + 'Compute time derivative of state variables. \n'
        self.outPy += ind8 + 'This function will be called by the solver repeatedly. \n'
        self.outPy += ind8 + '\'\'\' \n'
        #take the state variables out of the state vector
        #sequence of variables in the array is determined by self.stateVariables
        self.outPy += ind8 + '#take the state variables out of the state vector \n'
        #create long lines with 'var_ame1 = state[1]; var_name2 = state[2]; ...'
        line1 = ind8
        stateVarNames = self.stateVariables.values()
        for varDef, nState in zip(stateVarNames, range(len(stateVarNames))):
            line1 += '%s = state[%d]; ' % (varDef.targetName[tuple()], nState)
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind8 
        self.outPy += line1 + '\n'       
        self.outPy += ind8 + '#TODO: Create all algebraic variables? \n' 
        #print the method's statements
        self.outPy += ind8 + '#do computations \n'
        stmtGen = StatementGenerator()
        for statement in dynMethod:
            self.outPy += stmtGen.createStatement(statement, ind8)
        #assemble the time derivatives into the return vector
        self.outPy += ind8 + '#assemble the time derivatives into the return vector \n'
        line1 = ind8 + 'stateDt = array(['
        for varDef, nState in zip(stateVarNames, range(len(stateVarNames))):
            line1 += '%s, ' % varDef.targetName[('time',)]
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind8 + ' '*18 #indent of rectangular bracket
        self.outPy += line1 + '], \'float64\') \n'
        self.outPy += ind8 + 'return stateDt \n'
        #TODO: investigate method to also return the algebraic variables
        self.outPy += '\n\n'
    
    
    def writeOutputEquations(self):
        '''Generate method that computes the algebraic variables for a second time.'''
        #search the process' dynamic method 
        for dynMethod in self.iltProcess:
            if isinstance(dynMethod, NodeBlockDef) and \
               dynMethod.name == 'run':
                break
        #write method definition
        ind8 = ' '*8
        ind12 = ' '*12
        self.outPy += '    def outputEquations(self, simResult): \n'
        self.outPy += ind8 + '\'\'\' \n'
        self.outPy += ind8 + 'Compute algebraic variables for a second time. \n'
        self.outPy += ind8 + 'This is necessary because there is (currently) way to pass \n'
        self.outPy += ind8 + 'the algebraic variables out of the integration process. \n'
        self.outPy += ind8 + '\'\'\' \n'
        
        self.outPy += ind8 + 'for state in simResult: \n'

        #take the state variables out of the state vector
        #sequence of variables in the array is determined by self.stateVariables
        self.outPy += ind12 + '#take the state variables out of the state vector \n'
        #create long lines with 'var_ame1 = state[1]; var_name2 = state[2]; ...'
        line1 = ind12
        stateVarNames = self.stateVariables.values()
        for varDef, nState in zip(stateVarNames, range(len(stateVarNames))):
            line1 += '%s = state[%d]; ' % (varDef.targetName[tuple()], nState)
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind12 
        self.outPy += line1 + '\n'        
        self.outPy += ind12 + '#TODO: Create all algebraic variables? \n' 
        self.outPy += ind12 + '#TODO: Only compute algebraic variables?? \n' 
        #print the statements that compute algebraic variables
        self.outPy += ind12 + '#do computations \n'
        stmtGen = StatementGenerator()
        for statement in dynMethod:
            self.outPy += stmtGen.createStatement(statement, ind12)
        #assemble the algebraic variables into an array
        self.outPy += ind12 + '#assemble the algebraic variables into an array \n'
        algVarNames = self.algebraicVariables.values()
        line1 = ind12 + 'algVars = array(['
        for varDef, nState in zip(algVarNames, range(len(algVarNames))):
            line1 += '%s, ' % varDef.targetName[tuple()]
            if len(line1) > 75: #if line long enough: begin new line
                self.outPy += line1 + '\n'
                line1 = ind12 + ' '*18 #indent of rectangular bracket
        self.outPy += line1 + '], \'float64\') \n'
        self.outPy += ind12 + '#TODO: Store the algebraic variables. \n'

        self.outPy += '\n\n'



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
        
        print self.iltProcess
        
        self.writeClassDefStart()
        self.writeConstructor()
        self.writeInitMethod()
        self.writeDynamicMethod()
        self.writeOutputEquations()
                
        return self.outPy
        
        
        
class ProgramGenerator(object):
    '''Create a program from an ILT-tree'''
    
    def __init__(self):
        super(ProgramGenerator,self).__init__(self)
        self.outPy = ''
    
    
    def writeProgramStart(self):
        '''
        Write first few lines of the program. 
        Method looks really ugly because of raw string usage.
        '''
        self.outPy += \
'''
#------------------------------------------------------------------------------#
#                            Warning: Do not edit!                             #
#                                                                              #
# This file is generated, it will be overwritten every time the source file(s) #
# is/are changed.                                                              #
# Write a main routine in an other file. Use import or execfile to load        #
# the objects defined in this file into the Python interpreter.                #
#------------------------------------------------------------------------------#
'''
        import datetime
        dt = datetime.datetime.today()
        date = dt.date().isoformat()
        time = dt.time().strftime('%H:%M:%S')
        
        self.outPy += '# Generated by Siml version %s on %s %s. \n' % ('0.3.0', date, time)
        self.outPy += '# Source file(s): %s' % '???'
        self.outPy += \
'''
#------------------------------------------------------------------------------#


from numpy import *
#from scipy import *
from simulatorbase import SimulatorBase


'''
        return
    
    
    def createProgram(self, astRoot):
        '''Take an ILT and retun a python program as a string'''
        self.__init__()
        
        self.writeProgramStart()
                
        procGen = ProcessGenerator()
        for procedure in astRoot:
            if not isinstance(procedure, NodeClassDef):
                continue
            #create procedure
            self.outPy += procGen.createProcess(procedure)
            
        return self.outPy
    
    
    

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
