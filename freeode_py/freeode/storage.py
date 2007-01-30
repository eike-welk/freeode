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

#TODO: better docstrings
#TODO: some examples
'''
Two dict like classes to keep simulation results: ArrayStore, DictStore

Variables and parameters (here called attributes) can be given names, and 
then be retrieved under this name. Both classes behave much like dict; 
but can only store numeric data.

The classes have several convenience functions :
    -Save/Load the data on/from disk. 
    -Plot attributes 
    -Print some statistics

Diferences:
    ArrayStore can only store time series (variables).
    DictStore can store variables and parameters.
'''

from __future__ import division

from numpy import ndarray, array, hstack, zeros, isnan, all, empty, float #IGNORE:W0622
import copy
import cPickle
import csv
import datetime
import pylab



class BaseStore(object):
    '''
    Base class for the numeric containers. 
    Defines some common methods
    '''
    
#    csv_commentStart = '#'
#    '''Indicates comment lines in CSV files.'''
    
    #Derived classes must implement the following methods:
    #Is this a C++ habit? :-)
    def attributeNames(self):
        '''Return all attribute (variable, parameter) names in a list.'''
        raise Exception('Function must be implemented in derived classes!')
    def __getitem__(self, varName):
        '''Return the contents of one time series (through []).'''
        raise Exception('Function must be implemented in derived classes!')
    def numObs(self):
        '''Return number of obervations - length of array(s).'''
        raise Exception('Function must be implemented in derived classes!')
    def numAttr(self):
        '''Return the number of attributes (variables, parameters).'''
        raise Exception('Function must be implemented in derived classes!')

    @staticmethod 
    def _getExtension(fileName):
        '''Find the file extension of a filename.'''
        return fileName.split('.')[-1].strip()

    @staticmethod 
    def str2float(inStr):
        '''
        Convert a string to a float. 
        If the string does not encode a number, return a nan.
        '''
        try:
            return float(inStr)
        except ValueError:
            return float('nan')
    
    @staticmethod
    def stripStr(inStr):
        '''Remove leading or trailing whitespace from a string'''
        return inStr.strip()

    def plot(self, *attrNames):
        '''
        Plot the specified time series into the current graph.
        Argument:
            *attrNames : any number of attribute names; string
        '''
        #TODO: remove *attrNames magic: use list of string, or long string 't.V t.h'
#        #convert string to list containing one attribute name
#        if isinstance(attrNames, str):
#            attrNames = [attrNames]
        #If a time vector is present, use it as X-coordinate
        if 'time' in self.attributeNames():
            timeVect = self['time']
            pylab.xlabel("time")
            #plot attributes in attribute list
            for name1 in attrNames:
                pylab.plot(timeVect, self[name1], label=name1)
        #No time vector present
        else:
            pylab.xlabel("sequential number")
            #plot attributes in attribute list
            for name1 in attrNames:
                pylab.plot(self[name1], label=name1) 
        pylab.legend()        
        return


    def computeStats(self, attrNames):
        ''' 
        Print descriptive statistics on selected attributes
        Argument:
            attrNames : list of attribute names; list of strings
        '''
        #empty list means all attributes
        if len(attrNames) == 0:
            attrNames = self.attributeNames() #IGNORE:E1111
            attrNames.sort()
        
        stats = ''
        #stats += '\n============================================================================== \n'
        #stats += '============================ Statistical Information ============================ \n'
        stats += '============================================================================== \n'
        #stats += 'file:                %s' % self.DBname
        stats += '# observations : %s \n' % self.numObs()
        stats += '# attributes    : %s \n' % self.numAttr()
        stats += '\n'
        stats += 'attribute            min          max          mean         std.dev      nan \n'
        stats += '============================================================================== \n'

        for name1 in attrNames:
            var1 = self[name1]
            #compute some statistics
            whereNan = isnan(var1)
            varNoNan = var1[whereNan == False] #remove nan values from vector
            minValStr =  '%g' % varNoNan.min()
            maxValStr =  '%g' % varNoNan.max()
            meanValStr = '%g' % varNoNan.mean()
            stdDevStr =  '%g' % varNoNan.std()
            sumNanStr =  '%g' % sum(whereNan)
            stats += '%-20s %-12s %-12s %-12s %-12s %-12s \n' \
               % (name1, minValStr, maxValStr, meanValStr, stdDevStr, sumNanStr)    
        return stats
    
    
    #TODO: robust functions for checking and converting input arguments
    #TODO: robust functions for CSV reading



