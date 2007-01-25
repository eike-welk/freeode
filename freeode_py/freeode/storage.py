# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2007 by Vincent Nijs                                    #
#    v-nijs at kellogg.northwestern.edu                                    #
#                                                                          #
#    Copyright (C) 2007 by Eike Welk                                       #
#    eike.welk@post.rwth-aachen.de                                         #
#                                                                          #
#    License: LGPL                                                         #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU Library General Public License as       #
#    published by the Free Software Foundation; either version 2 of the    #
#    License, or (at your option) any later version.                       #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU Library General Public     #
#    License along with this program; if not, write to the                 #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################


from __future__ import division
#from scipy import c_, arange, array, unique, kron, ones, eye, nan, isnan, string_
from numpy import ndarray, array, hstack, zeros, isnan
#from numpy.random import randn
import pylab
import cPickle
#import shelve
import csv
import copy
#import os
import datetime


class ArrayStore(object):
    '''
    Doc:
    A simple data-frame, that reads and writes csv/pickle files with 
    variable names.
    Data is stored in an array, variable names are stored in an dictionary.
    '''
    
    csv_commentStart = '#'
    '''Indicates comment lines in CSV files.'''
    
    def __init__(self, dataArray=None, nameList=None, fileName=None):
        '''
        Initialize the DataStore class.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each variable is a collumn
        nameList  : the variable names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        '''
        self.dataArray = array([[]], 'float64')
        '''The numeric data; each collumn is a variable.''' #IGNORE:W0105
        self.varNameDict = {}
        '''The variable names, and associated collumn indices: {'foo':0, 'bar':1}''' #IGNORE:W0105
        #initialize from data
        if dataArray != None or nameList != None:
            self.createFromData(dataArray, nameList)
        #initialize from from file 
        elif fileName != None:
            self.load(fileName)
            
	

    def createFromData(self, dataArray=None, nameList=None):
        '''
        Create object from array and list of names.
        TODO: maybe integrate into __init__?
        '''
        #test prerequisites
        if not isinstance(dataArray, ndarray):
            raise TypeError('Argument "dataArray" must be of type "numpy.array"') #IGNORE:E1010
        if not isinstance(nameList, (list, tuple, dict)):
            raise TypeError('Argument "nameList" must be of type "list" or "dict"') #IGNORE:E1010
        if not (len(dataArray.shape) == 2):
            raise ValueError('Argument "dataArray" must be a 2D array.') #IGNORE:E1010
        if not (dataArray.shape[1] == len(nameList)):
            raise ValueError('"nameList" must have an entry for each collumn of "dataArray"') #IGNORE:E1010
        #create index dictionary 
        if isinstance(nameList, dict):
            self.varNameDict = nameList #a dict is accepted untested
        else:
            #create index dictionary from list
            for i, name in enumerate(nameList):
                if not isinstance(name, str):
                    raise TypeError('Variable names must be strings.') #IGNORE:E1010
                if name in self.varNameDict:
                    raise ValueError('Variable names must be unique.') #IGNORE:E1010
                self.varNameDict[name] = i
        #store the numbers
        #TODO: should the array be copied
        self.dataArray = dataArray

    
    def copy(self):
        '''Create a deep copy of the object'''
        return copy.deepcopy(self)
        
        
    def numVars(self):
        '''Return the number of variables'''
        #assert self.data.shape[1] == len(self.varNames)
        return self.dataArray.shape[1]
        
        
    def numObs(self):
        '''Return the number of obervations (same for each variable).'''
        return self.dataArray.shape[0]
    
    
    def variableNames(self):
        '''
        Return all variable names in a list. The variables are sorted 
        according to the index of the variable in the internal array. 
        Small index numbers come first.
        '''
        nameIndexTuples = self.varNameDict.items() #create list of tuple(<name>, <index>) 
        sortFunc = lambda a, b: cmp(a[1], b[1]) #function to compare the indices
        nameIndexTuples.sort(sortFunc) #sort variable names according to their indices
        nameList = [tup[0] for tup in nameIndexTuples] #remove the index numbers
        return nameList

        
    def _getExtension(self,fname):
        '''Find the file extension of a filename.'''
        return fname.split('.')[-1].strip()


    def load(self, fname):
        '''
        Load data from a csv or a pickle file of the DataStore class.
        
        The encoding is determined by the filename's extension:
        'csv' : When the filename ends in '.csv' the routine tries to 
                interpret the file as comma seperated values. The variable 
                names must be in the first row
        Any other extension is considered to mean a file in Python's pickle
        format.
        
        Arguments:
        fname    : filename; string
        
        Returns:
        None
        '''
        # setting the ascii/csv file name used for input
        #self.DBname = os.getcwd() + '/' + fname

        # getting the file extension
        fext = self._getExtension(fname)

        # opening the file for reading
        if fext == 'csv':
            self._loadCSV(fname)
        else: #fext == 'dstore':
            self._loadPickle(fname)
