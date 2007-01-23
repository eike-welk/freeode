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


class DataStore(object):
    """
    Doc:
    A simple data-frame, that reads and writes csv/pickle/shelve files with 
    variable names.
    Data is stored in an array, variable names are stored in an dictionary.
    """

    def __init__(self, dataArray=None, nameList=None):
        """
        Initialize the DataStore class.
        
        Arguments:
        dataArray : the data; 2D numpy.ndarray, each variable is a collumn
        nameList  : the variable names; list or tuple of strings. 
                    Also accepted is a dict with names:indices, which is 
                    accepted untested.
        """
        self.data = array([[]], 'float64')
        '''The numeric data; each collumn is a variable.''' #IGNORE:W0105
        self.varNames = {}
        '''The variable names, and associated collumn indices: {'foo':0, 'bar':1}''' #IGNORE:W0105
        if dataArray is not None or nameList is not None:
            self._createArrayFromData(dataArray, nameList)


    def _createArrayFromData(self, dataArray=None, nameList=None):
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
            self.varNames = nameList #a dict is accepted untested
        else:
            #create index dictionary from list
            for i, name in enumerate(nameList):
                if not isinstance(name, str):
                    raise TypeError('Variable names must be strings.') #IGNORE:E1010
                if name in self.varNames:
                    raise ValueError('Variable names must be unique.') #IGNORE:E1010
                self.varNames[name] = i
        #store the numbers
        #TODO: should the array be copied
        self.data = dataArray

    
    def numVars(self):
        '''Return the number of variables'''
        #assert self.data.shape[1] == len(self.varNames)
        return self.data.shape[1]
        
        
    def numObs(self):
        '''Return the number of obervations (same for each variable).'''
        return self.data.shape[0]
        
        
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
        #If this is csv file use pylab's load function. Seems much faster
        #than scipy.io.read_array.
        
        # setting the ascii/csv file name used for input
        #self.DBname = os.getcwd() + '/' + fname

        # getting the file extension
        fext = self._getExtension(fname)

        # opening the file for reading
        if fext == 'csv':
            self.load_csv(fname)
        else: #fext == 'dstore':
            self.load_pickle(fname)
#        elif fext == 'she':
#            self.load_shelve(fname,var)
#        else:
#            raise 'This class only works on csv, pickle, and shelve files'


    def csvconvert(self,col):
        """
        Converting data in a string array to the appropriate type
        """
        # convert missing values to nan
        col[col == ''] = 'nan'; col[col == '.'] = 'nan'
        try:
            # if a missing value is present int variables will be up-cast to float
            return col.astype('i')
        except ValueError:
            try:
                return col.astype('f')
            except ValueError:
                # if the data is a string, put back the empty string
                col[col == 'nan'] = ''
                return col

    def load_csv_nf(self,f):
        """
        Loading data from a csv file using the csv module. Return a list of arrays.
        Possibly with different types and/or missing values.
        """
        # resetting to the beginning of the file since pylab.load was already tried
        f.seek(0)

        reader = csv.reader(f)

        # putting the data in an array of strings
        datalist = array([i for i in reader])

        # converting the data to an appropriate type
        datalist = [self.csvconvert(datalist[1:,i]) for i in range(datalist.shape[1])]

        return datalist

    def load_csv(self,fname):
        """
        Loading data from a csv file. Uses pylab's load function. Seems much faster
        than scipy.io.read_array.
        """
        f = open(fname,'r')

        varnm = f.readline().split(',')

        # what is the date variable's key if any, based on index passed as argument
        if self.date_key != '':
            try:
                rawdata = pylab.load(f, delimiter=',',converters={self.date_key:pylab.datestr2num})            # don't need to 'skiprow' here
            except ValueError:                                                                                # if loading via pylab doesn't work use csv
                rawdata = self.load_csv_nf(f)

                # converting the dates column to a date-number
                rawdata[self.date_key] = pylab.datestr2num(rawdata[self.date_key])

            self.date_key = varnm[self.date_key]
        else:
            try:
                rawdata = pylab.load(f, delimiter=',')                                                        # don't need to 'skiprow' here
            except ValueError:                                                                                # if loading via pylab doesn't work use csv
                rawdata = self.load_csv_nf(f)

        # making sure that the variable names contain no leading or trailing spaces
        varnm = [i.strip() for i in varnm]

        # transforming the data into a dictionary
        if type(rawdata) == list:
            # if the csv module was used
            self.data = dict(zip(varnm,rawdata))
        else:
            # if the pylab.load module was used
            self.data = dict(zip(varnm,rawdata.T))
        
        f.close()


    def load_pickle(self,fname):
        """
        Loading data from a created earlier using the the DataStore class.
        """
        f = open(fname,'rb')
        newStore = cPickle.load(f) #this should also work for derived classes
        self.__dict__ = newStore.__dict__ #copy the data attributes
        f.close()


