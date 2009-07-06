# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2006 - 2009 by Eike Welk                                #
#    eike.welk@post.rwth-aachen.de                                         #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          *
#    License: GPL                                                          *
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
Compiler main loop with hight level functions for parsing command line
options, compiling and running the compiled program.
'''


from __future__ import division

#import pdb
import optparse
import sys
import os
import stat
from subprocess import Popen #, PIPE, STDOUT
import pyparsing
import freeode.simlparser as simlparser
import freeode.interpreter as interpreter
import freeode.pygenerator as pygenerator
import freeode.ast as ast  #for ast.PROGRAM_VERSION
from freeode.ast import UserException


class SimlCompilerMain(object):
    def __init__(self):
        super(SimlCompilerMain, self).__init__()
        self.input_file_name = ''
        self.output_file_name = ''
        #which process should be run after compiling
        self.runSimulation = None #can be: None, 'all', '0', '1', ...


    def parse_cmd_line(self):
        '''Parse the command line, and find out what the user wants from us.'''
        #set up parser for the command line aruments
        optPars = optparse.OptionParser(
                    usage='%prog <input_file> [-o <output_file>] [<options>]',
                    description='Compiler for the Siml simulation language.',
                    version='%prog ' + ast.PROGRAM_VERSION)

        optPars.add_option('-o', '--outfile', dest='outfile',
                           help='explicitly specify name of output file',
                           metavar='<output_file>')
        optPars.add_option('-r', '--run', dest='runone',
                           help='run generated simulation program after '
                              + 'compiling. Specify which process to simulate '
                              + 'with number or use special value "all" '
                              + '(number counts from top).',
                           metavar='<number>')
#        optPars.add_option('--runall', dest='runall',
#                           action="store_true", default=False,
#                           help='run all simulation processes after compiling')
        #do the parsing
        (options, args) = optPars.parse_args()

        #get name of input file
        if len(args) > 0:
            self.input_file_name = args[0]
        if not self.input_file_name:
            optPars.error('no input file given')
        #split input file name into basename and extension
        nameParts = self.input_file_name.rsplit('.',1)
        if len(nameParts)  > 1:
            inputFileExtension = nameParts[1]
        else:
            inputFileExtension = '' #filename contained no '.' char
        inputFileBaseName = nameParts[0]

        #see if file extension is good
        if inputFileExtension.lower() != 'siml':
            print 'warning: programs in the SIML language ' + \
                  'should have the extension ".siml"'

        #get name of output file
        if options.outfile:
            #output file name is explicitly given
            self.output_file_name = options.outfile
        else:
            #use input_file_name but replace extension with '.py'
            self.output_file_name = inputFileBaseName + '.py'

        #see if user whishes to run the simulation after compiling
        if options.runone == 'all':
            self.runSimulation = 'all'
        elif options.runone: #anything else is considered a number
            #test if argument is a number
            try:
                int(options.runone)
            except:
                optPars.error('option "-r": argument must be number or "all". I got: %s'
                              % options.runone)
            #convert into string containing a number
            self.runSimulation = str(int(options.runone))


    def do_compile(self):
        '''Do the work'''
        #create the top level objects that do the compilation
        intp = interpreter.Interpreter()
        prog_gen = pygenerator.ProgramGenerator()

        #the compilation proper
        intp.interpret_module_file(self.input_file_name, '__main__')
        prog_gen.create_program(self.input_file_name, intp.get_compiled_objects())
        prog_str = prog_gen.get_buffer()

        #write generated program to file
        try:
            output_file = open(self.output_file_name,'w')
            output_file.write(prog_str)
            output_file.close()
            #make genrated program executable
            mode_bits = os.stat(self.output_file_name).st_mode
            os.chmod(self.output_file_name, mode_bits | stat.S_IEXEC)
        except IOError, err:
            print >> sys.stderr, 'error: could not write output file\n', err
            sys.exit(1)

        print 'Compilation finished successfully.'
        #print 'input file: %s, output file: %s' % (self.input_file_name, self.output_file_name)


    def run_program(self):
        '''Run the generated program if the user wants it.'''
        if self.runSimulation == None:
            return

        #optStr = ' -r %s' % self.runSimulation
        cmdStr = 'python %s -r %s --prepend-newline' % (self.output_file_name,
                                                        self.runSimulation)
        proc = Popen([cmdStr], shell=True, #bufsize=1000,
                     stdin=None, stdout=None, stderr=None, close_fds=True)
        print 'running generated program. PID: %d\n\n' % proc.pid


    def main_func(self): 
        '''The main function. 
           Create the compiler object (SimlCompilerMain) and run this function 
           to run the compiler.
        '''
        try:
            self.parse_cmd_line()
            self.do_compile()
            self.run_program()
        except UserException, theError:
            #regular compilation error
            print >> sys.stderr, theError
            sys.exit(1)
        except SystemExit:
            raise #for sys.exit() - the error message was already printed
        except Exception: #Any other exception must be a malfunction of the compiler
            print >> sys.stderr, ('\n'
                  'Oh my golly! Compiler internal error! \n\n'
                  'Please file a bug report at the project\'s website, '
                  'or send an e-mail \n'
                  'with with a bug report to the developer(s).\n'
                  'The bug report should include the traceback '
                  'at the end of this message. \n'
                  'Please include also a short description of the error. \n'
                  'Bug-website: \n'
                  '  https://bugs.launchpad.net/freeode \n'
                  'E-mail: \n'
                  '  eike@users.berlios.de \n\n'
                  'SIML compiler version: %s \n' %  ast.PROGRAM_VERSION)
            raise #gets traceback and ends program
        #return with success
        sys.exit(0)


if __name__ == '__main__':
    pass
