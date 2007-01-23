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
from numpy import ndarray, array, hstack
#from numpy.random import randn
import pylab
import cPickle
import shelve
import csv
#import copy
import os
import datetime


class DataStore(object):
    """
    Doc:
    A simple data-frame, that reads and writes csv/pickle/shelve files with 
    variable names.
    Data is stored in an array, variable names are stored in an dictionary.
    """
    
    csv_commentStart = '#'
    '''Indicates comment lines in CSV files.'''
    
    def __init__(self, dataArray=None, nameList=None, fileName=None):
        """
        Initialize the DataStore class.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each variable is a collumn
        nameList  : the variable names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        """
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
            raise ValueError('Argument "dataArray" must be a 2D array.') 
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
        """
        Finding the file extension of a filename.
        """
        return fname.split('.')[-1].strip()


    def load(self, fname):
        """
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
        """
        # setting the ascii/csv file name used for input
        #self.DBname = os.getcwd() + '/' + fname

        # getting the file extension
        fext = self._getExtension(fname)

        # opening the file for reading
        if fext == 'csv':
            self._load_csv(fname)
        else: #fext == 'dstore':
            self._load_pickle(fname)
#        elif fext == 'she':
#            self.load_shelve(fname,var)
#        else:
#            raise 'This class only works on csv, pickle, and shelve files'


#    def csvconvert(self,col):
#        """
#        Converting data in a string array to the appropriate type
#        """
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


    def _load_csv(self,fname):
        """Load data from a csv file."""
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
            if lines[i].startswith(DataStore.csv_commentStart):
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
            #TODO: convert strings to nan
            lineFloat = map(float, line) #convert strings to floating point
            dataList.append(lineFloat)   #append to nested list
        
        #convert nested list to array
        dataArray = array(dataList)
        #put data into internal structures
        self.createFromData(dataArray, varNameList)
        return


    def _load_pickle(self,fname):
        """Load data from a file in pickle format."""
        f = open(fname,'rb')
        newStore = cPickle.load(f) #this should also work for derived classes
        self.__dict__ = newStore.__dict__ #copy the (all) data attributes
        f.close()


    def save(self,fname):
        """
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
        """
        fext = self._getExtension(fname)
        if fext == 'csv':
            self._save_csv(fname)
        else: #elif fext == 'pickle':
            self._save_pickle(fname)
#        elif fext == 'she':
#            self.save_shelve(fname)
#        else:
#            raise 'This class only works on csv, pickle, and shelve files'


    def _save_csv(self,fname):
        """Dump the data into a csv file"""
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


    def _save_pickle(self,fname):
        """Dump the data into a binary pickle file"""
        f = open(fname,'wb')
        cPickle.dump(self, f, 2)
        f.close()


    def delvar(self,*var):
        """
        Delete specified variables from the DataStore, changing the object in place
        """
        raise Exception('Method "delvar" is not yet implemented.') #IGNORE:E1010


    def extract(self, *varNames):
        '''
        Crate a new DataStore object with only the specified variables.
        
        Arguments:
            *varNames : Variable names of the time series that should be in 
                        the new object; string
        Returns:
            New DataStore object.
        '''
        raise Exception('Method "extract" is not yet implemented.') #IGNORE:E1010
        

    def delobs(self,sel):
        """
        Deleting specified observations, changing dictionary in place
        """
        raise Exception('Method "extract" is not yet implemented.') #IGNORE:E1010


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
            
        
    def info(self,*var, **adict):
        """
        Printing descriptive statistics on selected variables
        """

        # calling convenience functions to clean-up input parameters
        var, sel = self.__var_and_sel_clean(var, adict)
        dates, nobs = self.__dates_and_nobs_clean(var, sel)

        # setting the minimum and maximum dates to be used
        mindate = pylab.num2date(min(dates)).strftime('%d %b %Y')
        maxdate = pylab.num2date(max(dates)).strftime('%d %b %Y')

        # number of variables (excluding date if present)
        nvar = len(var)

        print '\n=============================================================================='
        print '============================ Database information ============================'
        print '==============================================================================\n'

        print 'file:                %s' % self.DBname
        print '# obs:                %s' % nobs
        print '# variables:        %s' % nvar
        print 'Start date:            %s' % mindate
        print 'End date:            %s' % maxdate

        print '\nvar                min            max            mean        std.dev        miss    levels'
        print '=============================================================================='

        sets = {}
        for i in var:
            col = self.dataArray[i][sel];
            if type(col[0]) == string_:
                _miss = sum(col == '')
                col_set = set(col)
                sets[i] = col_set
                print '''%-5s            %-5s        %-5s        %-5s        %-5s        % -5.0f    %-5i''' % tuple([i,'-','-','-','-',_miss,len(col_set)])
            else:
                _miss = isnan(col); col = col[_miss == False]; _min = col.min(); _max = col.max(); _mean = col.mean(); _std = col.std()
                print '''% -5s            % -5.2f        % -5.2f        % -5.2f        % -5.2f        % -5.0f''' % tuple([i,_min,_max,_mean,_std,sum(_miss)])

        if sets:
            print '\n\nLevels for non-numeric data:'
            for i in sets.keys():
                print '=============================================================================='
                print '''% -5s    % -5s''' % tuple([i,sets[i]])


    def plot(self, *varNames):
        """
        Plot the specified time series into the current graph.
        """
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

    #TODO: __repr__
    #TODO: __str__

