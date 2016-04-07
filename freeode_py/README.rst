###############################################################################
                                   Freeode
                            SIML Simulation Language
###############################################################################

This package contains a compiler for a specialized language (SIML) for the
simulation of differential equations (ODE). The generated simulation program
is in the Python programming language, using the Numpy and Scipy libraries.



Prerequisites
=============
- The compiler needs Python version 2.6 or newer; however below Python 3.0. 
  It contains a modified copy of the Pyparsing library. 
  http://www.python.org/
- The generated simulation programs additionally depend on three libraries for 
  numerical computations and plotting: "numpy", "scipy", "matplotlib". 
  http://numpy.scipy.org/
  http://www.scipy.org/
  http://matplotlib.sourceforge.net/

  These libraries exist for most popular operation systems (Linux/Windows/Mac). 
  Installation instructions:
    http://www.scipy.org/Installing_SciPy/Linux
  Suse users go to:
    http://download.opensuse.org/repositories/science/
    Package search:
    http://software.opensuse.org/search
  Windows users go to:
    http://www.pythonxy.com/
    http://code.enthought.com/enthon/



Installation
============
Issue the following commands in a terminal window (command line):
    python setup.py install

The file "hl_siml.xml" is a syntax highlighting definition for the Linux text
editor "kate" (more exactly for all editors using the "katepart" library). It 
will enable these editors to show SIML programs nicely colored for better
readability.
Copy it to:
~/.kde/share/apps/katepart/syntax



Usage
=====
Compile SIML programs with "simlc" script. The following command will read
the file "tank.siml" and generate a simulation program "tank.py".
	simlc tank.siml

Run the simulation program with:
	./tank.py

The compiler can also run the simulation program after compiling it
	simlc tank.siml -r all

The compiler understands the --help option.



Syntax
======
The syntax of the SIML language is fairly simple. However there exists
currently no description of the syntax, or even a tutorial. To learn the
syntax you must look at the *.siml example files in the directory "../models".



For more questions E-mail the author:
Eike.Welk@gmx.net

