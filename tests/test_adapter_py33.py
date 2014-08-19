from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from compat import PY2, PY3, exec_

DECORATORS_CODE = """
import wrapt

def prototype(arg1, arg2, *, arg3=None, **kwargs): pass
@wrapt.decorator(adapter=prototype)
def adapter1(wrapped, instance, args, kwargs):
    '''adapter documentation'''
    return wrapped(*args, **kwargs)
"""

decorators = imp.new_module('decorators')
exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

def function1(arg1, arg2):
    '''documentation'''
    return arg1, arg2

function1o = function1

@decorators.adapter1
def function1(arg1, arg2):
    '''documentation'''
    return arg1, arg2

function1d = function1

class TestArgumentSpecification(unittest.TestCase):

    def test_getfullargspec(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        def _adapter(arg1, arg2, *, arg3=None, **kwargs): pass

        function1a_argspec = inspect.getfullargspec(_adapter)
        function1d_argspec = inspect.getfullargspec(function1d)
        self.assertEqual(function1a_argspec, function1d_argspec)

    def test_signature(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        if PY2:
            return

        def _adapter(arg1, arg2, *, arg3=None, **kwargs): pass

        function1a_signature = str(inspect.signature(_adapter))
        function1d_signature = str(inspect.signature(function1d))
        self.assertEqual(function1a_signature, function1d_signature)

if __name__ == '__main__':
    unittest.main()
