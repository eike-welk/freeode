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
from  freeode.interpreter import *



class PyGenException(Exception):
    '''Exception thrown by the python code generator classes'''
    def __init__(self, *params):
        Exception.__init__(self, *params)



class ExpressionGenerator(Visitor):
    '''
    Take ILT sub-tree that describes a formula and
    convert it into a formula in the Python programming language.
    
    USAGE:
        Call the method
            create_expression(iltFormula)
        with an ILT tree as an argument. The method will convert it into
        a Python string, which it returns.
    '''
    
    def __init__(self):
        Visitor.__init__(self)
        
    def create_expression(self, iltFormula):
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
    
    def _create_graph_func_call(self, call):
        '''
        Create call to the graph pseudo-function.
        
        Arguments to the graph function are not interpreted as their value at 
        the current time, but as the complete history during the 
        simulation.
        '''
        ret_str = 'self.graph(['
        for arg in call.arguments:
            ret_str += '"' + str(arg.siml_dot_name) + '"' + ','
        ret_str += '])'
        return ret_str
        
    @Visitor.when_type(NodeFuncCall, 1)
    def _createBuiltInFuncCall(self, call):
        #Built in function: sin(...)
        nameDict = {'sin':'sin', 'cos':'cos', 'tan':'tan', 'sqrt':'sqrt',
                    'exp':'exp', 'log':'log', 'min':'min' , 'max':'max',
                    'print':'print', 'graph':'graph', 
                    'Float.__str__':'str', 'String.__str__':'str'}
#                    'overrideParam':'self._overrideParam' }
        #get name of the corresponding Python function
        func_name = nameDict[call.name.codegen_name] 
        #special handling of the graph pseudo-function
        if func_name == 'graph':
            return self._create_graph_func_call(call)
        #produce output
        ret_str = func_name + '('
        for arg in call.arguments:
            ret_str += self.dispatch(arg) + ','
        for name, arg in call.keyword_arguments.iteritems():
            ret_str += name + ' = ' + self.dispatch(arg) + ','
        ret_str += ')'
        return ret_str
        
    @Visitor.when_type(IFloat, 1)
    def _createNum(self, variable):
        #Number: 123.5 or variable with type float
        if variable.role is RoleConstant:
            return str(float(variable.value))
        else:
            return variable.target_name
        
    @Visitor.when_type(IString, 1)
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
        opDict = {'+':' + ', '-':' - ', '*':' * ', '/':' / ', '%':' % ',
                   '**':' ** ',}
#                  '<':' < ', '>':' > ', '<=':' <= ', '>=':' >= ',
#                  '==':' == ', '!=':' != ',
#                  'and':' and ', 'or':' or '}
        opStr = opDict[iltFormula.operator]
        return (self.dispatch(iltFormula.arguments[0]) + opStr +
                self.dispatch(iltFormula.arguments[1]))
        
    @Visitor.when_type(NodeOpPrefix1, 1)
    def _createOpPrefix1(self, iltFormula):
        #Prefix operator: - not
        opDict = {'-':' -', 'not':' not '}
        opStr = opDict[iltFormula.operator]
        return opStr + self.dispatch(iltFormula.arguments[0])
        
    @Visitor.default
    def _ErrorUnknownNode(self, iltFormula):
        #Internal error: unknown node
        raise PyGenException('Unknown node in ExpressionGenerator:\n' 
                             + str(iltFormula))



