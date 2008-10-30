# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2008 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
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
#                                                                          #
#                                                                          #
#    This Python module is the code generator of a compiler. The           #
#    generated computer program shall be licensed under any license that   #
#    the user of the compiler whishes. Even though the generated program   #
#    is assembled from pieces of software of contained in this file.       #
############################################################################

'''
Generator for python code.

The highlevel wrapper class is Program generator.
It consumes a modified AST, the intermediate language tree (ILT), and
generates some python classes that perform the simulations.
'''

from __future__ import division

import cStringIO
from freeode.ast import *
#import freeode.interpreter as interpreter
from  freeode.interpreter import *


__version__ = "$Revision: $"


class PyGenException(Exception):
    '''Exception thrown by the python code generator classes'''
    def __init__(self, *params):
        Exception.__init__(self, *params)



class FormulaGenerator(Visitor):
    '''
    Take ILT sub-tree that describes a formula and
    convert it into a formula in the Python programming language.
    
    USAGE:
        Call the method
            createFormula(iltFormula)
        with an ILT tree as an argument. The method will convert it into
        a Python string, which it returns.
    '''
    
    def __init__(self):
        Visitor.__init__(self)
        
    def createFormula(self, iltFormula):
        '''
        Take ILT sub-tree that describes a formula and
        convert it into a formula in the Python programming language.
        (recursive)

        Arguments:
            iltFormula : tree of Node objects
        Returns:
            string, formula in Python language
        '''
        return self.dispatch(iltFormula)
    
#    @Visitor.when_type(NodeBuiltInVal, 1)
#    def _createBuiltInVal(self, iltFormula):
#        #Built in value: pi, time
#        nameDict = {'pi':'pi', 'time':'time'}
#        return nameDict[iltFormula.dat]
        
#    @Visitor.when_type(NodeBuiltInFuncCall, 1)
#    def _createBuiltInFuncCall(self, iltFormula):
#        #Built in function: sin(...)
#        nameDict = {'sin':'sin', 'cos':'cos', 'tan':'tan', 'sqrt':'sqrt',
#                    'exp':'exp', 'log':'log', 'min':'min' , 'max':'max',
#                    'overrideParam':'self._overrideParam' }
#        #get name of the corresponding Python function
#        funcName = nameDict[iltFormula.dat] 
#        #produce output
#        retStr = funcName + '('
#        for funcArgument in iltFormula:
#            retStr += self.dispatch(funcArgument) + ','
#        retStr += ')'
#        return retStr
        
    @Visitor.when_type(InstFloat, 1)
    def _createNum(self, variable):
        #Number: 123.5 or variable with type float
        if variable.role is RoleConstant:
            return str(float(variable.value))
        else:
            return variable.target_name
        
    @Visitor.when_type(InstString, 1)
    def _createString(self, variable):
        #String: 'hello world' or variable with type str
        if variable.role is RoleConstant:
            return '\'' + variable.value + '\''
        else:
            return variable.target_name
        
    @Visitor.when_type(NodeParentheses, 1)
    def _createParentheses(self, iltFormula):
        #pair of prentheses: ( ... )
        return '(' + self.dispatch(iltFormula.arguments[0]) + ')'
        
    @Visitor.when_type(NodeOpInfix2, 1)
    def _createOpInfix2(self, iltFormula):
    #Infix operator: + - * / ^ and or
        opDict = {'+':' + ', '-':' - ', '*':'*', '/':'/', '**':'**',
                  '<':' < ', '>':' > ', '<=':' <= ', '>=':' >= ',
                  '==':' == ', '!=':' != ',
                  'and':' and ', 'or':' or '}
        opStr = opDict[iltFormula.operator]
        return (self.dispatch(iltFormula.arguments[0]) + opStr +
                self.dispatch(iltFormula.arguments[1]))
        
    @Visitor.when_type(NodeOpPrefix1, 1)
    def _createOpPrefix1(self, iltFormula):
        #Prefix operator: - not
        opDict = {'-':' -', 'not':' not '}
        opStr = opDict[iltFormula.operator]
        return opStr + self.dispatch(iltFormula.arguments[0])
        
    @Visitor.when_type(NodeAttrAccess, 1)
    def _createAttrAccess(self, iltFormula):
        #variable or parameter
        return iltFormula.targetName
        
    @Visitor.default
    def _ErrorUnknownNode(self, iltFormula):
        #Internal error: unknown node
        raise PyGenException('Unknown node in FormulaGenerator:\n' 
                             + str(iltFormula))



