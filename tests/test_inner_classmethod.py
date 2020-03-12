from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from compat import PY2, PY3, exec_

DECORATORS_CODE = """
import wrapt

@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
"""

decorators = imp.new_module('decorators')
exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

class Class(object):
    @classmethod
    def function(self, arg):
        '''documentation'''
        return arg

Original = Class

class Class(object):
    @decorators.passthru_decorator
    @classmethod
    def function(self, arg):
        '''documentation'''
        return arg

class TestNamingInnerClassMethod(unittest.TestCase):

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

class TestCallingInnerClassMethod(unittest.TestCase):

    def test_class_call_function(self):
        # Test calling classmethod.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        result = Class._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function(self):
        # Test calling classmethod via class instance.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_call_function_nested_decorators(self):
        # Test calling classmethod.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            @_decorator
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        result = Class._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function_nested_decorators(self):
        # Test calling classmethod via class instance.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            @_decorator
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_externally_applied_wrapper(self):
        # Test calling staticmethod via class when
        # the decorator has been applied from external to
        # the class using wrapping function.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Class(object):
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(Class, "_function", _decorator)

        result = Class._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_externally_applied_wrapper(self):
        # Test calling staticmethod via class instance when
        # the decorator has been applied from external to
        # the class using wrapping function.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Class(object):
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(Class, "_function", _decorator)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_externally_passed_wrapper(self):
        # Test calling classmethod via class when
        # the decorator has been applied around reference
        # to the function.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Class(object):
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        _function = _decorator(Class._function)

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_externally_passed_wrapper(self):
        # Test calling classmethod via class instance when
        # the decorator has been applied around reference
        # to the function.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Class(object):
            @classmethod
            def _function(cls, *args, **kwargs):
                return (args, kwargs)

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, Class)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        _function = _decorator(Class()._function)

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

if __name__ == '__main__':
    unittest.main()