class ArrayStore(BaseStore):
    '''
    Doc:
    A simple data-frame, that reads and writes csv/pickle files with 
    attribute names.
    Data is stored in an array, attribute names are stored in an dictionary.
    
    ArrayStore can only store time series (variables). All time series must have the same 
    length.
    '''
    
    def __init__(self, varArray=None, nameList=None, fileName=None):
        '''
        Initialize the object.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each attribute is a collumn
        nameList  : the attribute names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        fileName  : name of a file from which the object's contents is loaded.
                    The file name is ignored if any of the other arguments are
                    specified. (Specify fileName as: fileName='foo.csv')
        '''
        BaseStore.__init__(self)
        #create empty object first - mainly for documenting data members
        self.dataArray = array([[]], 'float64')
        '''The numeric data; each collumn is a attribute.''' 
        self.attrNameDict = {}
        '''The attribute names, and associated collumn indices: {'foo':0, 'bar':1}''' 
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
        #Special case: reshape 1D Array to 2D array with one collumn
        if len(varArray.shape) == 1:
            varArray = varArray.reshape(len(varArray),1)
        #see if shapes are compatible            
        if not (len(varArray.shape) == 2):
            raise ValueError('Argument "dataArray" must be a 2D array.') #IGNORE:E1010
        if not (varArray.shape[1] == len(nameList)):
            raise ValueError('"nameList" must have an entry for each collumn of "dataArray"') #IGNORE:E1010
        #create index dictionary 
        self.attrNameDict = {}
        for i, name in enumerate(nameList):
            if not isinstance(name, str):
                raise TypeError('attribute names must be strings.') #IGNORE:E1010
            if name in self.attrNameDict:
                raise ValueError('attribute names must be unique.') #IGNORE:E1010
            self.attrNameDict[name] = i
        #store the numbers
        self.dataArray = varArray

    
    def __repr__(self):
        '''Create a string representation that is valid python code.'''
        #TODO: make output more beautifull
        return 'ArrayStore(' \
                + repr(self.dataArray) +', ' \
                + repr(self.attributeNames()) + ')'
    
    def copy(self):
        '''Create a deep copy of the object'''
        return copy.deepcopy(self)
    
    def clear(self):
        '''Remove all data from the object.'''
        emptyStore = ArrayStore()
        self.__dict__ = emptyStore.__dict__
        
    def numAttr(self):
        '''Return the number of attributes'''
        #assert self.data.shape[1] == len(self.attrNameDict)
        return self.dataArray.shape[1]
        
    def numObs(self):
        '''Return the number of obervations (same for each attribute).'''
        return self.dataArray.shape[0]
    
    def attributeNames(self):
        '''
        Return all attribute names in a list. The attributes are sorted 
        according to the index of the attribute in the internal array. 
        Small index numbers come first.
        '''
        nameIndexTuples = self.attrNameDict.items() #create list of tuple(<name>, <index>) 
        sortFunc = lambda a, b: cmp(a[1], b[1]) #function to compare the indices
        nameIndexTuples.sort(sortFunc) #sort attribute names according to their indices
        nameList = [tup[0] for tup in nameIndexTuples] #remove the index numbers
        return nameList

    def load(self, fileName):
        '''
        Load data from a csv or a pickle file of the DataStore class.
        
        The encoding is determined by the filename's extension:
        'csv' : When the filename ends in '.csv' the routine tries to 
                interpret the file as comma seperated values. The attribute 
                names must be in the first row
        Any other extension is considered to mean a file in Python's pickle
        format.
        
        Arguments:
        fileName    : filename; string
        
        Returns:
        None
        '''
        # setting the ascii/csv file name used for input
        #self.DBname = os.getcwd() + '/' + fileName

        # getting the file extension
        fext = self._getExtension(fileName)

        # opening the file for reading
        if fext == 'csv':
            self._loadCSV(fileName)
        else: #fext == 'dstore':
            self._loadPickle(fileName)


    def _loadCSV(self, fileName):
        '''Load data from a csv file.'''
        #Uses the CSV reader and an entirey hommade algorithm.
        #however there are library functions for doing this, that are  
        #probably faster:
        #    scipy.io.read_array
        #    pylab's load function (seems to be fastest)
        #TODO: more robustness
        
        #read whole file at once
        f = open(fileName, 'r')
        lines = f.readlines() 
        f.close()
        
        #self.clear()
        #delete lines that the csv reader can not understand
        for i in range(len(lines)-1,-1,-1):
            #delete comment lines
            if lines[i].startswith('#'):
                del lines[i]
            #delete blank lines (conaining only whitespace)
            if len(lines[i].strip()) == 0:
                del lines[i]
                
        #interpret remaining lines as CSV
        reader = csv.reader(lines)
        varNameList = reader.next() #first line: attribute names
        varNameList = map(self.stripStr, varNameList) #remove leading trailing spaces
        #put numbers into nested list
        dataList = []
        for line in reader:
            lineFloat = map(self.str2float, line) #convert strings to floating point
            dataList.append(lineFloat)       #append to nested list
        #convert nested list to array
        dataArray = array(dataList)
        #put data into internal structures
        self.createFromData(dataArray, varNameList)


    def _loadPickle(self, fileName):
        '''Load data from a file in pickle format.'''
        f = open(fileName, 'rb')
        newStore = cPickle.load(f) #this should also work for derived classes
        self.__dict__ = newStore.__dict__ #copy the (all) data attributes
        f.close()


    def save(self, fileName):
        '''
        Dump the class data into a csv or pickle file
        
        The encoding is determined by the filename's extension:
        'csv' : When the filename ends in '.csv' the routine tries to 
                interpret the file as comma seperated values. The attribute 
                names must be in the first row
        Any other extension is considered to mean a file in Python's pickle
        format.
        
        Arguments:
        fileName    : filename; string
        
        Returns:
        None
        '''
        fext = self._getExtension(fileName)
        if fext == 'csv':
            self._saveCSV(fileName)
        else: #elif fext == 'pickle':
            self._savePickle(fileName)


    def _saveCSV(self, fileName):
        '''Dump the data into a csv file'''
        f = open(fileName, 'w')
        #write header - time and date
        today = datetime.datetime.today()
        date = today.date().isoformat()
        time = today.time().strftime('%H:%M:%S')
        f.write('#Generated on %s - %s\n' % (date, time))
        f.write('\n')
        #write data
        writer = csv.writer(f)
        nameList = self.attributeNames() #get sorted list of attribute names
        writer.writerow(nameList)   #write the attribute names
        writer.writerows(self.dataArray) #write the numeric data
        f.close()


    def _savePickle(self, fileName):
        '''Dump the data into a binary pickle file'''
        f = open(fileName, 'wb')
        cPickle.dump(self, f, 2)
        f.close()

