from __future__ import print_function

import unittest
import inspect

from .decorators import passthru_generic_decorator

class Class(object):
    @classmethod
    def function(self, arg):
        '''documentation'''
        return arg

Original = Class

class Class(object):
    @classmethod
    @passthru_generic_decorator
    def function(self, arg):
        '''documentation'''
        return arg

class TestCase(unittest.TestCase):

    def test_class_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(Class.function.__name__,
                Original.function.__name__)

    def test_instance_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(Class().function.__name__,
                Original().function.__name__)

    def test_class_object_qualname(self):
        # Test preservation of instance method __qualname__ attribute.

        try:
            __qualname__ = Original.original.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(Class.function.__qualname__, __qualname__)

    def test_instance_object_qualname(self):
        # Test preservation of instance method __qualname__ attribute.

        try:
            __qualname__ = Original().original.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(Class().function.__qualname__, __qualname__)

    def test_class_module_name(self):
       # Test preservation of instance method __module__ attribute.

        self.assertEqual(Class.function.__module__,
                Original.function.__module__)

    def test_instance_module_name(self):
       # Test preservation of instance method __module__ attribute.

        self.assertEqual(Class().function.__module__,
                Original().function.__module__)

    def test_class_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(Class.function.__doc__,
                Original.function.__doc__)

    def test_instance_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(Class().function.__doc__,
                Original().function.__doc__)

    def test_class_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getargspec(Original.function)
        function_argspec = inspect.getargspec(Class.function)
        self.assertEqual(original_argspec, function_argspec)

    def test_instance_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getargspec(Original().function)
        function_argspec = inspect.getargspec(Class().function)
        self.assertEqual(original_argspec, function_argspec)

    def test_class_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(Class.function,
                type(Original.function)))

    def test_instance_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(Class().function,
                type(Original().function)))
