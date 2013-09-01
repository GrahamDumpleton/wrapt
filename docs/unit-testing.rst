Unit Testing
------------

Unit tests are located in the ``tests`` directory.

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

If adding more tests and you need to add a test which is Python 2 or
Python 3 specific, then end the name of the Python code file as
``_py2.py`` or ``_py3.py`` appropriately.
