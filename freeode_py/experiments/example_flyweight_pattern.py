# -*- coding: utf-8 -*-

"""Example of the flyweight design pattern for Numpy arrays. 
   From the intention it is maybe really a proxy."""

from numpy import array

class MyThing(object):
    """This object pretends to possess one self.position data member in each
       instance. In reality however, the positions are stored collectively in
       the class attribute MyThing.position_array. 
       Each instance only stores an index to access the data in the 
       collectively used array."""
       
    position_array = array([], 'd')
    
    def __init__(self, index):
        self.index = index
        
    def get_position(self):
        return MyThing.position_array[self.index]
    def set_position(self, new_val):
        MyThing.position_array[self.index] = new_val
        
    position = property(get_position, set_position, None,
        'Position of MyThing, stored collectively for all objects in '
        'MyThing.position_array.')
    
    
#--------- Use the MyThig class -----------------------------------------------
#fill the array of positions with data
MyThing.position_array = array([[0,0,0], [0,1,0], [0,0,3]], 'd')

#create instance at index 1
thing1 = MyThing(1)
print thing1.get_position()
print thing1.position
assert (thing1.position == array([0,1,0])).all()

#create instance at index 2
thing2 = MyThing(2)
print thing2.position
assert (thing2.position == array([0,0,3])).all()
thing2.position = array([1,2,3])
print thing2.position
assert (thing2.position == array([1,2,3])).all()