#    #def __delitem__(self, key):
#    def delete(self, *attrNames):
#        '''
#        Delete specified attributes from the DataStore.
#        
#        This is a potentially slow operation, because it is implemented
#        with the extract() method. It internally creates a copy of the 
#        store object.
#        
#        Arguments:
#            *attrNames : attribute names of the time series that should be in 
#                        the new object; string
#        Returns:
#        '''
#        #create list of attributes we want to keep in the store
#        keepVars = self.attributeNames()
#        for name1 in attrNames:
#            keepVars.remove(name1)
#        #create new DataStore without the deleted attributes
#        newStore = self.extract(*keepVars)
#        #get the data attributes of the new store - become the new store
#        self.__dict__ = newStore.__dict__


    def extract(self, attrNames):
        '''
        Crate a new DataStore object with only the specified attributes.
        
        Arguments:
            attrNames : attribute names of the time series that should be in 
                        the new object; string
        Returns:
            New DataStore object.
        '''
        #test if all requested attributes are in the store
        myVars = set(self.attributeNames())
        reqVars = set(attrNames)
        unknownVars = reqVars - myVars
        if unknownVars:
            raise KeyError('Unknown attribute(s): %s' % str(list(unknownVars))) #IGNORE:E1010
        #compute size of new array and create it
        newNumCols = len(attrNames)
        newNumRows = self.numObs()
        newArray = zeros((newNumRows, newNumCols))
        #create new DataStore object
        newStore = ArrayStore(newArray, attrNames)
        #copy the attributes into the new array
        for name1 in attrNames:
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
        varName : attribute name; string.
        
        Returns:
        One attribute; ndarray. 
        '''
        i = self.attrNameDict[varName]
        return self.dataArray[:,i]
    

    #def set(self, varName, newVals):
    def __setitem__(self, varName, newVals):
        '''
        Change the values of one time series (through []).
        If the attribute name is unknown to the object, the attribute is added.
        
        Arguments:
        varName : attribute name; string.
        values  : an array of compatible size
        
        Retuns:
        self, the object (so operations can be chained).
        '''
        #test compatibility of input array
        if not isinstance(newVals, ndarray):
            raise TypeError('Argument "newVals" must be of type ' +
                            '"numpy.ndarray"') 
        if not (self.numObs() == newVals.shape[0]):
            raise ValueError('Argument "newVals" must have same number ' +
                             'of rows as the existing attributes.') 
        #change existing data
        if varName in self.attrNameDict:
            i = self.attrNameDict[varName]
            self.dataArray[:,i] = newVals
            return self
        #add new attribute 
        else:
            #add new attribute name to index dict
            self.attrNameDict[varName] = self.numAttr()
            #add new data to the array
            newVals = newVals.reshape((self.numObs(),1))
            self.dataArray = hstack((self.dataArray, newVals))
            return self
            
        
    def info(self, *attrNames):
        '''
        Print some information about the object's contens.
        Argguments:
            attrNames : varaible names; string(s)
        '''
        print 
        print self.computeStats(attrNames)

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
        return all(self.dataArray == other.dataArray) and \
               self.attrNameDict == other.attrNameDict

    def __ne__(self, other):
        '''Test for inequality. Called by: a!=b; a<>b'''
        return not self.__eq__(other)

#    TODO: def __iter__(self):
#        '''let for loop iterate over attributes'''

    def __len__(self):
        '''Return number of attributes. Same as self.numAttr()'''
        return self.numAttr()



class DictStore(BaseStore):
    '''
    Class stores data in a dict.
    
    DictStore can store variables and parameters:
    All time series (variables) must have the same length. Additionally 
    scalar values (parameters) can be stored.
    '''
    
    def __init__(self, varArray=None, nameList=None, valDict=None, fileName=None):
        '''
        Initialize the object.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each attribute is a collumn
        nameList  : the attribute names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        paramDict : Dictionary of parameter value pairs
        fileName  : name of a file from which the object's contents is loaded.
                    The file name is ignored if any of the other arguments are
                    specified. (Specify fileName as: fileName='foo.csv')
        '''
        BaseStore.__init__(self)
        #Create empty object - mainly for documenting data members
        self.dataDict = {}
        '''Storage for the time series and the parameters'''
        self._numObs = None
        '''Number of observations (items) in time series (number of array elements)'''
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
        self.dataDict = {}
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
#                #the first vector determines the number of observations
#                #all other vectors must have the same length
#                if self._numObs == None and isinstance(val, ndarray):
#                    self._numObs = val.shape[0]
                #put data into object - 
                #type checking and handling of self._numObs is done in __setitem__
                self[name] = val


    def __repr__(self):
        '''Create a string representation that is valid python code.'''
        repStr = 'DictStore(valDict={' 
        for name, attr in self.dataDict.iteritems():
            repStr += '\n'
            repStr += '    ' + repr(name) + ' : ' + repr(attr) + ','
        repStr += '})'
        return repStr
    
    def copy(self):
        '''Create a deep copy of the object'''
        return copy.deepcopy(self)
    
    def clear(self):
        '''Remove all data from the object.'''
        emptyStore = DictStore()
        self.__dict__ = emptyStore.__dict__
        
    def numAttr(self):
        '''Return the number of attributes'''
        #assert self.data.shape[1] == len(self.attrNames)
        return len(self.dataDict)
        
    def numObs(self):
        '''Return the number of obervations (same for each attribute).'''
        if self._numObs == None:
            return 1
        else:
            return self._numObs
    
    def attributeNames(self):
        '''
        Return all attribute names in a list.
        Returns:
            List of strings
        '''
        return self.dataDict.keys()

    def parameterNames(self):
        '''
        Return names of attributes, that are *no* time series. 
        Those are currently scalars (float, int)
        The function is not cheap as it searches throug the dict of attributes
        Returns:
            List of strings
        '''
        nameList = []
        for name, val in self.dataDict.iteritems():
            if isinstance(val, (float, int)):
                nameList.append(name)
        return nameList

    def variableNames(self):
        '''
        Return names of attributes, that *are* time series. 
        Those are called variables and are of type ndarray
        The function is not cheap as it searches throug the dict of attributes
        Returns:
            List of strings
        '''
        nameList = []
        for name, val in self.dataDict.iteritems():
            if isinstance(val, ndarray):
                nameList.append(name)
        return nameList


    def load(self, fileName):
        '''
        Load data from a csv or a pickle file of the DataStore class.
        
        The encoding is determined by the filename's extension:
        'csv' : When the filename ends in '.csv' the routine tries to 
                interpret the file as comma seperated values. The attribute 
                names must be in the first row
        Any other extension is considered to mean a file in Python's pickle
        format.
        
        Arguments:
        fileName    : filename; string
        
        Returns:
        None
        '''
        # setting the ascii/csv file name used for input
        #self.DBname = os.getcwd() + '/' + fileName

        # getting the file extension
        fext = self._getExtension(fileName)

        # opening the file for reading
        if fext == 'csv':
            self._loadCSV(fileName)
        else: #fext == 'dstore':
            self._loadPickle(fileName)


    def _loadCSV(self, fileName):
        '''Load data from a csv file.'''
        #Uses the CSV reader and an entirey hommade algorithm.
        #however there are library functions for doing this, that are  
        #probably faster:
        #    scipy.io.read_array
        #    pylab's load function (seems to be fastest)
        #TODO: more robustness
        
        #read whole file at once
        f = open(fileName, 'r')
        lines = f.readlines() 
        f.close()
        
        #self.clear()
        #delete lines that the csv reader can not understand
        for i in range(len(lines)-1,-1,-1):
            #delete comment lines
            if lines[i].startswith('#'):
                del lines[i]
            #delete blank lines (conaining only whitespace)
            if len(lines[i].strip()) == 0:
                del lines[i]
                
        #interpret remaining lines as  CSV
        reader = csv.reader(lines)
        #First two lines: scalar values (parameters)
        nameList = reader.next() #read parameter names
        nameList = map(self.stripStr, nameList) #remove leading or trailing spaces
        dataList = reader.next() #read parameter values
        dataList = map(self.str2float, dataList) #convert strings to floating point
        self.dataDict = dict(zip(nameList, dataList)) #put data into internal dict
        #Following lines until end: array values (attributes)
        nameList = reader.next() #read parameter names
        nameList = map(self.stripStr, nameList) #remove leading or trailing spaces
        #put numbers into nested list
        dataList = []
        for line in reader:
            lineFloat = map(self.str2float, line) #convert strings to floating point
            dataList.append(lineFloat)   #append to nested list
        dataArray = array(dataList).T    #convert nested list to array
        self.dataDict.update(dict(zip(nameList, dataArray))) #add data to internal dict


    def _loadPickle(self, fileName):
        '''Load data from a file in pickle format.'''
        f = open(fileName, 'rb')
        newStore = cPickle.load(f) #this should also work for derived classes
        self.__dict__ = newStore.__dict__ #copy the (all) data attributes
        f.close()


    def save(self, fileName):
        '''
        Dump the class data into a csv or pickle file
        
        The encoding is determined by the filename's extension:
        'csv' : When the filename ends in '.csv' the routine tries to 
                interpret the file as comma seperated values. The attribute 
                names must be in the first row
        Any other extension is considered to mean a file in Python's pickle
        format.
        
        Arguments:
        fileName    : filename; string
        
        Returns:
        None
        '''
        fext = self._getExtension(fileName)
        if fext == 'csv':
            self._saveCSV(fileName)
        else: #elif fext == 'pickle':
            self._savePickle(fileName)


    def _saveCSV(self, fileName):
        '''Dump the data into a csv file'''
        f = open(fileName, 'w')
        #write header - time and date
        today = datetime.datetime.today()
        date = today.date().isoformat()
        time = today.time().strftime('%H:%M:%S')
        f.write('#Generated on %s - %s\n' % (date, time))
        f.write('\n')
        #write data
        writer = csv.writer(f)
        #Get scalar values and write them first
        f.write('#Parameters:\n')
        paramNames = self.parameterNames()
        tempStore = self.extract(paramNames)
        writer.writerow(tempStore.dataDict.keys())   #write the names
        writer.writerow(tempStore.dataDict.values()) #write the values
        #Get arrays, assemble them in a big array, and write them
        f.write('#Variables:\n')
        varNames = self.variableNames()
        tempStore = self.extract(varNames)
        writer.writerow(tempStore.dataDict.keys())   #write the names
        tempArray = array(tempStore.dataDict.values()).T #convert dict values to big array
        writer.writerows(tempArray) #write the values 
        f.close()


    def _savePickle(self, fileName):
        '''Dump the data into a binary pickle file'''
        f = open(fileName, 'wb')
        cPickle.dump(self, f, 2)
        f.close()

    def __delitem__(self, attrName):
        '''
        Delete specified attribute from the DataStore.
        Arguments:
            attrName : Name of the time series that should be deleted; string
        '''
        if not self.dataDict.has_key(attrName):
            raise KeyError('Unknown attribute name: %s' % str(attrName))
        del self.dataDict[attrName]


    def extract(self, attrNames):
        '''
        Crate a new DataStore object with only the specified attributes.
        
        The function does *not* copy the array objects.
        
        Arguments:
            attrNames : attribute names of the time series that should be in 
                        the new object; string
        Returns:
            New DataStore object.
        '''
        #test if all requested attributes are in the store
        myVars = set(self.attributeNames())
        reqVars = set(attrNames)
        unknownVars = reqVars - myVars
        if unknownVars:
            raise KeyError('Unknown attribute(s): %s' % str(list(unknownVars))) #IGNORE:E1010
        #create new ArrayStore object and put data into it
        newStore = DictStore()
        newStore._numObs = self._numObs
        for name1 in attrNames:
            #copy the attributes without expanding floats to arrays in __getitem__
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
        varName : attribute name; string.
        
        Returns:
        One attribute; ndarray. 
        '''
        rawVal = self.dataDict[varName]
        if isinstance(rawVal, ndarray):
            return rawVal
        #convert scalars (floats) to 1D arrays of length numObs()
        else:
            arrVal = empty(self.numObs(), float)
            arrVal.fill(rawVal)
            return arrVal
        

    #def set(self, varName, newVals):
    def __setitem__(self, varName, newVal):
        '''
        Change the values of one time series (through []).
        If the attribute name is unknown to the object, the attribute is added.
        
        Arguments:
        varName : attribute name; string.
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
        #if self._numObs is undetermined; this array sets the number of array elements
        if self._numObs == None and isinstance(newVal, ndarray):
            self._numObs = newVal.shape[0]
        #arrays must all have the same number of rows
        if isinstance(newVal, ndarray) and \
           not (self.numObs() == newVal.shape[0]):
            raise ValueError('Argument "newVals" must have same number ' +
                             'of rows as the existing attributes.') 
        #put data into dict
        self.dataDict[varName] = newVal
            
        
    def info(self, *attrNames):
        '''
        Print some information about the object's contens.
        Argguments:
            attrNames : varaible names; string(s)
        '''
        print
        print self.computeStats(attrNames)

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
        #all attributes must be the same
        for n in self.dataDict.keys():
            if not all(self.dataDict[n] == other.dataDict[n]):
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
        '''Return number of attributes. Same as self.numAttr()'''
        return self.numAttr()

    def __contains__(self, name):
        '''
        Return True if object contains an attribute with the given name. 
        Return False otherwise.
        Called by the "in" operator.
        '''
        return self.dataDict.has_key(name)
    
    
    
#------------ testcode -------------------------------------------------------
if __name__ == '__main__':

    import unittest
    from scipy import ones, linspace
    
    class TestArrayStore(unittest.TestCase):
        '''Unit tests for the ArrayStore class'''
        
        def setUp(self):
            '''perform common setup tasks for each test'''
            #create some data and a sorage object
            self.numData = linspace(0, 29, 30).reshape(6, 5) #IGNORE:E1101
            self.attrNames = ['a','b','c','d','e']
            self.store = ArrayStore(self.numData, self.attrNames)
            #print self.store50.data
            #print self.store50.attrNames
            #Create storage object with special attribute 'time' 
            self.storeWithTime = ArrayStore(self.numData, ['a','b','c','d','time'])
    
            
        def test__init__1(self):
            '''ArrayStore: Test __init__ and createFromData'''
            #TODO: TEST results of init
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
            #init with 1D array
            data = array([1.0, 2, 3])
            names = ['a']
            store = ArrayStore(data, names)
            
        def test__init__2(self):
            '''ArrayStore: test __init__ from file'''
            filename = 'test_arraystore.dstore'
            self.store.save(filename)
            newStore = ArrayStore(fileName=filename)
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
            '''raise: data and attribute name must have compatible sizes'''
            data = self.numData
            names = ['a','b','c','d']
            ArrayStore(data, names)
        def raise__init__5(self):
            '''raise: attribute names must be strings'''
            data = self.numData
            names = ['a',1,'c','d','e']
            ArrayStore(data, names)
        def raise__init__6(self):
            '''raise: attribute names must be unique.'''
            data = self.numData
            names = ['a','a','c','d','e']
            ArrayStore(data, names)
            
        
        def test_copy(self):
            '''ArrayStore: Test copying the DataStore object'''
            newStore = self.store.copy()
            self.assertTrue(newStore == self.store)
    
            
        def test_clear(self):
            '''ArrayStore: Test copying the DataStore object'''
            newStore = ArrayStore()
            self.store.clear()
            self.assertTrue(newStore == self.store)
    
            
    #    def test_delete(self):
    #        '''ArrayStore: Test deleting attributes'''
    #        self.store.delete('d','b','e')
    #        self.assertTrue(self.store.numAttr() == 2)
            
    
        def test_extract(self):
            '''ArrayStore: Test the extract function'''
            newStore = self.store.extract(['d','b','e'])
            self.assertTrue(newStore.numAttr() == 3)
            self.assertTrue(all(newStore['d'] == self.store['d']))
            self.assertTrue(all(newStore['b'] == self.store['b']))
            self.assertTrue(all(newStore['e'] == self.store['e']))
            self.assertRaises(KeyError, self.raise_extract)
        def raise_extract(self):
            '''ArrayStore: Test errors of the extract function'''
            self.store.extract(['d','f','g'])
            
            
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
            #add attribute
            self.store['z'] = newData
            self.assertTrue(all(self.store['z'] == newData))
            
            
        def test_save_load_pickle(self):
            '''ArrayStore: Test saving and loading pickle files.'''
            fileName = 'test_arraystore.dstore'
            self.store.save(fileName)
            newStore = ArrayStore()
            newStore.load(fileName)
            self.assertTrue(all(self.store.dataArray == newStore.dataArray))
            self.assertTrue(self.store.attrNameDict == newStore.attrNameDict)
        
        
        def test_save_load_csv(self):
            '''ArrayStore: Test saving and loading CSV files.'''
            fileName = 'test_arraystore.csv'
            self.store.save(fileName)
            newStore = ArrayStore()
            newStore.load(fileName)
            self.assertTrue(all(self.store.dataArray == newStore.dataArray))
            self.assertTrue(self.store.attrNameDict == newStore.attrNameDict)
            
         
        def test_info(self):
            '''ArrayStore: Try if the info function.'''   
            self.store.info()
            self.store.info('a', 'b')
            
            
        def test_plot(self):
            '''ArrayStore: Test the plot function.'''
            #simple plot 
            pylab.figure()
            self.store.plot('b','c','d')
            #plot with time attribute as X axis
            pylab.figure()
            self.storeWithTime.plot('b','c','d')
            
            #pylab.show()
            
            
        def test__repr__(self):
            '''ArrayStore: Test __repr__ function.'''
            repStr = repr(self.store)
            exec 'newStore = ' + repStr #IGNORE:W0122
            self.assertTrue(self.store == newStore) #IGNORE:E0602
    
    
        def test__eq____ne__(self):
            '''ArrayStore: Test comparison operators "=="; "!=".'''
            self.assertTrue(self.store == self.store)
            self.assertFalse(self.store != self.store)
            
    
    
    class TestDictStore(unittest.TestCase):
        '''Test the DictStore class'''
        
        def setUp(self):
            '''perform common setup tasks for each test'''
            self.numData = linspace(0, 29, 30).reshape(6, 5) #IGNORE:E1101
            self.attrNames = ['a','b','c','d','time']
            self.valDict = {'p':10.0, 'q':20.0}
            #create store with only vectors
            self.storeV = DictStore(self.numData, self.attrNames)
            #create store with vectors and floats
            self.store = DictStore(self.numData, self.attrNames, self.valDict)
    
          
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
            fileName = 'test_dictstore.dstore'
            self.store.save(fileName)
            newStore = DictStore(fileName=fileName)
            self.assertTrue(newStore == self.store)
            
        def test__init__3(self):
            '''DictStore: test __init__ and createFromData - error handling'''
    #        self.assertRaises(TypeError, self.raise__init__1)
    #        self.assertRaises(TypeError, self.raise__init__2)
    #        self.assertRaises(ValueError, self.raise__init__3)
            self.assertRaises(ValueError, self.raise__init__4)
            self.assertRaises(TypeError, self.raise__init__5)
            self.assertRaises(TypeError, self.raise__init__6)
    #    def raise__init__1(self):
    #        '''raise: both arguments of init must be given'''
    #        data = self.numData
    #        DictStore(data)
    #    def raise__init__2(self):
    #        '''raise: both arguments of init must be given'''
    #        names = ['a','b','c','d','e']
    #        DictStore(names)
    #    def raise__init__3(self):
    #        '''raise: data must be 2D array'''
    #        data = ones(50) #create 1D array
    #        names = ['a','b','c','d','e']
    #        DictStore(data, names)
        def raise__init__4(self):
            '''raise: data arrays must have compatible sizes'''
            vals = {'a':array([1.0,2,3]), 'b':array([4.0,5,6,7])}
            DictStore(valDict = vals)
        def raise__init__5(self):
            '''raise: attribute names must be strings'''
            vals = {1:array([1.0,2,3]), 'b':array([4.0,5,6])}
            DictStore(valDict = vals)
        def raise__init__6(self):
            '''raise: valDict must be a dict.'''
            vals = [array([1.0,2,3]), array([4.0,5,6])]
            DictStore(valDict = vals)
            
        
        def test_copy(self):
            '''DictStore: Test copying the DataStore object'''
            newStore = self.store.copy()
            self.assertTrue(newStore == self.store)
    
            
        def test_clear(self):
            '''ArrayStore: Test copying the DataStore object'''
            newStore = DictStore()
            self.store.clear()
            self.assertTrue(newStore == self.store)
    
            
        def test_delvar(self):
            '''DictStore: Test deleting attributes'''
            del self.store['d']
            del self.store['b']
            del self.store['p']
            self.assertTrue(self.store.numAttr() == 4)
            
            
        def test_extract(self):
            '''DictStore: Test the extract function'''
            newStore = self.store.extract(['d','b','p'])
            #newStore.save('test_dictstore1.csv')
    #        print self.store['p']
    #        print newStore['p']
            self.assertTrue(newStore.numAttr() == 3)
            self.assertTrue(all(newStore['d'] == self.store['d']))
            self.assertTrue(all(newStore['b'] == self.store['b']))
            self.assertTrue(all(newStore['p'] == self.store['p']))
            self.assertRaises(KeyError, self.raise_extract)
        def raise_extract(self):
            '''DictStore: extract: fail because unknown attribute name.'''
            self.store.extract(['d','f','g'])
            
            
        def test__getitem__(self):
            '''DictStore: Test retrieving information from the object.'''
            varA = self.store['a']
            varC = self.store['c']
            parP = self.store['p']
            #print repr(varA)
            #print repr(varC)
            self.assertTrue(all(varA == array([0., 5., 10., 15., 20., 25.])))
            self.assertTrue(all(varC == array([2., 7., 12., 17., 22., 27.])))
            self.assertTrue(all(parP == array([10., 10., 10., 10., 10., 10.])))
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
            #add attribute
            self.store['z'] = newData
            self.assertTrue(all(self.store['z'] == newData))
            
            
        def test_save_load_pickle(self):
            '''DictStore: Test saving and loading pickle files.'''
            fileName = 'test_dictstore.dstore'
            self.store.save(fileName)
            newStore = DictStore()
            newStore.load(fileName)
            self.assertTrue(self.store == newStore)
        
        
        def test_save_load_csv(self):
            '''DictStore: Test saving and loading CSV files.'''
            fileName = 'test_dictstore.csv'
            self.store.save(fileName)
            newStore = DictStore()
            newStore.load(fileName)
            #newStore.save('test_dictstore1.csv')
            self.assertTrue(self.store == newStore)
            
         
        def test_info(self):
            '''DictStore: Try the info function.'''   
            self.store.info()
            
            
        def test_plot(self):
            '''DictStore: Test the plot function.'''
            #simple plot time attribute as X axis
            pylab.figure()
            self.store.plot('b','c','d','p')
            #pylab.show()
            
            
        def test__repr__(self):
            '''DictStore: Test __repr__ function.'''
            repStr = repr(self.store)
            #print repStr
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
            

#------ Run the tests --------------------------------------------------------
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

    #pylab.show()
    
#    numData50 = linspace(0, 29, 30).reshape(6, 5)
#    numData50 /= 3
#    attrNamesAF = ['a','b','c','d','e']
#    store = ArrayStore(numData50, attrNamesAF)
#    print repr(store)
#    store.info()
#    #print store.data
#    #print store.attrNames
#    pylab.figure()
#    store.plot('b','c','d')
#    pylab.show()