#        elif fext == 'she':
#            self.load_shelve(fname,var)
#        else:
#            raise 'This class only works on csv, pickle, and shelve files'


#    def csvconvert(self,col):
#        '''
#        Converting data in a string array to the appropriate type
#        '''
#        # convert missing values to nan
#        col[col == ''] = 'nan'; col[col == '.'] = 'nan'
#        try:
#            # if a missing value is present int variables will be up-cast to float
#            return col.astype('i')
#        except ValueError:
#            try:
#                return col.astype('f')
#            except ValueError:
#                # if the data is a string, put back the empty string
#                col[col == 'nan'] = ''
#                return col


    def _loadCSV(self,fname):
        '''Load data from a csv file.'''
        #Uses the CSV reader and an entirey hommade algorithm.
        #however there are library functions for doing this, that are  
        #probably faster:
        #    scipy.io.read_array
        #    pylab's load function (seems to be fastest)
        #TODO: more robustness
        
        #read whole file at once
        f = open(fname,'r')
        lines = f.readlines() 
        f.close()
        
        #delete lines that the csv reader can not understand
        for i in range(len(lines)-1,-1,-1):
            #delete comment lines
            if lines[i].startswith(ArrayStore.csv_commentStart):
                del lines[i]
            #delete blank lines (conaining only whitespace)
            if len(lines[i].strip()) == 0:
                del lines[i]
                
        #interpret remaining lines as  CSV
        reader = csv.reader(lines)
        varNameList = reader.next() #first line: variable names
        #put numbers into nested list
        dataList = []
        for line in reader:
            #TODO: convert strings that might be found between the numbers to nan.
            #see commented out csvconvert(...) method
            lineFloat = map(float, line) #convert strings to floating point
            dataList.append(lineFloat)   #append to nested list
        
        #convert nested list to array
        dataArray = array(dataList)
        #put data into internal structures
        self.createFromData(dataArray, varNameList)
        return


    def _loadPickle(self,fname):
        '''Load data from a file in pickle format.'''
        f = open(fname,'rb')
        newStore = cPickle.load(f) #this should also work for derived classes
        self.__dict__ = newStore.__dict__ #copy the (all) data attributes
        f.close()


    def save(self,fname):
        '''
        Dump the class data into a csv or pickle file
        
        The encoding is determined by the filename's extension:
        'csv' : When the filename ends in '.csv' the routine tries to 
                interpret the file as comma seperated values. The variable 
                names must be in the first row
        Any other extension is considered to mean a file in Python's pickle
        format.
        
        Arguments:
        fname    : filename; string
        
        Returns:
        None
        '''
        fext = self._getExtension(fname)
        if fext == 'csv':
            self._saveCSV(fname)
        else: #elif fext == 'pickle':
            self._savePickle(fname)
