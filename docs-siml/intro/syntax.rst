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

Expressions
===================================


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




.. index::
    single: statement; expression
    single: expression statement 

.. _expression-statement:

Expression Statement
------------------------




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

.. todo:: Link to roles




Compound Statements
===================================

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

Like in Python there is an alternative syntax for compound statements: 
The dependent statements can be written directly after the colon (``:``),
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

.. _func-statement:

``func`` Statement
------------------------

See also :ref:`return-statement`




.. index::
    single: keyword; class
    single: statement; class
    single: class statement 

.. _class-statement:

``class`` Statement
------------------------