class StatementGenerator(Visitor):
    '''
    Generate statements in Python from an AST or ILT syntax tree.
    
    self.createStatements(stmtList, indent) can take the entire body
    of a function and convert it to Python statements.
    '''

    def __init__(self, outPyFile):
        '''
        ARGUMENT:
            outPyFile : File like object where the Python program 
                        will be stored.
        '''
        super(StatementGenerator, self).__init__()
        #File like object, where the Python program will be stored.
        self.out_py = outPyFile
        #Object that creates a formula from an AST sub-tree
        self.genFormula = FormulaGenerator()


#    def createStatement(self, iltStmt, indent):
#        '''
#        Take ILT sub-tree and convert it into one
#        or several Python statements.
#        This is the dispatcher function for the statements.
#
#        ARGUMENT:
#            iltStmt : tree of Node objects
#            indent  : string of whitespace, put in front of each line
#        RETURN:
#            None
#        OUTPUT:
#            self.out_py - text is written to object
#        '''
#        self.dispatch(iltStmt, indent)
        
        
    def create_statements(self, stmt_list, indent):
        '''
        Take list of statement nodes. Convert it into one or several 
        Python statements.
        
        Main loop of statement generator

        ARGUMENT:
        stmt_list: list(Node())
            The statements
        indent: str() 
            String of whitespace characters, put in front of each line
        RETURN:
            None
        OUTPUT:
            self.out_py - text is written to object
        '''
        for node in stmt_list:
            self.dispatch(node, indent)


    def createFormula(self, iltFormula):
        '''
        Take ILT sub-tree that describes a formula (expression) and
        convert it into a formula in the Python programming language.
        (recursive)

        ARGUMENT:
            iltFormula : tree of Node objects
        RETURN:
            string, formula in Python language
        '''
        return self.genFormula.createFormula(iltFormula)


    @Visitor.when_type(NodeAssignment, 1)
    def _createAssignment(self, iltStmt, indent):
        #Assignment  ---------------------------------------------------------
        outPy = self.out_py
        outPy.write(indent + iltStmt.target.target_name + ' = ' +
                    self.createFormula(iltStmt.expression) + '\n')
    
        
    @Visitor.when_type(NodeIfStmt, 1)
    def _createIfStmt(self, iltStmt, indent):
        #if statement --------------------------------------------------------
        outPy = self.out_py
        ind4 = ' '*4
        outPy.write(indent + 'if '
                           + self.createFormula(iltStmt.condition)
                           + ':\n')
        self.dispatch(iltStmt.ifTruePart, indent + ind4)
        #Only create else clause if necessary
        if len(iltStmt.elsePart) > 0:
            outPy.write(indent + 'else: \n')
            self.dispatch(iltStmt.elsePart, indent + ind4)


    @Visitor.when_type(NodePrintStmt, 1)
    def _createPrintStmt(self, iltStmt, indent):
        #print statement -----------------------------------------------------
        outPy = self.out_py
        line = indent + 'print '
        for expr in iltStmt:
            line += self.createFormula(expr) + ', '
        #take awway last comma if newline is wanted
        if iltStmt.newline:
            line = line[:-2]
        outPy.write(line + '\n')


#    @Visitor.when_type(NodeStoreStmt, 1)
#    def _createStoreStmt(self, iltStmt, indent):
#        #save statement -----------------------------------------------------
#        #One optional argument:
#        #    -the file name: string
#        #generated code is a function call:
#        #    self.save('file_name')
#        outPy = self.out_py
#        if len(iltStmt) > 1:               #Number of arguments: 0,1
#            raise UserException('The save statement can have 1 or no arguments.',
#                                iltStmt.loc)
#        outPy.write(indent + 'self.save(') #write start of statement
#        for expr in iltStmt:               #iterate over arguments (max 1)
#            #child is a string
#            if isinstance(expr, NodeString):
#                filename = self.createFormula(expr)   #write filename
#                outPy.write(filename)
#            #anything else is illegal
#            else:
#                raise UserException('Argument of save statement must be a file name.',
#                                    iltStmt.loc)
#        outPy.write(') \n')                #write end of statement
#
#
#    @Visitor.when_type(NodeGraphStmt, 1)
#    def _createGraphStmt(self, iltStmt, indent):
#        #graph statement -----------------------------------------------------
#        #Any number of arguments. Legal types are:
#        #    -Variable for inclusion in graph: attribute access
#        #    -Graph title: string
#        #generated code is a function call:
#        #    self.graph(['t.V', 't.h', 't.qOut0', 't.qOut1', ], 'graph title')
#        outPy = self.out_py
#        graphTitle = ''
#        outPy.write(indent + 'self.graph([') #write start of statement
#        for expr in iltStmt:                 #iterate over arguments
#            #Argument is variable name
#            if   isinstance(expr, NodeAttrAccess):
#                outPy.write("'%s', " % str(expr.attrName)) #write variable name
#            #Argument is graph title
#            elif isinstance(expr, NodeString):
#                graphTitle = expr.dat        #store graph title
#            #anything else is illegal
#            else:
#                raise UserException('Illegal argument in graph statement.',
#                                    iltStmt.loc)
#        outPy.write('], ')                   #end list of var names
#        #A graph title was found
#        if graphTitle:
#            outPy.write("'%s'" % graphTitle) #write write grapt title as 2nd argument
#        outPy.write(') \n')                  #write end of statement


