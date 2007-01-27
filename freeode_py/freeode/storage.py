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
from numpy import ndarray, array, hstack, zeros, isnan, all, dtype
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
    
    def __init__(self, varArray=None, nameList=None, fileName=None):
        '''
        Initialize the object.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each variable is a collumn
        nameList  : the variable names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        fileName  : name of a file from which the object's contents is loaded.
                    The file name is ignored if any of the other arguments are
                    specified. (Specify fileName as: fileName='foo.csv')
        '''
        #TODO: name
        #create empty object first - mainly for documenting data members
        self.varArray = array([[]], 'float64')
        '''The numeric data; each collumn is a variable.''' 
        self.varNameDict = {}
        '''The variable names, and associated collumn indices: {'foo':0, 'bar':1}''' 
        #initialize from data
        if varArray != None or nameList != None:
            self.createFromData(varArray, nameList)
        #initialize from from file 
        elif fileName != None:
            self.load(fileName)
            
	

    def createFromData(self, varArray=None, nameList=None):
        '''
        Create object from array and list of names.
        The array in varArray is *not* copied.
        '''
        #test for correct types
        if not isinstance(varArray, ndarray):
            raise TypeError('Argument "varArray" must be of type "numpy.array"') #IGNORE:E1010
        if not isinstance(nameList, (list, tuple, dict)):
            raise TypeError('Argument "nameList" must be of type "list" or "dict"') #IGNORE:E1010
        #see if shapes are compatible
        #TODO: reshape 1D Array to 2D array with one collumn
        if not (len(varArray.shape) == 2):
            raise ValueError('Argument "dataArray" must be a 2D array.') #IGNORE:E1010
        if not (varArray.shape[1] == len(nameList)):
            raise ValueError('"nameList" must have an entry for each collumn of "dataArray"') #IGNORE:E1010
        #create index dictionary 
        #TODO: remove possibility to use dict
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
        #TODO: should the array always be copied?
        self.varArray = varArray

    
    def copy(self):
        '''Create a deep copy of the object'''
        return copy.deepcopy(self)
        
    def numAttr(self):
        '''Return the number of variables'''
        #assert self.data.shape[1] == len(self.varNames)
        return self.varArray.shape[1]
        
    def numObs(self):
        '''Return the number of obervations (same for each variable).'''
        return self.varArray.shape[0]
    
    def attributeNames(self):
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
        nameList = self.attributeNames() #get sorted list of variable names
        writer.writerow(nameList)   #write the variable names
        writer.writerows(self.varArray) #write the numeric data
        f.close()


    def _savePickle(self,fname):
        '''Dump the data into a binary pickle file'''
        f = open(fname,'wb')
        cPickle.dump(self, f, 2)
        f.close()

    #def __delitem__(self, key):
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
        keepVars = self.attributeNames()
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
        myVars = set(self.attributeNames())
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
            newStore[name1] = self[name1]
            
        return newStore
            

