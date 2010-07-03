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
Check the output of the interpreter for some semantic errors.

A bit hacked together because a real optimizer is difficult.
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

#import copy
#import weakref
#from weakref import ref
import sys
#import math

from freeode.ast import (NodeParentheses, NodeExpressionStmt,
                         NodeFuncCall, NodeAssignment, NodeIfStmt, NodeClause, 
                         RoleConstant, RoleParameter, RoleInputVariable, 
                         RoleOutputVariable, RoleIntermediateVariable)
from freeode.interpreter import (InterpreterObject, SimlFunction,
                                 CodeGeneratorObject, CompiledClass,
                                 isrole, 
                                 isknownconst,
                                 )
from freeode.util import UserException, DotName



class MultiDict(dict):
    '''
    Store multiple values under the same key. 
    Returns a list of items instead the item itself.
    
    Taken from Active State recipe #440502:
        http://code.activestate.com/recipes/440502-a-dictionary-with-multiple-values-for-each-key/
    '''
    def __setitem__(self, key, value):
        '''
        Add the given value to the list of values for this key.
        
        Sets are accepted as keys too:
            Each item in the set is treated as a key, and the value is added
            to the list for this key.
        '''
        if isinstance(key, set):
            for key_item in key:
                self.setdefault(key_item, []).append(value)
        else:
            self.setdefault(key, []).append(value)
        
    def __getitem__(self, key):
        if isinstance(key, set):
            return KeyError('Illegal key type "set": '
                            'Sets are only legal to put values into MultiDict.')
        return dict.__getitem__(self, key)



class MakeDataFlowDecorations(object):
    '''
    Create sets of input and output attributes, for all statements, "if" clauses
    function calls, methods, and the complete simulation object.
    
    Every analyzed object is decorated with the following attributes:
    inputs : set
        All variables that are used as inputs by this statement.
        For compound objects this value is cumulative and includes all 
        attributes used by statements in the body.
    outputs : set
        All variables that are changed by this object. (Cumulative for compound 
        objects.)
        
    Methods get additional attributes.
    input_locs : MultiDict[CodeGeneratorObject] -> TextLocation
        Locations where the attributes used as inputs. Needed to easily generate
        error messages if illegal usage of a variable was detected.
    output_locs : MultiDict[CodeGeneratorObject] -> TextLocation
        Locations where the attributes used as outputs.
        
    Usage:
    -----_
    md = MakeDataFlowDecorations()
    md.decorate_simulation_object(sim_obj)
    '''
    def __init__(self):
        object.__init__(self)    
        #locations where the variables of the current function are used
        #Necessary for making useful error messages.
        #MultiDict[CodeGeneratorObject] -> TextLocation
        self.input_locs = MultiDict()
        self.output_locs = MultiDict()
        
        
    def discover_expr_input_variables(self, expr):
        '''Go through an expression, find all input variables'''
        #A variable in an expression is always an input
        if isinstance(expr, InterpreterObject):
            return set([expr])
        #if its a function call recurse for each of its arguments
        elif isinstance(expr, (NodeFuncCall, NodeParentheses)):
            inputs = set()
            for arg in list(expr.arguments) + expr.keyword_arguments.values():
                arg_inputs = self.discover_expr_input_variables(arg)
                #create set union of all arguments' inputs
                inputs.update(arg_inputs)
            #decorate call with discovered inputs
            expr.inputs = inputs
            return inputs
        else:
            raise Exception('Unexpected node in expression. type: %s; value: %s' 
                            % (str(type(arg)), str(arg)))
        
    
    def decorate_assignment(self, assignment):
        '''Put sets of input and output variables on an assignment statement.'''
        assert isinstance(assignment, NodeAssignment)
        #compute sets of input and output objects
        inputs = self.discover_expr_input_variables(assignment.expression)
        outputs = set([assignment.target])
        self.input_locs[inputs] = assignment.loc
        self.output_locs[assignment.target] = assignment.loc
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
            cond_inp = self.discover_expr_input_variables(clause.condition)
            self.input_locs[cond_inp] = clause.loc #remember locs of condition's attributes
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
            elif isinstance(stmt, NodeExpressionStmt):
                inp = self.discover_expr_input_variables(stmt.expression)
                inputs.update(inp)
                self.input_locs[inp] = stmt.loc
                stmt.inputs = inp
                stmt.outputs = set()
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
        #Reset usage locations of variables for the current function
        self.input_locs = MultiDict()
        self.output_locs = MultiDict()

        #TODO: decorate function arguments
        inputs, outputs = self.decorate_statement_list(main_function.statements)
        main_function.inputs = inputs
        main_function.outputs = outputs
        main_function.input_locs = self.input_locs
        main_function.output_locs = self.output_locs
        return inputs, outputs
        
    
    def decorate_simulation_object(self, sim_obj):
        '''Discover inputs and outputs of the whole flattened class.''' 
        inputs, outputs = set(), set()
        for attr in sim_obj.attributes.itervalues():
            if isinstance(attr, SimlFunction):
