# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2006 - 2008 by Eike Welk                                #
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
############################################################################
'''
Creation of the program's intermediate representation (language). 

This intermediate representation is a tree made of AST nodes (classes 
inheriting from ast.Node).
It is created from the abstract syntax tree (AST), and it is given to the 
generator of the output language (currently only Python). 
'''

#TODO: Implement namespaces. Usefull would be:
#       - Global namespace for: classes, global functions.
#       - Class namespace for class attributes 
#       - Function local namespace for: data attributes, function attributes


from __future__ import division

import os
#import our own syntax tree classes
from freeode.ast import *
#import the standard library of the SIML language
import freeode.simlstdlib as simlstdlib
#import the parser for the siml language
import freeode.simlparser as simlparser


class ILTGenException(Exception):
    '''Exception thrown by the ILT-Process Generator (Compiler internal error)'''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)



class ILTProcessGenerator(object):
    '''
    Generate process for the intermediate language tree (ILT).

    Takes a process from the AST and generates a new process. This new process
    contains the attributes of all submodels. The code of the submodels' blocks
    is inserted (inlined) into the new process' blocks.
    The new process is a 'flattened' version of the original structured process.
    '''
    def __init__(self, astRoot):
        self.astRoot = astRoot
        '''The AST'''
        self.astClasses = {}
        '''dict of classes in ast: {'mod1':NodeClassDef}'''
        self.astProcess = NodeClassDef() #dummy for pydev's completion
        '''the original process that is now instantiated'''
        self.astProcessAttributes = {}
        '''Atributes of the original process. Dict: {('mod1', 'var1'):NodeDataDef}'''
        self.process = NodeClassDef() #dummy for pydev's completion
        '''The new process which is currently assembled'''
        self.processAttributes = {}
        '''Attributes of the new process: {('mod1', 'var1'):NodeDataDef}'''
        self.stateVariables = {}
        '''State variables of the new process; {('mod1', 'var1'):NodeDataDef}'''
        self.atomicClasses = set([('Real',),('Distribution',),('DistributionDomain',)])
        '''Classes that have no internal structure'''

        #populate self.classes and self.processes
        self.findClassesInAst()


    def findClassesInAst(self):
        '''
        Extract all class definitions from the ast and put them into self.classes.
        Additionally the process definitions go into self.processes.
        '''
        for classDef in self.astRoot:
            #check for duplicate classes
            if classDef.className in self.astClasses:
                raise UserException('Redefinition of class: %s'
                                    % str(classDef.className),
                                    classDef.loc)
            self.astClasses[classDef.className] = classDef 


    def addBuiltInParameters(self):
        '''
        Some parameters exist without beeing defined; create them here.

        -In a later stage they could be inherited from a base class.
        -This method could be expanded into a more general mechanism for
         built-in values, like pi.
        '''
        #Put solutionparameters as first attribute into the process
        solParAttr = NodeDataDef(loc=0, attrName=DotName('solutionParameters'),
                                 className=DotName('solutionParametersClass'))
        self.astProcess.insertChild(0, solParAttr)


    def findAttributesRecursive(self, astClass, namePrefix=DotName(), recursionDepth=0):
        '''
        Find all of the process' attributes (recursing into the sub-models)
        and put then into self.astProcessAttributes.

        Attributes are: parameters, variables, sub-models, and functions.
        The definition in the AST is searched NOT the new process.

        Arguments:
            astClass   : class definition from the AST (NodeClassDef),
                         or NodeDataDefMulti, NodeStmtList
            namePrefix : tuple of strings. Prefix for the dotted name of the
                         class' attributes.
        Output:
            self.astProcessAttributes : dict: {('mod1', 'var1'):NodeDataDef}
        '''
        #check recursion depth
        maxRecursionDepth = 100
        if recursionDepth > maxRecursionDepth:
            raise UserException('Maximum submodel nesting depth (%d) exeeded'
                                % maxRecursionDepth, astClass.loc)
        #each of the class' children is a definition or a list of definitions
        for attrDef in astClass:
            #inspect Node type
            #list of definitions - look into list: recurse
            if isinstance(attrDef, NodeStmtList):
                self.findAttributesRecursive(attrDef, namePrefix, #note same name prefix
                                             recursionDepth+1)
                continue #do not create an attribute for the list Node
            #definition of data attribute or submodel: get name, store attribute
            elif isinstance(attrDef, NodeDataDef):
                attrName = attrDef.name
            #definition of method (function): get name, store attribute
            elif isinstance(attrDef, NodeFuncDef):
                attrName = attrDef.name
            else:
                raise ILTGenException('Unknown Node.' + repr(attrDef))

            #store attribute in dict
            #prepend prefix to attribute name
            longAttrName = namePrefix + attrName
            #Check redefinition
            if longAttrName in self.astProcessAttributes:
                raise UserException('Redefinition of: ' +
                                    str(longAttrName), attrDef.loc)
            #put new attribute into dict.
            self.astProcessAttributes[longAttrName] = attrDef

            #recurse into submodel, if definition of submodel
            if isinstance(attrDef, NodeDataDef) and \
              (not attrDef.className in self.atomicClasses):
                #User visible error if class does not exist
                if not attrDef.className in self.astClasses:
                    raise UserException('Undefined class: '
                                        + str(attrDef.className),
                                        attrDef.loc)
                subModel = self.astClasses[attrDef.className]
                self.findAttributesRecursive(subModel, longAttrName,
                                             recursionDepth+1)


    def copyDataAttributes(self):
        '''
        Copy variables and parameters from all submodels into the procedure
        Additionally puts all attributes into self.processAttributes
        arguments:
        '''
        #Iterate over the (variable, parameter, submodel, function) definitions
        for longName, defStmt in self.astProcessAttributes.iteritems():
            #we only want atomic data! No user defined classes, no methods
            if (not isinstance(defStmt, NodeDataDef)) or \
               (not defStmt.className in self.atomicClasses):
                continue
            newAttr = defStmt.copy() #copy definition,
            newAttr.name = longName #exchange name with long name (a.b.c)
            self.process.appendChild(newAttr) #put new attribute into ILT process
            self.processAttributes[longName] = newAttr #and into quick access dict
        return


    def copyFuncRecursive(self, block, namePrefix, newBlock, illegalBlocks, recursionDepth=0):
        '''
        Copy block into newBlock recursively.
        Copies all statements of block and all statements of blocks that are
        executed in this block, recursively.
            block          : A block definition
            namePrefix     : a tuple of strings. prefix for all variable names.
            newBlock       : the statements are copied here
            illegalBlocks  : blocks (functions) that can not be called
                             (included) in this context.
        '''
        #Protect against infinite recursion
        maxRecursionDepth = 100
        if recursionDepth > maxRecursionDepth:
            raise UserException('Maximum function recursion depth (%d) exeeded'
                                % maxRecursionDepth, block.loc)
        for statement in block:
            #Block execution statement: insert the block's code
            if isinstance(statement, NodeFuncExecute):
                subBlockName = namePrefix + statement.name #dotted block name
                subModelName = subBlockName[:-1] #name of model, where block is defined
