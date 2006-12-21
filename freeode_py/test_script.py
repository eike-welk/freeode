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

from subprocess import Popen, PIPE, STDOUT
import sys

#execute the compiler
proc = Popen(['python', 'freeode.py', 'tank.siml'], shell=False, #bufsize=1000,
             stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
(procStdin, procComboOut) = (proc.stdin, proc.stdout)
#stop when compiler error is detected
retStr = procComboOut.read()
print retStr
if retStr.lower().find('error') != -1:
    print 'termination due to error'
    sys.exit(1)
    

#import the generated python program
import tank

#create simulation object and do the simulation
sim = tank.FillTank() 
sim.simulateDynamic()

#show some results
sim.graph('t.V t.h t.qOut')
