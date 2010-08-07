..  Copyright (C) 2010 - 2010 Eike Welk

    License: GNU FDL

    Everyone is permitted to copy, distribute and/or modify this
    document under the terms of the GNU Free Documentation License,
    Version 1.3 or any later version published by the Free Software
    Foundation; with no Invariant Sections, no Front-Cover Texts and
    no Back-Cover Texts. A copy of the license is included in the
    file "GNU-Free-Documentation-License-1.3.txt"


****************************************************
The Built-In Library
****************************************************

.. module:: __siml_builtin__
    :synopsis: Siml's built in library.

The Siml language has a built in library. The objects from this library are
always visible in the global name space. 
(One can type ``sqrt(2)`` instead of ``__siml_builtin__.sqrt(2)``.) 
 
Shadowing built in objects is possible, by defining an object 
with the same name. The following two lines make the built in 
function ``sqrt`` invisible, in the module where they a are written.
 
.. code-block:: siml

    func sqrt(x):
        return x + 1

Shadowing a built in object with your own object will almost always create 
confusion. The possibility to do so, provides flexibility for the 
exceptional case, where it may be necessary.


Built in Classes
========================================

.. class:: Float
    
    A Floating point number.

    This is the ``data`` type you will use most often. 
    Declaring variables of any other data type is only rarely necessary.

.. todo:: Mention all operators of **Float** and their associated special functions.


.. class:: Bool

    A logical (binary) value;
    its value can be either :data:`TRUE` or :data:`FALSE`. 

    The comparison operators (``<``, ``>``, ``==``, ...) return Bool values. 
    The logical operators (``and``, ``or``, ``not``) work only on Bool values 
    and also return Bool vaues.
    
.. todo:: Mention all operators of **Bool** and their associated special functions.

    
.. class:: String

    A sequence of characters.
    
    Siml's string class implements only very few operations:
    
    * Concatenation with the ``+`` operator.
    * Comparison with the ``==`` and ``!=`` operators.
    * Assignment
    * Printing


.. class:: NoneType
    
    Type of the global constant :data:`NONE`.
    
    Functions and methods that don't return anything, really return :data:`NONE`.

    Defining attributes of type NoneType is not useful as NoneType 
    does not support assignment. 



Built in Constants and Special Variables
========================================

.. data:: time

    Special global variable that contains the current time.

    At compile time it is an unknown variable (but it is accessible).
    At runtime it is always known, it has sensible values in all *main* functions.

    * ``initialize``, ``init_*``: 0
    * ``dynamic``: the current simulation time.
    * ``final``: the last value simulated by the solver.


.. data:: TRUE

    Global constant that represents the boolean (:class:`Bool`) value **true**.


.. data:: FALSE

    Global constant that represents the boolean (:class:`Bool`) value **false**.


.. data:: NONE
    
    The one and only instance of class :class:`NoneType`. 

    Functions and methods that don't return anything, really return ``NONE``.



Built in Functions
========================================

Math
----------------------

.. function:: sqrt(x:Float) -> Float

    Compute the square root of a number.


.. function:: log(x:Float) -> Float

    Compute the natural logarithm of a number.


.. function:: exp(x:Float) -> Float

    Compute :math:`e^x`.


.. function:: sin(x:Float) -> Float

    Compute the sinus of a number.


.. function:: cos(x:Float) -> Float

    Compute the cosinus of a number.


.. function:: tan(x:Float) -> Float

    Compute the tangens of a number.


.. function:: max(a:Float, b:Float) -> Float

    Return the bigger of the two arguments.


.. function:: min(a:Float, b:Float) -> Float

    Return the smaller of the two arguments.


Output
----------------------

.. function::  printc(* args, area="", end="\\n") -> NoneType 

    Print text at **compile time**.

    The ``printc`` function takes an arbitrary number of positional arguments.
    The arguments are converted to strings and printed at compile time.
    The function prints unevaluated expressions as ASCII-art trees, that show 
    the structure of the AST.

    Additionally the function supports a number of keyword arguments (see 
    below).

    The function executes at **compile time**; calling this function does 
    **not create code**.
    
    **ARGUMENTS**
    
    `*args` : Any type
        The function can print all legal Siml expressions.

    area="" : :class:`String`
        Only produce output when area is in global set DEBUG_AREAS.
        The special value "" means: print unconditionally.

        To change use command line ``option --debug-area=area1,area2,...`` 
        of the compiler or the generated program. 
    
    end="\\n": :class:`String`
        This string is appended at the end of the printed output.

    **RETURNS**

    :data:`NONE`

    See also: :ref:`ifc-statement`

---------------------------------------------------------------------


