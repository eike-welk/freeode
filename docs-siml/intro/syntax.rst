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


Statements
===================================

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

.. code-block:: siml

    func square(x):
        return x * x

Example: The function ``square`` multiplies its argument ``x`` by itself. The expression 
``x * x`` is computed and the result is delivered to part(s) of the program
where the function is called.

See also: :ref:`func-statement`


``pragma`` Statement
------------------------

These statements are used to invoke behavior/algorithms for which no special 
syntax has been developed yet.

At the time of writing, no behavior can be triggered with the ``pragma`` 
statement.


``pass`` Statement
------------------------

The pass statement does nothing. It is needed to create *empty* compound 
statements (``if``, ``ifc``, ``func``, ``class``), 
because of the whitespace sensitive syntax. 

.. code-block:: siml

    func dummy():
        pass

Example: The function ``dummy`` does nothing.


.. _data-statement:

``data`` Statement
------------------------


.. _if-statement:

``if elif else``  Statement
---------------------------

``return`` statements are illegal inside ``if`` statements: :ref:`return-statement`

See also :ref:`ifc-statement`


.. _ifc-statement:

``ifc`` Statement
------------------------


.. _func-statement:

``func`` Statement
------------------------

See also :ref:`return-statement`

.. _class-statement:

``class`` Statement
------------------------


