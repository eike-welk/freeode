'''
Created on Jun 17, 2010

@author: eike

Change the program text from:
    @return_type(BOOLP)
    @argument_type(BOOLP, BOOLP)
to:
    @signature([BOOLP, BOOLP], BOOLP)
'''

#import os
#print os.system('ls')

in_file_name = '../freeode/interpreter.py'
out_file_name = '../freeode/interpreter.py.mod.py'

in_file = open(in_file_name, 'r')
out_file = open(out_file_name, 'w')

line = '+'
while line:
    line = in_file.readline()
    sline = line.strip()
    
    if sline.startswith('@return_type') or sline.startswith('@argument_type'):
        return_type = 'None'
        argument_type = 'None'
        in_signature = True
        while in_signature:
            #print line
            if sline.startswith('@return_type'):
                start = sline.find('(') + 1
                end = sline.find(')')
                return_type = sline[start:end]
                #print 'return_type: ', start, end, return_type
            elif sline.startswith('@argument_type'):
                start = sline.find('(') + 1
                end = sline.find(')')
                argument_type = '[' + sline[start:end] + ']'
                #print 'argument_type: ', start, end, argument_type
            else:
                in_signature = False
                signature = '    @signature(%s, %s) \n' % (argument_type, return_type)
                print 'signature', signature
                out_file.write(signature)
                break
            line = in_file.readline()
            sline = line.strip()
    
    #print line
    out_file.write(line)
    

in_file.close()
out_file.close()

