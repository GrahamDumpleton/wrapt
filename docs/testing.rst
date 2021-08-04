Running Unit Tests
==================

Unit tests are located in the ``tests`` directory.

To test both the pure Python and C extension module based implementations,
run the command:

::

    tox

By default tests are run for Python 2.7, 3.4-3.9 and PyPy, with and
without the C extensions.

::

    py27-without-extensions
    py34-without-extensions
    py35-without-extensions
    py36-without-extensions
    py37-without-extensions
    py38-without-extensions
    py39-without-extensions

    py27-install-extensions
    py34-install-extensions
    py35-install-extensions
    py36-install-extensions
    py37-install-extensions
    py38-install-extensions
    py39-install-extensions

    py27-disable-extensions
    py34-disable-extensions
    py35-disable-extensions
    py36-disable-extensions
    py37-disable-extensions
    py38-disable-extensions
    py39-disable-extensions

    pypy-without-extensions

If wishing to run tests for a specific Python combination you can run
``tox`` with the ``-e`` option.

::

    tox -e py39-install-extensions

If adding more tests and you need to add a test which is Python 2 or
Python 3 specific, then end the name of the Python code file as
``_py2.py`` or ``_py3.py`` appropriately.

For further options refer to the documentation for ``tox``.

Coverage
--------

Coverage is collected and sent to `Coveralls <https://coveralls.io>`_ when
running the tests automatically in `GitHub Actions <https://github.com/GrahamDumpleton/wrapt/actions>`_.
To collect and view coverage results locally, here's the sequence of
commands:

::

    tox
    coverage combine
    coverage html --ignore-errors

At this point there's a directly called ``htmlcov`` with the formatted
results.

