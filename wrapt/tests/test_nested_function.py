from __future__ import print_function

import unittest
import inspect

from .decorators import passthru_function_decorator

def function():
    def inner(arg):
        '''documentation'''
        return arg
    return inner

original = function

def function():
    @passthru_function_decorator
    def inner(arg):
        '''documentation'''
        return arg
    return inner

class TestCase(unittest.TestCase):

    def test_object_name(self):
        # Test preservation of function __name__ attribute.

        self.assertEqual(function().__name__, original().__name__)

    def test_object_qualname(self):
        # Test preservation of function __qualname__ attribute.

        try:
            __qualname__ = original().__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(function().__qualname__, __qualname__)

    def test_module_name(self):
       # Test preservation of function __module__ attribute.

        self.assertEqual(function().__module__, __name__)

    def test_doc_string(self):
        # Test preservation of function __doc__ attribute.

        self.assertEqual(function().__doc__, original().__doc__)

    def test_argspec(self):
        # Test preservation of function argument specification.

        original_argspec = inspect.getargspec(original())
        function_argspec = inspect.getargspec(function())
        self.assertEqual(original_argspec, function_argspec)

    def test_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(function(), type(original())))