#        elif fext == 'she':
#            self.save_shelve(fname)
#        else:
#            raise 'This class only works on csv, pickle, and shelve files'


    def _saveCSV(self,fname):
        '''Dump the data into a csv file'''
        f = open(fname,'w')
        #write header - time and date
        today = datetime.datetime.today()
        date = today.date().isoformat()
        time = today.time().strftime('%H:%M:%S')
        f.write('#Generated on %s - %s\n' % (date, time))
        #f.write('\n')
        #write data
        writer = csv.writer(f)
        nameList = self.variableNames() #get sorted list of variable names
        writer.writerow(nameList)   #write the variable names
        writer.writerows(self.dataArray) #write the numeric data
        f.close()


    def _savePickle(self,fname):
        '''Dump the data into a binary pickle file'''
        f = open(fname,'wb')
        cPickle.dump(self, f, 2)
        f.close()


    def delete(self, *varNames):
        '''
        Delete specified variables from the DataStore.
        
        This is a potentially slow operation, because it is implemented
        with the extract() method. It internally creates a copy of the 
        store object.
        
        Arguments:
            *varNames : Variable names of the time series that should be in 
                        the new object; string
        Returns:
        '''
        #create list of variables we want to keep in the store
        keepVars = self.variableNames()
        for name1 in varNames:
            keepVars.remove(name1)
        #create new DataStore without the deleted variables
        newStore = self.extract(*keepVars)
        #get the data attributes of the new store - become the new store
        self.__dict__ = newStore.__dict__


    def extract(self, *varNames):
        '''
        Crate a new DataStore object with only the specified variables.
        
        Arguments:
            *varNames : Variable names of the time series that should be in 
                        the new object; string
        Returns:
            New DataStore object.
        '''
        #test if all requested variables are in the store
        myVars = set(self.variableNames())
        reqVars = set(varNames)
        unknownVars = reqVars - myVars
        if unknownVars:
            raise KeyError('Unknown variable(s): %s' % str(list(unknownVars))) #IGNORE:E1010
        #compute size of new array and create it
        newNumCols = len(varNames)
        newNumRows = self.numObs()
        newArray = zeros((newNumRows, newNumCols))
        #create new DataStore object
        #TODO: create object of derived class
        newStore = ArrayStore(newArray, varNames)
        #copy the variables into the new array
        for name1 in varNames:
            newStore.set(name1, self.get(name1))
            
        return newStore
            

#    def delobs(self,sel):
#        '''
#        Deleting specified observations, changing dictionary in place
#        '''
#        raise Exception('Method "delobs" is not yet implemented.') #IGNORE:E1010


    def get(self, varName):
        '''
        Return the contents of one time series. 
        Does not copy the data, but returns a slice of the original array.
        
        Arguments:
        varName : variable name; string.
        
        Returns:
        One variable; ndarray. 
        '''
        i = self.varNameDict[varName]
        return self.dataArray[:,i]
    

    def set(self, varName, newVals):
        '''
        Change the values of one time series.
        If the variable name is unknown to the object, the variable is added.
        
        Arguments:
        varName : variable name; string.
        values  : an array of compatible size
        
        Retuns:
        self, the object (so operations can be chained).
        '''
        #test compatibility of input array
        if not isinstance(newVals, ndarray):
            raise TypeError('Argument "newVals" must be of type "numpy.ndarray"') #IGNORE:E1010
        if not (self.numObs() == newVals.shape[0]):
            raise ValueError('Argument "newVals" must have same number of rows as the existing variables.') #IGNORE:E1010
        #change existing data
        if varName in self.varNameDict:
            i = self.varNameDict[varName]
            self.dataArray[:,i] = newVals
            return self
        #add new variable 
        else:
            #add new variable name to index dict
            self.varNameDict[varName] = self.numVars()
            #add new data to the array
            newVals = newVals.reshape((self.numObs(),1))
            self.dataArray = hstack((self.dataArray, newVals))
            return self
            
        
    def printStats(self, *varNames):
        ''' Printing descriptive statistics on selected variables'''
        #no arguments means all variables
        if len(varNames) == 0:
            varNames = self.variableNames()

        print
        #print '\n=============================================================================='
        #print '============================ Database information ============================'
        print '==============================================================================\n'
        #print 'file:                %s' % self.DBname
        print '# observations : %s' % self.numObs()
        print '# variables    : %s' % self.numVars()
        print
        print 'var                  min          max          mean         std.dev      nan'
        print '=============================================================================='

        for name1 in varNames:
            variable1 = self.get(name1)
            whereNan = isnan(variable1)
            variable1 = variable1[whereNan == False] #remove nan values from vector
            minVal = variable1.min()
            maxVal = variable1.max()
            meanVal = variable1.mean()
            stdDev = variable1.std()
            print '''%-20s %-12g %-12g %-12g %-12g %-12.0g''' \
               % (name1, minVal, maxVal, meanVal, stdDev, sum(whereNan))


    def plot(self, *varNames):
        '''
        Plot the specified time series into the current graph.
        '''
        #get the time. If a time vector is present, 
        #it will then be used as X-coordinate
        timeVect = None
        if self.varNameDict.has_key('time'):
            timeVect = self.get('time')
            pylab.xlabel("time")
        #plot variables in variable list
        for name1 in varNames:
            varVect = self.get(name1)
            if timeVect:
                pylab.plot(timeVect, varVect, label=name1)
            else:
                pylab.plot(varVect, label=name1)
        
        #pylab.legend()        
        return 


    def __repr__(self):
        '''Create a string representation that is valid python code.'''
        #TODO: make output more beautifull
        return 'ArrayStore(' \
                + repr(self.dataArray) +', ' \
                + repr(self.variableNames()) + ')'
    
    
