Running Unit Tests
==================

Unit tests are located in the ``tests`` directory.

To test both the pure Python and C extension module based implementations,
run the command:

::

    tox

By default tests are run for Python 3.8-3.14 and PyPy 3.8-3.10, with and
without the C extensions.

::

    py38-without-extensions
    py39-without-extensions
    py310-without-extensions
    py311-without-extensions
    py312-without-extensions
    py313-without-extensions
    py314-without-extensions

    py38-install-extensions
    py39-install-extensions
    py310-install-extensions
    py311-install-extensions
    py312-install-extensions
    py313-install-extensions
    py314-install-extensions

    py38-disable-extensions
    py39-disable-extensions
    py310-disable-extensions
    py311-disable-extensions
    py312-disable-extensions
    py313-disable-extensions
    py314-disable-extensions

    pypy-without-extensions

If wishing to run tests for a specific Python combination you can run
``tox`` with the ``-e`` option.

::

    tox -e py311-install-extensions

If adding more tests and you need to add a test which is Python 3 specific,
then end the name of the Python code file as ``_py3.py`` appropriately.

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