#    def delobs(self,sel):
#        '''
#        Deleting specified observations, changing dictionary in place
#        '''
#        raise Exception('Method "delobs" is not yet implemented.') #IGNORE:E1010


    #def get(self, varName):
    def __getitem__(self, varName):
        '''
        Return the contents of one time series (through []). 
        Does not copy the data, but returns a slice of the original array.
        
        Arguments:
        varName : variable name; string.
        
        Returns:
        One variable; ndarray. 
        '''
        i = self.varNameDict[varName]
        return self.varArray[:,i]
    

    #def set(self, varName, newVals):
    def __setitem__(self, varName, newVals):
        '''
        Change the values of one time series (through []).
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
            self.varArray[:,i] = newVals
            return self
        #add new variable 
        else:
            #add new variable name to index dict
            self.varNameDict[varName] = self.numAttr()
            #add new data to the array
            newVals = newVals.reshape((self.numObs(),1))
            self.varArray = hstack((self.varArray, newVals))
            return self
            
        
    def stats(self, *varNames):
        ''' Printing descriptive statistics on selected variables'''
        #no arguments means all variables
        if len(varNames) == 0:
            varNames = self.attributeNames()

        print
        #print '\n=============================================================================='
        #print '============================ Database information ============================'
        print '==============================================================================\n'
        #print 'file:                %s' % self.DBname
        print '# observations : %s' % self.numObs()
        print '# variables    : %s' % self.numAttr()
        print
        print 'var                  min          max          mean         std.dev      nan'
        print '=============================================================================='

        for name1 in varNames:
            variable1 = self.__getitem__(name1)
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
        if self.varNameDict.has_key('time'):
            #If a time vector is present, get the time. 
            #It will then be used as X-coordinate
            timeVect = self.__getitem__('time')
            pylab.xlabel("time")
            #plot variables in variable list
            for name1 in varNames:
                pylab.plot(timeVect, self[name1], label=name1)
        else:
            #No time vector present
            pylab.xlabel("sequential number")
            #plot variables in variable list
            for name1 in varNames:
                pylab.plot(self[name1], label=name1)
                
        #pylab.legend()        
        return 

    def __repr__(self):
        '''Create a string representation that is valid python code.'''
        #TODO: make output more beautifull
        return 'ArrayStore(' \
                + repr(self.varArray) +', ' \
                + repr(self.attributeNames()) + ')'
    
#    #Rich comparison operators (unimplemented)
#    def __lt__(self, other):
#        return NotImplemented
#    def __le__(self, other):
#        return NotImplemented
#    def __gt__(self, other):
#        return NotImplemented
#    def __ge__(self, other):
#        return NotImplemented
    
    def __eq__(self, other):
        '''Test for equality. Called by: a==b'''
        return all(self.varArray == other.varArray) and \
               self.varNameDict == other.varNameDict

    def __ne__(self, other):
        '''Test for inequality. Called by: a!=b; a<>b'''
        return not self.__eq__(other)

#    TODO: def __iter__(self):
#        '''let for loop iterate over children'''
#
#    TODO: def __len__(self):
#        '''return number of children'''



class DictStore(object):
    '''
    Store variables and parameters
    
    All time series (variables) must have the same length.
    '''
    def __init__(self, varArray=None, nameList=None, valDict=None, fileName=None):
        '''
        Initialize the object.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each variable is a collumn
        nameList  : the variable names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        paramDict : Dictionary of parameter value pairs
        fileName  : name of a file from which the object's contents is loaded.
                    The file name is ignored if any of the other arguments are
                    specified. (Specify fileName as: fileName='foo.csv')
        '''
        #TODO: name
        #Create empty object 
        self.dataDict = {}
        '''Storage for the time series and the parameters'''
        self._numObs = 0
        '''Number of observations (items) in time series'''
        #initialize from data
        if varArray != None or nameList != None or valDict != None:
            self.createFromData(varArray, nameList, valDict)
        #initialize from from file 
        elif fileName != None:
            self.load(fileName)


    def createFromData(self, varArray=None, nameList=None, valDict=None):
        '''
        Create object from other storage. 
        Accepts array and list of names; and also a dict of arrays or floats.
        '''
        #use data from array and name list
        if varArray != None or nameList != None:
            #Construct an Array Store object (to do all the type checking)
            tempStore = ArrayStore(varArray, nameList)
            #determine the number of observations
            self._numObs = tempStore.numObs()
            #put data into object
            for name in nameList:
                self[name] = tempStore[name]
        #if a dictionary of values is given, take the data out of it
        if valDict != None:
            if not isinstance(valDict, dict):
                raise TypeError('Argument "valDict" must be of type "dict"') 
            #get data from dict and put it into object
            for name, val in valDict.iteritems():
                if name in self:
                    raise ValueError('Variable names must be unique.') 
                #the first vector determines the number of observations
                #all other vectors must have the same length
                if self._numObs == 0 and isinstance(val, ndarray):
                    self._numObs = val.shape[0]
                #put data into object - type checking is done in __setitem__
                self[name] = val


    def copy(self):
        '''Create a deep copy of the object'''
        return copy.deepcopy(self)
        
    def numAttr(self):
        '''Return the number of variables'''
        #assert self.data.shape[1] == len(self.varNames)
        return len(self.dataDict)
        
    def numObs(self):
        '''Return the number of obervations (same for each variable).'''
        return self._numObs
    
    def attributeNames(self):
        '''Return all attribute names in a list.'''
        return self.dataDict.keys()

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
        writer.writerows(self.varArray) #write the numeric data
        f.close()


    def _savePickle(self,fname):
        '''Dump the data into a binary pickle file'''
        f = open(fname,'wb')
        cPickle.dump(self, f, 2)
        f.close()

    #def __delitem__(self, key):
    def delete(self, *varNames):
        '''
        Delete specified variables from the DataStore.
        
        Arguments:
            *varNames : Variable names of the time series that should be in 
                        the new object; string
        Returns:
        '''
        for name1 in varNames:
            del self.dataDict[name1]


    def extract(self, *varNames):
        '''
        Crate a new DataStore object with only the specified variables.
        
        The function does *not* copy the array objects.
        
        Arguments:
            *varNames : Variable names of the time series that should be in 
                        the new object; string
        Returns:
            New DataStore object.
        '''
        #test if all requested variables are in the store
        myVars = set(self.attributeNames())
        reqVars = set(varNames)
        unknownVars = reqVars - myVars
        if unknownVars:
            raise KeyError('Unknown attribute(s): %s' % str(list(unknownVars))) #IGNORE:E1010
        #create new ArrayStore object and put data into it
        #TODO: create object of derived class
        newStore = DictStore()
        for name1 in varNames:
            #copy the variables without the special cases in __getitem__
            newStore.dataDict[name1] = self.dataDict[name1]
            
        return newStore
            

#    def delobs(self,sel):
#        '''
#        Deleting specified observations, changing dictionary in place
#        '''
#        raise Exception('Method "delobs" is not yet implemented.') #IGNORE:E1010


    #def get(self, varName):
    def __getitem__(self, varName):
        '''
        Return the contents of one time series (through []). 
        Does *not* copy the data.
        
        Arguments:
        varName : variable name; string.
        
        Returns:
        One variable; ndarray. 
        '''
        #Special case for floats they should be converted to 1D arrays of _numObs length
        return self.dataDict[varName]
    

    #def set(self, varName, newVals):
    def __setitem__(self, varName, newVal):
        '''
        Change the values of one time series (through []).
        If the variable name is unknown to the object, the variable is added.
        
        Arguments:
        varName : variable name; string.
        values  : an array of compatible size
        
        Retuns:
        self, the object (so operations can be chained).
        '''
        #attribute names must be strings
        if not isinstance(varName, str):
            raise TypeError('Argument "varName" must be of type str.') 
        #functions accepts arrays and floats
        if not isinstance(newVal, (ndarray, float, int)):
            raise TypeError('Argument "newVals" must be of either type ' + 
                            'numpy.ndarray", "float" or "int".') 
        #arrays must all have the same number of rows
        if isinstance(newVal, ndarray) and \
           not (self.numObs() == newVal.shape[0]):
            raise ValueError('Argument "newVals" must have same number ' +
                             'of rows as the existing variables.') 
        #put data into dict
        self.dataDict[varName] = newVal
            
        
    def stats(self, *varNames):
        ''' Printing descriptive statistics on selected variables'''
        #no arguments means all variables
        if len(varNames) == 0:
            varNames = self.attributeNames()

        print
        #print '\n=============================================================================='
        #print '============================ Database information ============================'
        print '==============================================================================\n'
        #print 'file:                %s' % self.DBname
        print '# observations : %s' % self.numObs()
        print '# variables    : %s' % self.numAttr()
        print
        print 'var                  min          max          mean         std.dev      nan'
        print '=============================================================================='

        for name1 in varNames:
            var1 = self.__getitem__(name1)
            if isinstance(object, ndarray):
                #compute some statistics if var is a vector
                whereNan = isnan(var1)
                sunNanStr = '%-12g' % sum(whereNan)
                varNoNan = var1[whereNan == False] #remove nan values from vector
                minValStr = '%-12g' % varNoNan.min()
                maxValStr = '%-12g' % varNoNan.max()
                meanValStr = '%-12g' % varNoNan.mean()
                stdDevStr = '%-12g' % varNoNan.std()
            else:
                #print value if var is a float
                meanValStr = '%-12g' % var1
                minValStr, maxValStr, stdDevStr, sunNanStr = '', '', '', ''
            print '''%-20s %-12s %-12g %-12s %-12s %-12s''' \
               % (name1, minValStr, maxValStr, meanValStr, stdDevStr, sunNanStr)


    def plot(self, *varNames):
        '''
        Plot the specified time series into the current graph.
        '''
        if self.dataDict.has_key('time'):
            #If a time vector is present, get the time. 
            #It will then be used as X-coordinate
            timeVect = self.__getitem__('time')
            pylab.xlabel("time")
            #plot variables in variable list
            for name1 in varNames:
                pylab.plot(timeVect, self[name1], label=name1)
        else:
            #No time vector present
            pylab.xlabel("sequential number")
            #plot variables in variable list
            for name1 in varNames:
                pylab.plot(self[name1], label=name1)
                
        #pylab.legend()        
        return 