#    @Visitor.when_type(NodeStmtList, 1)
#    def _createStatementList(self, node, indent):
#        '''
#        Take NodeStmtList and convert
#        into multiple Python statements.
#
#        arguments:
#            node : Node object that contains statements as children
#            indent   : string of whitespace, put in front of each line
#        output:
#            self.out_py - text is written to object
#        '''
#        if len(node.statements) == 0:
#            self.out_py.write(indent + 'pass \n')
#            return
#        self.create_statements(node.statements, indent)
            
            
    @Visitor.default
    def _ErrorUnknownNode(self, iltStmt, indent):
        #Internal error: unknown statement -----------------------------------
        raise PyGenException('Unknown node in StatementGenerator:\n'
                             + str(iltStmt))



class ProcessGenerator(object):
    '''create python class that simulates a process'''

    def __init__(self, buffer):
        '''
        Arguments:
            buffer : File where the Python program will be stored.
        '''
        super(ProcessGenerator, self).__init__()
        #The input: an IL-tree of the process. It has no external dependencies.
        self.ilt_process = CompiledClass()
        #File where the Python program will be stored.
        self.out_py = buffer
        #Python name of the process
        self.process_py_name = ''
        #The parameters: dict: {DotName: InterpreterObject]
        self.parameters = {}
        #The algebraic variables: dict: {DotName: InterpreterObject]
        self.algebraic_variables = {}
        #The state variables: dict: {DotName: InterpreterObject]
        self.state_variables = {}
        #generated differential variables: dict: {DotName: InterpreterObject]
        self.time_differentials = {}


    def find_attributes(self):
        '''
        Loop over the attribute definitions and classify the attributes into
        parameters, algebraic variables, state variables.
        Results:
        self.parameters, self.algebraic_variables, self.state_variables
        '''
        time_differentials = set()
        #create dicts to find and classify attributes fast
        for name, attr in self.ilt_process.attributes.iteritems():
            if not isinstance(attr, (InstFloat, InstString)):
                continue
            if attr.role is RoleParameter:
                self.parameters[name] = attr
            elif attr.role is RoleStateVariable:
                self.state_variables[name] = attr
                time_differentials.add(attr.time_derivative)
            elif issubclass(attr.role, RoleDataCanVaryAtRuntime) and attr in time_differentials:
                self.time_differentials[name] = attr
            elif issubclass(attr.role, RoleDataCanVaryAtRuntime) and attr not in time_differentials:
                self.algebraic_variables[name] = attr
            else:
                raise PyGenException('Unknown attribute definition:\n'+ str(attr))


    @staticmethod
    def make_unique_str(base_string, existing_strings):
        '''
        Make a unique string that is not in existing_strings.
        
        If base_string is already contained in existing_strings a number is appended 
        to base_string to make it unique.
        
        Arguments:
        base_string: str 
            The name that should become unique.
        existing_strings: container that supports the 'in' operation
            Container with the existing strings.
            
        Returns: string
            Unique name; base_string with number appended if necessary
            
        TODO: unify with make_unique_name(...)!!!
        '''
        for number in range(1, 100000):
            if base_string not in existing_strings:
                return  base_string
            #append number to last component of DotName
            base_string = base_string + str(number)
        raise Exception('Too many similar names')    
    
    
    def createAttrPyNames(self):
        '''
        Create python names for all attributes
        The python names are stored in the data attribute:
        self.targetName of NodeDataDef and NodeAttrAccess
        '''
        #TODO: prepend variables and parameters with different additional strings?