.. function::  print(* args, area="", end="\\n") -> NoneType 
    
    Print text at **run time**.

    The ``print`` function takes an arbitrary number of positional arguments.
    For each argument print calls its ``__siml_str__`` function to create a text
    representation of the object.

    Additionally the function supports a number of keyword arguments (see 
    below).
 
    **ARGUMENTS**
    
    `*args` : Any type
        The function can print all legal Siml expressions.

    area="" : :class:`String`
        Only produce output when area is in global set DEBUG_AREAS.
        The special value "" means: print unconditionally.

        To change use command line ``option --debug-area=area1,area2,...`` 
        of the compiler or the generated program. 
    
    end="\\n": :class:`String`
        This string is appended at the end of the printed output.

    **RETURNS**

    :data:`NONE`
    
---------------------------------------------------------------------


.. function::  graph(* args, title="") -> NoneType 
    
    Create a graph (at runtime).

    The ``graph`` function takes an arbitrary number of positional arguments.
    These values must be ``Float`` values that were created with a ``data`` 
    statement, and whose values are also recorded during the solution process. 
    The function's arguments are interpreted specially: 
    As all recorded values at all points in time; 
    not as a single value at a specific moment in time, like variables
    are interpreted normally.

    Additionally the function supports a keyword argument ``title`` (see 
    below).

    **ARGUMENTS**
    
    `*args`: :class:`Float`
        The variable(s) that is/are graphed.
        
    title="": :class:`String`
        The title of the graph, shown at the top.
        
    **RETURNS**
    
    :data:`NONE`

---------------------------------------------------------------------


.. function::  save(file_name) -> NoneType 

    Save the simulation's results (at runtime).

    Stores the data in a **CSV** or **Pickle** file.
    The encoding is determined by the filename's extension:
    
    ".csv": Comma Separated Values 
        When the filename ends in ".csv" the data is stored in a human 
        readable format, where values are separated by commas: CSV. 
        
        * Comments in the CSV file start with "#" and continue to the end of 
          the line.
        * Two blocks of information are written, separated by comments: 
          first the parameters, then the variables. 
        * In each block the first row contains the 
          attribute names, subsequent rows contain the numeric values.
            
    For any other extension a file in Python's "pickle" format (version 2) is created. 
        Python's "pickle" mechanism is documented 
        `here <http://docs.python.org/library/pickle.html>`_.
 
    **ARGUMENTS**
    
    file_name: :class:`String`
        Name of the file where the simulation results are stored.
        
        When the filename ends with ".csv" a human readable file with 
        comma separated values is created.
        Otherwise Python's "pickle" format (version 2) is used. 
 
    **RETURNS**
    
    :data:`NONE`
         
---------------------------------------------------------------------


Administrative
----------------------

.. function::  solution_parameters(duration, reporting_interval) -> NoneType 

    Determine parameters for the solver (at run time).

    **ARGUMENTS**
    
    duration:  :class:`Float`
        Duration of the simulation.
        
    reporting_interval: :class:`Float`
        Interval at which the simulation results are recorded. - 
        Time between data points.

    **RETURNS**
    
    :data:`NONE`

---------------------------------------------------------------------


.. function::  istype(in_object, class_or_tuple) -> Bool

    Check if an object has a certain type.

    Similar to isinstance(...) but works with unevaluated expressions too, 
    because attribute ``__siml_type__``  is used instead of ``__class__``.
    If an expression (in_object) would evaluate to an object of the
    correct type, the function returns TRUE.

    This function executes at compile time and does not produce any code
    in the compiled program.

    **ARGUMENTS**
    
    in_object : any object or expression
        The object that is tested whether it has the correct type.

    class_or_tuple : a class or a tuple of classes
        The class that ``in_object`` must be an instance of.

        The argument can be a tuple of classes, then the function returns TRUE
        if ``in_object`` is an instance of any of these classes.

    **RETURNS**
    
    :class:`Bool` 
        The function returns TRUE if ``in_object`` is an instance of 
        ``class_or_tuple``. It returns FALSE otherwise.

        ``class_or_tuple`` can be a tuple of classes, then the function returns TRUE
        if ``in_object`` is an instance of any of these classes.

---------------------------------------------------------------------


.. function::  associate_state_dt(state_var, derivative_var) -> NoneType 
    
    Associate a state variable and its time derivative.

    Sets the correct roles on both variables.

    **ARGUMENTS**
    
    state_var: :class:`Float`
        The variable which is converted to a state variable.

    derivative_var: :class:`Float`
        The variable which will act as time derivative from now on. 

    **RETURNS**
    
    :data:`NONE`


