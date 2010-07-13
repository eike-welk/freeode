************************************
The Fermenter Intro
************************************

The Siml programming language is a simple domain speciffic language to solve 
differential equations. The differential equation are solved numerically.
The compiler produces a program in the Python langauge, that performs the numerical computations.
The generated Python program can be used as a stand-dalone program, 
in an interactive Python session, or as building blocks of more complex programs.

This rough example should give a first impression of the usage
of the compiler and of the generated program.
Also it should show what code the compiler emits.

A simple biological reactor should be simulated. The simulation has two
state variables:
**X** the concentration of biomass, and
**S** the concentration of sugar.
The growth speed **µ** is an algebraic variable.



Differential Equations
======================

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
============

.. code-block:: siml
    :linenos:

    #Biological reactor with no inflow or outfow
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
            mu_max = 0.32; #max growth speed
            Ks     = 0.01; #at this sugar concentration growth speed is 0.5*mu_max
            Yxs    = 0.5;  #one g sugar gives this much biomass
            #Give initial values to the state variables.
            X      = 0.1;  #initial biomass concentration
            S      = 20;   #initial sugar concentration

        #compute dynamic behaviour - the system's 'equations'
        func dynamic(this):
            mu = mu_max * S/(S+Ks); #growth speed (of biomass)
            $X = mu*X;              #change of biomass concentration
            $S = -1/Yxs*mu*X;       #change of sugar concentration

        #show results
        func final(this):
            graph(mu, X, S);


    compile Batch

This is a complete SIML program to to solve the system of differential equations.
The differential equations are in the **dynamic** function.
The **init** function is invoked once at the beginning of the simulation,
the **final** function is invoked at the end.



Shell Commands
==============

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