#        paramPrefix = 'self.p'
#        varPrefix = 'v'
        py_names = set() #mapping between attribute name and python name: {('a','b'):'v_a_b'}

        #loop over all attribute definitions and create an unique python name
        #for each attribute
        for name, attr in self.ilt_process.attributes.iteritems():
            if not isinstance(attr, (InstFloat, InstString)):
                continue
            #create underline separated name string
            py_name1 = '_'.join(name)
            #see if python name is unique; append number to make it unique
            py_name1 = self.make_unique_str(py_name1, py_names)
            py_names.add(py_name1)
            #store python name
            attr.target_name = py_name1        


    def writeClassDefStart(self):
        '''Write first few lines of class definition.'''
        self.out_py.write('class %s(SimulatorBase): \n' % self.process_py_name)
        self.out_py.write('    \'\'\' \n')
        self.out_py.write('    Object to simulate process %s \n'
                         % self.ilt_process.type().name)
        self.out_py.write('    Definition in\n    file: \'%s\'\n    line: %s \n'
                         % (self.ilt_process.loc.fileName(), 
                            self.ilt_process.loc.lineNo()))
        self.out_py.write('    \'\'\' \n')
        self.out_py.write('    \n')


    def writeConstructor(self):
        '''Generate the __init__ function.'''
        outPy = self.out_py
        ind8 = ' '*8
        outPy.write('    def __init__(self): \n')
        outPy.write('        super(%s, self).__init__() \n' % self.process_py_name)
        #out_py.write(ind8 + 'self.variableNameMap = {} \n')
        #create default file name
        outPy.write(ind8 + 'self.defaultFileName = \'%s.simres\' \n' % self.process_py_name)
        #create the parameters
        outPy.write(ind8 + '#create all parameters with value 0; ' +
                           'to prevent runtime errors. \n')
        for paramDef in self.parameters.values():
            outPy.write(ind8 + '%s = %s \n' % (paramDef.target_name, paramDef.zero_value))
        outPy.write('\n\n')


    def writeInitializeMethod(self):
        '''Generate method that initializes variables and parameters'''
        #get the process' init method
        #get the process' dynamic method
        method_name = DotName('init')
        if self.ilt_process.has_attribute(method_name):
            method = self.ilt_process.get_attribute(method_name)
        else:
            return
        #write method definition
        outPy = self.out_py 
        ind8 = ' '*8
        outPy.write('    def initialize(self,  *args, **kwArgs): \n')
        outPy.write(ind8 + '\'\'\' \n')
        outPy.write(ind8 + 'Compute parameter values and \n')
        outPy.write(ind8 + 'compute initial values of state variables \n')
        outPy.write(ind8 + '\'\'\' \n')
        #create all variables
        outPy.write(ind8 + '#create all variables with value 0; '
                           'to prevent runtime errors.\n')
        for var in (self.algebraic_variables.values() + 
                    self.state_variables.values() + 
                    self.time_differentials.values()):
            outPy.write(ind8 + '%s = %s \n' % (var.target_name, var.zero_value))

        #create dict for parameter override
        outPy.write(ind8 + '#create dict for parameter override \n')
        outPy.write(ind8 + 'self._createParamOverrideDict(args, kwArgs) \n')

        #print the method's statements
        outPy.write(ind8 + '#do computations \n')
        stmtGen = StatementGenerator(outPy)
        stmtGen.create_statements(method.statements, ind8) 
        outPy.write(ind8 + '\n')

        #put initial values into array and store them
        outPy.write(ind8 + '#assemble initial values to array and store them \n')
        #sequence of variables in the array is determined by self.state_variables
        #create long lines with 'var_ame11, var_name12, var_name13, ...'
        outPy.write(ind8 + 'self.initialValues = array([')
        for var in self.state_variables.values():
            outPy.write('%s, ' % var.target_name)
        outPy.write('], \'float64\') \n')
        outPy.write(ind8 + 'self.stateVectorLen = len(self.initialValues) \n')
        #assemble vector with algebraic variables to compute their total size
        outPy.write(ind8 + '#put algebraic variables into array, only to compute its size \n')
        outPy.write(ind8 + 'algVars = array([')
        for var in self.algebraic_variables.values():
            outPy.write('%s, ' % var.target_name)
        outPy.write('], \'float64\') \n')
        outPy.write(ind8 + 'self.algVectorLen = len(algVars) \n')
        #TODO: compute self.variableNameMap from the actual sizes of the variables
        outPy.write(ind8 + '#Create mapping between variable names and array indices \n')
        #Create mapping between variable names and array indices
        outPy.write(ind8 + 'self.variableNameMap = {')
        for i, varName in zip(range(len(self.state_variables) +
                                    len(self.algebraic_variables)),
                              self.state_variables.keys() +
                              self.algebraic_variables.keys()):
            outPy.write('\'%s\':%d, ' % (str(varName), i))
        outPy.write('}')
        outPy.write('\n\n')


    def writeDynamicMethod(self):
        '''Generate the method that contains the differential equations'''
        #get the process' dynamic method
        method_name = DotName('dynamic')
        if self.ilt_process.has_attribute(method_name):
            method = self.ilt_process.get_attribute(method_name)
        else:
            return
        #write method definition
        outPy = self.out_py
        ind8 = ' '*8; ind12 = ' '*12; #ind16 = ' '*16
        outPy.write('    def dynamic(self, time, state, returnAlgVars=False): \n')
        outPy.write(ind8 + '\'\'\' \n')
        outPy.write(ind8 + 'Compute time derivative of state variables. \n')
        outPy.write(ind8 + 'This function will be called by the solver repeatedly. \n')
        outPy.write(ind8 + '\'\'\' \n')
        #take the state variables out of the state vector
        #sequence of variables in the array is determined by self.state_variables
        outPy.write(ind8 + '#take the state variables out of the state vector \n')
        stateVars = self.state_variables.values()
        for var, n_var in zip(stateVars, range(len(stateVars))):
            outPy.write(ind8 + '%s = state[%d] \n' % (var.target_name, n_var))
        #Create all algebraic variables
        #TODO: remove this, once proper detection of unused variables exists
        outPy.write(ind8 + '#create all algebraic variables with value 0; ' +
                           'to prevent runtime errors.\n')
        for var in (self.algebraic_variables.values()):
            outPy.write(ind8 + '%s = %s \n' % (var.target_name, var.zero_value))

        #print the method's statements
        outPy.write(ind8 + '#do computations \n')
        stmtGen = StatementGenerator(outPy)
        stmtGen.create_statements(method.statements, ind8)
        outPy.write(ind8 + '\n')

        #return either state variables or algebraic variables
        outPy.write(ind8 + 'if returnAlgVars: \n')
        #assemble vector with algebraic variables
        outPy.write(ind12 + '#put algebraic variables into array \n')
        outPy.write(ind12 + 'algVars = array([')
        for var in self.algebraic_variables.values():
            outPy.write('%s, ' % var.target_name)
        outPy.write('], \'float64\') \n')
        outPy.write(ind12 + 'return algVars \n')

        outPy.write(ind8 + 'else: \n')
        #assemble the time derivatives into the return vector
        outPy.write(ind12 + '#assemble the time derivatives into the return vector \n')
        outPy.write(ind12 + 'stateDt = array([')
        for var, n_var in zip(stateVars, range(len(stateVars))):
            outPy.write('%s, ' % var.target_name)
        outPy.write('], \'float64\') \n')
        outPy.write(ind12 + 'return stateDt \n')

        outPy.write('\n\n')


    def writeFinalMethod(self):
        '''Generate the method that dispays/saves results after the simulation.'''
        #get the process' final method
        method_name = DotName('final')
        if self.ilt_process.has_attribute(method_name):
            method = self.ilt_process.get_attribute(method_name)
        else:
            return
        #write method definition
        outPy = self.out_py
        ind8 = ' '*8 #; ind12 = ' '*12; ind16 = ' '*16
        outPy.write('    def final(self): \n')
        outPy.write(ind8 + '\'\'\' \n')
        outPy.write(ind8 + 'Display and save simulation results. \n')
        outPy.write(ind8 + 'This function will be called once; after the simulation results \n')
        outPy.write(ind8 + 'have been computed. \n')
        outPy.write(ind8 + '\'\'\' \n')
        #TODO: create all variables, with values from the last iteration?
        #generate code for the statements
        outPy.write(ind8 + '#the final method\'s statements \n')
        stmtGen = StatementGenerator(outPy)
        stmtGen.create_statements(method.statements, ind8)
        outPy.write(ind8 + "print 'simulation %s finished.'\n" % self.process_py_name)
        outPy.write(ind8 + '\n')


    def create_process(self, ilt_process, name):
        '''
        Take part of ILT tree that defines one procedure and ouput definition
        of python class as string
        '''
        self.ilt_process = ilt_process #.copy()

        #collect information about the process
        self.process_py_name = name
        self.find_attributes()
        self.createAttrPyNames()

        #print self.ilt_process
        self.writeClassDefStart()
        self.writeConstructor()
        self.writeInitializeMethod()
        self.writeDynamicMethod()
        self.writeFinalMethod()
        #self.writeOutputEquations()

        self.out_py.write('\n\n')



