# -*- coding: utf-8 -*-
#***************************************************************************
#    Copyright (C) 2009 by Eike Welk                                       *
#    eike.welk@gmx.net                                                     *
#                                                                          *
#    License: GPL                                                          *
#                                                                          *
#    This program is free software; you can redistribute it and/or modify  *
#    it under the terms of the GNU General Public License as published by  *
#    the Free Software Foundation; either version 2 of the License, or     *
#    (at your option) any later version.                                   *
#                                                                          *
#    This program is distributed in the hope that it will be useful,       *
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#    GNU General Public License for more details.                          *
#                                                                          *
#    You should have received a copy of the GNU General Public License     *
#    along with this program; if not, write to the                         *
#    Free Software Foundation, Inc.,                                       *
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#***************************************************************************

"""
Test code for the "optimizer.py" module
"""

from __future__ import division
from __future__ import absolute_import              #IGNORE:W0410

from py.test import skip as skip_test # pylint: disable-msg=F0401,E0611,W0611
from py.test import fail as fail_test # pylint: disable-msg=F0401,E0611,W0611

from freeode.util import assert_raises



def test_MultiDict_1(): #IGNORE:C01111
    msg = '''Test the MultiDict class.'''
    #skip_test(msg)
    print msg
    
    from freeode.optimizer import MultiDict

    class Dummy(object): pass
    
    a, b, c, d = Dummy(), Dummy(), Dummy(), Dummy()
    
    #Test usage with regular objects
    md = MultiDict()
    md[a] = 1; md[a] = 2; md[a] = 3; md[a] = 4; md[a] = 5
    md[b] = 4; md[b] = 5; md[b] = 6; md[b] = 7; md[b] = 8
    md[c] = 1
    
    assert md[a] == [1, 2, 3, 4, 5]
    assert md[b] == [4, 5, 6, 7, 8]
    assert md[c] == [1]
    def raise1(): 
        _x = md[d]
    assert_raises(KeyError, None, raise1)
    
    #Test indexing with sets
    md = MultiDict()
    md[a] = 1
    md[b] = 2
    md[c] = 3    
    md[set([a, b, c, d])] = 4
    
    assert md[a] == [1, 4]
    assert md[b] == [2, 4]
    assert md[c] == [3, 4]
    assert md[d] == [4]

    def raise2(): 
        _x = md[md[set([a, b, c, d])]]
    assert_raises(KeyError, None, raise2)
    
    
    
def test_MakeDataFlowDecorations_1(): #IGNORE:C01111
    msg = '''Test the creation of data flow annotations.'''
    #skip_test(msg)
    print msg
    
    from freeode.optimizer import MakeDataFlowDecorations
    from freeode.interpreter import Interpreter, IFloat
    #from freeode.ast import NodeAssignment
    from freeode.util import DotName

    prog_text = \
