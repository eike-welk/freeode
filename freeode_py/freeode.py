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
#import pdb
from optparse import OptionParser
import pygenerator
import simlparser

progVersion = '0.3.0'


def parseCmdLine():
    '''Parse the command line, and find out what the user wants from us.'''
    global progVersion
    #set up parser for the command line aruments
    usage = '%prog <input_file> [-o <output_file>] [-m | -n]\n\n' + \
            'Compiler for the Siml simulation language.\n'
    optPars = OptionParser(usage=usage, version='%prog ' + progVersion)
    
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
    pass

   
def mainFunc():
    '''the main function'''
    inputFileName, outputFileName, genMainRoutine = parseCmdLine()
    doCompile(inputFileName, outputFileName)
    
    
mainFunc()


def testfunc():  
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
    
    #-------- the code -----------------------------------------------------
    parser = simlparser.ParseStage()
    astGen = simlparser.ASTGenerator()
    iltGen = simlparser.ILTGenerator()
    progGen = pygenerator.ProgramGenerator()
    
    pres = parser.parseProgram(testProg1)
    #print 'parse result:'
    #print pres
    
    astTree = astGen.createSyntaxTree(pres)
    #print 'AST tree:'
    #print astTree
    
    iltTree = iltGen.createIntermediateTree(astTree)
    print 'ILT tree:'
    print iltTree
    
    progGen.createProgram(iltTree)
    progStr = progGen.buffer()
    #print 'python program:'
    #print progStr
    
    pyFile = open('/home/eike/codedir/freeode/trunk/freeode_py/test.py','w')
    pyFile.write(progStr)
    pyFile.close()
    
    from test import RunTest
    sim = RunTest()
    sim.simulateDynamic()
    #sim.graph('test.V')
    print 'test finished'

#testfunc()
