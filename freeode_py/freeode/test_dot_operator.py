# -*- coding: utf-8 -*-
#############################################################################
#    Copyright (c) 2008  Eike Welk                                          #
#    eike.welk@post.rwth-aachen.de                                          #
#                                                                           #
#    License: Expat License (X11 License)                                   #
#                                                                           #
#    Permission is hereby granted, free of charge, to any person obtaining  #
#    a copy of this software and associated documentation files (the        #
#    "Software"), to deal in the Software without restriction, including    #
#    without limitation the rights to use, copy, modify, merge, publish,    #
#    distribute, sublicense, and/or sell copies of the Software, and to     #
#    permit persons to whom the Software is furnished to do so, subject to  #
#    the following conditions:                                              #
#                                                                           #
#    The above copyright notice and this permission notice shall be         #
#    included in all copies or substantial portions of the Software.        #
#                                                                           #
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,        #
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF     #
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. #
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY   #
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,   #
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE      #
#    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                 #
#############################################################################

'''
Hack, to permit a syntax that looks like an additional operator for the dot 
product would exist:

    c = a *dot* b

(The idea is from some Python website; maybe cheese shop.)
'''

from __future__ import division

import numpy as np



class DotHelper1(object):
    '''Helper class for the dot pseudo operator'''
    __array_priority__ = 10.0
    
    def __init__(self, axes=None):
        self.axes = axes
    
    def __call__(self, axes=None):
        '''Might be used to pass the dimension over which the dot product is taken'''
        return DotHelper1(axes)
    
    def __rmul__(self, leftOP):
        if not isinstance(leftOP, np.ndarray):
            return NotImplemented
        return DotHelper2(leftOP, self.axes)


class DotHelper2(object):
    '''Helper class for the dot pseudo operator'''
    
    def __init__(self, operand=None, axes=None):
        self.operand = operand
        self.axes = axes
    
    def __mul__(self, rightOp):
        if not isinstance(rightOp, np.ndarray):
            return NotImplemented
        if self.operand is None:
            raise Exception('Unknown left operand!')
        #finally do the desired computation
        if self.axes is None:
            return np.dot(self.operand, rightOp)
        else:
            return np.tensordot(self.operand, rightOp, self.axes)
    
    
dot = DotHelper1()


if __name__ == '__main__':
    from numpy import array, linspace
    
    a = array([1.0, 2, 3])
    b = array([4.0, 5, 6])
    m = linspace(1, 9, 9).reshape((3,3)) #IGNORE:E1101
    
    print 'a: ', a 
    print 'b: ', b 
    print 'm: '; print m 
    print
    
    print 'a *dot* b         : ', a *dot* b
    print 'm *dot* a         : ', m *dot* a
    print 'a *dot* m         : ', a *dot* m
    print 'a *dot* m *dot* a : ', a *dot* m *dot* a
    
    print 'm *dot* m : ';        print m *dot* m
    print 'm *dot((1,0))* m : '; print m *dot((1,0))* m
    print 'm *dot((0,0))* m : '; print m *dot((0,0))* m
