..  Copyright (C) 2010 - 2010 Eike Welk 

    License: GNU FDL

    Everyone is permitted to copy, distribute and/or modify this
    document under the terms of the GNU Free Documentation License,
    Version 1.3 or any later version published by the Free Software
    Foundation; with no Invariant Sections, no Front-Cover Texts and
    no Back-Cover Texts. A copy of the license is included in the
    file "GNU-Free-Documentation-License-1.3.txt"

************************************
The Siml Tutorial - Bioreactors
************************************

The Siml programming language is a simple domain specific language to solve 
differential equations. The differential equation are solved numerically.
The compiler produces a program in the Python language, that performs the 
numerical computations.
The generated Python program can be used as a stand-alone program, 
or as a module of a more complex program.

This introduction should teach you enough of the Siml language
that you can write simple simulations yourself.
The text assumes that you have some experience in writing simple computer 
programs, and a basic knowledge of differential equations.

The examples are taken from the field of biotechnology.


Example 1: Exponential Growth
=============================

Under favorable conditions bacteria grow at a constant (and often fairly fast)
rate. If these favorable conditions can be maintained, the newly produced 
bacteria also grow at the same rate. This results in exponential growth of the 
bacterial biomass.   

Differential equation :eq:`biomass_exp` describes this behavior. The constant 
**µ** is the growth speed.

.. math::
    :label: biomass_exp

    {dx \over dt} = \mu \cdot X

With :math:`\mu = 0.3`, and the initial value :math:`x = 0.1`, one can 
compute a closed-form solution :eq:`biomass_exp_soln`. This exact solution
can be used to check the correctness of the numerical solution.

.. math::
    :label: biomass_exp_soln 

    x = 0.1 \cdot e^{0.3 \cdot time}

The listing below shows a Siml program that computes a numerical solution of 
differential equation :eq:`biomass_exp`.

.. literalinclude:: models/biological/exponential_growth.siml
    :language: siml
    :linenos:    

The Exponential Growth program.

The following sections discuss the program in detail:


Comments
--------

Comments start with a ``#`` character and extend to the end of the line.
The first line of the program contains a comment that covers the whole line.
In line three there is a comment that covers only part of the line.  


Whitespace
----------

In Siml whitespace is significant, exactly as in the 
`Python <http://docs.python.org/tutorial/>`_ language. 
Statements are grouped by indenting them to a common level.
Observe how the four lines starting with: ``data`` and ``func`` are all 
indented to the same column.
Also observe that the lines immediately following the ``func`` statements
also have the same indent.  


Object Oriented Language
------------------------

