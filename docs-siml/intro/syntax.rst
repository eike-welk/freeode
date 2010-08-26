..  Copyright (C) 2010 - 2010 Eike Welk 

    License: GNU FDL

    Everyone is permitted to copy, distribute and/or modify this
    document under the terms of the GNU Free Documentation License,
    Version 1.3 or any later version published by the Free Software
    Foundation; with no Invariant Sections, no Front-Cover Texts and
    no Back-Cover Texts. A copy of the license is included in the
    file "GNU-Free-Documentation-License-1.3.txt"


.. Let all references go to the built in module. This shortens all references.
.. currentmodule:: __siml_builtin__

.. Set default syntax highlighting language to Siml.
.. highlight:: siml


************************************
Syntax of the Siml Language
************************************

Basics
===================================

Whitespace Sensitive Syntax
-----------------------------

Floating Point Numbers
----------------------

Text Strings
-------------------

Identifiers
-------------------

Type Systems
-------------------

Structural typing
    This type system is enforced by the compiler for data attributes that are 
    passed to the code generator. These built in objects (Float, String, Bool)
    must be compatible for all operations. 
    `<http://en.wikipedia.org/wiki/Structural_typing>`_
    
Nominal typing
    Nominal typing is used at function call sites, if type annotations are 
    present. `<http://en.wikipedia.org/wiki/Nominative_type_system>`_

Duck typing
    Duck typing is used for data attributes with user defined types. 
    The attribute must only have the correct name. If the attribute 
    can be used correctly is determined by its leaf objects.
    `<http://en.wikipedia.org/wiki/Duck_typing>`_


Expressions
===================================



.. index::
    single: statement; simple statements
    single: simple statements 

Simple Statements
===================================




.. index::
    single: keyword; return
    single: statement; return
    single: return statement 

.. _return-statement:

``return`` Statement
------------------------

The ``return`` statement delivers data from a function back to its caller.
Additionally it ends the execution of the function.

The keyword ``return`` is followed an expression. The expression is evaluated
and the result is delivered to the function's caller. Only a single 
value can be returned. 
Even though functions are always inlined (their code is copied into the 
caller), the illusion (semantics) of calling a function and returning a value is 
maintained for the user. 

Return statements are illegal inside ``if`` statements: :ref:`if-statement`
::

    func square(x):
        return x * x

Example: The function ``square`` multiplies its argument ``x`` by itself. The expression 
``x * x`` is computed and the result is delivered to part(s) of the program
where the function is called.

See also: :ref:`func-statement`




.. index::
    single: keyword; pragma
    single: statement; pragma
    single: pragma statement 

``pragma`` Statement
------------------------

These statements are used to invoke behavior/algorithms for which no special 
syntax has been developed yet.

At the time of writing, no behavior can be triggered with the ``pragma`` 
statement.




.. index::
    single: keyword; pass
    single: statement; pass
    single: pass statement 

``pass`` Statement
------------------------

The ``pass`` statement does nothing. It is needed to create *empty* compound 
statements (``if``, ``ifc``, ``func``, ``class``), 
because of the whitespace sensitive syntax. 

::

    func dummy():
        pass

Example: The function ``dummy`` does nothing.




.. index::
    single: statement; assignment
    single: assignment statement 

.. _assignment-statement:

Assignment (``=``) Statement
----------------------------

The *assignment statement* stores values in *data attributes* (variables, 
parameters, constants). The value on the *right hand side* of the ``=`` operator
is stored in the attribute on the *left hand side*. Attributes must be assigned 
to exactly once; however it is possible to implement special *classes* that 
behave differently.

An *assignment statement* begins with the *expression* on the left hand side, 
followed by an equal (``=``) character, followed by the *expression* on the 
right hand side.
::

    a = 3 * 2

Example: This assignment stores the value 6 in an attribute named ``a``.

If an assignment is possible is constrained by the *roles* of attribute and 
value. If both objects are *constant* the assignment is performed at *compile 
time*.

The *assignment statement* calls the *method* ``__siml_assign__`` of the 
attribute on the *left hand side*. Therefore the exact meaning of a particular
assignment is determined by the programmer who writes 
the *class* of the attribute on the *left hand side*.

.. todo:: Link to roles
.. todo:: Expand roles section




.. index::
    single: statement; expression statement
    single: expression statement 

.. _expression-statement:

Expression Statement
------------------------

The expression statement contains an expression, which is evaluated. 
The expression's value is discarded. This statement is normally used to call 
a function or method.
::

    print('hello')

Example: Call the built in function ``print`` with a ``String`` argument.

.. todo:: Link to function call