class ProgramGenerator(object):
    '''Create a program from an ILT-tree'''

    def __init__(self):
        '''
        Arguments:
            pyFile : file where the program will be stored,
                     or a StringStream for debuging.
        '''
        super(ProgramGenerator, self).__init__(self)
        #root of intermediate language tree
        self.ilt_root = None
        #buffer for generated python code; with file interface
        self.out_py = cStringIO.StringIO()
        #names of the generated classes.
        self.process_class_names = []


    def buffer(self):
        '''Return the the generated Python text.'''
        return self.out_py.getvalue()
    
    
    def write(self, string):
        '''Put part of program text into buffer'''
        self.out_py.write(string)
        

    def write_program_start(self):
        '''
        Write first few lines of the program.
        Method looks really ugly because of raw string usage.
        '''
        self.write(
'''#!/usr/bin/env python
################################################################################
#                            Warning: Do not edit!                             #
#                                                                              #
# This file is generated, it will be overwritten every time the source file(s) #
# is/are changed.                                                              #
# If you want to change the behavior of a simulation object                    #
# write a main routine in an other file. Use import or execfile to load        #
# the objects defined in this file into the Python interpreter.                #
################################################################################
'''     )
        import datetime
        dt = datetime.datetime.today()
        date = dt.date().isoformat()
        time = dt.time().strftime('%H:%M:%S')

        self.write('# Generated by SIML compiler version %s on %s %s. \n'
                         % (PROGRAM_VERSION, date, time))
        self.write('# Source file(s): %s' % str(self.ilt_root.file_name))
        self.write(
'''
################################################################################


from numpy import array, pi, sin, cos, tan, sqrt, exp, log, min, max
from freeode.simulatorbase import SimulatorBase
from freeode.simulatorbase import simulatorMainFunc


'''     )
        return

    def write_program_end(self):
        '''Write last part of program, such as main routine.'''
        self.write(
'''

#Main function - executed when file (module) runs as an independent program.
#When file is imported into other programs, if-condition is false.
if __name__ == '__main__':
    simulatorClasses = ['''     )
        #create list with generated classes
        for name in self.process_class_names:
            self.write(str(name) + ', ')
        self.write(']')
        self.write(
'''
    simulatorMainFunc(simulatorClasses) #in module simulatorbase

'''     )
        return


    def create_program(self, ilt_root):
        '''
        Take an ILT and create as python program from it.
        Write the python program into the StringIO (file like) object 
        self.out_py
        '''
        self.ilt_root = ilt_root

        self.write_program_start()

        #every class definition in the ILT is a process (currently)
        #create code for it
        process_names = ilt_root.attributes.keys()
        process_names.sort()
        for name in process_names:
            self.process_class_names.append(name)
            process = ilt_root.get_attribute(name)
            procGen = ProcessGenerator(self.out_py)
            procGen.create_process(process, name)

        self.write_program_end()