#    def load_shelve(self,fname,var):
#        """
#        Loading data from a created earlier using the the DataStore class.
#        """
#        data = shelve.open(fname)                # loading the data dictionary
#
#        # find out if a variable list is provided
#        if var == ():
#            var = data.keys()
#
#        # making sure the date variable is fetched from shelve
#        if self.date_key != '':
#            if not self.date_key in var: var = var + list(self.date_key)
#
#        self.data = dict([(i,data[i]) for i in var])
#        data.close()


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
            self.save_csv(fname)
        else: #elif fext == 'pickle':
            self.save_pickle(fname)
#        elif fext == 'she':
#            self.save_shelve(fname)
#        else:
#            raise 'This class only works on csv, pickle, and shelve files'


    def save_csv(self,fname):
        """
        Dumping the class data dictionary into a csv file
        """
        f = open(fname,'w')

        writer = csv.writer(f)
        writer.writerow(self.data.keys())

        data = self.data                        # a reference to the data dict
        if self.date_key != []:
            data = dict(data)                # making a copy so the dates can be changed to strings
            dates = pylab.num2date(data[self.date_key])
            dates = array([i.strftime('%d %b %y') for i in dates])
            data[self.date_key] = dates

        writer.writerows(array(data.values()).T)
        
        f.close()


    def save_pickle(self,fname):
        """
        Dumping the class data dictionary and date_key into a binary pickle file
        """
        f = open(fname,'wb')
        cPickle.dump(self, f, 2)
        f.close()


#    def save_shelve(self,fname):
#        """
#        Dumping the class data dictionary into a shelve file
#        """
#        f = shelve.open('data.she','c')
#        f = self.data
#        f.close()

#    def add_trend(self,tname = 'trend'):
#        # making a trend based on nobs in arbitrary series in dictionary
#        self.data[tname] = arange(self.nobs)

#    def add_dummy(self,dum, dname = 'dummy'):
#        if self.data.has_key(dname):
#            print "The variable name '" + str(dname) + "' already exists. Please select another name."
#        else:
#            self.data[dname] = dum
#
#    def add_seasonal_dummies(self,freq=52,ndum=13):
#        """
#        This function will only work if the freq and ndum 'fit. That is,
#        weeks and 4-weekly periods will work. Weeks and months/quarters
#        will not.
#        """
#        if self.date_key == []:
#            print "Cannot create seasonal dummies since no date array is known"
#        else:
#            # list of years
#            years = array([pylab.num2date(i).year for i in self.data[self.date_key]])
#
#            # how many periods in does the data start
#            start = freq - sum(years ==    min(years))
#
#            # how many unique years
#            nyear = unique(years).shape[0]
#
#            # using kronecker products to make a big dummy matrix
#            sd = kron(ones(nyear),kron(eye(ndum),ones(freq/ndum))).T;
#            sd = sd[start:start+self.nobs]        # slicing the dummies to fit the data
#            sd = dict([(("sd"+str(i+1)),sd[:,i]) for i in range(1,ndum)])
#            self.data.update(sd)                # adding the dummies to the main dict

    def delvar(self,*var):
        """
        Deleting specified variables in the data dictionary, changing dictionary in place
        """
        [self.data.pop(i) for i in var]

#    def keepvar(self,*var):
#        """
#        Keeping specified variables in the data dictionary, changing dictionary in place
#        """
#        [self.data.pop(i) for i in self.data.keys() if i not in var]

    def delvar_copy(self,*var):
        """
        Deleting specified variables in the data dictionary, making a copy
        """
        return dict([(i,self.data[i]) for i in self.data.keys() if i not in var])