# TODO: __repr__
#    def __repr__(self):
#        '''Create a string representation that is valid python code.'''
#        #TODO: make output more beautifull
#        return 'ArrayStore(' \
#                + repr(self.varArray) +', ' \
#                + repr(self.variableNames()) + ')'
    
    
#    #Rich comparison operators (unimplemented)
#    def __lt__(self, other):
#        return NotImplemented
#    def __le__(self, other):
#        return NotImplemented
#    def __gt__(self, other):
#        return NotImplemented
#    def __ge__(self, other):
#        return NotImplemented
    
    def __eq__(self, other):
        '''Test for equality. Called by: a==b'''
#        if len(self.dataDict) != len(other.dataDict):
#            return False
        #The attribute names must be the same
        n1set = set(self.dataDict.keys())
        n2set = set(other.dataDict.keys())
        if n1set != n2set:
            return False
        #all variables must be the same
        for n in self.dataDict.keys():
            if not all(self[n] == other[n]):
                return False
        #we got till here: the objects must be the same
        return True
        
    def __ne__(self, other):
        '''Test for inequality. calling Called by: a!=b; a<>b'''
        return not self.__eq__(other)

    def __iter__(self):
        '''let for loop iterate over children'''
        return self.dataDict.__iter__()

    def __len__(self):
        '''return number of attributes'''
        return len(self.dataDict)

    def __contains__(self, name):
        '''
        Return True if object contains an attribute with the given name. 
        Return False otherwise.
        Called by the "in" operator.
        '''
        return name in self.dataDict
        
        