#                #Error if submodel or method does not exist
#                if not subModelName in self.astProcessAttributes:
#                    raise UserException('Undefined submodel: ' +
#                                        str(subModelName), statement.loc)
                if not subBlockName in self.astProcessAttributes:
                    raise UserException('Undefined method: ' +
                                        str(subBlockName), statement.loc)
                #Check if executing (inlining) this block is allowed
                if statement.name in illegalBlocks:
                    raise UserException('Function can not be called here: ' +
                                        str(statement.name), statement.loc)
                #Find definition of function
                subBlockDef = self.astProcessAttributes[subBlockName]
                #Check if subBlockDef is really a function definition
                if not isinstance(subBlockDef, NodeFuncDef):
                    raise UserException('Only functions can be called',
                                        statement.loc)
                #Recurse into the function definition.
                #Insert its text in place of the call statement
                self.copyFuncRecursive(subBlockDef, subModelName, newBlock,
                                       illegalBlocks, recursionDepth+1)
            #Any other statement: copy statement
            else:
                newStmt = statement.copy()
                #put prefix before all varible names in new Statement
                for var in newStmt.iterDepthFirst():
                    if not isinstance(var, NodeAttrAccess):
                        continue
                    newAttrName = namePrefix + var.name
                    var.name = newAttrName
                #put new statement into new block
                newBlock.appendChild(newStmt)


    def checkUndefindedReferences(self, tree):
        '''
        Look at all attribute accessors and see if the attributes exist in
        the new process.
        '''
        #iterate over all nodes in the syntax tree
        for node in tree.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            if not (node.name) in self.processAttributes:
                raise UserException('Undefined reference: ' +
                                    str(node.name), node.loc)



    def findStateVariables(self, dynamicMethod):
        '''
        Search for variables with a $ and mark them:
            1.: in their definition set role = RoleStateVariable;
            2.: put them into self.stateVariables.
        All other variables are considered algebraic variables and in their
        definition role = RoleAlgebraicVariable.
        Arguments:
            dynamicMethod : method definition that is searched (always the
                            dynamic/run method)
        output:
            self.stateVariables    : dict: {('a','b'):NodeDataDef(...)}
            definition of variable : role = RoleStateVariable if variable is
                                     state variable;
                                     role = RoleAlgebraicVariable otherwise.
        '''
        #initialization: in all variable definitions set role = RoleAlgebraicVariable
        for varDef in self.processAttributes.itervalues():
            if varDef.role != RoleVariable:
                continue
            varDef.role = RoleAlgebraicVariable
        #iterate over all nodes in the syntax tree and search for variable accesses
        for node in dynamicMethod.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            #State variables are those that have time derivatives
            if node.deriv != ('time',):
                continue
            #OK, there is a '$' operator; the thing is a state variable
            #get definition of variable
            stateVarDef = self.processAttributes[node.name]
            #Check conceptual constraint: no $parameter allowed
            if stateVarDef.role == RoleParameter:
                raise UserException('Parameters can not be state variables: ' +
                              str(node.name), node.loc)
            #remember: this is a state variable; in definition and in dict
            stateVarDef.role = RoleStateVariable
            self.stateVariables[node.name] = stateVarDef



    def findParameters(self):
        '''Search for parameters (in the new procress) and return a dict'''
        #attrDef = NodeDataDef()
        paramDict = {}
        #iterate over all nodes in the syntax tree and search for variable accesses
        for name, attrDef in self.processAttributes.iteritems():
            #we only want to see parameters
            if attrDef.role != RoleParameter:
                continue
            #put parameter definition in dict
            paramDict[name] = attrDef
        return paramDict



    def isPossibleParamPropagation(self, highParam, lowParam):
        '''
        Test for parameter propagation

        Example:
          propagate: mu   --> m1.mu, m2.mu
          propagate: m1.l --> m1.sm1.l, m1.sm2.l
          no       : m1.l --> m2.l, l

        Arguments:
            highParam : tuple of strings
            lowParam  : tuple of strings
        Return:
            True if propagation is possible.
            False otherwise.
        '''
        #name of high level parameter must be shorter (otherwise it
        #is not from higher level)
        if not (len(highParam) < len(lowParam)):
            return False
        #last parts of names must be same. (Propagate to parameters of same
        #name, but at lower level in hierarchy)
        if not (highParam[-1] == lowParam[-1]):
            return False
        #both parameters must start with same sequence
        #(both parameters must be from the same branch in the hierarchy)
        for i in range(0, len(highParam)-1):
            if not (highParam[i] == lowParam[i]):
                return False
        return True



    def propagateParameters(self, initMethod):
        '''
        Propagate parameter values from models high in the hierarchy to their
        sub-models. Both conditions must be true, for Parameter propagation to
        happen:
        1.: Both parameters have the same name (in high level model and in
            child model)
        2.: Parameter is not initialized in child model

        This is currently done by deleting parameters in the child models
        and accessing parameters in the high level models instead.

        Arguments:
            initMethod : Definition of init method in ILT; for identifying
                         those parameters that are initialized
        Output:
            Deletes parameters;
            changes attribute accessors, in whole process.
        '''
        parameters = self.findParameters()
        #classify parameters in: 1. explicitly initialized, 2. not initialized
        initedParams = set()
        for assignStmt in initMethod.iterDepthFirst():
            #we only want to look at assignments
            if not isinstance(assignStmt, NodeAssignment):
                continue
            #those assignments must assign values to parameters
            accPar = assignStmt.lhs
            if not accPar.name in parameters:
                continue
            #OK, this parameter is initialized, remember it
            initedParams.add(accPar.name)
        notInitedParams = set(parameters.keys()) - initedParams

        #for each initialized parametr: search for not initialized Parameter
        #to which the value can be propagated. (that has same name but is
        #deeper in the model hierarchy.)
        #Example:
        #  propagate: mu   --> m1.mu, m2.mu
        #  propagate: m1.l --> m1.sm1.l, m1.sm2.l
        #  no       : m1.l --> m2.l, l
        initedParams = list(initedParams)
        #start with the names with the most dots (defined deep in submodels)
        initedParams.sort(key=len, reverse=True)
        paramReplaceDict = {}
        for iPar in initedParams:
            for nPar in notInitedParams.copy():
                if self.isPossibleParamPropagation(iPar, nPar):
                    #we found parameter to rename
                    paramReplaceDict[nPar] = iPar #remember rename action
                    notInitedParams.remove(nPar)  #we cared for this parameter
        #print paramReplaceDict

        #raise error for all still uninitialized parameters
        if len(notInitedParams) > 0:
            msg = 'In process %s' % self.astProcess.className
            loc = self.astProcess.loc
            errList = [(msg, loc)]
            #mention all uninited params
            for nPar in notInitedParams:
                msg = 'Uninitialized prameter: %s' % str(parameters[nPar].name)
                loc = parameters[nPar].loc
                errList.append((msg, loc))
            raise MultiErrorException(errList)

        #rename all attribute accesses according to paramReplaceDict
        for accPar in self.process.iterDepthFirst():
            if not isinstance(accPar, NodeAttrAccess):
                continue
            oldParamName = accPar.name
            if not oldParamName in paramReplaceDict:
                continue
            accPar.name = paramReplaceDict[oldParamName]

        #delete replaced parameters
        for i in range(len(self.process)-1, -1, -1): #iterate backwards
            defPar = self.process[i]
            if not isinstance(defPar, NodeDataDef):
                continue
            parName = defPar.name
            if not parName in paramReplaceDict:
                continue
            del self.process[i]
            self.processAttributes.pop(parName)


    def checkDynamicMethodConstraints(self, block):
        '''See if the method is a valid dynamic method.'''
        #iterate over all nodes in the syntax tree and search for assignments
        for node in block.iterDepthFirst():
            if not isinstance(node, NodeAssignment):
                continue
            lVal = node.lhs #must be NodeValAccess
            lValDef = self.processAttributes[lVal.name]
            #No assignment to parameters
            if lValDef.role == RoleParameter:
                raise UserException('Illegal assignment to parameter: ' +
                                    str(lVal.name), lVal.loc)
            #No assignment to state variables - only to their time derivatives
            if lValDef.role == RoleStateVariable and (lVal.deriv != ('time',)):
                raise UserException('Illegal assignment to state variable: ' +
                                    str(lVal.name) +
                                    '. You must however assign to its time derivative. ($' +
                                    str(lVal.name) +')', lVal.loc)


    def checkInitMethodConstraints(self, block):
        '''See if the method is a valid init method.'''
        #iterate over all nodes in the syntax tree and search for variable accesses
        for node in block.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            #$ operators are illegal in init method
            if node.deriv == ('time',):
                raise UserException('Time derivation illegal in init: ' +
                                    str(node.name), node.loc)


    def modifyInitMethod(self, method):
        '''
        Modify init function for parameter value overriding

        Assignments to parameters are changed. The built in
        function 'overrideParam' is inserted:
        par1 = 5; ---> par1 = overrideParam('par1', 5);

        Override param looks into an overide dict and may return
        a new value for the parameter if it finds one in the
        override dict. Otherwise it returns the original value.
        '''
        parameters = self.findParameters()
        for assign in method.iterDepthFirst():
            #we only want to see assignments
            if not isinstance(assign, NodeAssignment):
                continue
            #the assignment must be to a parameter
            paramName = assign.lhs.name
            if not paramName in parameters:
                continue
            #OK: this is an assignment to a parameter
            loc = assign.loc
            #create the helper function for parameter overriding
            funcNode = NodeBuiltInFuncCall([], loc, 'overrideParam')
            paramNameNode = NodeString([], loc, str(paramName))
            origExprNode = assign.rhs
            funcNode.appendChild(paramNameNode)
            funcNode.appendChild(origExprNode)
            #use helper function as new rhs
            assign.rhs = funcNode


    def createProcess(self, inAstProc):
        '''generate ILT subtree for one process'''
        #store original process
        self.astProcess = inAstProc.copy()
        #init new process
        self.process = NodeClassDef()
        self.process.name = self.astProcess.name
        self.process.baseName = self.astProcess.baseName
        self.process.loc = self.astProcess.loc
        #init quick reference dicts
        self.processAttributes = {}
        self.astProcessAttributes = {}
        self.stateVariables = {}

        #add some built in attributes to the AST process
        #this will be gone once inheritance is implemented
        self.addBuiltInParameters()
        #discover all attributes
        self.findAttributesRecursive(self.astProcess, tuple())
        #create the new process' data attributes
        self.copyDataAttributes()

        #dynamic(...), init(...), final(...) are the prosess' main functions.
        #if they are not defined an empty function is created
        principalFuncs = set([DotName('dynamic'), DotName('init'),
                              DotName('final')])
        #create dynamic function
        dynamicFunc = NodeFuncDef(name=DotName('dynamic')) #create empty function
        self.process.appendChild(dynamicFunc) #put new function into process
        #if function is defined in the AST, copy it into the new ILT function
        if DotName('dynamic') in self.astProcessAttributes:
            #set of functions that should not appear in dynamic function
            illegalFuncs = principalFuncs - set([DotName('dynamic')]) \
                           | set([DotName('load'), DotName('store'),
                                  DotName('graph',)])
            #copy the function's statements from AST to ILT; recursive
            self.copyFuncRecursive(self.astProcessAttributes[DotName('dynamic')],
                                   DotName(), dynamicFunc, illegalFuncs)
        #create init function
        initFunc = NodeFuncDef(name=DotName('init'))
        self.process.appendChild(initFunc) #put new block into process
        if DotName('init') in self.astProcessAttributes:
            illegalFuncs = principalFuncs - set([DotName('init')])
            self.copyFuncRecursive(self.astProcessAttributes[DotName('init')],
                                   DotName(), initFunc, illegalFuncs)
        #create final function
        finalFunc = NodeFuncDef(name=DotName('final'))
        self.process.appendChild(finalFunc) #put new block into process
        if DotName('final') in self.astProcessAttributes:
            illegalFuncs = principalFuncs - set([DotName('final')])
            self.copyFuncRecursive(self.astProcessAttributes[DotName('final')],
                                   DotName(), finalFunc, illegalFuncs)

        self.checkUndefindedReferences(self.process) #Check undefined reference
        self.findStateVariables(dynamicFunc) #Mark state variables
        self.propagateParameters(initFunc) #rename some parameters
        self.checkDynamicMethodConstraints(dynamicFunc)
        self.checkInitMethodConstraints(initFunc)

        #TODO: Check correct order of assignments (or initialization).
        #TODO: Check if all parameters and state vars have been initialized.
        #TODO: Check if any variable name is equal to a keyword. (in findAttributesRecursive)

        #Modify init function for parameter value overriding
        self.modifyInitMethod(initFunc)

        return self.process



