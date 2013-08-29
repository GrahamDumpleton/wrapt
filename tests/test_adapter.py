from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from wrapt import six

DECORATORS_CODE = """
import wrapt

def prototype(arg): pass
@wrapt.decorator(adapter=prototype)
def adapter1(wrapped, instance, args, kwargs):
    '''adapter documentation'''
    return wrapped(*args, **kwargs)
"""

decorators = imp.new_module('decorators')
six.exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

def function1(arg1, arg2):
    '''documentation'''
    return arg1, arg2

function1o = function1

@decorators.adapter1
def function1(arg1, arg2):
    '''documentation'''
    return arg1, arg2

function1d = function1

class TestNamingAdapter(unittest.TestCase):

    def test_object_name(self):
        # Test preservation of function __name__ attribute.

        self.assertEqual(function1d.__name__, function1o.__name__)

    def test_object_qualname(self):
        # Test preservation of function __qualname__ attribute.

        try:
            __qualname__ = function1o.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(function1d.__qualname__, __qualname__)

    def test_module_name(self):
       # Test preservation of function __module__ attribute.

        self.assertEqual(function1d.__module__, __name__)

    def test_doc_string(self):
        # Test preservation of function __doc__ attribute. It is
        # still the documentation from the wrapped function, not
        # of the adapter.

        self.assertEqual(function1d.__doc__, 'documentation')

    def test_argspec(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        def _adapter(arg): pass

        function1a_argspec = inspect.getargspec(_adapter)
        function1d_argspec = inspect.getargspec(function1d)
        self.assertEqual(function1a_argspec, function1d_argspec)

    def test_signature(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        if six.PY2:
            return

        def _adapter(arg): pass

        function1a_signature = inspect.getargspec(_adapter)
        function1d_signature = inspect.getargspec(function1d)
        self.assertEqual(function1a_signature, function1d_signature)

    def test_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(function1d, type(function1o)))

if __name__ == '__main__':
    unittest.main()
