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
from ast import UserException


#import pdb
import optparse
import sys
import simlparser
import pygenerator


#These global variables are defined in ast.py and are therefore accessible 
#in all modules of the compiler
global progVersion, inputFileName, inputFileContents
#version of the Siml compiler
progVersion = '0.3.0'
#name of the Siml file which is compiled
inputFileName = '???'
#The contents of the input file as a string
inputFileContents = '???'


def parseCmdLine():
    '''Parse the command line, and find out what the user wants from us.'''
    global progVersion
    #set up parser for the command line aruments
    optPars = optparse.OptionParser(
                usage='%prog <input_file> [-o <output_file>] [-m | -n]',
                description='Compiler for the Siml simulation language.', 
                version='%prog ' + progVersion)
    
    optPars.add_option('-o', '--outfile', dest='outfile', 
                       help='explicitly specify name of output file', 
                       metavar='<output_file>')
    optPars.add_option('-m', '--genmain', dest='genmain',
                       action="store_true", default=False,
                       help='generate main routine, that starts the ' + \
                            'simulation (currently non functional)')
    optPars.add_option('-n', '--nomain', dest='genmain',
                       action="store_false", 
                       help='do not generate a main routine [default]')
    #do the parsing
    (options, args) = optPars.parse_args()
    
    #get name of input file
    inputFileName = None
    if len(args) > 0:
        inputFileName = args[0]
    if inputFileName == None:
        optPars.error('no input file given')
        
    #test extension
    inputFileExtension = inputFileName.rsplit('.',1)[1]
    if inputFileExtension.lower() != 'siml':
        print 'warning: programs in the Siml language ' + \
              'should have the extension ".siml"'
    
    #get name of output file
    if options.outfile != None:
        #output file name is explicitly given
        outputFileName = options.outfile
    else:
        #take away extension from inputFileName and replace with '.py'
        baseName = inputFileName.rsplit('.',1)[0]
        outputFileName = baseName + '.py'
    
    #care for main routine flag
    if options.genmain:
        optPars.error('main routine generation does currently not work')
    genMainRoutine = options.genmain
    
#    print 'inputFileName: ', inputFileName, \
#          ', outputFileName: ', outputFileName, \
#          ', genMainRoutine: ', genMainRoutine
          
    return (inputFileName, outputFileName, genMainRoutine)
          

def doCompile(inputFileName, outputFileName):
    '''Do the work'''
    global inputFileContents
    
    #open the file
    try:
        inputFile = open(inputFileName, 'r')
        inputFileContents = inputFile.read()
        inputFile.close()
    except IOError, theError:
        print 'error: could not read input file\n', theError
        return
    
    #create the top level objects that do the compilation
    parser = simlparser.ParseStage()
    astGen = simlparser.ASTGenerator()
    iltGen = simlparser.ILTGenerator()
    progGen = pygenerator.ProgramGenerator()
    
    #the compilation proper
    try:
        pres = parser.parseProgram(inputFileContents)
        astTree = astGen.createSyntaxTree(pres)
        iltTree = iltGen.createIntermediateTree(astTree)
        progGen.createProgram(iltTree)
        progStr = progGen.buffer()
    except UserException, theError:
        theError.str = inputFileContents
        print theError
        return
    except simlparser.ParseException, theError:
        print theError
        return
        
    #write generated program to file
    try:    
        outputFile = open(outputFileName,'w')
        outputFile.write(progStr)
        outputFile.close()
    except IOError, theError:
        print 'error: could nor write output file\n', theError 
        return
 
   
def mainFunc():
    '''the main function'''
    global inputFileName
    
    inputFileName, outputFileName, genMainRoutine = parseCmdLine()
    try:
        doCompile(inputFileName, outputFileName)
    except:
        print 'Compiler internal error! Please file a bug report at:\n',\
              'https://developer.berlios.de/projects/freeode/\n'
        raise
    

#run the compiler
mainFunc()