if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #TODO: add doctest tests.


#    from simlparser import Parser
#------------ testProg1 -----------------------
    testProg1 = (
'''
class Test:
    data V, h: Float 
    data A_bott, A_o, mu, q, g: Float param

    func dynamic():
        h = V/A_bott
#        $V = q - mu*A_o*sqrt(2*g*h)
        $V = q + - mu*A_o*(2*g*h)
#        print 'h: ', h,

    func init():
        V = 0
        A_bott = 1; A_o = 0.02; mu = 0.55; 
        q = 0.05
 
 
class RunTest:
    data g: Float param
    data test: Test

    func dynamic():
        test.dynamic()

    func init():
        g = 9.81
        test.init()
#        solutionParameters.simulationTime = 100
#        solutionParameters.reportingInterval = 1

    func final():
#        graph test.V, test.h
        print 'Simulation finished successfully.'
        

compile RunTest
''' )

#    parser = Parser()
    intp = Interpreter()
    progGen = ProgramGenerator()
#
#    astTree = parser.parseModuleStr(testProg1)
#    print 'AST tree:'
#    print astTree

    intp.interpret_module_string(testProg1, 'test.siml', 'test')
    iltTree = intp.compile_module
    print 'ILT tree:'
    print iltTree

    progGen.create_program(iltTree)
    progStr = progGen.buffer()
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