'''
class A:
    data p1,p2: Float param
    data a,b,c,d: Float
                              #5 
    func dynamic(this):            
        a = p1
        b = a - p2
        if a > p1:
            c = p1           #10
            d = p1
        else:
            c = p2 
            d = p2

compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    #mod = intp.modules['test']
    #print mod
    
    #get the flattened version of the A class
    sim = intp.get_compiled_objects()[0]
    #print sim
    #get attributes
    a = sim.get_attribute(DotName('a'))
    b = sim.get_attribute(DotName('b'))
    c = sim.get_attribute(DotName('c'))
    d = sim.get_attribute(DotName('d'))
    p1 = sim.get_attribute(DotName('p1'))
    p2 = sim.get_attribute(DotName('p2'))
    #get generated main function
    dyn = sim.get_attribute(DotName('dynamic'))    
    #print object ids in hex (for easier manual testing)
    hexid = lambda x: hex(id(x))
    print 'a:', hexid(a), ' b:', hexid(b),  ' c:', hexid(c),  ' d:', hexid(d), \
          ' p1:', hexid(p1),  ' p2:', hexid(p2) 

    #------- the test -------------------
    #create the input and output decorations on each statement of the 
    #function
    dd = MakeDataFlowDecorations()
    dd.decorate_simulation_object(sim)
    #dd.decorate_main_function(dyn)

    #see if the inputs and outputs were detected correctly
    # a = p1   
    stmt0 = dyn.statements[0]
    assert stmt0.inputs == set([p1])
    assert stmt0.outputs == set([a])
    #  b = a - p2
    stmt1 = dyn.statements[1]
    assert stmt1.inputs == set([a, p2])
    assert stmt1.outputs == set([b])
    
    #'if' statement
    stmt2 = dyn.statements[2]
    #look at inputs
    assert stmt2.inputs.issuperset(set([a, p1, p2])) 
    #there is an additional constant IFloat(1) in the condition of the else
    one_set = stmt2.inputs - set([a, p1, p2])
    assert len(one_set) == 1
    one_obj = one_set.pop()
    assert one_obj == IFloat(1)
    #look at outputs
    assert stmt2.outputs == set([c, d])
    
    #the dynamic function
    assert dyn.inputs == set([p1, p2, one_obj])
    assert dyn.outputs == set([a, b, c, d])
    
    #The input_locs, output_locs mappings for creating error messages
    p1_in_locs = dyn.input_locs[p1]
    assert len(p1_in_locs) == 4
    assert p1_in_locs[0].line_no() == stmt0.loc.line_no()
    assert p1_in_locs[1].line_no() == stmt2.loc.line_no()
#    for loc in p1_in_locs:
#        print loc
    a_out_loc = dyn.output_locs[a]
    assert len(a_out_loc) == 1
    assert a_out_loc[0].line_no() == stmt0.loc.line_no()
    
        

def test_VariableUsageChecker_1(): #IGNORE:C01111
    msg = '''Test checking of variable usage. Simple program with no errors.
    
    These are the rules:
    Constants (rules enforced in the interpreter):
        - All constants must be known.
        - No assignments to constants.
        
    Parameters:
        - All must be assigned in all init**** function.
        - No assignment to parameters elsewhere.
        
    Variables:
        - All derivatives must be assigned in dynamic function.
        - No states must be assigned in dynamic function.
        - All states must be assigned initial values in init*** function.
    '''
    #skip_test(msg)
    print msg
    
    from freeode.optimizer import MakeDataFlowDecorations, VariableUsageChecker
    from freeode.interpreter import Interpreter
    from freeode.util import DotName #, aa_make_tree

    prog_text = \
'''
class A:
    data p1,p2: Float param
    data a,b,c: Float
    
    func initialize(this):
        p1 = 1
        p2 = 1
        a = 0
        data lo: Float
        lo = 1
        
    func dynamic(this): 
        $a = p1
        b = a - p2
        
        if a > p1:
            c = p1
        else:
            c = p2 
        data lo: Float
        lo = 1


    func final(this):
        b = 1
        print(a, b, p1)
        data lo: Float
        lo = 1
        
        
compile A
'''

    #interpret the program
    intp = Interpreter()
    intp.interpret_module_string(prog_text, None, 'test')

    #the module
    #mod = intp.modules['test']
    #print mod
    
    #get the flattened version of the A class
    sim = intp.get_compiled_objects()[0]
    #aa_make_tree(sim)
    
    #create the input and output decorations on each statement of the 
    #function
    dd = MakeDataFlowDecorations()
    dd.decorate_simulation_object(sim)

    #Find all input and output variables
    vu = VariableUsageChecker()
    vu.set_annotated_sim_object(sim) 
    
    #Check the usage of the variables 
    initialize = vu.main_funcs[DotName('initialize')]
    vu.check_initialize_function(initialize) 
    
    dynamic = vu.main_funcs[DotName('dynamic')]
    vu.check_dynamic_function(dynamic) 
    
    final = vu.main_funcs[DotName('final')]
    vu.check_final_function(final) 
    
#    print aa_make_tree(initialize)
#    print aa_make_tree(dynamic)
#    print aa_make_tree(final)
#    
#    def get_varnames(var_set, sim_obj):
#        var_names = []
#        for attr in var_set:
#            var_names.append(sim_obj.find_attribute_name(attr))
#        var_names = map(str, var_names)
#        print var_names
#        return var_names
# 
#    get_varnames(initialize.outputs, sim)
#    get_varnames(dynamic.outputs, sim)
#    get_varnames(final.outputs, sim)
    
    #TODO: assertions


if __name__ == '__main__':
    # Debugging code may go here.
    test_VariableUsageChecker_1()
    #test_unknown_const_1()
    #test_MultiDict_1()
    #test_unknown_const_1()
    pass


