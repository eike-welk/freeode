# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
#    eike.welk@gmx.net                                                     *
#                                                                          *
#                                                                          *
#    License: GPL                                                          *
#                                                                          *
#    This program is free software; you can redistribute it and/or modify  *
#    it under the terms of the GNU General Public License as published by  *
#    the Free Software Foundation; either version 2 of the License, or     *
#    (at your option) any later version.                                   *
#                                                                          *
#    This program is distributed in the hope that it will be useful,       *
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#    GNU General Public License for more details.                          *
#                                                                          *
#    You should have received a copy of the GNU General Public License     *
#    along with this program; if not, write to the                         *
#    Free Software Foundation, Inc.,                                       *
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#***************************************************************************

"""
Optimizer for the output of the interpreter.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#import copy
#import weakref
#from weakref import ref
import sys
#import math

from freeode.ast import (NodeParentheses, NodeOpInfix2, NodeOpPrefix1, 
                         NodeFuncCall, NodeAssignment, NodeIfStmt, NodeClause, 
                         RoleConstant, RoleParameter, RoleInputVariable, 
                         RoleOutputVariable, RoleIntermediateVariable)
from freeode.interpreter import (InterpreterObject, CallableObject, 
                                 CodeGeneratorObject, CompiledClass,
                                 i_isrole, siml_isknown)



class MakeDataFlowDecorations(object):
    '''
    Create sets of input and output variables, 
    for all statements and all function calls.
    '''
    
    def __init__(self):
        object.__init__(self)
        
        
    def discover_expr_input_variables(self, expr):
        '''Go through an expression, find all input variables'''
        #A variable in an expression is always an input
        if isinstance(expr, InterpreterObject):
            return set([expr])
        #if its a function call recurse for each of its arguments
        elif isinstance(expr, (NodeFuncCall, NodeOpInfix2, NodeOpPrefix1, 
                               NodeParentheses)):
            inputs = set()
            for arg in list(expr.arguments) + expr.keyword_arguments.values():
                arg_inputs = self.discover_expr_input_variables(arg)
                #create set union of all arguments' inputs
                inputs.update(arg_inputs)
            #decorate call with discovered inputs
            expr.inputs = inputs
            return inputs
        else:
            raise Exception('Unexpected type of argument '
                            'for Siml function. type: %s; value: %s' 
                            % (str(type(arg)), str(arg)))
        
    
    def decorate_assignment(self, assignment):
        '''Put sets of input and output variables on an assignment statement.'''
        assert isinstance(assignment, NodeAssignment)
        #compute sets of input and output objects
        inputs = self.discover_expr_input_variables(assignment.expression)
        outputs = set([assignment.target])
        #decorate the assignment
        assignment.inputs = inputs
        assignment.outputs = outputs
        return (inputs, outputs)
        
        
    def decorate_if_statement(self, stmt):
        '''Find inputs and outputs of an 'if' statement.'''
        assert isinstance(stmt, NodeIfStmt)
        inputs, outputs = set(), set()
        for clause in stmt.clauses:
            assert isinstance(clause, NodeClause)
            #TODO: decorate condition
            cond_inp = self.discover_expr_input_variables(clause.condition)
            stmt_inp, out = self.decorate_statement_list(clause.statements)
            inp = cond_inp | stmt_inp
            #decorate the clause
            clause.inputs = inp
            clause.outputs = out
            #compute inputs and outputs of whole 'if' statement
            inputs.update(inp)
            outputs.update(out)
        #decorate the 'if' statement
        stmt.inputs = inputs
        stmt.outputs = outputs
        return (inputs, outputs)
        
            
    def decorate_statement_list(self, stmt_list):  
        '''
        Find inputs and outputs of a list of statements.
        '''  
        inputs, outputs = set(), set()
        for stmt in stmt_list:
            if isinstance(stmt, NodeAssignment):
                inp, out = self.decorate_assignment(stmt)
                inputs.update(inp)
                outputs.update(out)
            elif isinstance(stmt, NodeIfStmt):
                inp, out = self.decorate_if_statement(stmt)
                inputs.update(inp)
                outputs.update(out)
            else:
                raise Exception('Unexpected type of statement '
                                'type: %s; value: %s' 
                                % (str(type(stmt)), str(stmt)))
        #Correct for data flow inside the statement list.
        #If some outputs are used as inputs by subsequent statements,
        #these outputs should not appear in the inputs too.
        inputs = inputs - outputs
        return inputs, outputs
    
    
    def decorate_main_function(self, main_function):
        '''Put input and output decorations on all elements of the class'''
        #TODO: decorate function arguments
        inputs, outputs = self.decorate_statement_list(main_function.statements)
        main_function.inputs = inputs
        main_function.outputs = outputs
        return inputs, outputs
        
    
    def decorate_simulation_object(self, sim_obj):
        '''Discover inputs and outputs of the whole flattened class.''' 
        inputs, outputs = set(), set()
        for attr in sim_obj.attributes.itervalues():
            if isinstance(attr, CallableObject):
#                print 'decorating: ', attr.name
                inp, out = self.decorate_main_function(attr)
                inputs.update(inp)
                outputs.update(out)
        sim_obj.inputs = inputs
        sim_obj.outputs = outputs
        return inputs, outputs



class DataFlowChecker(object):
    '''Test if data flow is possible and do changes to AST if necessary.'''
    
    def __init__(self):
        #self.sim_obj = InterpreterObject()
        #The data attributes get into these sets according to their roles
        self.constants = set()
        self.parameters = set()
        self.iput_variables = set() #state variables
        self.intermediate_variables = set() #algebraic variables 
        self.output_variables = set() #time derivatives
        #TODO: also care for the external inputs - arguments of main functions 
        #currently known attributes - to check data flow and single assignment
        self.known_attributes = set()
        #attributes that can legally be the target of assignments
        self.legal_outputs = set()
        #these variables must be assigned by the main function;
        #at the end of the main function these variables must be known
        self.required_assignments = set()

    
    def set_sim_object(self, sim_obj):
        '''Prepare simulation object for data flow analysis.'''
        assert isinstance(sim_obj, CompiledClass)
        
        #iterate over simulation's attributes
        #put data attributes into sets according to their role
        for attr in sim_obj.attributes.itervalues():
            assert isinstance(attr, InterpreterObject)
            #only look at built in data (ignore functions)
            if not isinstance(attr, CodeGeneratorObject):
                continue
            #classify attributes according to their role
            if i_isrole(attr.role, RoleConstant):
                raise Exception('The simulation object must not have constant attributes!')
            elif i_isrole(attr.role, RoleParameter):
                self.parameters.add(attr)
            elif i_isrole(attr.role, RoleInputVariable):
                self.iput_variables.add(attr)
            elif i_isrole(attr.role, RoleIntermediateVariable):
                self.intermediate_variables.add(attr)
            elif i_isrole(attr.role, RoleOutputVariable):
                self.output_variables.add(attr)
            else:
                raise Exception('Unknown attribute role!')
            
        #Constants embedded in the code are put into a special set.
        all_inputs = sim_obj.inputs
        for attr in all_inputs:
            if i_isrole(attr.role, RoleConstant):
                #TODO: detecting unknown constants should be handled in the interpreter
                if not siml_isknown(attr):
                    name = '<anonymous constant>'
                    if attr.parent and attr.parent():
                        name = str(attr.parent().find_name(attr))
                    print >> sys.stderr, 'Warning! detected unknown constant: ', name
                    continue
                self.constants.add(attr)
        #TODO: care for the external inputs - arguments of main functions 


    def prepare_initialize_function(self):
        '''Prepare checking one of the initialization functions'''
        #TODO: care for the external inputs - arguments of main functions 
        #these attributes are already known when the main function is executed
        self.known_attributes = self.constants 
        #these variables are legal targets for assignments
        self.legal_outputs = self.parameters | self.iput_variables | \
                             self.intermediate_variables 
        #these variables must be assigned by the main function
        #at the end of the main function these variables must be known
        self.required_assignments = self.parameters | self.iput_variables

    def prepare_dynamic_function(self):
        '''Prepare checking the dynamic function'''
        #these attributes are already known when the main function is executed
        self.known_attributes = self.constants | self.parameters | \
                                self.iput_variables
        #these variables are legal targets for assignments
        self.legal_outputs = self.intermediate_variables | self.output_variables
        #these variables must be assigned by the main function
        #at the end of the main function these variables must be known
        self.required_assignments = self.intermediate_variables | self.output_variables
        
    def prepare_final_function(self):
        '''Prepare checking the final function'''
        #these attributes are already known when the main function is executed
        self.known_attributes = self.constants | self.parameters | \
                                self.output_variables
        #these variables are legal targets for assignments
        self.legal_outputs = set()
        #these variables must be assigned by the main function
        #at the end of the main function these variables must be known
        self.required_assignments = set()
        
        
    def check_assignment(self, assignment):
        '''Check one assignment statement'''
        assert isinstance(assignment, NodeAssignment)
        #test for reading unknown values
        _unknown_inputs = assignment.inputs - self.known_attributes
        #test for writing already known values
        _duplicate_assign = assignment.outputs & self.known_attributes
        #the outputs of the assignment become known values
        self.known_attributes.update(assignment.outputs)
        
    def check_if_statement(self, _stmt):
        '''Check an if statement'''    
        
    def normalize_if_statement(self, _stmt):
        '''Put the same number of assignments into each clause of an if statement'''
#        #TODO: create dummy assignments when clauses don't assign to the same variables
#        for clause in stmt.clauses:
#            missing_outputs = stmt.outputs - clause.outputs
#            for attr in missing_outputs:
#                assert isinstance(attr, InterpreterObject)
#                print 'dummy assignment needed for', attr.parent().find_name(attr)

    def check_statement_list(self, stmt_list):
        '''
        Check a list of statements.
        
        Calls the specialized checking functions.
        '''
        #TODO: reorder statements
        for stmt in stmt_list:
            if isinstance(stmt, NodeAssignment):
                self.check_assignment(stmt)
            elif isinstance(stmt, NodeIfStmt):
                self.check_if_statement(stmt)
            else:
                raise Exception('Unexpected type of statement '
                                'type: %s; value: %s' 
                                % (str(type(stmt)), str(stmt)))
        
    def check_function(self, function):
        self.check_statement_list(function.statements)
    
    
    
#TODO: test: the methods of a flat object must not use any data from 
#      outside of the flat_object.

#TODO: test if all variables are assigned once (single assignment)     
#TODO: test if data flow is possible
#TODO: reorder statements
#TODO: create missing assignments in 'if' statements

#TODO: remove unused variables
#TODO: remove assignments to unused variables from each branch of in 'if' statement separately.
#TODO: substitute away variables that are used only once