class ILTGenerator(object):
    '''
    Generate a tree that represents the intermediate language.
    intermediate language tree (ILT)
    '''

    def __init__(self):
        super(ILTGenerator, self).__init__()


    def addBuiltInClasses(self, astRoot):
        '''
        Some classes exist without beeing defined; create them here.

        -This method could be expanded into a more general mechanism for
         built-in values and functions, like pi, sin(x).
        '''
        #Create the solution parameters' definition
        solPars = NodeClassDef(loc=0,
                               className=DotName('solutionParametersClass'),
                               superName=DotName('Model'))
        solPars.appendChild(NodeDataDef(loc=0,
                                        attrName=DotName('simulationTime'),
                                        className=DotName('Real'),
                                        role=RoleParameter))
        solPars.appendChild(NodeDataDef(loc=0,
                                        attrName=DotName('reportingInterval'),
                                        className=DotName('Real'),
                                        role=RoleParameter))
        #add solutionparameTers to AST, and update class dict
        astRoot.insertChild(0, solPars)


    def createIntermediateTree(self, astRoot):
        '''generate ILT tree from AST tree'''
        #add built ins to AST
        self.addBuiltInClasses(astRoot)
#        #possible replacements in ech class of ast
#        self.replaceMultiAttributeDefinitions(astRoot)
#        print astRoot
        #create ILT root node
        iltRoot = NodeModule()
        iltRoot.loc = astRoot.loc

        procGen = ILTProcessGenerator(astRoot)
        #search for processes in the AST and instantiate them in the ILT
        for processDef in astRoot:
            if ((not isinstance(processDef, NodeClassDef)) or
                (not processDef.superName == DotName('Process'))):
                continue
            newProc = procGen.createProcess(processDef)
            iltRoot.appendChild(newProc)
        #warnig if no code was generated
        if len(iltRoot) == 0:
            print 'Warnig: program contains no "Process" objects. ' + \
                  'No simulation code is generated.'

        return iltRoot