class StatementGenerator(Visitor):
    '''
    Generate statements in Python from an AST or ILT syntax tree.
    
    self.createStatements(stmtList, indent) can take the entire body
    of a function and convert it to Python statements.
    '''

    def __init__(self, buffer):
        '''
        ARGUMENT:
            buffer : File like object where the Python program 
                        will be stored.
        '''
        super(StatementGenerator, self).__init__()
        #File like object, where the Python program will be stored.
        self.out_py = buffer
        #Object that creates a formula from an AST sub-tree
        self.genFormula = ExpressionGenerator()

    def write(self, string):
        '''Put a string of python code into the buffer.'''
        self.out_py.write(string)

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


    def create_expression(self, iltFormula):
        '''
        Take ILT sub-tree that describes a formula (expression) and
        convert it into a formula in the Python programming language.
        (recursive)

        ARGUMENT:
            iltFormula : tree of Node objects
        RETURN:
            string, formula in Python language
        '''
        return self.genFormula.create_expression(iltFormula)


    @Visitor.when_type(NodeAssignment, 1)
    def _createAssignment(self, iltStmt, indent):
        #Assignment  ---------------------------------------------------------
        self.write(indent + iltStmt.target.target_name + ' = ' +
                    self.create_expression(iltStmt.expression) + '\n')
    
        
    @Visitor.when_type(NodeIfStmt, 1)
    def _createIfStmt(self, iltStmt, indent):
        #if statement --------------------------------------------------------
        ind4 = ' '*4
        self.write(indent + 'if '
                           + self.create_expression(iltStmt.condition)
                           + ':\n')
        self.dispatch(iltStmt.ifTruePart, indent + ind4)
        #Only create else clause if necessary
        if len(iltStmt.elsePart) > 0:
            self.write(indent + 'else: \n')
            self.dispatch(iltStmt.elsePart, indent + ind4)


    @Visitor.when_type(NodeExpressionStmt, 1)
    def _createExpressionStmt(self, iltStmt, indent):
        #Expression with side effects: print(), graph(), store()
        self.write(indent + self.create_expression(iltStmt.expression) + '\n')
        
    
#    @Visitor.when_type(NodePrintStmt, 1)
#    def _createPrintStmt(self, iltStmt, indent):
#        #print statement -----------------------------------------------------
#        line = indent + 'print '
#        for expr in iltStmt.arguments:
#            line += self.create_expression(expr) + ', '
#        #take away last comma if newline is wanted
#        if iltStmt.newline:
#            line = line[:-2]
#        self.write(line + '\n')


#    @Visitor.when_type(NodeStoreStmt, 1)
#    def _createStoreStmt(self, iltStmt, indent):
#        #save statement -----------------------------------------------------
#        #One optional argument:
#        #    -the file name: string
#        #generated code is a function call:
#        #    self.save('source_file_name')
#        outPy = self.out_py
#        if len(iltStmt) > 1:               #Number of arguments: 0,1
#            raise UserException('The save statement can have 1 or no arguments.',
#                                iltStmt.loc)
#        self.write(indent + 'self.save(') #write start of statement
#        for expr in iltStmt:               #iterate over arguments (max 1)
#            #child is a string
#            if isinstance(expr, NodeString):
#                filename = self.create_expression(expr)   #write filename
#                self.write(filename)
#            #anything else is illegal
#            else:
#                raise UserException('Argument of save statement must be a file name.',
#                                    iltStmt.loc)
#        self.write(') \n')                #write end of statement
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
#        self.write(indent + 'self.graph([') #write start of statement
#        for expr in iltStmt:                 #iterate over arguments
#            #Argument is variable name
#            if   isinstance(expr, NodeAttrAccess):
#                self.write("'%s', " % str(expr.attrName)) #write variable name
#            #Argument is graph title
#            elif isinstance(expr, NodeString):
#                graphTitle = expr.dat        #store graph title
#            #anything else is illegal
#            else:
#                raise UserException('Illegal argument in graph statement.',
#                                    iltStmt.loc)
#        self.write('], ')                   #end list of var names
#        #A graph title was found
#        if graphTitle:
#            self.write("'%s'" % graphTitle) #write write grapt title as 2nd argument
#        self.write(') \n')                  #write end of statement


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