#    def keepvar_copy(self,*var):
#        """
#        Keeping specified variables in the data dictionary, making a copy
#        """
#        return dict([(i,self.data[i]) for i in var])

    def delobs(self,sel):
        """
        Deleting specified observations, changing dictionary in place
        """
        for i in self.data.keys(): self.data[i] = self.data[i][sel]

        # updating the value of self.nobs
        self.nobs -= sum(sel)

#    def keepobs(self,sel):
#        """
#        Keeping specified observations, changing dictionary in place
#        """
#        # updating the value of self.nobs
#        self.nobs -= sum(sel)
#
#        sel -= 1                # making true, false and vice-versa
#        self.delobs(sel)

    def delobs_copy(self,sel):
        """
        Deleting specified observations, making a copy
        """
        return dict([(i,self.data[i][sel]) for i in self.data.keys()])

#    def keepobs_copy(self,sel):
#        """
#        Keeping specified observations, making a copy
#        """
#        sel -= 1                # making true, false and vice-versa
#        self.delobs_copy(sel)


    def get(self, varName):
        '''
        Return the contents of one time series. 
        Does not copy the data, but returns a slice of the original array.
        
        Arguments:
        varName : variable name; string.
        
        Returns:
        One variable; ndarray. 
        '''
        i = self.varNames[varName]
        return self.data[:,i]
    

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
        if varName in self.varNames:
            i = self.varNames[varName]
            self.data[:,i] = newVals
            return self
        #add new variable 
        else:
            #add new variable name to index dict
            self.varNames[varName] = self.numVars()
            #add new data to the array
            newVals = newVals.reshape((self.numObs(),1))
            self.data = hstack((self.data, newVals))
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
            col = self.data[i][sel];
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

    def dataplot(self,*var, **adict):
        """
        Plotting the data with variable names
        """
        # calling convenience functions to clean-up input parameters
        var, sel = self.__var_and_sel_clean(var, adict)
        dates, nobs = self.__dates_and_nobs_clean(var, sel)

        # don't try to plot non-numerical variables
        nvar = []
        for i in var:
            col = self.data[i][sel]
            if type(col[0]) != string_:
                pylab.plot_date(dates,self.data[i][sel],'o-')
                nvar = nvar + [i]

        pylab.xlabel("Time (n = " + str(nobs) + ")")
        pylab.title("Data plot of " + self.DBname)
        pylab.legend(nvar)
        if adict.has_key('file'):
            pylab.savefig(adict['file'],dpi=600)
        pylab.show()

#    def __var_and_sel_clean(self, var, sel, dates_needed = True):
#        """
#        Convenience function to avoid code duplication
#        """
#        # find out if a variable list is provided
#        if var == ():
#            var = self.data.keys()
#
#        # removing the date variable if it is present
#        var = [x for x in var if x != self.date_key]
#
#        # report variable label in alphabetical order
#        var.sort()
#
#        # find out if a selection rule is being used
#        # if not, set to empty tuple
#        if not sel.has_key('sel'):
#            sel = ()
#        else:
#            sel = sel['sel']
#
#        return var, sel

#    def __dates_and_nobs_clean(self, var, sel):
#        """
#        Convenience function to avoid code duplication
#        """
#        nobs = self.nobs
#        if len(sel):
#            nobs = nobs - (nobs - sum(sel))
#
#        if self.date_key != None and self.data.has_key(self.date_key):
#            # selecting dates from data base
#            dates = self.data[self.date_key][sel]
#        else:
#            # setting date series to start on 1/1/1950
#            dates = range(711858,nobs+711858)
#
#        return dates, nobs


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

        
    def test__init__(self):
        '''test __init__ and _createArrayFromData'''
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
        nameDict = store.varNames
        store = DataStore(data, nameDict)
        #test error handling
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
        store = DataStore(data, names)
    def raise__init__6(self):
        '''raise: variable names must be unique.'''
        data = self.numData50
        names = ['a','a','c','d','e']
        store = DataStore(data, names)
        
    
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
        fileName = 'pickle_test.dstore'
        self.store50.save(fileName)
        newStore = DataStore()
        newStore.load(fileName)
        self.assertTrue(all(self.store50.data == newStore.data))
        self.assertTrue(self.store50.varNames == newStore.varNames)
        
        
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