#--------------- new intermediate tree creation ----------------------------------
#TODO: better and shorter handling of common errors 
class UserDuplicateAttributeError(UserException):
    '''User visible duplicate attribute error.'''
    def __init__(self, msg='Duplicate attribute: ', attrName=None, loc=None):
        msgComplete = msg + str(attrName) if attrName is not None else msg
        UserException.__init__(self, msgComplete, loc)

class UserUndefinedAttributeError(UserException):
    '''User visible undefined attribute error.'''
    def __init__(self, msg='Undefined attribute: ', attrName=None, loc=None):
        msgComplete = msg + str(attrName) if attrName is not None else msg
        UserException.__init__(self, msgComplete, loc)
        
        

class ProgramTreeCreator(Visitor):
    '''
    Create the AST for the whole program.
    
    Calls the parser; no separate calls to parser necessary.
    
    Usage:
        ptc = ProgramTreeCreator()
        ptc.importMainModule('myfile.siml')
    '''
    
    def __init__(self):
        Visitor.__init__(self)
        #cache for imported modules
        self.moduleCache = {}
        #main module - the root of program tree
        self.mainModule = None
        #trees for flattening - the output
        self.compileObjects = []
        #the built in library (treated specially)
        self.builtInLib = None
        bLib = simlstdlib.createParseTree()
        self.visitModule(bLib)
        self.builtInLib = bLib
        
        
    @staticmethod
    def flattenMultiDataDefs(tree):
        '''
        Take data definitions out of statement lists.
        
        Data definitions of the form:
            data a,b,c: Real;
        are in statement special lists. This funciton takes them out and 
        places them in the top level or class body.
        
        The function calls itself recursively.
        
        Parameters
        ----------
        tree : ast.Node
            A piece of a parse tree. It must be a program or a class definiton
            to be useful. The argument is modified.
        ''' 
        i = 0
        while i < len(tree):
            node = tree[i]
            if isinstance(node, NodeDataDefList):
                #this is a multiple definition
                #copy data statements, delete list, correct index
                tree.insertChildren(i+1, node)
                del tree[i]
                i += len(node) - 1
            elif isinstance(node, NodeClassDef):
                #this is a class definition: recurse
                ProgramTreeCreator.flattenMultiDataDefs(node)
            elif isinstance(node, NodeFuncDef):
                #this is a function definition: recurse
                ProgramTreeCreator.flattenMultiDataDefs(node.body)
            i += 1


    @staticmethod
    def setDataRoleDefault(tree):
        '''
        Put default roles into data definitions that don't define roles.
        
        The default roles are different depending on where the data is 
        defined:
        module (top level): constant
        class             : variable (state or algebraic is determined later)
        function          : local variable
        
        The function calls itself recursively.
        
        Parameters
        ----------
        tree : ast.Node
            A piece of a parse tree. It must be a program or a class definiton
            to be useful. The argument is modified.
        '''
        #TODO: put functionality into interpreter?
        #determine the default role for the current subtree
        if isinstance(tree, NodeModule):
            defaultRole = RoleConstant
        elif isinstance(tree, NodeClassDef):
            defaultRole = RoleVariable
        elif isinstance(tree, NodeFuncDef):
            defaultRole = RoleLocalVariable
        else:
            raise Exception('Unexpected node type: ' + str(type(tree)))
        #go through children, set role or recurse
        for child in tree:
            if isinstance(child, NodeDataDef) and child.role is None:
                child.role = defaultRole
            #recurse into subtrees, where data can be defined
            elif isinstance(child, (NodeModule, NodeClassDef, NodeFuncDef)):
                ProgramTreeCreator.setDataRoleDefault(child)
             
        
    @Visitor.when_type(NodeForeignCodeStmt)
    def visitForeignCodeStmt(self, foreignCodeStmt, stmtContainer, environment):
        '''Interpret NodeForeignCodeStmt.'''
        print 'visiting NodeForeignCodeStmt: '
        
    @Visitor.when_type(NodePragmaStmt)
    def visitPragmaStmt(self, pragmaStmt, stmtContainer, environment):
        '''Interpret pragma statement.'''
        print 'visiting pragma: ', pragmaStmt      
        
    @Visitor.when_type(NodeGraphStmt)
    def visitGraphStmt(self, graphStmt, stmtContainer, environment):
        '''Interpret graph statement.'''
        print 'interpreting graph statement: '
        for expr in graphStmt:
            self.checkExpression(expr, (AttributeRole,), stmtContainer, environment)
           
    @Visitor.when_type(NodeStoreStmt)
    def visitStoreStmt(self, storeStmt, stmtContainer, environment):
        '''Interpret store statement.'''
        print 'interpreting store statement: '
        for expr in storeStmt:
            self.checkExpression(expr, (AttributeRole,), stmtContainer, environment)
    
    @Visitor.when_type(NodePrintStmt)
    def visitPrintStmt(self, printStmt, stmtContainer, environment):
        '''Interpret print statement.'''
        print 'interpreting print statement: '
        for expr in printStmt:
            self.checkExpression(expr, (AttributeRole,), stmtContainer, environment)
    
    @Visitor.when_type(NodeReturnStmt)
    def visitReturnStmt(self, printStmt, stmtContainer, environment):
        '''Interpret return statement.'''
        print 'interpreting return statement: '
        raise Exception('Implementation missing!')
    
    @Visitor.when_type(NodeIfStmt)
    def visitIfStmt(self, ifStmt, stmtContainer, environment):
        '''Interpret if ... elif ... else ... statement.'''
        print 'interpreting if statement: '
        for i in range(0, len(ifStmt), 2):
            condition = ifStmt[i]
            statements = ifStmt[i+1]
            #TODO: better design to constrain arrtibute access with different 
            #      attribute roles necessary: 
            #      When computing constants (on module level) an 'if' statement
            #      must not use variables anywhere.
            self.checkExpression(condition, (AttributeRole,), stmtContainer, environment)
            for stmt in statements:
                self.dispatch(stmt, stmtContainer, environment)

    
    @Visitor.when_type(NodeClassDef)
    def visitClassDef(self, classDef, stmtContainer, environment):
        '''Interpret class definition statement.'''
        print 'visiting class def: ', classDef.name
        try:
            #add the class definition to the namespace
            stmtContainer.setAttr(classDef.name, classDef)
            #find base class
            #with special case for class "Object" which has no base class.
            if classDef.baseName is not None: 
                classDef.base = environment.findDotName(classDef.baseName)
            #store the environment - will de used by data statements
            classDef.defEnvironment = environment
            
            #Look at the class body statements 
            for stmt in classDef:
                if isinstance(stmt, NodePragmaStmt):
                    #interpret pragmas.
                    if stmt.options[0] == 'built_in_type':
                        classDef.isBuiltinType = True
                    elif stmt.options[0] == 'no_flatten':
                        classDef.noFlatten = True
                elif isinstance(stmt, NodeFuncDef):
                    #interpret function definitions
                    self.visitFuncDef(stmt, classDef, environment)
                    
        except DuplicateAttributeError, error:
            raise UserDuplicateAttributeError(attrName=error.attrName, 
                                              loc=classDef.loc)
        except UndefinedAttributeError, error:
            raise UserUndefinedAttributeError(attrName=error.attrName, 
                                              loc=classDef.loc)
    
    
    @Visitor.when_type(NodeGenFunc, 2)
    def visitGenFunc(self, _funcGen, _stmtContainer, _environment):
        '''Do nothing. These nodes are generated during the compilation.'''
        print 'visiting generated code: ', _funcGen.name
        
    @Visitor.when_type(NodeFuncDef)
    def visitFuncDef(self, funcDef, stmtContainer, environment):
        '''
        Interpret function definition statement.
        
        NodeFuncDef should only be processed in class definition; 
        processing it in data tree expansion will process it multiple times.
        The individual function objects for flattening must be created 
        when NodeFuncExecute is processed.
        '''
        print 'interpreting func def: ', funcDef.name
        #put function into module or class, store global scope
        stmtContainer.setFuncAttr(funcDef.name, funcDef) 
        #functions are executed in the global scope where they are defined.       
        funcDef.environment.globalScope = environment.globalScope

        if isinstance(stmtContainer, NodeClassDef):
            #create "this" pointer and put into argument list
            if len(funcDef.argList) == 0 or \
               funcDef.argList[0].name != 'this':
                thisArgument = NodeDataDef(name='this', loc=funcDef.loc,
                                           role=RoleFuncArgument)
                funcDef.argList.insertChild(0, thisArgument)
            #TODO: give correct type to "this"
            #TODO: a reference or pointer type is necessary
            funcDef.argList[0].className = stmtContainer.name
            
        #Parse pragmas. (For built in functions)
        for stmt in funcDef.body:
            if not isinstance(stmt, NodePragmaStmt):
                continue
            if stmt.options[0] == 'built_in_func':
                funcDef.isBuiltIn = True
        return


    @Visitor.when_type(NodeFuncExecute)
    def visitFuncExecute(self, funcCall, stmtContainer, environment):
        '''Interpret function call.'''
        print 'interpreting function call'
        try:
            funcName = funcCall.name
            #Find the function definition - the template for creating the function
            multiFunc = environment.findDotName(funcName)
            if not isinstance(multiFunc, FunctionOverloadingResolver):
                raise UserException('Object is not callable: ' + str(funcName), 
                                    funcCall.loc)
            #Distinguish: function <-> instance method
            #Get the object that contains the function/method
            if len(funcName) >= 2:
                #name with dots - take part left of last dot
                funcParent = environment.findDotName(funcName[0:-1])
            elif environment.localScope.findDotName(funcName, None) is not None:
                #local (nested) function - future extension
                funcParent = environment.localScope
            elif environment.thisScope.findDotName(funcName, None) is not None:
                #member function of same class
                funcParent = environment.thisScope 
            elif environment.globalScope.findDotName(funcName, None) is not None:
                funcParent = environment.globalScope            
            #Prepend "this" pointer if it is call to member function
            #and remember "this" namespace
            if isinstance(funcParent, NodeDataDef):
                #Yes it is a member function (instance method)
                thisScope = funcParent
                #TODO: put useful reference to 'this' into 'this'-pointer
                #      needs pointer/reference implementation 
                thisPointer = NodeAttrAccess(name=funcCall.name[:-1], 
                                             loc=funcCall.loc)
                funcCall.insertChild(0, thisPointer)
            elif isinstance(funcParent, NodeClassDef):
                #TODO: this pointer is taken from function arguments
                #      needs pointer/reference implementation 
                thisPointer = funcCall[0].value
                raise Exception('Pointer/Reference implementation missing!')
            else:
                thisScope = None
            #get the correct overloaded function
            funcDef = multiFunc.resolve(funcCall)        
            #stop processing for built in functions.
            if funcDef.isBuiltIn:
                return
            
            #Create new function object 
            newFunc = NodeGenFunc(name=funcDef.name, loc=funcDef.loc, 
                                  returnType=funcDef.returnType)
            newFunc.argList = funcDef.argList.copy()
            newFunc.body = funcDef.body.copy()
            #put copied function into "this" object or into module
            funcParent.body.appendChild(newFunc)
            #funcParent.setFuncAttr(newFunc.name, newFunc) ????
            #Put pointer to function into NodeFuncCall (to easily find it for flattening)
            funcCall.attrRef = newFunc
     
            #Set up execution environment for the function
            newFunc.environment.globalScope = funcDef.environment.globalScope
            newFunc.environment.thisScope = thisScope
            newFunc.environment.localScope = NameSpace()
            
            #TODO create a NodeDataDef for each function argument
    #        #TODO: put function arguments into function's local namespace
    #        for argDef in funcDef.argList:
    #            if namespace.hasAttr(argDef.name):
    #                raise UserException('Duplicate function argument: ' +
    #                                    str(argDef.name), funcDef.loc)
    #            funcDef.setAttr(argDef.name, argDef)
    
            #TODO: pass the function's arguments: Create an assignment for each argument
    
            #visit the function's code
            for stmt in newFunc.body:
                self.dispatch(stmt, newFunc, newFunc.environment)
            return
        except UndefinedAttributeError, error:
            raise UserUndefinedAttributeError(attrName=error.attrName, 
                                              loc=funcCall.loc)
        
        
    @Visitor.when_type(NodeCompileStmt, 2)
    def visitCompileStmt(self, compileStmt, stmtContainer, environment):
        '''Interpret compile statement.'''
        print 'interpreting compile statement'
        try:
            #create name if none given
            if compileStmt.name is None:
                compileStmt.name = 'simulation' + '_'.join(compileStmt.className)
                print ('Creating name for compiled object because none given: ' 
                       + compileStmt.name)
            #put compiled object into global namespace
            #TODO: better solution to make names of compiled objects unique
            #TODO: better solution look up attributes of compiled object
            stmtContainer.setAttr(compileStmt.name, compileStmt)
            #Find the class definition - the template for creating the compiled object
            classDef = environment.findDotName(compileStmt.className)
    
            #Create recursive data definitions that contain only base types. 
            #Same like "data" statement
            self.createDataDefTreeRecursive(compileStmt, classDef)
    
            #search for pragmas that declare the main functions
            #Pragmas were copied from class definition (createDataDefTreeRecursive)
            mainFuncNames = []
            for pragma in compileStmt.body:
                if isinstance(pragma, NodePragmaStmt) and \
                   pragma.options[0] == 'compile_main_function':
                    mainFuncNames.append(pragma.options[1])
            #TODO: automatically call/generate the main functions in all
            #      suitable objects (models).
            #TODO: How can the flattening algorithm find the automatically
            #      generated code? How can this code be put into the right 
            #      flattened main function?
            #call the main functions from the global namespace
            #this will create the main functions and will recursively 
            #create all functions called by each main function.
            for funcName in mainFuncNames:
                funcDotName = DotName((compileStmt.name, funcName))
                funcCall = NodeFuncExecute(name=funcDotName)
                self.visitFuncExecute(funcCall, stmtContainer, environment) 
                #remember generated main function in separate list
                compileStmt.mainFuncs.append(funcCall.attrRef)
            #put the expanded object into the results list
            self.compileObjects.append(compileStmt)
        except DuplicateAttributeError, error:
            raise UserDuplicateAttributeError(attrName=error.attrName, 
                                              loc=compileStmt.loc)
        except UndefinedAttributeError, error:
            raise UserUndefinedAttributeError(attrName=error.attrName, 
                                              loc=compileStmt.loc)

    
    @Visitor.when_type(NodeDataDef)
    def visitDataDef(self, dataDef, stmtContainer, environment):
        '''Interpret data definition statement.'''
        print 'interpreting data def: ', dataDef.name
        try:
            #TODO: New design necessary for local variables in functions.
            #      setAttr(...) should be called in top namespace of environment?
            #put symbol into namespace, 
            stmtContainer.setAttr(dataDef.name, dataDef)
            #Find the class definition - the template for creating the data definition
            classDef = environment.findDotName(dataDef.className)
            #TODO: Create pointers to class definitions? 
            #      - unnecessary data is expanded.
            #      - usefull for type checking (implementation of isinstance())
            
            #Data at the top level of a module must be constant.
            if isinstance(stmtContainer, NodeModule) and \
               dataDef.role != RoleConstant:
                raise UserException('Module data must have role "const"!',
                                     dataDef.loc)
            #Copy flags
            dataDef.isBuiltinType = classDef.isBuiltinType
            dataDef.noFlatten = classDef.noFlatten
            #Create recursive definitions that contain only base types.
            #Built in types however are not expanded (one can not see into them).
            if not classDef.isBuiltinType: # and not classDef.isReference
                self.createDataDefTreeRecursive(dataDef, classDef)
            
            #TODO: if data root is const all recursive attributes must be const?
            #TODO: if data root is parameter all recursive attributes must be parameter?
        except DuplicateAttributeError, error:
            raise UserDuplicateAttributeError(attrName=error.attrName, 
                                        loc=dataDef.loc)
        except UndefinedAttributeError, error:
            raise UserUndefinedAttributeError(attrName=error.attrName, 
                                        loc=dataDef.loc)
        
            
    def createDataDefTreeRecursive(self, ioDataDef, classDef):
        '''
        Create recursive data definitions that contain only base types.
        
        Arguments
        ---------
        ioDataDef : NodeDataDef
            The data statement that is expanded to a tree. The function's 
            result is in ioDataDef.
        classDef : NodeClassDef
            The type of the data. All statements from the class definition
            are copied into ioDataDef and the data statemnts are themselfs
            expanded.
        '''
        #Copy and interpret the base class' statements recursively.
        #The inherited statements are accumulating in ioDataDef.statements.
        #The attribute names are accumulating in ioDataDef's namespace as well
        if classDef.base is not None:
            self.createDataDefTreeRecursive(ioDataDef, classDef.base)
        
        #Copy all definitions out of the class definition
        #Assignments are only referenced, functions are omitted 
        #they only get into namespace
        classBodyStmts = NodeStmtList()
        for stmt in classDef:
            if isinstance(stmt, NodeDataDef):
                classBodyStmts.appendChild(stmt.copy())
            elif isinstance(stmt, NodeFuncDef):
                #put functions into name space, but do not copy and interpret 
                ioDataDef.setFuncAttr(stmt.name, stmt)
            else:
                classBodyStmts.appendChild(stmt)
        
        #Interpret the copied statements ----------------------------
        # Use the global scope where the class was defined.
        # The definition of a (base) class might be in an other module than
        # the data statement, and might therefore have an other global scope.
        environment = ExecutionEnvironment()
        environment.globalScope = classDef.defEnvironment.globalScope
        environment.localScope = ioDataDef
        #interpret each statement, the definitions are expanded recursively
        for stmt in classBodyStmts:
            self.dispatch(stmt, ioDataDef, environment)
           
        #put the interpreted (and expanded) statements into the data definition
        ioDataDef.body.insertChildren(len(ioDataDef.body), 
                                            classBodyStmts)
        return
            
    
    def checkAttrAccess(self, attrAccess, environment):
        '''
        Retrieve the accessed NodeDataDef. 
        
        Throw user errors if necessary. Store pointer to NodeDataDef.
        '''
        attrDef = environment.findDotName(attrAccess.name, None)
        if attrDef is None:
            raise UserException('Undefined data: ' + 
                                str(attrAccess.name), attrAccess.loc)
        if not isinstance(attrDef, NodeDataDef):
            raise UserException('Only data can be assigned: ' +
                                str(attrAccess.name), attrAccess.loc)
        #store pointer to attribute in NodeAttrAccess
        attrAccess.attrRef = attrDef
        return attrDef

    
    def checkExpression(self, expression, legalRoles, stmtContainer, environment):   
        '''
        Check an expression and store some annotations.
        
        As a side effect called functions are emitted.
        TODO: this ad hoc function should be replace by an object, 
              that does in a detailed analysis of the expression.
        ''' 
        #TODO: test type compatibility of operands.
        #TODO: test unit compatibility of operands.
        #Check existence of attributes, correct roles of attributes
        for node in expression.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            rhsData = self.checkAttrAccess(node, environment)
            if not issubclass(rhsData.role, legalRoles):
                raise UserException('Illegal role! role: %s, data: %s' % 
                                    (rhsData.role.userStr, str(node.name)), 
                                    expression.loc)
        #Check existence of functions, check correct function arguments
        for node in expression.iterDepthFirst():
            if not isinstance(node, NodeFuncExecute):
                continue
            self.visitFuncExecute(node, stmtContainer, environment)
        
        
    @Visitor.when_type(NodeAssignment)
    def visitAssignment(self, assignment, stmtContainer, environment):
        '''Interpret assignment statement.'''
        print 'interpreting assignment: ', assignment.lhs
        #Check LHS --------------------
        #TODO: automatic creation of local variables in functions
        #TODO: put into function checkAttrAccess
        lhsData = self.checkAttrAccess(assignment.lhs, environment)
        #TODO: better design to constrain arrtibute access with different 
        #      attribute roles necessary: maybe introduce:
        #      self.lhsRoles, self.rhsRoles ,  (self.environmentStack)?
        #Roles describe when the data is computed
        lhsRole = lhsData.role
        if lhsRole == RoleFuncArgument:
            raise UserException('Function arguments are read only: ' +
                                str(assignment.lhs.name), assignment.loc)            
        if lhsRole == RoleConstant:
            rhsLegalRoles = (RoleConstant,)
        elif lhsRole == RoleParameter:
            rhsLegalRoles = (RoleConstant, RoleParameter)
        else:
            rhsLegalRoles = (RoleConstant, RoleParameter, RoleDataCanVaryDuringSimulation)
        #TODO:Check type compatibility
        #lhsClass = namespace.findDotName(lhsData.className)
        
        #Check RHS -------------------------
        #Check existence of attributes, correct roles of data
        self.checkExpression(assignment.rhs, rhsLegalRoles, stmtContainer, environment)
        #TODO: compute the constant expression, and replace the contents of the instance object?
        #TODO: constant computations are collected and put into a special method: __initConstants__?
        #TODO: perform the assignment for trivial cases (a=42)
        #      Important for pointers; dependencies between grids and distributions
        return
    
        
    @Visitor.when_type(NodeImportStmt)
    def visitImportStmt(self, importStmt, stmtContainer, environment):
        '''Interpret import statement.'''
        moduleName = importStmt.moduleName