#                print 'decorating: ', attr.name
                inp, out = self.decorate_main_function(attr)
                inputs.update(inp)
                outputs.update(out)
        sim_obj.inputs = inputs
        sim_obj.outputs = outputs
        return inputs, outputs



class VariableUsageChecker(object):
    '''
    Test if all variables are used correctly.
    
    The main functions have different constraints on the usage of variables.
    For example the init*** functions must compute all parameters and all initial 
    variables.
    '''
    def __init__(self):
        #The simulation object that is analyzed
        self.sim_obj = CompiledClass('--dummy--')
        #The simulation object's main functions
        self.main_funcs = {}
        
        #The data attributes get into these sets according to their roles
        self.constants = set()
        self.parameters = set()
        self.external_parameters = set() #arguments of the init_* functions
        self.input_variables = set() #state variables
        self.intermediate_variables = set() #algebraic variables 
        self.output_variables = set() #time derivatives
        self.func_locals = set() #local variables of all functions.
 

    def set_annotated_sim_object(self, sim_obj):
        '''
        Store simulation object and categorize its attributes
        
        ARGUMENT
        --------
        sim_obj : CompiledClass
            Simulation object with annotations created by
            MakeDataFlowDecorations.decorate_simulation_object(...)
        '''
        assert isinstance(sim_obj, CompiledClass)
        self.sim_obj = sim_obj
        
        #care for the external inputs - arguments of main functions 
        self.external_parameters = set(sim_obj.external_inputs)
        #local variables of all functions.
        self.func_locals = set(sim_obj.func_locals)
        
        #iterate over simulation's attributes
        #put data attributes into sets according to their role
        for name, attr in sim_obj.attributes.iteritems():
            assert isinstance(attr, InterpreterObject)
            #find main functions
            if isinstance(attr, SimlFunction):
                self.main_funcs[name] = attr
                continue
            #classify data attributes according to their role
            assert isinstance(attr, CodeGeneratorObject)
            if isrole(attr, RoleConstant):
                raise Exception('Constant attribute in compiled simulation object.')
            elif isrole(attr, RoleParameter):
                self.parameters.add(attr)
            elif isrole(attr, RoleInputVariable):
                self.input_variables.add(attr)
            elif isrole(attr, RoleIntermediateVariable):
                self.intermediate_variables.add(attr)
            elif isrole(attr, RoleOutputVariable):
                self.output_variables.add(attr)
            else:
                raise Exception('Unknown attribute role!')
            
        #Search for constants in the simulation's input attributes (collected 
        #by MakeDataFlowDecorations). 
        all_inputs = sim_obj.inputs
        for attr in all_inputs:
            if isrole(attr, RoleConstant):
                if not isknownconst(attr):
                    raise Exception('Unknown constant: %s' % attr)
                self.constants.add(attr)
    
    
    def check_function_var_access(self, func, known_attributes, 
                                     legal_outputs, required_assignments):
        '''
        Check if a function makes illegal access to any variable.
        Raise UserException if any illegal access is found.
        '''
        #Check for illegal reads (currently unknown attributes)
        if not(func.inputs <= known_attributes):
            ill_input = func.inputs - known_attributes
            ill_names, err_locs = [], []
            for attr in ill_input:
                ill_names.append(self.sim_obj.find_attribute_name(attr))
                err_locs += func.input_locs[attr]
            ill_names = map(str, ill_names)
            err_locs = map(str, err_locs)
            raise UserException('Illegal read access to variable(s) ' +
                                ', '.join(ill_names) + '\n' +
                                '\n'.join(err_locs), func.loc, 
                                errno=4500100)
                
        #Check for illegal assignments
        if not(func.outputs <= legal_outputs):
            ill_output = func.outputs - legal_outputs
            ill_names, err_locs = [], []
            for attr in ill_output:
                attr_str = '%s (%s)' % (str(self.sim_obj.find_attribute_name(attr)),
                                        str(attr.__siml_role__)) 
                ill_names.append(attr_str)
                err_locs += func.output_locs[attr]
            ill_names = map(str, ill_names)
            err_locs = map(str, err_locs)
            raise UserException('Illegal assignment to variable(s): ' +
                                ', '.join(ill_names) + '\n' +
                                '\n'.join(err_locs), func.loc, 
                                errno=4500200)
            
        #Test for missing assignments
        if not(required_assignments <= func.outputs):
            missing_output = required_assignments - func.outputs
            missing_names = []
            for attr in missing_output:
                missing_names.append(self.sim_obj.find_attribute_name(attr))
                missing_names = map(str, missing_names)
            raise UserException('Missing assignment to variable(s): ' +
                                ', '.join(missing_names), func.loc, 
                                errno=4500300)

        
    def check_initialize_function(self, func):
        '''Check one of the initialization functions'''
        #these attributes are already known when the main function is executed
        time = self.sim_obj.get_attribute(DotName('time'))
        known_attributes = self.constants | self.external_parameters | set([time])
        #these variables are legal targets for assignments
        legal_outputs = self.parameters | self.input_variables | \
                        self.intermediate_variables  | self.external_parameters
        #these variables must be assigned by the main function
        #at the end of the main function these variables must be known
        required_assignments = (self.parameters | self.input_variables) \
                               - self.func_locals
        
        self.check_function_var_access(func, known_attributes, legal_outputs, 
                                       required_assignments)


    def check_dynamic_function(self, func):
        '''check the dynamic function'''
        #these attributes are already known when the main function is executed
        #It in illegal to assign to them
        time = self.sim_obj.get_attribute(DotName('time'))
        known_attributes = self.constants | self.parameters | \
                           self.input_variables | set([time])
        #these variables are legal targets for assignments
        legal_outputs = self.intermediate_variables | self.output_variables
        #these variables must be assigned by the main function
        #at the end of the main function these variables must be known
        #required_assignments = self.intermediate_variables | self.output_variables
        required_assignments = self.output_variables
        
        self.check_function_var_access(func, known_attributes, legal_outputs, 
                                       required_assignments)
                
        
    def check_final_function(self, func):
        '''check the final function'''
        #these attributes are already known when the main function is executed
        time = self.sim_obj.get_attribute(DotName('time'))
        known_attributes = self.constants | self.parameters | \
                           self.input_variables | self.intermediate_variables | \
                           set([time])
        #these variables are legal targets for assignments
        legal_outputs = set(self.intermediate_variables)
        #these variables must be assigned by the main function
        #at the end of the main function these variables must be known
        required_assignments = set()
        
        self.check_function_var_access(func, known_attributes, legal_outputs, 
                                       required_assignments)
        

    def check_simulation_object(self, sim_obj):
        '''
        Test semantic errors in a simulation object
        
        
        ARGUMENT
        --------
        sim_obj : CompiledClass
            Simulation object with annotations created by
            MakeDataFlowDecorations.decorate_simulation_object(...)
        '''
        self.__init__()
        assert isinstance(sim_obj, CompiledClass)
        self.set_annotated_sim_object(sim_obj)
        
        #check the parameterized initialization functions
        for name, func in sim_obj.attributes.iteritems():
            if str(name).startswith('init_'):
                self.check_initialize_function(func)
        #check the main functions with fixed names
        ini_func = sim_obj.get_attribute(DotName('initialize'))
        self.check_initialize_function(ini_func)
        dyn_func = sim_obj.get_attribute(DotName('dynamic'))
        self.check_dynamic_function(dyn_func)
        fin_func = sim_obj.get_attribute(DotName('final'))
        self.check_final_function(fin_func)


