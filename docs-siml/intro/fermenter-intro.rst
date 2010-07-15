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

Lines 2-4 of the Exponential Growth program.

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

Define the variable **x**.

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

.. todo:: editor save bash run

.. code-block:: bash

    $> kwrite exponential_growth.siml        #Edit Siml file
    $> simlc exponential_growth.siml -r all  #Run compiler


When run, the simulation opens a window with a graph similar to the one below.
The graph matches the exact solution :eq:`biomass_exp_soln` 
(:math:`x = 0.1 \cdot e^{0.3 \cdot time}`) very well.

.. image:: exponential_growth_x.png


Example 2: Growth Limited by Available Food
===========================================

A simple biological reactor should be simulated. The simulation has two
state variables:
**X** the concentration of biomass, and
**S** the concentration of nutrient (often called *substrate*).
The growth speed **µ** is an algebraic variable.



Differential Equations
----------------------

Change of biomass concentration :eq:`biomass_eq`

.. math::
    :label: biomass_eq

    {dX \over dt} = \mu \cdot X

Change of sugar concentration :eq:`substrate_eq`

.. math:: 
    :label: substrate_eq
    
    {dS \over dt} = - {1 \over Y_{xs}} \cdot  \mu \cdot X

with:
Growth speed of biomass :eq:`growth_speed`

.. math::
    :label: growth_speed

    \mu = \mu_{max} \cdot {S \over S+K_s}

Initial values and the values of the parameters have been omitted for brevity.



SIML Program
------------

.. code-block:: siml
    :linenos:

    #Biological reactor with no inflow or outflow
    class Batch:
        #Define values that stay constant during the simulation.
        data mu_max, Ks, Yxs: Float param
        #Define values that change during the simulation.
        data mu, X, S: Float

        #Initialize the simulation.
        func initialize(this):
            #Specify options for the simulation algorithm.
            solution_parameters(duration=20, reporting_interval=0.1)
            #Give values to the parameters
            mu_max = 0.32 #max growth speed
            Ks     = 0.01 #at this sugar concentration growth speed is 0.5*mu_max
            Yxs    = 0.5  #one g sugar gives this much biomass
            #Give initial values to the state variables.
            X      = 0.1  #initial biomass concentration
            S      = 20   #initial sugar concentration

        #compute dynamic behaviour - the system's 'equations'
        func dynamic(this):
            mu = mu_max * S/(S+Ks) #growth speed (of biomass)
            $X = mu*X              #change of biomass concentration
            $S = -1/Yxs*mu*X       #change of sugar concentration

        #show results
        func final(this):
            graph(mu, X, S)
            #For the test scripts
            print('final-values:', X, S)

    compile Batch

This is a complete SIML program to to solve the system of differential equations.
The differential equations are in the **dynamic** function.
The **initialize** function is invoked once at the beginning of the simulation,
the **final** function is invoked at the end.



Shell Commands
--------------

These are the (bash) commands to edit the program, compile it, and run it.

.. code-block:: bash

    $> kwrite bioreactor_simple.siml #Edit Siml file
    $> simlc bioreactor_simple.siml  #Run compiler
    $> ./bioreactor_simple.py        #Run generated program

The compiler can also run the generated Program.
This is useful for the development of simulation programs.

.. code-block:: bash

    $> kwrite bioreactor_simple.siml        #Edit Siml file
    $> simlc bioreactor_simple.siml -r all  #Run compiler

After the commands have been executed, a window opens, that shows the simulation results:

.. image:: bioreactor_simple--S-X.png

Graph of X, S and mu, versus simulation time.


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

.. [#dollar_operator] The dollar operator has really three functions: it 
        accesses the time derivative; it marks a variable as a state variable;
        and it creates a place to store the time derivative (if necesary). The time 
        derivative is just an other variable, but it can usually only be 
        accessed by the ``$`` operator. 
                
                
