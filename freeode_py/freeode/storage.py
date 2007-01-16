############################################################################
#    Copyright (C) 2007 by Vincent Nijs                                    #
#    v-nijs at kellogg.northwestern.edu                                    #
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
from scipy import c_, arange, array, unique, kron, ones, eye, nan, isnan, string_
from numpy import array
from numpy.random import randn
import pylab, cPickle, shelve, csv, copy, os

class DataStore(object):
	"""
	Doc:
	A simple data-frame, that reads and writes csv/pickle/shelve files with variable names.
	Data is stored in an array, variable names are stored in an dictionary.
	"""

	def __init__(self, dataArray=None, nameList=None):
		"""
		Initializing the DataStore class. 
		"""
		self.data = array([[]], 'float64')
		self.varNames = {}

	def load(self,fname,var,date):
		"""
		Loading data from a csv or a pickle file of the DataStore class.
		If this is csv file use pylab's load function. Seems much faster
		than scipy.io.read_array.
		"""
		# setting the ascii/csv file name used for input
		self.DBname = os.getcwd() + '/' + fname

		# assuming self.date_key = '' unless otherwise given
		self.date_key = date

		# getting the file extension
		fext = self._getExtension(fname)

		# opening the file for reading
		if fext == 'csv':
			f = open(fname,'r')
			self.load_csv(f)
			f.close()
		elif fext == 'pickle':
			f = open(fname,'rb')
			self.load_pickle(f)
			f.close()
		elif fext == 'she':
			self.load_shelve(fname,var)
		else:
			raise 'This class only works on csv, pickle, and shelve files'

		# specifying nobs in self.data
		self.nobs = self.data[self.data.keys()[0]].shape[0]

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

	def load_csv(self,f):
		"""
		Loading data from a csv file. Uses pylab's load function. Seems much faster
		than scipy.io.read_array.
		"""
		varnm = f.readline().split(',')

		# what is the date variable's key if any, based on index passed as argument
		if self.date_key != '':
			try:
				rawdata = pylab.load(f, delimiter=',',converters={self.date_key:pylab.datestr2num})			# don't need to 'skiprow' here
			except ValueError:																				# if loading via pylab doesn't work use csv
				rawdata = self.load_csv_nf(f)	

				# converting the dates column to a date-number
				rawdata[self.date_key] = pylab.datestr2num(rawdata[self.date_key])

			self.date_key = varnm[self.date_key]
		else:
			try:
				rawdata = pylab.load(f, delimiter=',')														# don't need to 'skiprow' here
			except ValueError:																				# if loading via pylab doesn't work use csv
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

	def load_pickle(self,f):
		"""
		Loading data from a created earlier using the the DataStore class.
		"""
		self.data = cPickle.load(f)					# loading the data dictionary

		# what is the date variable's key if any
		if self.date_key == '':
			try:
				self.date_key = cPickle.load(f)		# if nothing given assume it is in the pickle file
			except:
				print "No date series in pickle file"

	def load_shelve(self,fname,var):
		"""
		Loading data from a created earlier using the the DataStore class.
		"""
		data = shelve.open(fname)				# loading the data dictionary

		# find out if a variable list is provided
		if var == ():
			var = data.keys()

		# making sure the date variable is fetched from shelve
		if self.date_key != '':
			if not self.date_key in var: var = var + list(self.date_key)

		self.data = dict([(i,data[i]) for i in var])
		data.close()

	def save(self,fname):
		"""
		Dumping the class data dictionary into a csv or pickle file
		"""
		fext = self._getExtension(fname)
		if fext == 'csv':
			f = open(fname,'w')
			self.save_csv(f)
			f.close()
		elif fext == 'pickle':
			f = open(fname,'wb')
			self.save_pickle(f)
			f.close()
		elif fext == 'she':
			self.save_shelve(fname)
		else:
			raise 'This class only works on csv, pickle, and shelve files'

	def save_csv(self,f):
		"""
		Dumping the class data dictionary into a csv file
		"""
		writer = csv.writer(f)
		writer.writerow(self.data.keys())

		data = self.data						# a reference to the data dict
		if self.date_key != []:
			data = dict(data)				# making a copy so the dates can be changed to strings
			dates = pylab.num2date(data[self.date_key])
			dates = array([i.strftime('%d %b %y') for i in dates])
			data[self.date_key] = dates

		writer.writerows(array(data.values()).T)

	def save_pickle(self,f):
		"""
		Dumping the class data dictionary and date_key into a binary pickle file
		"""
		cPickle.dump(self.data,f,2)
		cPickle.dump(self.date_key,f,2)

	def save_shelve(self,fname):
		"""
		Dumping the class data dictionary into a shelve file
		"""
		f = shelve.open('data.she','c') 
		f = self.data
		f.close()

#	def add_trend(self,tname = 'trend'):
#		# making a trend based on nobs in arbitrary series in dictionary
#		self.data[tname] = arange(self.nobs)