class SimulationClassGenerator(object):
    '''create python class that simulates a process'''

    def __init__(self, buffer):
        '''
        Arguments:
            buffer : File where the Python program will be stored.
        '''
        super(SimulationClassGenerator, self).__init__()
        #The input: an IL-tree of the process. It has no external dependencies.
        self.flat_object = CompiledClass()
        #File where the Python program will be stored.
        self.out_py = buffer
        #Python name of the process
        self.class_py_name = ''
        #The parameters: dict: {DotName: InterpreterObject]
        self.parameters = {}
        #The algebraic variables: dict: {DotName: InterpreterObject]
        self.algebraic_variables = {}
        #The state variables: dict: {DotName: InterpreterObject]
        self.state_variables = {}
        #generated differential variables: dict: {DotName: InterpreterObject]
        self.time_differentials = {}
        
        
    def write(self, string):
        '''Put a string of python code into the buffer.'''
        self.out_py.write(string)


    def classify_attributes(self):
        '''
        Loop over the attribute definitions and classify the attributes into
        parameters, algebraic variables, state variables.
        Results:
        self.parameters, self.algebraic_variables, self.state_variables
        '''
        #time_differentials = set()
        #create dicts to find and classify attributes fast
        for name, attr in self.flat_object.attributes.iteritems():
            if not isinstance(attr, (IFloat, IString)):
                continue
            if issubclass(attr.role, RoleParameter):
                self.parameters[name] = attr
            elif issubclass(attr.role, RoleInputVariable):
                self.state_variables[name] = attr
                #time_differentials.add(attr.time_derivative)
            elif issubclass(attr.role, RoleOutputVariable):
                self.time_differentials[name] = attr
            elif issubclass(attr.role, RoleIntermediateVariable):
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
    
    
    def create_attr_py_names(self):
        '''
        Create python names for all variables and parameters
        The python names are stored in the attribute: target_name 
        Additionally the dotted Siml name is stored in: siml_dot_name
        '''
        #TODO: prepend variables and parameters with different additional strings?
        param_prefix = 'param.'
#        varPrefix = 'v'
        py_names = set() #set of already existing target names.

        #loop over all attribute definitions and create an unique python name
        #for each attribute
        for name, attr in self.flat_object.attributes.iteritems():
            if not isinstance(attr, (IFloat, IString)):
                continue
            #create underline separated name string, replace '$' with '_D'
            py_name1 = '_'.join(name)
            py_name1 = py_name1.replace('$', '_D')
            #add prefix to parameters
            if attr.role is RoleParameter:
                py_name1 = param_prefix + py_name1
            #see if python name is unique; append number to make it unique
            py_name1 = self.make_unique_str(py_name1, py_names)
            py_names.add(py_name1)
            #store python name in attribute   
            attr.target_name = py_name1
            #store Siml name in attribute
            attr.siml_dot_name = name


    def write_class_def_start(self):
        '''Write first few lines of class definition.'''
        self.write('class %s(SimulatorBase): \n' % self.class_py_name)
        self.write('    \'\'\' \n')
#        self.write('    Object to simulate class %s \n'
#                         % self.flat_object.type().name)
        self.write('    Definition in\n    file: \'%s\'\n    line: %s \n'
                         % (self.flat_object.loc.fileName(), 
                            self.flat_object.loc.lineNo()))
        self.write('    \'\'\' \n')
        self.write('    \n')


    def write_constructor(self):
        '''Generate the __init__ function.'''
        ind8 = ' '*8
        self.write('    def __init__(self): \n')
        self.write('        SimulatorBase.__init__(self) \n') #% self.class_py_name)
        #out_py.write(ind8 + 'self.variableNameMap = {} \n')
        #create default file name
        self.write(ind8 + 'self.defaultFileName = \'%s.simres\' \n' % self.class_py_name)
        #create the parameters
        self.write(ind8 + '#create all parameters with value 0; '
                           'to prevent runtime errors. \n')
        self.write(ind8 + 'param = self.param \n')
        for paramDef in self.parameters.values():
            self.write(ind8 + '%s = 0 \n' % (paramDef.target_name))
        self.write('\n\n')


    def write_initialize_method(self):
        '''Generate method that initializes variables and parameters'''
        #get the process' init method
        method_name = DotName('initialize')
        if self.flat_object.has_attribute(method_name):
            method = self.flat_object.get_attribute(method_name)
        else:
            return
        #write method definition
        ind8 = ' '*8
        self.write('    def initialize(self,  *args, **kwArgs): \n')
        self.write(ind8 + '\'\'\' \n')
        self.write(ind8 + 'Compute parameter values and \n')
        self.write(ind8 + 'compute initial values of state variables \n')
        self.write(ind8 + '\'\'\' \n')
        #create all variables
        self.write(ind8 + '#create all variables with value 0; '
                           'to prevent runtime errors.\n')
        for var in (self.algebraic_variables.values() + 
                    self.state_variables.values() + 
                    self.time_differentials.values()):
            self.write(ind8 + '%s = 0 \n' % (var.target_name, ))

