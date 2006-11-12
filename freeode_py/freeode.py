#!/usr/bin/env python

import pdb
import simlparser

def main():
    print 'Run simlparser tests ...'
    simlparser.doTests()

main()


##try to reproduce the list init and append bug, where data attributes
##behaved like class attributes
#class test1(object):
    #def __init__(self, liArg=[]):
        #self.li = liArg      #bug
        ##self.li = liArg[:]  #works

#a = test1()
#b = test1()

#a.li.append(1)
#print a.li
#print b.li



#pdb.set_trace()


#Reload a previously imported module.
#reload(simlparser)