In Siml all simulations are objects [#like_java]_. They must have certain *main* methods,
that are called by the run time library during the simulation:

* The **initialize** method is invoked once at the beginning of the simulation.
* The **dynamic** method contains the differential equations. It is called 
  repeatedly during the simulation.
* The **final** method is invoked at the end.


``class`` Statement
-------------------

.. literalinclude:: models/biological/exponential_growth.siml
    :lines: 2-6
    :language: siml

Lines 2-6 of the Exponential Growth program.

The ``class`` statement defines an object. The 
simulation object's name ``ExponentialGrowth`` can be freely chosen by the user.
The colon ``:`` after the name is mandatory. All statements in the body 
of the simulation object have to be indented to the same level.


``data`` Statement
------------------
   
.. literalinclude:: models/biological/exponential_growth.siml
    :lines: 3
    :language: siml

Line 3 of the Exponential Growth program.

Define the variable **x** as a floating point number.

.. todo:: Float ":"

The ``data`` statement defines attributes (variables, parameters and constants).
In Siml attributes have to be defined before they can be used 
(differently to Python). 


``func`` Statement 
------------------

.. literalinclude:: models/biological/exponential_growth.siml
    :lines: 5
    :language: siml

Line 5 of the Exponential Growth program.

Here the method ``initialize`` is defined.
The ``func`` keyword defines functions and methods [#member_functions]_.
All statements in the method's body must be indented to the same level.

.. todo:: this

.. todo:: attribute access


``initialize`` method
---------------------

.. literalinclude:: models/biological/exponential_growth.siml
    :lines: 5-7 
    :language: siml

Lines 5-7 of the Exponential Growth program.

The ``initialize`` method is invoked once at the beginning of the simulation.

Here it first computes the *initial value* of the (state) variable **x**.

Then the *duration* of the simulation (20), and the *resolution* on the time
axis (0.1) are determined. 
The simulation always starts at time=0.
Therefore the simulation's variables will be recorded 200 times.

The built in function ``solution_parameters`` has two parameters:

* ``duration``:           Duration of the simulation.
* ``reporting_interval``: Time between data points
                                

``dynamic`` method
---------------------

.. literalinclude:: models/biological/exponential_growth.siml
    :lines: 9-10 
    :language: siml

Lines 9-10 of the Exponential Growth program.

The ``dynamic`` method contains the *differential equations*.
It is invoked many times during the simulation by the solver.

In this simulation, ``dynamic`` computes the *time derivative* of ``x``.

The expression ``$x`` denotes the *time derivative*. 
The dollar(``$``) operator is multi functional: it accesses the time derivative, 
and it also tells the compiler that a variable is a *state variable* 
[#dollar_operator]_. 


``final`` method
---------------------

.. literalinclude:: models/biological/exponential_growth.siml
    :lines: 12-14 
    :language: siml

Lines 12-14 of the Exponential Growth program.

The ``final`` method is invoked at the end of the simulation.

In this simulation proigram is creates a graph of the variable ``x`` versus
``time`` with the built in ``graph`` function. 
Then it sends a short text to the standard output with the built in ``print`` 
function. The text contains the final values of ``x`` and ``time``. 


Running the Simulation
----------------------

The Exponential Growth program is available on the website, and in the 
``*.tar.gz`` and ``*.zip`` archives as ``models/biological/exponential_growth.siml``

The simulation program can be typed into any text editor. 
For details on editors see: :ref:`editor-usage-intro`.

If you have saved the Exponential Growth program under the name 
``exponential_growth.siml`` you can compile and run the program at once by typing 
the following into a shell window:

.. code-block:: bash

    $> simlc exponential_growth.siml -r all

When run, the simulation opens a window with a graph similar to the one below.
The graph matches the exact solution :eq:`biomass_exp_soln` 
(:math:`x = 0.1 \cdot e^{0.3 \cdot time}`) very well.

.. figure:: exponential_growth_x.png

    Biomass concentration versus simulation time.

Example 2: Batch Reactor 
========================

The second example is more complex as well as more detailed. 
It consists of two coupled differential
equations, both are non linear. The bacteria this time live in a 
*batch reactor*. This is a 
container which is initially full of nutrient broth, and a small initial 
amount of bacteria. While the bacteria multiply in the reactor, they consume 
the nutrients until there are none left. In the end there is a 
high concentration of bacteria in the reactor and a low concentration of 
nutrients.

The simulation does not simulate the size of the reactor, only the 
concentrations of bacteria and nutrients. The reactor could be a shaking flask
as well as a big tank. 

The simulation has two state variables:
**X** the concentration of biomass, and
**S** the concentration of nutrients (usually called *substrate*).
The growth speed **µ** is an algebraic variable.


The growth of the bacteria is described by equation :eq:`biomass_eq`; 
the nutrient consumption is described by equation :eq:`substrate_eq`.
The growth speed of the biomass :eq:`growth_speed` is dependent on the 
nutrient concentration.

.. math::
    :label: biomass_eq

    {dX \over dt} = \mu \cdot X

.. math:: 
    :label: substrate_eq
    
    {dS \over dt} = - {1 \over Y_{xs}} \cdot  \mu \cdot X

.. math::
    :label: growth_speed

    \mu = \mu_{max} \cdot {S \over S+K_s}


SIML Program
------------

This SIML program solves the system of differential equations.
The initial values and parameters are realistic values for 
*Corynebacterium Glutamicum* growing on lactate.

.. literalinclude:: models/biological/bioreactor_simple.siml
    :language: siml
    :linenos:

.. todo:: param const
.. todo:: short all functions

The differential equations are in the **dynamic** function.
The **initialize** function is invoked once at the beginning of the simulation,
the **final** function is invoked at the end.



Running the Simulation
----------------------

The program for the batch reactor is available on the website, and in the 
``*.tar.gz`` and ``*.zip`` archives as ``models/biological/bioreactor_simple.siml``

The simulation program can be typed into any text editor. 
For details on editors see: :ref:`editor-usage-intro`.

If you have saved the program under the name 
``bioreactor_simple.siml`` you can compile and run the program at once by typing 
the following into a shell window:

.. code-block:: bash

    $> simlc bioreactor_simple.siml -r all

At the end of the simulation a window opens, that shows the simulation results:

.. figure:: bioreactor_simple--S-X.png

    Graph of X, S and mu, versus simulation time.




.. _editor-usage-intro:

Editors
=======

A program in the Siml language can be typed into any text editor. If the editor has
syntax highlighting, choose Python highlighting which works reasonably well
for Siml.

For editors based on the *Kate Part* (
`Kate <http://kate-editor.org/>`_,
`Kwrite <http://kate-editor.org/about-kwrite/>`_,
`Kdevelop <http://www.kdevelop.org/>`_)
there is a special highlight file for Siml available: ``hl_siml.xml``.
To copy this file to the Kate Part's highlight directory run the script
``hl_install`` (in a shell window).

.. code-block:: bash

    $> ./hl_install 




.. rubric:: Footnotes

.. [#like_java] In this respect Siml is similar to the 
        `Java <http://en.wikipedia.org/wiki/Java_%28programming_language%29#Hello_world>`_ 
        programming language.

.. [#member_functions] You may call methods *member functions* in Siml, 
        because there are some deliberate similarities to the 
        `C++ <http://en.wikipedia.org/wiki/C%2B%2B_classes#Member_functions>`_    
        programming language: The special `this` argument (which is hidden in C++)
        that contains a refference to the current object, and the automatic 
        attribute lookup through ``this``.

.. [#dollar_operator] The dollar operator really has three functions: it 
        accesses the time derivative; it marks a variable as a state variable;
        and it creates a place to store the time derivative (if necesary). The time 
        derivative is just an other variable, but usually it can only be 
        accessed by the ``$`` operator. 
                
                
