# -*- coding: utf-8 -*-
'''
Copyright (C) 2010, Eike Welk
License GPL

Create class and meta-class so that repr( <class> ) returns the class name.
This way the class behaves like a global constant that knows its name.
'''

class EnumMeta(type):
    def __repr__(self):
        return self.__name__
    
class Enum(object):
    __metaclass__ = EnumMeta
    

#Use it:
#Create some global constants
class FOO(Enum):
    pass

class BAR(Enum):
    buzz = 1
    bong = "hello"

#These things really know their name
print FOO
print BAR
#None works the same way
print None

a = FOO
if a is FOO:
    print
    print "This is really foo!"
    print

#Nothing special about FOO
print type(FOO)