#------------ testcode --------------------------------------------------
import unittest
from scipy import ones, linspace, all

class TestDataStore(unittest.TestCase):
    '''Unit tests for the DataStore class'''
    
    def setUp(self):
        '''perform common setup tasks for each test'''
        self.numData50 = linspace(0, 29, 30).reshape(6, 5)
        self.varNamesAF = ['a','b','c','d','e']
        self.store50 = DataStore(self.numData50, self.varNamesAF)
        #print self.store50.data
        #print self.store50.varNames

        
    def test__init__1(self):
        '''test __init__ and createFromData'''
        #init empty object
        store = DataStore
        #init with array and list
        data = self.numData50
        names = ['a','b','c','d','e']
        store = DataStore(data, names)
        #init with array and tuple
        data = self.numData50
        names = ('a','b','c','d','e')
        store = DataStore(data, names)
        #init with array and dict
        #use the internal dict as argument for init
        data = self.numData50
        nameDict = store.varNameDict
        store = DataStore(data, nameDict)
        
    def test__init__2(self):
        '''test __init__ and createFromData - init from file'''
        self.store50.save('test_datastore.dstore')
        newStore = DataStore(fileName='test_datastore.dstore')
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
        DataStore(data)
    def raise__init__2(self):
        '''raise: both arguments of init must be given'''
        names = ['a','b','c','d','e']
        DataStore(names)
    def raise__init__3(self):
        '''raise: data must be 2D array'''
        data = ones(50) #create 1D array
        names = ['a','b','c','d','e']
        DataStore(data, names)
    def raise__init__4(self):
        '''raise: data and variable name must have compatible sizes'''
        data = self.numData50
        names = ['a','b','c','d']
        DataStore(data, names)
    def raise__init__5(self):
        '''raise: variable names must be strings'''
        data = self.numData50
        names = ['a',1,'c','d','e']
        DataStore(data, names)
    def raise__init__6(self):
        '''raise: variable names must be unique.'''
        data = self.numData50
        names = ['a','a','c','d','e']
        DataStore(data, names)
        
    
    def test_get(self):
        '''Test the get function'''
        varA = self.store50.get('a')
        varC = self.store50.get('c')
        #print repr(varA)
        #print repr(varC)
        self.assertTrue(all(varA == array([0., 5., 10., 15., 20., 25.])))
        self.assertTrue(all(varC == array([2., 7., 12., 17., 22., 27.])))
        self.assertRaises(KeyError, self.raise__get_1)
    def raise__get_1(self):
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
        newStore = DataStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store50.dataArray == newStore.dataArray))
        self.assertTrue(self.store50.varNameDict == newStore.varNameDict)
    
    
    def test_save_load_csv(self):
        '''Test saving and loading CSV files.'''
        fileName = 'test_datastore.csv'
        self.store50.save(fileName)
        newStore = DataStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store50.dataArray == newStore.dataArray))
        self.assertTrue(self.store50.varNameDict == newStore.varNameDict)
        
        
    def test_plot(self):
        '''Test the plot function.'''
        pylab.figure()
        self.store50.plot('b','c','d')
        #pylab.show()
        
    
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
#    varNamesAF = ['a','b','c','d','e']
#    store50 = DataStore(numData50, varNamesAF)
#    #print store50.data
#    #print store50.varNames
#    pylab.figure()
#    store50.plot('b','c','d')
#    pylab.show()

