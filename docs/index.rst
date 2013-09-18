wrapt
=====

A Python module for decorators, wrappers and monkey patching.

Overview
--------

The aim of the **wrapt** module is to provide a transparent object proxy
for Python, which can be used as the basis for the construction of function
wrappers and decorator functions.

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

Installation
------------

The **wrapt** module is available from PyPi and can be installed using
``pip``.

    pip install wrapt

Repository
----------

Full source code for the **wrapt** module, including documentation files
and unit tests, can be obtained from github.

* https://github.com/GrahamDumpleton/wrapt

Presentations
-------------

Conference presentations related to the **wrapt** module:

* http://lanyrd.com/2013/kiwipycon/scpkbk

Contents
--------

.. toctree::
   :maxdepth: 1

   quick-start
   decorators
   examples
   benchmarks
   testing
   changes
   issues

..   wrappers
..   proxies
