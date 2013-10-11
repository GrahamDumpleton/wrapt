wrapt
=====

A Python module for decorators, wrappers and monkey patching.

Overview
--------

The aim of the **wrapt** module is to provide a transparent object proxy
for Python, which can be used as the basis for the construction of function
wrappers and decorator functions.

An easy to use decorator factory is provided to make it simple to create
your own decorators that will behave correctly in any situation they may
be used.

::

    import wrapt

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    def function():
        pass

In addition to the support for creating object proxies, function wrappers
and decorators, the module also provides a post import hook mechanism and
other utilities useful in performing monkey patching of code.

The **wrapt** module focuses very much on correctness. It therefore goes
way beyond existing mechanisms such as ``functools.wraps()`` to ensure that
decorators preserve introspectability, signatures, type checking abilities
etc. The decorators that can be constructed using this module will work in
far more scenarios than typical decorators and provide more predictable and
consistent behaviour.

To ensure that the overhead is as minimal as possible, a C extension module
is used for performance critical components. An automatic fallback to a
pure Python implementation is also provided where a target system does not
have a compiler to allow the C extension to be compiled.

Documentation
-------------

.. toctree::
   :maxdepth: 1

   quick-start
   decorators
   wrappers
   examples
   benchmarks
   testing
   changes
   issues

Presentations
-------------

Conference presentations related to the **wrapt** module:

* http://lanyrd.com/2013/kiwipycon/scpkbk

Installation
------------

The **wrapt** module is available from PyPi at:

* https://pypi.python.org/pypi/wrapt

and can be installed using ``pip``.

::

    pip install wrapt

Source Code
-----------

Full source code for the **wrapt** module, including documentation files
and unit tests, can be obtained from github.

* https://github.com/GrahamDumpleton/wrapt
