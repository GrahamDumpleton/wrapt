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

Testing
-------

To test both the pure Python and C extension module based implementations,
run the command:

    ./tests/run.sh

The test script uses ``tox``. By default tests are run for Python 2.6, 2.7,
3.3 and PyPy.

If wishing to run tests for a specific Python version you can run ``tox``
directly.

    tox -e py33

This will attempt to compile the C extension module by default. To force
the running of tests against the pure Python version set the
``WRAPT_EXTENSIONS`` environment variable to ``false`` at the time of
running the test.

    WRAPT_EXTENSIONS=false tox -e py33

Individual tests in the ``tests`` directory can be run by supplying the
path of the test file to ``tox`` when run.