#	def add_dummy(self,dum, dname = 'dummy'):
#		if self.data.has_key(dname):
#			print "The variable name '" + str(dname) + "' already exists. Please select another name."
#		else:
#			self.data[dname] = dum
#
#	def add_seasonal_dummies(self,freq=52,ndum=13):
#		"""
#		This function will only work if the freq and ndum 'fit. That is,
#		weeks and 4-weekly periods will work. Weeks and months/quarters
#		will not.
#		"""
#		if self.date_key == []:
#			print "Cannot create seasonal dummies since no date array is known"
#		else:
#			# list of years
#			years = array([pylab.num2date(i).year for i in self.data[self.date_key]])
#
#			# how many periods in does the data start
#			start = freq - sum(years ==	min(years))
#
#			# how many unique years
#			nyear = unique(years).shape[0]
#
#			# using kronecker products to make a big dummy matrix
#			sd = kron(ones(nyear),kron(eye(ndum),ones(freq/ndum))).T;
#			sd = sd[start:start+self.nobs]		# slicing the dummies to fit the data	
#			sd = dict([(("sd"+str(i+1)),sd[:,i]) for i in range(1,ndum)])
#			self.data.update(sd)				# adding the dummies to the main dict

	def delvar(self,*var):
		"""
		Deleting specified variables in the data dictionary, changing dictionary in place
		"""
		[self.data.pop(i) for i in var]

#	def keepvar(self,*var):
#		"""
#		Keeping specified variables in the data dictionary, changing dictionary in place
#		"""
#		[self.data.pop(i) for i in self.data.keys() if i not in var]

	def delvar_copy(self,*var):
		"""
		Deleting specified variables in the data dictionary, making a copy
		"""
		return dict([(i,self.data[i]) for i in self.data.keys() if i not in var])

#	def keepvar_copy(self,*var):
#		"""
#		Keeping specified variables in the data dictionary, making a copy
#		"""
#		return dict([(i,self.data[i]) for i in var])

	def delobs(self,sel):
		"""
		Deleting specified observations, changing dictionary in place
		"""
		for i in self.data.keys(): self.data[i] = self.data[i][sel]

		# updating the value of self.nobs
		self.nobs -= sum(sel)

#	def keepobs(self,sel):
#		"""
#		Keeping specified observations, changing dictionary in place
#		"""
#		# updating the value of self.nobs
#		self.nobs -= sum(sel)
#
#		sel -= 1				# making true, false and vice-versa
#		self.delobs(sel)

	def delobs_copy(self,sel):
		"""
		Deleting specified observations, making a copy
		"""
		return dict([(i,self.data[i][sel]) for i in self.data.keys()])

#	def keepobs_copy(self,sel):
#		"""
#		Keeping specified observations, making a copy
#		"""
#		sel -= 1				# making true, false and vice-versa
#		self.delobs_copy(sel)

	def get(self,*var,**sel):
		"""
		Copying data and keys of selected variables for further analysis
		"""
		# calling convenience function to clean-up input parameters
		var, sel = self.__var_and_sel_clean(var, sel)

		# copying the entire dictionary (= default)
		d = dict((i,self.data[i][sel]) for i in var)

		return d.keys(), array(d.values()).T

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

		print 'file:				%s' % self.DBname
		print '# obs:				%s' % nobs
		print '# variables:		%s' % nvar 
		print 'Start date:			%s' % mindate
		print 'End date:			%s' % maxdate

		print '\nvar				min			max			mean		std.dev		miss	levels'
		print '=============================================================================='
		
		sets = {}
		for i in var:
			col = self.data[i][sel];
			if type(col[0]) == string_:
				_miss = sum(col == '')
				col_set = set(col)
				sets[i] = col_set
				print '''%-5s			%-5s		%-5s		%-5s		%-5s		% -5.0f	%-5i''' % tuple([i,'-','-','-','-',_miss,len(col_set)]) 
			else:
				_miss = isnan(col); col = col[_miss == False]; _min = col.min(); _max = col.max(); _mean = col.mean(); _std = col.std()
				print '''% -5s			% -5.2f		% -5.2f		% -5.2f		% -5.2f		% -5.0f''' % tuple([i,_min,_max,_mean,_std,sum(_miss)]) 

		if sets:
			print '\n\nLevels for non-numeric data:'
			for i in sets.keys():
				print '=============================================================================='
				print '''% -5s	% -5s''' % tuple([i,sets[i]])
	
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

#	def __var_and_sel_clean(self, var, sel, dates_needed = True):
#		"""
#		Convenience function to avoid code duplication
#		"""
#		# find out if a variable list is provided
#		if var == ():
#			var = self.data.keys()
#			
#		# removing the date variable if it is present
#		var = [x for x in var if x != self.date_key]
#
#		# report variable label in alphabetical order
#		var.sort()
#
#		# find out if a selection rule is being used
#		# if not, set to empty tuple
#		if not sel.has_key('sel'):
#			sel = ()
#		else:
#			sel = sel['sel']
#
#		return var, sel

#	def __dates_and_nobs_clean(self, var, sel):
#		"""
#		Convenience function to avoid code duplication
#		"""
#		nobs = self.nobs
#		if len(sel):
#			nobs = nobs - (nobs - sum(sel))
#
#		if self.date_key != None and self.data.has_key(self.date_key):
#			# selecting dates from data base
#			dates = self.data[self.date_key][sel]
#		else:
#			# setting date series to start on 1/1/1950
#			dates = range(711858,nobs+711858)
#
#		return dates, nobs

	def _getExtension(self,fname):
		"""
		Finding the file extension of the filename passed to DataStore
		"""
		return fname.split('.')[-1].strip()

if __name__ == '__main__':
	pass

