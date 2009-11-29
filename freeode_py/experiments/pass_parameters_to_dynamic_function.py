# -*- coding: utf-8 -*-
#Test different ways to transport the parameters into the simulation function.

from time import clock

#Parameters are instance attributes and they are used in dynamic functions 
#with self.name
class Sim1(object):
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
        self.d = 4
        self.e = 5
        self.f = 6
        self.g = 7
        self.h = 8
        self.i = 9
        self.j = 10
        
    def dynamic(self):
        ret = (self.a + self.b + self.c + self.d + self.e + self.f + 
               self.g + self.h + self.i + self.j)
        return ret
 
 
#Parameters are kept separate in parameter storage object 
#(which is an instance attribute).
class ParamStore(object):
    pass       
class Sim2(object):
    def __init__(self):
        self.param = ParamStore()
        self.param.a = 1
        self.param.b = 2
        self.param.c = 3
        self.param.d = 4
        self.param.e = 5
        self.param.f = 6
        self.param.g = 7
        self.param.h = 8
        self.param.i = 9
        self.param.j = 10
        
    def dynamic(self):
        param = self.param
        ret = (param.a + param.b + param.c + param.d +  param.e + param.f + 
               param.g + param.h + param.i + param.j)
        return ret
        
        
#Parameters are transported into the dynamic function with a closure:
#Dynamic function is constructed in a namespace that contains the
#parameters, shortly before it is called repeatedly. Therefore the
#parameters exist in the function's local namespace.
class Sim3(object):
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
        self.d = 4
        self.e = 5
        self.f = 6
        self.g = 7
        self.h = 8
        self.i = 9
        self.j = 10
        
    def make_dynamic(self):
        a = self.a; b = self.b; c = self.c; d = self.d; e = self.e
        f = self.f; g = self.g; h = self.h; i = self.i; j = self.j
        
        def dynamic():
            ret = a + b + c + d + e + f + g + h + i + j
            return ret
        
        return dynamic
 
 
iterations = 3000000
print '%s iterations.' % str(iterations)
sim1 = Sim1()
sim2 = Sim2()
sim3 = Sim3()
 
start = clock()
dynamic = sim1.dynamic
for i in range(iterations):
    dynamic()
end = clock()
print 'Parameters are regular instance attributes: class Sim1 \n' \
      'Calling dynamic function repeatedly took %s s.' % str(end - start)

start = clock()
dynamic = sim2.dynamic
for i in range(iterations):
    dynamic()
end = clock()
print 'Parameters are stored in separate object: class Sim2 \n'\
      'Calling dynamic function repeatedly took %s s.' % str(end - start)

start = clock()
dynamic = sim3.make_dynamic()
for i in range(iterations):
    dynamic()
end = clock()
print 'Parameters are stored in closure: class Sim3 \n'\
      'Calling dynamic function repeatedly took %s s.' % str(end - start)
    
 