#        moduleTree = importStmt.kids[0]
        print 'visiting import: ', moduleName
        try:
            #read module from file
            #TODO: implement packages
            #TODO: implement list of directories for searching files
            modNameStr = str(moduleName)
            moduleTree = self.importModuleFile(modNameStr + '.siml', modNameStr)
            #put the imported attributes into our namespace
            if importStmt.fromStmt == True:
                #behave like Python from statement
                #TODO implement selecting individual attributes from the package
                #TODO implement 'as' keyword
                #currently 'from moduleTree import *' behavior
                stmtContainer.update(moduleTree)
            else:
                #behave like Python import statement
                #TODO implement 'as' keyword
                stmtContainer.setAttr(moduleName, moduleTree)
        except DuplicateAttributeError, theErr:
            raise UserException('Duplicate attribute definition while '
                                'importing module "%s". ' 
                                'Duplicate Attribute: "%s".'
                                % (str(moduleName), 
                                   str(theErr.attrName)), 
                                importStmt.loc)
            
        
    def visitModule(self, moduleTree):
        '''
        Import a module given as a parse tree.
        
        This function performs the semantic analysis and creates the complete 
        program tree from multiple modules. The function interprets the 
        statements at the module level.
        The function may call itself recursively.
        
        Parameters
        ----------
        moduleTree : ast.Node
            The module's parse tree, the output of 
            simlparser.Parser.parseModuleStr(...).
            This tree will be modified in place to become the program tree.
    
        Returns
        -------
        moduleTree : ast.Node
            The modifed input tree; AST of a module. 
            Will be assembled into a complete program tree.
        '''
        #flatten data a,b,c: Real; into tree separate definitions.
        self.flattenMultiDataDefs(moduleTree)
        #Give default data roles to definitions where role==None
        self.setDataRoleDefault(moduleTree)
        #Put built in symbols into each module's namespace as if the 
        #first statement was: from builtinlib import *  
        #This way the built in library can be processed by this method too.
        if self.builtInLib is not None:
            moduleTree.update(self.builtInLib)
        #create module (global) namespace
        environment = ExecutionEnvironment()
        environment.globalScope = moduleTree
        #interpret module nodes
        for node in moduleTree:
            self.dispatch(node, moduleTree, environment)
        return
        
        
    def importModuleFile(self, fileName, moduleName=None):
        '''
        Import a module (program file).
        
        Semantic analysis is performed by self.visitModule(...).
        Modules are cached, and their AST is constucted only once, 
        even when they are imported multiple times.
        The function is recursively executed for each import statement.
        
        Parameters
        ----------
        fileName : str
            The module's file name. The module's text is read from this file.
        moduleName : str
            Name of module, will be put into NodeModule().name attribute.
    
        Returns
        -------
        moduleTree : ast.Node
            AST of a module. Will be assembled into a complete program tree.
        '''
        absFileName = os.path.abspath(fileName)
        #Test if tree is in cache and return cached tree if yes
        if absFileName in self.moduleCache:
            return self.moduleCache[absFileName]
        #open and read the file
        try:
            inputFile = open(absFileName, 'r')
            inputFileContents = inputFile.read()
            inputFile.close()
        except IOError, theError:
            message = 'Could not read input file.\n' + str(theError)
            raise UserException(message, None)
        #parse the program
        parser = simlparser.Parser()
        parseTree = parser.parseModuleStr(inputFileContents, fileName, moduleName) 
        #do semantic analysis and decorate tree
        self.visitModule(parseTree)
        #put tree in cache
        self.moduleCache[absFileName] = parseTree
        return parseTree
        
        
