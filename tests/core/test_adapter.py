import inspect
import types
import unittest

import wrapt

DECORATORS_CODE = """
import wrapt

def prototype(arg1, arg2, arg3=None, *args, **kwargs): pass
@wrapt.decorator(adapter=prototype)
def adapter1(wrapped, instance, args, kwargs):
    '''adapter documentation'''
    return wrapped(*args, **kwargs)
"""

decorators = types.ModuleType("decorators")
exec(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)


def function1(arg1, arg2):
    """documentation"""
    return arg1, arg2


function1o = function1


@decorators.adapter1
def function1(arg1, arg2):
    """documentation"""
    return arg1, arg2


function1d = function1


class TestAdapterAttributes(unittest.TestCase):

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

        self.assertEqual(function1d.__doc__, "documentation")


class TestArgumentSpecification(unittest.TestCase):

    def test_argspec(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        def _adapter(arg1, arg2, arg3=None, *args, **kwargs):
            pass

        function1a_argspec = inspect.getfullargspec(_adapter)
        function1d_argspec = inspect.getfullargspec(function1d)
        self.assertEqual(function1a_argspec, function1d_argspec)

        # Now bind the function to an instance. The argspec should
        # still match.

        bound_function1d = function1d.__get__(object(), object)
        bound_function1d_argspec = inspect.getfullargspec(bound_function1d)
        self.assertEqual(function1a_argspec, bound_function1d_argspec)

    def test_signature(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        def _adapter(arg1, arg2, arg3=None, *args, **kwargs):
            pass

        function1a_signature = str(inspect.signature(_adapter))
        function1d_signature = str(inspect.signature(function1d))
        self.assertEqual(function1a_signature, function1d_signature)

    def test_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(function1d, type(function1o)))


class TestDynamicAdapter(unittest.TestCase):

    def test_dynamic_adapter_function(self):
        def _adapter(arg1, arg2, arg3=None, *args, **kwargs):
            pass

        argspec = inspect.getfullargspec(_adapter)

        @wrapt.decorator(adapter=argspec)
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_wrapper_1
        def _function_1():
            pass

        self.assertEqual(inspect.getfullargspec(_function_1), argspec)

        args = "(arg1, arg2, arg3=None, *args, **kwargs)"

        @wrapt.decorator(adapter=args)
        def _wrapper_2(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_wrapper_2
        def _function_2():
            pass

        self.assertEqual(inspect.getfullargspec(_function_2), argspec)

    def test_dynamic_adapter_instancemethod(self):
        def _adapter(self, arg1, arg2, arg3=None, *args, **kwargs):
            pass

        argspec = inspect.getfullargspec(_adapter)

        @wrapt.decorator(adapter=argspec)
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class1:
            @_wrapper_1
            def function(self):
                pass

        instance1 = Class1()

        self.assertEqual(inspect.getfullargspec(Class1.function), argspec)
        self.assertEqual(inspect.getfullargspec(instance1.function), argspec)

        args = "(self, arg1, arg2, arg3=None, *args, **kwargs)"

        @wrapt.decorator(adapter=args)
        def _wrapper_2(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class2:
            @_wrapper_2
            def function(self):
                pass

        instance2 = Class2()

        self.assertEqual(inspect.getfullargspec(Class2.function), argspec)
        self.assertEqual(inspect.getfullargspec(instance2.function), argspec)

    def test_dynamic_adapter_classmethod(self):
        def _adapter(cls, arg1, arg2, arg3=None, *args, **kwargs):
            pass

        argspec = inspect.getfullargspec(_adapter)

        @wrapt.decorator(adapter=argspec)
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class1:
            @_wrapper_1
            @classmethod
            def function(cls):
                pass

        instance1 = Class1()

        self.assertEqual(inspect.getfullargspec(Class1.function), argspec)
        self.assertEqual(inspect.getfullargspec(instance1.function), argspec)

        args = "(cls, arg1, arg2, arg3=None, *args, **kwargs)"

        @wrapt.decorator(adapter=args)
        def _wrapper_2(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class2:
            @_wrapper_2
            @classmethod
            def function(cls):
                pass

        instance2 = Class2()

        self.assertEqual(inspect.getfullargspec(Class2.function), argspec)
        self.assertEqual(inspect.getfullargspec(instance2.function), argspec)

    def test_adapter_factory(self):
        def factory(wrapped):
            argspec = inspect.getfullargspec(wrapped)
            argspec.args.insert(0, "arg0")
            return argspec

        @wrapt.decorator(adapter=wrapt.adapter_factory(factory))
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_wrapper_1
        def _function_1(arg1, arg2):
            pass

        argspec = inspect.getfullargspec(_function_1)

        self.assertEqual(argspec.args, ["arg0", "arg1", "arg2"])

    def test_adapter_factory_evaluates_false(self):
        # An adapter factory must be recognised by its type and not by
        # its truth value, so a factory which evaluates as false because
        # it defines __bool__() or __len__() must still be called.

        calls = []

        class FalseFactory(wrapt.AdapterFactory):
            def __bool__(self):
                return False

            def __call__(self, wrapped):
                calls.append(wrapped)
                argspec = inspect.getfullargspec(wrapped)
                argspec.args.insert(0, "arg0")
                return argspec

        class EmptyFactory(wrapt.AdapterFactory):
            def __len__(self):
                return 0

            __call__ = FalseFactory.__call__

        for factory_type in (FalseFactory, EmptyFactory):
            with self.subTest(factory=factory_type.__name__):
                calls.clear()

                factory = factory_type()

                self.assertFalse(factory)

                @wrapt.decorator(adapter=factory)
                def _wrapper(wrapped, instance, args, kwargs):
                    return wrapped(*args, **kwargs)

                def _function(arg1):
                    return arg1

                _decorated = _wrapper(_function)

                self.assertEqual(calls, [_function])

                self.assertEqual(str(inspect.signature(_decorated)), "(arg0, arg1)")
                self.assertEqual(
                    inspect.getfullargspec(_decorated).args, ["arg0", "arg1"]
                )

                self.assertEqual(_decorated(1), 1)

    def test_adapter_factory_returns_none(self):
        # A factory which returns None, or any other false value, means
        # that no adapter is to be used for that function.

        for result in (None, ""):
            with self.subTest(result=result):
                calls = []

                def factory(wrapped):
                    calls.append(wrapped)
                    return result

                @wrapt.decorator(adapter=wrapt.adapter_factory(factory))
                def _wrapper(wrapped, instance, args, kwargs):
                    return wrapped(*args, **kwargs)

                def _function(arg1):
                    return arg1

                _decorated = _wrapper(_function)

                self.assertEqual(calls, [_function])

                self.assertEqual(
                    inspect.signature(_decorated), inspect.signature(_function)
                )
                self.assertEqual(inspect.getfullargspec(_decorated).args, ["arg1"])

                self.assertEqual(_decorated(1), 1)

    def test_adapter_evaluates_false(self):
        # Passing a false value directly as the adapter means there is no
        # adapter, so the original signature is retained.

        for adapter in (None, False, ""):
            with self.subTest(adapter=adapter):

                @wrapt.decorator(adapter=adapter)
                def _wrapper(wrapped, instance, args, kwargs):
                    return wrapped(*args, **kwargs)

                def _function(arg1):
                    return arg1

                _decorated = _wrapper(_function)

                self.assertEqual(
                    inspect.signature(_decorated), inspect.signature(_function)
                )

                self.assertEqual(_decorated(1), 1)


if __name__ == "__main__":
    unittest.main()