#------------ testcode --------------------------------------------------
import unittest
from scipy import ones, linspace

class TestArrayStore(unittest.TestCase):
    '''Unit tests for the ArrayStore class'''
    
    def setUp(self):
        '''perform common setup tasks for each test'''
        #create some data and a sorage object
        self.numData = linspace(0, 29, 30).reshape(6, 5) #IGNORE:E1101
        self.varNames = ['a','b','c','d','e']
        self.store = ArrayStore(self.numData, self.varNames)
        #print self.store50.data
        #print self.store50.varNames
        #Create storage object with special variable 'time' 
        self.storeWithTime = ArrayStore(self.numData, ['a','b','c','d','time'])

        
    def test__init__1(self):
        '''ArrayStore: Test __init__ and createFromData'''
        #init empty object
        store = ArrayStore()
        #init with array and list
        data = self.numData
        names = ['a','b','c','d','e']
        store = ArrayStore(data, names)
        #init with array and tuple
        data = self.numData
        names = ('a','b','c','d','e')
        store = ArrayStore(data, names)
        #init with array and dict
        #use the internal dict as argument for init
        data = self.numData
        nameDict = store.varNameDict
        store = ArrayStore(data, nameDict)
        
    def test__init__2(self):
        '''ArrayStore: test __init__ from file'''
        self.store.save('test_datastore.dstore')
        newStore = ArrayStore(fileName='test_datastore.dstore')
        self.assertTrue(newStore == self.store)
        
    def test__init__3(self):
        '''ArrayStore: test __init__ and createFromData - error handling'''
        self.assertRaises(TypeError, self.raise__init__1)
        self.assertRaises(TypeError, self.raise__init__2)
        self.assertRaises(ValueError, self.raise__init__3)
        self.assertRaises(ValueError, self.raise__init__4)
        self.assertRaises(TypeError, self.raise__init__5)
        self.assertRaises(ValueError, self.raise__init__6)
    def raise__init__1(self):
        '''raise: both arguments of init must be given'''
        data = self.numData
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
        data = self.numData
        names = ['a','b','c','d']
        ArrayStore(data, names)
    def raise__init__5(self):
        '''raise: variable names must be strings'''
        data = self.numData
        names = ['a',1,'c','d','e']
        ArrayStore(data, names)
    def raise__init__6(self):
        '''raise: variable names must be unique.'''
        data = self.numData
        names = ['a','a','c','d','e']
        ArrayStore(data, names)
        
    
    def test_copy(self):
        '''ArrayStore: Test copying the DataStore object'''
        newStore = self.store.copy()
        self.assertTrue(all(newStore.varArray == self.store.varArray))
        self.assertTrue(all(newStore.varNameDict == self.store.varNameDict))

        
    def test_delvar(self):
        '''ArrayStore: Test deleting variables'''
        self.store.delete('d','b','e')
        self.assertTrue(self.store.numAttr() == 2)
        
        
    def test_extract(self):
        '''ArrayStore: Test the extract function'''
        newStore = self.store.extract('d','b','e')
        self.assertTrue(newStore.numAttr() == 3)
        self.assertTrue(all(newStore['d'] == self.store['d']))
        self.assertTrue(all(newStore['b'] == self.store['b']))
        self.assertTrue(all(newStore['e'] == self.store['e']))
        self.assertRaises(KeyError, self.raise_extract)
    def raise_extract(self):
        '''ArrayStore: Test errors of the extract function'''
        self.store.extract('d','f','g')
        
        
    def test__getitem__(self):
        '''ArrayStore: Test retrieving information from the object.'''
        varA = self.store['a']
        varC = self.store['c']
        #print repr(varA)
        #print repr(varC)
        self.assertTrue(all(varA == array([0., 5., 10., 15., 20., 25.])))
        self.assertTrue(all(varC == array([2., 7., 12., 17., 22., 27.])))
        self.assertRaises(KeyError, self.raise__getitem__1)
    def raise__getitem__1(self):
        dummy = self.store['z']
    
    
    def test__setitem__(self):
        '''ArrayStore: Test changing object contents.'''
        newData = array([1., 2., 3., 4., 5., 6.])
        #change existing data
        self.store['a'] = newData
        self.store['c'] = newData
        #self.store50['c', newData.reshape((6,1))) #does not work
        #print repr(self.store50['a'])
        self.assertTrue(all(self.store['a'] == newData))
        self.assertTrue(all(self.store['c'] == newData))
        #add variable
        self.store['z'] = newData
        self.assertTrue(all(self.store['z'] == newData))
        
        
    def test_save_load_pickle(self):
        '''ArrayStore: Test saving and loading pickle files.'''
        fileName = 'test_datastore.dstore'
        self.store.save(fileName)
        newStore = ArrayStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store.varArray == newStore.varArray))
        self.assertTrue(self.store.varNameDict == newStore.varNameDict)
    
    
    def test_save_load_csv(self):
        '''ArrayStore: Test saving and loading CSV files.'''
        fileName = 'test_datastore.csv'
        self.store.save(fileName)
        newStore = ArrayStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store.varArray == newStore.varArray))
        self.assertTrue(self.store.varNameDict == newStore.varNameDict)
        
     
    def test_info(self):
        '''ArrayStore: Try if the info function.'''   
        self.store.stats()
        
        
    def test_plot(self):
        '''ArrayStore: Test the plot function.'''
        #simple plot 
        pylab.figure()
        self.store.plot('b','c','d')
        #plot with time variable as X axis
        pylab.figure()
        self.storeWithTime.plot('b','c','d')
        
        #pylab.show()
        
        
    def test__repr__(self):
        '''ArrayStore: Test __repr__ function.'''
        repStr = repr(self.store)
        exec 'newStore = ' + repStr
        self.assertTrue(all(self.store.varArray == newStore.varArray)) #IGNORE:E0602
        self.assertTrue(self.store.varNameDict == newStore.varNameDict)  #IGNORE:E0602


    def test__eq____ne__(self):
        '''ArrayStore: Test comparison operators "=="; "!=".'''
        self.assertTrue(self.store == self.store)
        self.assertFalse(self.store != self.store)
        