.. index::
    single: keyword; data
    single: statement; data
    single: data statement 

.. _data-statement:

``data`` Statement
------------------------

The ``data`` statement creates *data attributes* (variables, parameters, constants): 
It instantiates a class, and binds the new object to a name. 
The new objects are intended to be unknown attributes,
but the exact semantics can be decided by the implementor of the class.

The ``data`` statement can create multiple objects of the same type.

The ``data`` keyword is followed by one or more comma separated *attribute names*,
a colon, a *class name*, and an optional *role modifier*.
::

    data a, b, c: Float param

Example: The data statement creates three unknown attributes of type Float, with 
*role* parameter. 

See also: :ref:`class-statement`

.. todo:: Link to roles




.. index::
    single: keyword; compile
    single: statement; compile
    single: compile statement 

.. _compile-statement:

``compile`` Statement
------------------------

See also: :ref:`class-statement`, :ref:`data-statement`





.. ----------------------------------------------------------------------------------------------------------

.. index::
    single: statement; compound statements
    single: compound statements

Compound Statements
===================================

*Compound statements* [#like_python_compound_statement]_ 
contain other dependent statements. They somehow 
control the execution or meaning of those dependent statements. They usually 
occupy multiple lines, although they can sometimes be written in a single line.

All *compound statements* have a similar syntactic structure:
They consist of a *header*, and a *suite* of dependent statements.
The *header* starts with a unique keyword (``if``, ``ifc``, ``func``, ``class``, ...),
followed by syntax specific to the statement, it always ends with a colon (``:``).
Then follows the *suite*.   
                 
.. index::
    single: suite of statements

A **suite** is a group of statements. It is usually written as an indented 
block of statements; but simple statements can be written on the same line
as the compound statement's *header*, separated by semicolons (``;``).
::

    #The suite in the function body is written as an indented block of statements.
    func bacterial_growth_1(s, x): #The compound statement's header
        mu = 0.3 * s/(s+0.01) # This
        dx = mu*x             # is 
        return dx             # the suite
        
    #Function definition written in one line:
    #---- This is the header ----| |----------- This is the suite -----------|
    func bacterial_growth_2(s, x): mu = 0.3 * s/(s+0.01); dx = mu*x; return dx

Example: Two functions that perform the same computation. 

.. index::
    single: clause

Some *compound statements* (``if``, ``ifc``) consist of multiple **clauses**. 
A *clause* is a *header* with its *suite*.
::

    if a < 2:             #clause 1
        b = 0             #   ~   1
    else:                 #clause 2
        b = (a - 2) * 0.5 #   ~   2

Example: An ``if`` statement, which consists of two *clauses*.




.. index::
    single: keyword; if
    single: statement; if
    single: if statement 

.. _if-statement:

``if`` Statement
---------------------------

The keywords ``if``, ``elif``, and ``else`` together form a conditional 
statement. Different computations can be executed depending on one or more 
conditions. The decision to perform a specific computation is done at **run-time**, 
in contrast to the ``ifc`` (note the **c**) statement, which is evaluated 
at **compile-time**. :ref:`ifc-statement`

The statement is structured into several *clauses*. The ``if`` clause is always 
the first clause, it is followed by optional ``elif`` clauses, the ``else`` 
clause comes always last.

    * The ``if`` clause begins with the keyword ``if``, which is followed by an 
      expression (the condition), a colon (``:``), and a usually indented *suite* of 
      statements. 
    * The ``elif`` clause is structured exactly like the ``if`` clause.
    * The ``else`` clause has no condition; the keyword ``else``
      it is directly followed by a colon and a *suite* of statements. 

The conditions must evaluate to a :class:`Bool` value. The clauses' conditions 
are evaluated in the order in which they appear in the program text. 
If a condition evaluates to :data:`TRUE` the statements in the clause's suite 
are executed. If no condition is :data:`TRUE`
then the statements of the ``else`` clause are executed. Only the statements of 
one clause are executed.  
::

    if a < 0:
        b = 0
    elif a < 2:
        b = 0.5 * a
    else:
        b = 1

Example: Definition of a piecewise function *b(a)*. 

The dependent statements can also be written directly after the colon (``:``),
separated by semicolons (``;``).
::

    if a < 0:   b = 0
    elif a < 2: b = 0.5 * a
    else:       b = 1

Example: The same piecewise function as above, but more compact syntax.

.. note::
    As the ``if`` statement is executed at run-time, it must be part of a useful
    set of differential equations. Therefore it is subject to several restrictions: 

    * All clauses of the if statement must contain assignments to the same variables.
        * The above is a simplification. The exact rules are not finished yet, but
          will be similar to: 
          All variables that are used outside the ``if`` statement must be assigned 
          in all clauses.
    * An ``else`` clause is compulsory, because all variables must always be 
      computed; ``elif`` clauses however are optional.  
    * ``return`` statements are illegal inside ``if`` statements: :ref:`return-statement`

See also: :ref:`ifc-statement`



.. index::
    single: keyword; ifc
    single: statement; ifc
    single: ifc statement 

.. _ifc-statement:

``ifc`` Statement
------------------------

The keywords ``ifc``, ``elif``, and ``else`` together form a conditional 
statement, which is executed at **compile-time**. Different pieces of program code
can be compiled depending on one or more conditions; it must be possible to 
evaluate the conditions at **compile-time**.

The ``elif`` and ``else`` clauses are optional. There are no restrictions
for the ``ifc`` statement, all statements can appear inside each clause.

The syntax is exactly like the ``if`` (note no **c**) statement.

See also: :ref:`if-statement`, :func:`printc`

.. Alternative "See also" syntax: 
    .. seealso:: :ref:`if-statement`, :func:`printc`

.. todo:: Define  **compile-time** and **run-time**




.. index::
    single: keyword; func
    single: statement; func
    single: func statement 
    single: statement; function definition
    single: function definition

.. _func-statement:

Function Definition 
------------------------

A function definition creates a function object and binds it to a name in 
the local *name space*. 


::

    func bacterial_growth(s, x): 
        mu = 0.3 * s/(s+0.01) 
        dx = mu*x              
        return dx             
        
Example: A function definition that could be useful in the context of 
:ref:`intro-batch-reactor-example`.

Function definitions can often be written in a single line, although it 
usually results in poorly readable programs.
::
        
    func bacterial_growth(s, x): mu = 0.3 * s/(s+0.01); dx = mu*x; return dx

Example: The same function as above, but written in one line.

See also: :ref:`return-statement`

.. todo:: Link to function call
.. todo:: Functions are polymorphic (generic), but argument types can be constrained
.. todo:: Arguments: type annotations
.. todo:: Arguments: default values
.. todo:: Code of functions is copied into caller
.. todo:: Complete section.



.. index::
    single: keyword; class
    single: statement; class
    single: class statement 
    single: statement; class definition
    single: class definition

.. _class-statement:

Class Definition
------------------------

A *class* definition creates a class *object* and binds it to a name. 
*Data attributes* and *methods* must be defined in the class definition 
[#python_class_defines_no_data_attributes]_. 
**Currently there is no inheritance.**

A *class* definition begins with the ``class`` keyword, followed by the 
class' name, and a colon (``:``). 
Then follows a *suite* of statements, the class' body.
::

    class LinearGrowth:
        data x: Float  

        func initialize(this):
            x = 0  
            solution_parameters(20, 0.1)

        func dynamic(this):
            $x = 0.5  

        func final(this):
            graph(x, title="Linear Growth")
            
Example: A class definition. When compiled this class solves the equation 
:math:`{dx \over dt} = 0.5`.

When the compiler encounters a *class definition* it creates a new local 
*name space*, and executes the statements of the class' body in it. 
The attributes of this *name space* then become the class' *attributes*.
As the class' body's statements are executed at *compile time* they must not 
contain any computations with unknown variables.

Classes are *specifications* that say how *other objects* should be structured. 
Objects that are structured to a class' specification are called the class'
*instances*. Creating instances of a class is called *instantiation*. 
During *instantiation* the class' *data attributes* are copied into the new 
instance. The *methods* are not copied but shared by all instances of a class.

The first argument of all methods must be named ``this``. It contains the
instance upon which the method currently acts [#this_equivalent_to_python_self]_. 

See also: :ref:`data-statement`, :ref:`compile-statement`




.. [#like_python_compound_statement] The general definition of  
        *compound statements* is 
        `exactly <http://docs.python.org/reference/compound_stmts.html>`_
        as in the Python language.

..
    .. [#like_python_function_definition] Function definitions are 
            `very similar <http://docs.python.org/reference/compound_stmts.html#function-definitions>`_
            to Python's function definitions. However some features are not 
            implemented: *decorators*, and the special arguemnts ``*args`` and 
            ``**kwargs``.

.. [#python_class_defines_no_data_attributes] Python classes by contrast 
        do not define their instances' data attributes. In Python data attributes 
        can be created any time after instantiation. They are often created in  
        the ``__init__`` method.

.. [#this_equivalent_to_python_self] The special ``this`` argument is 
        equivalent to Python's ``self``. However Siml requires that it 
        is named "this".

