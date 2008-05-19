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
        '''Atributes of the original process. Dict: {('mod1', 'var1'):NodeAttrDef}'''
        self.process = NodeClassDef() #dummy for pydev's completion
        '''The new process which is currently assembled'''
        self.processAttributes = {}
        '''Attributes of the new process: {('mod1', 'var1'):NodeAttrDef}'''
        self.stateVariables = {}
        '''State variables of the new process; {('mod1', 'var1'):NodeAttrDef}'''
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
        solParAttr = NodeAttrDef(loc=0, attrName=DotName('solutionParameters'),
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
                         or NodeAttrDefMulti, NodeStmtList
            namePrefix : tuple of strings. Prefix for the dotted name of the
                         class' attributes.
        Output:
            self.astProcessAttributes : dict: {('mod1', 'var1'):NodeAttrDef}
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
            elif isinstance(attrDef, NodeAttrDef):
                attrName = attrDef.attrName
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
            if isinstance(attrDef, NodeAttrDef) and \
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
            if (not isinstance(defStmt, NodeAttrDef)) or \
               (not defStmt.className in self.atomicClasses):
                continue
            newAttr = defStmt.copy() #copy definition,
            newAttr.attrName = longName #exchange name with long name (a.b.c)
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
                subBlockName = namePrefix + statement.funcName #dotted block name
                subModelName = subBlockName[:-1] #name of model, where block is defined
#                #Error if submodel or method does not exist
#                if not subModelName in self.astProcessAttributes:
#                    raise UserException('Undefined submodel: ' +
#                                        str(subModelName), statement.loc)
                if not subBlockName in self.astProcessAttributes:
                    raise UserException('Undefined method: ' +
                                        str(subBlockName), statement.loc)
                #Check if executing (inlining) this block is allowed
                if statement.funcName in illegalBlocks:
                    raise UserException('Function can not be called here: ' +
                                        str(statement.funcName), statement.loc)
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
                    newAttrName = namePrefix + var.attrName
                    var.attrName = newAttrName
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
            if not (node.attrName) in self.processAttributes:
                raise UserException('Undefined reference: ' +
                                    str(node.attrName), node.loc)



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
            self.stateVariables    : dict: {('a','b'):NodeAttrDef(...)}
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
            stateVarDef = self.processAttributes[node.attrName]
            #Check conceptual constraint: no $parameter allowed
            if stateVarDef.role == RoleParameter:
                raise UserException('Parameters can not be state variables: ' +
                              str(node.attrName), node.loc)
            #remember: this is a state variable; in definition and in dict
            stateVarDef.role = RoleStateVariable
            self.stateVariables[node.attrName] = stateVarDef



    def findParameters(self):
        '''Search for parameters (in the new procress) and return a dict'''
        #attrDef = NodeAttrDef()
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
            if not accPar.attrName in parameters:
                continue
            #OK, this parameter is initialized, remember it
            initedParams.add(accPar.attrName)
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
                msg = 'Uninitialized prameter: %s' % str(parameters[nPar].attrName)
                loc = parameters[nPar].loc
                errList.append((msg, loc))
            raise MultiErrorException(errList)

        #rename all attribute accesses according to paramReplaceDict
        for accPar in self.process.iterDepthFirst():
            if not isinstance(accPar, NodeAttrAccess):
                continue
            oldParamName = accPar.attrName
            if not oldParamName in paramReplaceDict:
                continue
            accPar.attrName = paramReplaceDict[oldParamName]

        #delete replaced parameters
        for i in range(len(self.process)-1, -1, -1): #iterate backwards
            defPar = self.process[i]
            if not isinstance(defPar, NodeAttrDef):
                continue
            parName = defPar.attrName
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
            lValDef = self.processAttributes[lVal.attrName]
            #No assignment to parameters
            if lValDef.role == RoleParameter:
                raise UserException('Illegal assignment to parameter: ' +
                                    str(lVal.attrName), lVal.loc)
            #No assignment to state variables - only to their time derivatives
            if lValDef.role == RoleStateVariable and (lVal.deriv != ('time',)):
                raise UserException('Illegal assignment to state variable: ' +
                                    str(lVal.attrName) +
                                    '. You must however assign to its time derivative. ($' +
                                    str(lVal.attrName) +')', lVal.loc)


    def checkInitMethodConstraints(self, block):
        '''See if the method is a valid init method.'''
        #iterate over all nodes in the syntax tree and search for variable accesses
        for node in block.iterDepthFirst():
            if not isinstance(node, NodeAttrAccess):
                continue
            #$ operators are illegal in init method
            if node.deriv == ('time',):
                raise UserException('Time derivation illegal in init: ' +
                                    str(node.attrName), node.loc)


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
            paramName = assign.lhs.attrName
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
        self.process.className = self.astProcess.className
        self.process.superName = self.astProcess.superName
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

        self.checkUndefindedReferences(self.process) #Check undefined refference
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
        solPars.appendChild(NodeAttrDef(loc=0,
                                        attrName=DotName('simulationTime'),
                                        className=DotName('Real'),
                                        role=RoleParameter))
        solPars.appendChild(NodeAttrDef(loc=0,
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
        iltRoot = NodeProgram()
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
class ProgramTreeCreator(object):
    '''Create the AST for the whole program,'''
    
    def __init__(self):
        #cache for imported modules
        self.moduleCache = {}
        #the standard library (treated specially)
        self.stdLib = None
        stdLib = simlstdlib.createParseTree()
        self.stdLib = self.importModuleTree(stdLib)

        
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
            to be useful.
    
        Returns
        -------
        None
        ''' 
        i = 0
        while i < len(tree):
            node = tree[i]
            if isinstance(node, NodeAttrDefList):
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
                ProgramTreeCreator.flattenMultiDataDefs(node.funcBody)
            i += 1


    def importModuleTree(self, parseTree):
        '''
        Import a module given as a parse tree.
        
        This function performs the semantic analysis and creates the complete 
        program tree from multiple modules.
        
        Parameters
        ----------
        parseTree : ast.Node
            The module's parse tree, the output of 
            simlparser.ParseStage.parseModuleStr(...).
    
        Returns
        -------
        moduleTree : ast.Node
            AST of a module. Will be assembled into a complete program tree.
        '''
        self.flattenMultiDataDefs(parseTree)
        #TODO: Give default data roles to definitions where role==None
        #If the standard library exists prepend it to the module.
        # This way the standard library can be processed by this method too.
        if self.stdLib is not None:
            parseTree.insertChildren(0, self.stdLib)
        #TODO: Build symbol tables
        #TODO: Create inheritance pointers?
        #TODO: Create pointers to class definitions?
        return parseTree
        
        
    def importModuleFile(self, fileName):
        '''
        Import a module (program file).
        
        Semantic analysis is performed by self.importModuleTree(...).
        TODO: Modules are cached, and their AST is constucted only once, 
              even when they are imported multiple times.
        The function is recursively executed for each import statement.
        
        Parameters
        ----------
        fileName : str
            The module's file name. The module's text is read from this file.
    
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
        parser = simlparser.ParseStage()
        parseTree = parser.parseModuleStr(inputFileContents, fileName) 
        #do semantic analysis and decorate tree
        ast = self.importModuleTree(parseTree)
        #put tree in cache
        self.moduleCache[absFileName] = ast
        return ast
        
        
    def importModuleStr(self, moduleStr, fileName=None):
        '''
        Import a module (program file) as a string.
        Convenience function for development. (See self.importModuleFile)
               
        Parameters
        ----------
        moduleStr : str
            The module's (program's) text.
        fileName : str
            The module's file name, used for generating error messages.
    
        Returns
        -------
        moduleTree : ast.Node
            AST of a module. Will be assembled into a complete program tree.
        '''
        parser = simlparser.ParseStage()
        parseTree = parser.parseModuleStr(moduleStr, fileName) 
        return self.importModuleTree(parseTree)
        

def doTests():
    '''Perform various tests.'''

#------------ testProg1 -----------------------
    testProg1 = (
'''
class Test(Model):
{
    data V, h: Real;
    data A_bott, A_o, mu, q, g: Real param;

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
        q = 0.05;
    }
}

class RunTest(Process):
{
    data g: Real param;
    data test: Test;

    func dynamic():
    {
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
        #store;
        graph test.V, test.h;
        print 'Simulation finished successfully.';
    }
}
''' )

#------------ testProg2 -----------------------
    testProg2 = (
'''
data a, b, c: Real;

class Test(Model):
{
    data a, b, c: Real;
    data d: Real;
    
    func test(a,b,c): 
    {
        
    }
}
''' )

    #test the intermedite tree generator ------------------------------------------------------------------
    flagTestILTGenerator = False
    #flagTestILTGenerator = True
    if flagTestILTGenerator:
        parser = simlparser.ParseStage()
        iltGen = ILTGenerator()

        astTree = parser.parseModuleStr(testProg1)
        print 'AST tree:'
        print astTree

        iltTree = iltGen.createIntermediateTree(astTree)
        print 'ILT tree:'
        print iltTree

    #test program 2 ------------------------------------------------------------------
    flagTestProg2 = False
    flagTestProg2 = True
    if flagTestProg2:
        
        tc = ProgramTreeCreator()
        astTree = tc.importModuleStr(testProg2)
        
        print 'AST tree:'
        print astTree

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