#    def importModuleStr(self, moduleStr, fileName=None, moduleName=None):
#        '''
#        Import a module (program file) as a string.
#        Convenience function for development. (See self.importModuleFile)
#               
#        Parameters
#        moduleStr : str
#            The module's (program's) text.
#        fileName : str
#            The module's file name, used for generating error messages.
#        moduleName : str
#            Name of module, will be put into NodeModule().name attribute.
#    
#        Returns
#        moduleTree : ast.Node
#            AST of a module. Will be assembled into a complete program tree.
#        '''
#        parser = simlparser.Parser()
#        parseTree = parser.parseModuleStr(moduleStr, fileName, moduleName) 
#        self.visitModule(parseTree)
#        return parseTree


    def importMainModule(self, fileName=None, moduleContentStr=None):
        '''
        Compile the SIML program's main module. 
        
        Main entry point to generate the program tree. When the function returns 
        this parse stage is finished. The compilation result is stored in 
        self.mainModule and self.compileObjects .
        
        Programs can be entered as files on the local disks, or as strings that
        contain the program text.
        
        Parameters
        ----------
        fileName : str
            The module's file name. The module's text is read from this file.
        moduleContentStr : str
            The module's (program's) text. Alternative method to enter the 
            program text (for debuging).
        
        Returns
        -------
        moduleTree : ast.Node
            The program tree, result of this parse stage. Same as self.mainModule
        '''
        moduleName = '__main__'
        if moduleContentStr is not None:
            #The program text is given as a string.
            parser = simlparser.Parser()
            programTree = parser.parseModuleStr(moduleContentStr, fileName, moduleName) 
            self.visitModule(programTree)
        else:
            #Read the program text from a file.
            programTree = self.importModuleFile(fileName, moduleName)
        #put import statement for 'builtinlib' module into '__main__' module.
        #Needed to give long names to built in symbols for flattening
        importStmt = NodeImportStmt(moduleName='builtin', fromStmt=True, 
                                    attrsToImport=["*"], loc=programTree.loc, 
                                    kids=[self.builtInLib])
        programTree.insertChild(0, importStmt)
        #store main module
        self.mainModule = programTree
        return
            

