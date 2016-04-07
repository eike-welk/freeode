###############################################################################
                                   Freeode
###############################################################################

Compiler for the SIML Simulation Language
###############################################################################

This package contains a compiler for a specialized language (SIML), for the
simulation of continuous systems, by solving differential equations. 
Only ordinary differential equations (ODE) can be currently solved.

The Compiler is written in ``Python``.
The generated simulation program is also in the Python programming language, 
using the ``Numpy``, ``Scipy`` and ``Matplotlib`` libraries.

The project's website, which contains more information about the SIML language
is here:

    http://freeode.sourceforge.net/index.html


Directories
===============================================================================

The top level directories:

docs-ideas/
    General project documentation, for example about implementing programming
    languages.

docs-siml/
    Documentation of the SIML language.

freeode_cpp/
    Source code of the old compiler, which was written in C++.

freeode_py/
    Source code of the current compiler, which is written in Python.

models/
    Example models.

website/
    Code for the project's website.