#        #create dict for parameter override
#        self.write(ind8 + '#create dict for parameter override \n')
#        self.write(ind8 + 'self._createParamOverrideDict(args, kwArgs) \n')

        #print the method's statements
        self.write(ind8 + '#do computations \n')
        stmtGen = StatementGenerator(self.out_py)
        stmtGen.create_statements(method.statements, ind8) 
        self.write(ind8 + '\n')

        #put initial values into array and store them
        self.write(ind8 + '#assemble initial values to array and store them \n')
        #sequence of variables in the array is determined by self.state_variables
        #create long lines with 'var_ame11, var_name12, var_name13, ...'
        self.write(ind8 + 'self.initialValues = array([')
        for var in self.state_variables.values():
            self.write('%s, ' % var.target_name)
        self.write('], \'float64\') \n')
        self.write(ind8 + 'self.stateVectorLen = len(self.initialValues) \n')
        #assemble vector with algebraic variables to compute their total size
        self.write(ind8 + '#put algebraic variables into array, only to compute its size \n')
        self.write(ind8 + 'algVars = array([')
        for var in self.algebraic_variables.values():
            self.write('%s, ' % var.target_name)
        self.write('], \'float64\') \n')
        self.write(ind8 + 'self.algVectorLen = len(algVars) \n')
        #TODO: compute self.variableNameMap from the actual sizes of the variables
        self.write(ind8 + '#Create mapping between variable names and array indices \n')
        #Create mapping between variable names and array indices
        self.write(ind8 + 'self.variableNameMap = {')
        for i, varName in zip(range(len(self.state_variables) +
                                    len(self.algebraic_variables)),
                              self.state_variables.keys() +
                              self.algebraic_variables.keys()):
            self.write('\'%s\':%d, ' % (str(varName), i))
        self.write('}\n')
        self.write('\n\n')


    def write_dynamic_method(self):
        '''Generate the method that contains the differential equations'''
        #get the process' dynamic method
        method_name = DotName('dynamic')
        if self.flat_object.has_attribute(method_name):
            method = self.flat_object.get_attribute(method_name)
        else:
            return
        #write method definition
        ind8 = ' '*8; ind12 = ' '*12 #; ind16 = ' '*16
        self.write('    def dynamic(self, time, state, returnAlgVars=False): \n')
        self.write(ind8 + '\'\'\' \n')
        self.write(ind8 + 'Compute time derivative of state variables. \n')
        self.write(ind8 + 'This function will be called by the solver repeatedly. \n')
        self.write(ind8 + '\'\'\' \n')
        #take the state variables out of the state vector
        #sequence of variables in the array is determined by self.state_variables
        self.write(ind8 + '#take the state variables out of the state vector \n')
        stateVars = self.state_variables.values()
        for var, n_var in zip(stateVars, range(len(stateVars))):
            self.write(ind8 + '%s = state[%d] \n' % (var.target_name, n_var))
        #Create all algebraic variables
        #TODO: remove this, once proper detection of unused variables exists
        self.write(ind8 + '#create all algebraic variables with value 0; ' +
                           'to prevent runtime errors.\n')
        for var in (self.algebraic_variables.values()):
            self.write(ind8 + '%s = 0 \n' % (var.target_name))

        #print the method's statements
        self.write(ind8 + '#do computations \n')
        stmtGen = StatementGenerator(self.out_py)
        stmtGen.create_statements(method.statements, ind8)
        self.write(ind8 + '\n')

        #return either state variables or algebraic variables
        self.write(ind8 + 'if returnAlgVars: \n')
        #assemble vector with algebraic variables
        self.write(ind12 + '#put algebraic variables into array \n')
        self.write(ind12 + 'algVars = array([')
        for var in self.algebraic_variables.values():
            self.write('%s, ' % var.target_name)
        self.write('], \'float64\') \n')
        self.write(ind12 + 'return algVars \n')

        self.write(ind8 + 'else: \n')
        #assemble the time derivatives into the return vector
        self.write(ind12 + '#assemble the time derivatives into the return vector \n')
        self.write(ind12 + 'stateDt = array([')
        for var, n_var in zip(stateVars, range(len(stateVars))):
            self.write('%s, ' % var.time_derivative().target_name)
        self.write('], \'float64\') \n')
        self.write(ind12 + 'return stateDt \n')

        self.write('\n\n')


    def write_final_method(self):
        '''Generate the method that dispays/saves results after the simulation.'''
        #get the process' final method
        method_name = DotName('final')
        if self.flat_object.has_attribute(method_name):
            method = self.flat_object.get_attribute(method_name)
        else:
            return
        #write method definition
        ind8 = ' '*8 #; ind12 = ' '*12; ind16 = ' '*16
        self.write('    def final(self): \n')
        self.write(ind8 + '\'\'\' \n')
        self.write(ind8 + 'Display and save simulation results. \n')
        self.write(ind8 + 'This function will be called once; after the simulation results \n')
        self.write(ind8 + 'have been computed. \n')
        self.write(ind8 + '\'\'\' \n')
        #TODO: create all variables, with values from the last iteration?
        #generate code for the statements
        self.write(ind8 + '#the final method\'s statements \n')
        stmtGen = StatementGenerator(self.out_py)
        stmtGen.create_statements(method.statements, ind8)
        self.write(ind8 + "print 'simulation %s finished.'\n" % self.class_py_name)
        self.write(ind8 + '\n')


    def create_sim_class(self, class_name, flat_object):
        '''
        Take part of ILT tree that defines one procedure and ouput definition
        of python class as string
        '''
        self.flat_object = flat_object #.copy()

        #collect information about the process
        self.class_py_name = class_name
        self.classify_attributes()
        self.create_attr_py_names()

        #output program text
        self.write_class_def_start()
        self.write_constructor()
        self.write_initialize_method()
        self.write_dynamic_method()
        self.write_final_method()
        #TODO: separate function to compute the algebraic variables.
        #self.write_output_equations()

        self.write('\n\n')