class ProgramTreeFlattener(object):
    '''Class to flatten the program tree'''
    
    def __init__(self):
        #program tree which is translated
        self.mainModule = None
        #count generated code objects with same (function) name
        #to give the generated objects unique names
        self.funcCount = {}
        self.deepTree = None
        self.flatTree = None

    
    def importProgramTree(self, mainModule):
        '''
        Store program tree and prepare it for flattening.
        Creates long names, that are used in the flat namespace.
        Alters program tree.
        '''
        self.mainModule = mainModule
        
        self.funcCount.clear()
        self.createLongNames(mainModule)
        self.funcCount.clear()
        
        self.flatTree = NodeFlatModule()
        self.flattenDataTree(self.mainModule)
        

    def createLongNames(self, dataContainer, prefix=DotName()):
        '''
        Create the long attribute names that will be used after flattening.
        The long names are stored in the targetName attribute.
        '''
        for node in dataContainer:
            if isinstance(node, NodeImportStmt):
                module = node[0]
                module.targetName = prefix + module.name
                self.createLongNames(module, module.targetName)
            elif isinstance(node, NodeDataDef):
                node.targetName = prefix + node.name
                self.createLongNames(node.body, node.targetName)
            elif isinstance(node, NodeGenFunc):
                #Each function expansion/invocation needs a unique name
                #count functions with the same name
                targetNameGeneral = prefix + node.name
                num = self.funcCount.get(targetNameGeneral, 0)
                self.funcCount[targetNameGeneral] = num + 1
                #append '#'+number to make name unique
                targetNameUnique = prefix + (str(node.name) + '#' + str(num))
                node.targetName = targetNameUnique
                #give (unique) long names to local variables
                self.createLongNames(node.body, node.targetName)
        return
    
     
    def flattenDataTree(self, dataContainer):
        for node in dataContainer:
            if isinstance(node, NodeImportStmt):
                module = node[0]
            elif isinstance(node, NodeDataDef):
                pass
            elif isinstance(node, NodeGenFunc):
                #TODO how should local variables from different compile 
                #     statements be distinguished.
                pass
        return
    
    
    def flattenCodeTree(self):
        pass
        
        
        