#    def check_assignment(self, assignment):
#        '''Check one assignment statement'''
#        assert isinstance(assignment, NodeAssignment)
#        #test for reading unknown values
#        _unknown_inputs = assignment.inputs - self.known_attributes
#        #test for writing already known values
#        _duplicate_assign = assignment.outputs & self.known_attributes
#        #the outputs of the assignment become known values
#        self.known_attributes.update(assignment.outputs)
#        
#    def check_if_statement(self, _stmt):
#        '''Check an if statement'''    
#        
#    def normalize_if_statement(self, _stmt):
#        '''Put the same number of assignments into each clause of an if statement'''
##        #TODO: create dummy assignments when clauses don't assign to the same variables
##        for clause in stmt.clauses:
##            missing_outputs = stmt.outputs - clause.outputs
##            for attr in missing_outputs:
##                assert isinstance(attr, InterpreterObject)
##                print 'dummy assignment needed for', attr.parent().find_name(attr)
#
#    def check_statement_list(self, stmt_list):
#        '''
#        Check a list of statements.
#        
#        Calls the specialized checking functions.
#        '''
#        #TODO: reorder statements
#        for stmt in stmt_list:
#            if isinstance(stmt, NodeAssignment):
#                self.check_assignment(stmt)
#            elif isinstance(stmt, NodeIfStmt):
#                self.check_if_statement(stmt)
#            else:
#                raise Exception('Unexpected type of statement '
#                                'type: %s; value: %s' 
#                                % (str(type(stmt)), str(stmt)))
#        
#    def check_function(self, function):
#        self.check_statement_list(function.statements)
    
    
def check_simulation_objects(obj_list):
    '''
    Check a list of simulation objects for errors. Raises UserException when
    errors are detected.
    '''
    deco = MakeDataFlowDecorations()
    check = VariableUsageChecker()
    
    for sim_obj in obj_list:
        deco.decorate_simulation_object(sim_obj)
        check.check_simulation_object(sim_obj)
        
    
#TODO: test: the methods of a flat object must not use any data from 
#      outside of the flat_object.

#TODO: test if all variables are assigned once (single assignment)     
#TODO: test if data flow is possible
#TODO: reorder statements
#TODO: create missing assignments in 'if' statements

#TODO: remove unused variables
#TODO: remove assignments to unused variables from each branch of in 'if' statement separately.
#TODO: substitute away variables that are used only once