class TestDictStore(unittest.TestCase):
    '''Test the DictStore class'''
    
    def setUp(self):
        '''perform common setup tasks for each test'''
        self.numData = linspace(0, 29, 30).reshape(6, 5) #IGNORE:E1101
        self.varNames = ['a','b','c','d','time']
        self.valDict = {'p':1.0, 'q':2}
        #create store with only vectors
        self.storeV = DictStore(self.numData, self.varNames)
        #create store with vectors and floats
        self.store = DictStore(self.numData, self.varNames, self.valDict)

      
    def test__init__1(self):
        '''DictStore: Test __init__ and createFromData'''
        #TODO: test results of init
        #init empty object
        store = DictStore()
        #init with array and list, dict
        data = self.numData
        names = ['a','b','c','d','e']
        vals = {'p':1.0, 'q':2}
        store = DictStore(data, names, vals)
        #init only with dict
        vals = {'a':array([1.0,2,3]), 'b':array([4.0,5,6])}
        store = DictStore(data, names)
        
    def test__init__2(self):
        '''DictStore: test __init__ from file'''
        self.store.save('test_datastore.dstore')
        newStore = DictStore(fileName='test_datastore.dstore')
        self.assertTrue(newStore == self.store)
        
    def test__init__3(self):
        '''DictStore: test __init__ and createFromData - error handling'''
        #TODO: meaningfull errors - current tests all fail in ArrayStore
        self.assertRaises(TypeError, self.raise__init__1)
        self.assertRaises(TypeError, self.raise__init__2)
        self.assertRaises(ValueError, self.raise__init__3)
        self.assertRaises(ValueError, self.raise__init__4)
        self.assertRaises(TypeError, self.raise__init__5)
        self.assertRaises(ValueError, self.raise__init__6)
    def raise__init__1(self):
        '''raise: both arguments of init must be given'''
        data = self.numData
        DictStore(data)
    def raise__init__2(self):
        '''raise: both arguments of init must be given'''
        names = ['a','b','c','d','e']
        DictStore(names)
    def raise__init__3(self):
        '''raise: data must be 2D array'''
        data = ones(50) #create 1D array
        names = ['a','b','c','d','e']
        DictStore(data, names)
    def raise__init__4(self):
        '''raise: data and variable name must have compatible sizes'''
        data = self.numData
        names = ['a','b','c','d']
        DictStore(data, names)
    def raise__init__5(self):
        '''raise: variable names must be strings'''
        data = self.numData
        names = ['a',1,'c','d','e']
        DictStore(data, names)
    def raise__init__6(self):
        '''raise: variable names must be unique.'''
        data = self.numData
        names = ['a','a','c','d','e']
        DictStore(data, names)
        
    
    def test_copy(self):
        '''DictStore: Test copying the DataStore object'''
        newStore = self.store.copy()
        self.assertTrue(newStore == self.store)

        
    def test_delvar(self):
        '''DictStore: Test deleting variables'''
        self.store.delete('d','b','p')
        self.assertTrue(self.store.numAttr() == 4)
        
        
    def test_extract(self):
        '''DictStore: Test the extract function'''
        newStore = self.store.extract('d','b','p')
        self.assertTrue(newStore.numAttr() == 3)
        self.assertTrue(all(newStore['d'] == self.store['d']))
        self.assertTrue(all(newStore['b'] == self.store['b']))
        self.assertTrue(all(newStore['p'] == self.store['p']))
        self.assertRaises(KeyError, self.raise_extract)
    def raise_extract(self):
        '''DictStore: extract: fail because unknown attribute name.'''
        self.store.extract('d','f','g')
        
        
    def test__getitem__(self):
        '''DictStore: Test retrieving information from the object.'''
        varA = self.store['a']
        varC = self.store['c']
        parP = self.store['p']
        #print repr(varA)
        #print repr(varC)
        self.assertTrue(all(varA == array([0., 5., 10., 15., 20., 25.])))
        self.assertTrue(all(varC == array([2., 7., 12., 17., 22., 27.])))
        self.assertTrue(parP == 1.0)
        self.assertRaises(KeyError, self.raise__getitem__1)
    def raise__getitem__1(self):
        dummy = self.store['z']
    
    
    def test__setitem__(self):
        '''DictStore: Test changing object contents.'''
        newData = array([1., 2., 3., 4., 5., 6.])
        #change existing data
        self.store['a'] = newData
        self.store['c'] = newData
        #self.store['c', newData.reshape((6,1))) #does not work
        #print repr(self.store['a'])
        self.assertTrue(all(self.store['a'] == newData))
        self.assertTrue(all(self.store['c'] == newData))
        #add variable
        self.store['z'] = newData
        self.assertTrue(all(self.store['z'] == newData))
        
        
    def test_save_load_pickle(self):
        '''DictStore: Test saving and loading pickle files.'''
        fileName = 'test_datastore.dstore'
        self.store.save(fileName)
        newStore = DictStore()
        newStore.load(fileName)
        self.assertTrue(self.store == newStore)
    
    
    def test_save_load_csv(self):
        '''DictStore: Test saving and loading CSV files.'''
        fileName = 'test_datastore.csv'
        self.store.save(fileName)
        newStore = DictStore()
        newStore.load(fileName)
        self.assertTrue(self.store == newStore)
        
     
    def test_info(self):
        '''DictStore: Try if the info function.'''   
        self.store.stats()
        
        
    def test_plot(self):
        '''DictStore: Test the plot function.'''
        #simple plot time variable as X axis
        pylab.figure()
        self.store.plot('b','c','d','p')
                
        #pylab.show()
        
        
    def test__repr__(self):
        '''DictStore: Test __repr__ function.'''
        repStr = repr(self.store)
        exec 'newStore = ' + repStr #IGNORE:W0122
        self.assertTrue(self.store == newStore) #IGNORE:E0602


    def test__eq____ne__(self):
        '''DictStore: Test comparison operators "=="; "!=".'''
        #test identity to self
        self.assertTrue(self.store == self.store)
        self.assertFalse(self.store != self.store)
        #try if copy is really equal to original - just in case
        newStore = self.store.copy()
        self.assertTrue(newStore == self.store)
        #make a copy, mutate and test for inequality
        #change existing vector
        newStore = self.store.copy()
        newStore['b'] = array([0., 1., 0., 1., 0., 1.])
        self.assertFalse(newStore == self.store)
        #change existing float
        newStore = self.store.copy()
        newStore['p'] = 0. 
        self.assertFalse(newStore == self.store)
        #add new attribute
        newStore = self.store.copy()
        newStore['dummy'] = 23 
        self.assertFalse(newStore == self.store)
        


if __name__ == '__main__':
#    #perform the doctests
#    def doDoctest():
#        import doctest
#        doctest.testmod()   
#    doDoctest()
    
    #perform the unit tests
    #unittest.main() #exits interpreter
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestArrayStore))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDictStore))
    unittest.TextTestRunner(verbosity=2).run(suite)


#    numData50 = linspace(0, 29, 30).reshape(6, 5)
#    numData50 /= 3
#    varNamesAF = ['a','b','c','d','e']
#    store = ArrayStore(numData50, varNamesAF)
#    print repr(store)
#    store.info()
#    #print store.data
#    #print store.varNames
#    pylab.figure()
#    store.plot('b','c','d')
#    pylab.show()

