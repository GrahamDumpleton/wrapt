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

class OldClass1():
    def function(self, arg):
        '''documentation'''
        return arg

OldClass1o = OldClass1

class OldClass1():
    @decorators.passthru_decorator
    def function(self, arg):
        '''documentation'''
        return arg

OldClass1d = OldClass1

class TestNamingInstanceMethodOldStyle(unittest.TestCase):

    def test_class_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(OldClass1d.function.__name__,
                OldClass1o.function.__name__)

    def test_instance_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(OldClass1d().function.__name__,
                OldClass1o().function.__name__)

    def test_class_object_qualname(self):
        # Test preservation of instance method __qualname__ attribute.

        try:
            __qualname__ = OldClass1o.original.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(OldClass1d.function.__qualname__, __qualname__)

    def test_instance_object_qualname(self):
        # Test preservation of instance method __qualname__ attribute.

        try:
            __qualname__ = OldClass1o().original.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(OldClass1d().function.__qualname__, __qualname__)

    def test_class_module_name(self):
        # Test preservation of instance method __module__ attribute.

        self.assertEqual(OldClass1d.function.__module__,
                OldClass1o.function.__module__)

    def test_instance_module_name(self):
        # Test preservation of instance method __module__ attribute.

        self.assertEqual(OldClass1d().function.__module__,
                OldClass1o().function.__module__)

    def test_class_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(OldClass1d.function.__doc__,
                OldClass1o.function.__doc__)

    def test_instance_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(OldClass1d().function.__doc__,
                OldClass1o().function.__doc__)

    def test_class_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getargspec(OldClass1o.function)
        function_argspec = inspect.getargspec(OldClass1d.function)
        self.assertEqual(original_argspec, function_argspec)

    def test_instance_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getargspec(OldClass1o().function)
        function_argspec = inspect.getargspec(OldClass1d().function)
        self.assertEqual(original_argspec, function_argspec)

    def test_getmembers(self):
        original_members = inspect.getmembers(OldClass1o().function)
        function_members = inspect.getmembers(OldClass1d().function)

    def test_class_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(OldClass1d.function,
                type(OldClass1o.function)))

    def test_instance_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(OldClass1d().function,
                type(OldClass1o().function)))

class NewClass1(object):
    def function(self, arg):
        '''documentation'''
        return arg

NewClass1o = NewClass1

class NewClass1(object):
    @decorators.passthru_decorator
    def function(self, arg):
        '''documentation'''
        return arg

NewClass1d = NewClass1

class TestNamingInstanceMethodNewStyle(unittest.TestCase):

    def test_class_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(NewClass1d.function.__name__,
                NewClass1o.function.__name__)

    def test_instance_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(NewClass1d().function.__name__,
                NewClass1o().function.__name__)

    def test_class_object_qualname(self):
        # Test preservation of instance method __qualname__ attribute.

        try:
            __qualname__ = NewClass1o.original.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(NewClass1d.function.__qualname__, __qualname__)

    def test_instance_object_qualname(self):
        # Test preservation of instance method __qualname__ attribute.

        try:
            __qualname__ = NewClass1o().original.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(NewClass1d().function.__qualname__, __qualname__)

    def test_class_module_name(self):
        # Test preservation of instance method __module__ attribute.

        self.assertEqual(NewClass1d.function.__module__,
                NewClass1o.function.__module__)

    def test_instance_module_name(self):
        # Test preservation of instance method __module__ attribute.

        self.assertEqual(NewClass1d().function.__module__,
                NewClass1o().function.__module__)

    def test_class_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(NewClass1d.function.__doc__,
                NewClass1o.function.__doc__)

    def test_instance_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(NewClass1d().function.__doc__,
                NewClass1o().function.__doc__)

    def test_class_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getargspec(NewClass1o.function)
        function_argspec = inspect.getargspec(NewClass1d.function)
        self.assertEqual(original_argspec, function_argspec)

    def test_instance_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getargspec(NewClass1o().function)
        function_argspec = inspect.getargspec(NewClass1d().function)
        self.assertEqual(original_argspec, function_argspec)

    def test_class_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(NewClass1d.function,
                type(NewClass1o.function)))

    def test_instance_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(NewClass1d().function,
                type(NewClass1o().function)))

class TestCallingInstanceMethodOldStyle(unittest.TestCase):

    def test_class_call_function(self):
        # Test calling instancemethod via class and passing in the class
        # instance directly.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class():
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class._function(*((Class(),)+_args), **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function(self):
        # Test calling instancemethod via class instance.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class():
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_call_function_nested(self):
        # Test calling instancemethod via class and passing in the class
        # instance directly.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class():
            @_decorator
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class._function(*((Class(),)+_args), **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function_nested(self):
        # Test calling instancemethod via class instance.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class():
            @_decorator
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

class TestCallingInstanceMethodNewStyle(unittest.TestCase):

    def test_class_call_function(self):
        # Test calling instancemethod via class and passing in the class
        # instance directly.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class._function(Class(), *_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function(self):
        # Test calling instancemethod via class instance.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_call_function_nested(self):
        # Test calling instancemethod via class and passing in the class
        # instance directly.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class._function(Class(), *_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function_nested(self):
        # Test calling instancemethod via class instance.

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertNotEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            self.assertEqual(wrapped.__module__, _function.__module__)
            self.assertEqual(wrapped.__name__, _function.__name__)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class(object):
            @_decorator
            @_decorator
            def _function(self, *args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

if __name__ == '__main__':
    unittest.main()