def doTests():
    '''Perform various tests.'''

#------------ testProg1 -----------------------
    testProg1 = (
'''
class Test(Model):
{
    data V, h, q: Real;
    data A_bott, A_o, mu, g: Real param;

    func dynamic():
    {
        h = V/A_bott;
        $V = q - mu*A_o*sqrt(2*g*h);
        print 'h: ', h,;
    }

    func init():
    {
        V = 0;
        A_bott = 1; A_o = 0.02; mu = 0.55;
    }
}

class RunTest(Process):
{
    #TODO: the following line creates error in pyparsing:
    #data time: Real;
    data time1: Real;
    data g: Real param;
    data test: Test;

    func dynamic():
    {
        $time1 = 1;
        if time1 < 10:{
            test.q = 0.01;}
        else:{
            test.q = 0.03;}
        test.dynamic();
    }
    func init():
    {
        g = 9.81;
        test.init();
        solutionParameters.simulationTime = 100;
        solutionParameters.reportingInterval = 1;
    }
    func final():
    {
        save 'test1';
        graph test.V, test.h;
        print 'Simulation finished successfully.';
    }
}

#data r: RunTest;
compile RunTest;
''' )

#------------ testProg2 -----------------------
    testProg2 = (
'''
class Foo(Model):
{   
    data r, s: Real;
    func foo1(): 
    { 
        r = 1;
    }
}

class Bar(Process):
{   
    data a, b: Real;
    #data f1, f2: Foo;
    
    func init(): 
    {
        a = sqrt(2)+sqrt(3);
        b = a;
    }
    
    func dynamic(): 
    {
        #init();
        #f1.foo1();
    }
    
    func final(): {}
}

compile bar1: Bar;
''' )

    #test the intermedite tree generator ------------------------------------------------------------------
    flagTestILTGenerator = False
    #flagTestILTGenerator = True
    if flagTestILTGenerator:
        parser = simlparser.Parser()
        #iltGen = ILTGenerator()

        astTree = parser.parseModuleStr(testProg2)
        print 'AST tree:'
        print astTree

#        iltTree = iltGen.createIntermediateTree(astTree)
#        print 'ILT tree:'
#        print iltTree

    #test program 2 ------------------------------------------------------------------
    flagTestProg2 = False
    flagTestProg2 = True
    if flagTestProg2:
        tc = ProgramTreeCreator()
        tc.importMainModule(moduleContentStr=testProg1)
        
        tf = ProgramTreeFlattener()
        tf.importProgramTree(tc.mainModule)
        
        print 'AST tree:'
        print tc.mainModule

#        iltTree = iltGen.createIntermediateTree(astTree)
#        print 'ILT tree:'
#        print iltTree



if __name__ == '__main__':
    # Self-testing code goes here.
    #TODO: add unit tests
    #TODO: add doctest tests. With doctest tests are embedded in the documentation

    doTests()
else:
    # This will be executed in case the
    #    source has been imported as a
    #    module.
    pass
