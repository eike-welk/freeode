###############################################################################
                                 **Freeode**
###############################################################################

Compiler for the SIML Simulation Language
###############################################################################

This project provides a compiler for the domain specific language **SIML**, 
that is intended for simulation of continuous systems.
The systems are described with differential equations, 
which are solved during the simulation.
Only ordinary differential equations (ODE) can be solved. 

The Compiler is written in ``Python``.
The generated simulation program is also in the Python programming language, 
using the ``Numpy``, ``Scipy`` and ``Matplotlib`` libraries.

The project's website, which contains more information about the SIML language
is here:

    http://freeode.sourceforge.net/index.html

Bugs and Ideas are kept in Launchpad:

    https://bugs.launchpad.net/freeode


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

