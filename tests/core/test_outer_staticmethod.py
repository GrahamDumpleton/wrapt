import inspect
import types
import unittest

import wrapt

DECORATORS_CODE = """
import wrapt

@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
"""

decorators = types.ModuleType("decorators")
exec(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)


class Class:
    @staticmethod
    def function(arg):
        """documentation"""
        return arg


Original = Class


class Class:
    @staticmethod
    @decorators.passthru_decorator
    def function(arg):
        """documentation"""
        return arg


class TestNamingOuterStaticMethod(unittest.TestCase):

    def test_class_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(Class.function.__name__, Original.function.__name__)

    def test_instance_object_name(self):
        # Test preservation of instance method __name__ attribute.

        self.assertEqual(Class().function.__name__, Original().function.__name__)

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

        self.assertEqual(Class.function.__module__, Original.function.__module__)

    def test_instance_module_name(self):
        # Test preservation of instance method __module__ attribute.

        self.assertEqual(Class().function.__module__, Original().function.__module__)

    def test_class_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(Class.function.__doc__, Original.function.__doc__)

    def test_instance_doc_string(self):
        # Test preservation of instance method __doc__ attribute.

        self.assertEqual(Class().function.__doc__, Original().function.__doc__)

    def test_class_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getfullargspec(Original.function)
        function_argspec = inspect.getfullargspec(Class.function)
        self.assertEqual(original_argspec, function_argspec)

    def test_instance_argspec(self):
        # Test preservation of instance method argument specification.

        original_argspec = inspect.getfullargspec(Original().function)
        function_argspec = inspect.getfullargspec(Class().function)
        self.assertEqual(original_argspec, function_argspec)

    def test_class_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(Class.function, type(Original.function)))

    def test_instance_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(Class().function, type(Original().function)))


class TestCallingOuterStaticMethod(unittest.TestCase):

    def test_class_call_function(self):
        # Test calling staticmethod. The instance and class passed to the
        # wrapper will both be None because our decorator is surrounded
        # by the staticmethod decorator. The staticmethod decorator
        # doesn't bind the method and treats it like a normal function.

        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class:
            @staticmethod
            @_decorator
            def _function(*args, **kwargs):
                return (args, kwargs)

        result = Class._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_call_function(self):
        # Test calling staticmethod via class instance. The instance
        # and class passed to the wrapper will both be None because our
        # decorator is surrounded by the staticmethod decorator. The
        # staticmethod decorator doesn't bind the method and treats it
        # like a normal function.

        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        class Class:
            @staticmethod
            @_decorator
            def _function(*args, **kwargs):
                return (args, kwargs)

        result = Class()._function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))


if __name__ == "__main__":
    unittest.main()