#    TODO: def __iter__(self):
#        '''let for loop iterate over children'''
#
#    TODO: def __len__(self):
#        '''return number of children'''
#
#    TODO: def __getitem__(self, i):
#        '''Read variable through []'''
#        
#    TODO: def __setitem__(self, i, val):
#        '''Change variable through []'''


#------------ testcode --------------------------------------------------
import unittest
from scipy import ones, linspace, all

class TestDataStore(unittest.TestCase):
    '''Unit tests for the DataStore class'''
    
    def setUp(self):
        '''perform common setup tasks for each test'''
        self.numData50 = linspace(0, 29, 30).reshape(6, 5) #IGNORE:E1101
        self.varNamesAF = ['a','b','c','d','e']
        self.store50 = ArrayStore(self.numData50, self.varNamesAF)
        #print self.store50.data
        #print self.store50.varNames

        
    def test__init__1(self):
        '''test __init__ and createFromData'''
        #init empty object
        store = ArrayStore
        #init with array and list
        data = self.numData50
        names = ['a','b','c','d','e']
        store = ArrayStore(data, names)
        #init with array and tuple
        data = self.numData50
        names = ('a','b','c','d','e')
        store = ArrayStore(data, names)
        #init with array and dict
        #use the internal dict as argument for init
        data = self.numData50
        nameDict = store.varNameDict
        store = ArrayStore(data, nameDict)
        
    def test__init__2(self):
        '''test __init__ from file'''
        self.store50.save('test_datastore.dstore')
        newStore = ArrayStore(fileName='test_datastore.dstore')
        self.assertTrue(all(newStore.dataArray == self.store50.dataArray))
        self.assertTrue(all(newStore.varNameDict == self.store50.varNameDict))
        
    def test__init__3(self):
        '''test __init__ and createFromData - error handling'''
        self.assertRaises(TypeError, self.raise__init__1)
        self.assertRaises(TypeError, self.raise__init__2)
        self.assertRaises(ValueError, self.raise__init__3)
        self.assertRaises(ValueError, self.raise__init__4)
        self.assertRaises(TypeError, self.raise__init__5)
        self.assertRaises(ValueError, self.raise__init__6)
    def raise__init__1(self):
        '''raise: both arguments of init must be given'''
        data = self.numData50
        ArrayStore(data)
    def raise__init__2(self):
        '''raise: both arguments of init must be given'''
        names = ['a','b','c','d','e']
        ArrayStore(names)
    def raise__init__3(self):
        '''raise: data must be 2D array'''
        data = ones(50) #create 1D array
        names = ['a','b','c','d','e']
        ArrayStore(data, names)
    def raise__init__4(self):
        '''raise: data and variable name must have compatible sizes'''
        data = self.numData50
        names = ['a','b','c','d']
        ArrayStore(data, names)
    def raise__init__5(self):
        '''raise: variable names must be strings'''
        data = self.numData50
        names = ['a',1,'c','d','e']
        ArrayStore(data, names)
    def raise__init__6(self):
        '''raise: variable names must be unique.'''
        data = self.numData50
        names = ['a','a','c','d','e']
        ArrayStore(data, names)
        
    
    def test_copy(self):
        '''Test copying the DataStore object'''
        newStore = self.store50.copy()
        self.assertTrue(all(newStore.dataArray == self.store50.dataArray))
        self.assertTrue(all(newStore.varNameDict == self.store50.varNameDict))

        
    def test_delvar(self):
        '''Test deleting variables'''
        self.store50.delete('d','b','e')
        self.assertTrue(self.store50.numVars() == 2)
        
        
    def test_extract(self):
        '''Test the extract function'''
        newStore = self.store50.extract('d','b','e')
        self.assertTrue(newStore.numVars() == 3)
        self.assertTrue(all(newStore.get('d') == self.store50.get('d')))
        self.assertTrue(all(newStore.get('b') == self.store50.get('b')))
        self.assertTrue(all(newStore.get('e') == self.store50.get('e')))
        self.assertRaises(KeyError, self.raise_extract)
    def raise_extract(self):
        '''Test errors of the extract function'''
        self.store50.extract('d','f','g')
        
        
    def test_get(self):
        '''Test the get function'''
        varA = self.store50.get('a')
        varC = self.store50.get('c')
        #print repr(varA)
        #print repr(varC)
        self.assertTrue(all(varA == array([0., 5., 10., 15., 20., 25.])))
        self.assertTrue(all(varC == array([2., 7., 12., 17., 22., 27.])))
        self.assertRaises(KeyError, self.raise_get_1)
    def raise_get_1(self):
        self.store50.get('z')
    
    
    def test_set(self):
        '''Test the set funtion.'''
        newData = array([1., 2., 3., 4., 5., 6.])
        #change existing data
        self.store50.set('a', newData)
        self.store50.set('c', newData)
        #self.store50.set('c', newData.reshape((6,1))) #does not work
        #print repr(self.store50.get('a'))
        self.assertTrue(all(self.store50.get('a') == newData))
        self.assertTrue(all(self.store50.get('c') == newData))
        #add variable
        self.store50.set('z', newData)
        self.assertTrue(all(self.store50.get('z') == newData))
        
        
    def test_save_load_pickle(self):
        '''Test saving and loading pickle files.'''
        fileName = 'test_datastore.dstore'
        self.store50.save(fileName)
        newStore = ArrayStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store50.dataArray == newStore.dataArray))
        self.assertTrue(self.store50.varNameDict == newStore.varNameDict)
    
    
    def test_save_load_csv(self):
        '''Test saving and loading CSV files.'''
        fileName = 'test_datastore.csv'
        self.store50.save(fileName)
        newStore = ArrayStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store50.dataArray == newStore.dataArray))
        self.assertTrue(self.store50.varNameDict == newStore.varNameDict)
        
     
    def test_info(self):
        '''Try if the info function.'''   
        self.store50.printStats()
        
        
    def test_plot(self):
        '''Test the plot function.'''
        pylab.figure()
        self.store50.plot('b','c','d')
        #pylab.show()
        
        
    def test__repr__(self):
        '''Test __repr__ function.'''
        repStr = repr(self.store50)
        exec 'newStore = ' + repStr
        self.assertTrue(all(self.store50.dataArray == newStore.dataArray)) #IGNORE:E0602
        self.assertTrue(self.store50.varNameDict == newStore.varNameDict)  #IGNORE:E0602

        
if __name__ == '__main__':
#    #perform the doctests
#    def doDoctest():
#        import doctest
#        doctest.testmod()   
#    doDoctest()
    
    #perform the unit tests
    #unittest.main() #exits interpreter
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataStore)
    unittest.TextTestRunner(verbosity=3).run(suite)


#    numData50 = linspace(0, 29, 30).reshape(6, 5)
#    numData50 /= 3
#    varNamesAF = ['a','b','c','d','e']
#    store50 = ArrayStore(numData50, varNamesAF)
#    print repr(store50)
#    store50.info()
#    #print store50.data
#    #print store50.varNames
#    pylab.figure()
#    store50.plot('b','c','d')
#    pylab.show()