class ProgramGenerator(object):
    '''Create a program from an ILT-tree'''

    def __init__(self):
        '''
        Arguments:
            pyFile : file where the program will be stored,
                     or a StringStream for debuging.
        '''
        super(ProgramGenerator, self).__init__(self)
        #filename of source file
        self.source_file_name = None
        #buffer for generated python code; with file interface
        self.out_py = cStringIO.StringIO()
        #names of the generated classes.
        self.simulation_class_names = []


    def get_buffer(self):
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
        self.write('# Source file: %s' % str(self.source_file_name))
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
        #TODO: add program text to output file as string.
        self.write(
'''

#Main function - executed when file (module) runs as an independent program.
#When file is imported into other programs, if-condition is false.
if __name__ == '__main__':
    simulatorClasses = ['''     )
        #create list with generated classes
        for name in self.simulation_class_names:
            self.write(str(name) + ', ')
        self.write(']')
        self.write(
'''
    simulatorMainFunc(simulatorClasses) #in module simulatorbase

'''     )
        return


    def create_program(self, source_file_name, obj_list):
        '''
        Take a list of flattened simulation objects and create a python 
        program from it. Write the python program into the StringIO (file 
        like) object self.out_py.
        '''
        self.source_file_name = source_file_name

        self.write_program_start()

        #create code for each simulation object in the list
        for sim_object in obj_list:
            #TODO: make unique class names
            self.simulation_class_names.append(sim_object.class_name)
            procGen = SimulationClassGenerator(self.out_py)
            procGen.create_sim_class(sim_object.class_name, sim_object)

        self.write_program_end()



if __name__ == '__main__':
    #TODO: add doctest tests.
    pass
