import functools
import inspect
import unittest

import wrapt


class TestPartialCallableObjectProxy(unittest.TestCase):

    def test_no_arguments(self):
        def func0():
            return ((), {})

        partial0 = wrapt.partial(func0)

        args, kwargs = (), {}

        self.assertEqual(partial0(), (args, kwargs))

    def test_empty_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {}

        partial0 = wrapt.partial(func0, *args, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_1_positional_argument(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (1,), {}

        partial0 = wrapt.partial(func0, *args)

        self.assertEqual(partial0(), (args, kwargs))

    def test_1_keyword_argument(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {"k1": 1}

        partial0 = wrapt.partial(func0, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_multiple_positional_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (1, 2, 3), {}

        partial0 = wrapt.partial(func0, *args)

        self.assertEqual(partial0(), (args, kwargs))

    def test_multiple_keyword_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {"k1": 1, "k2": 2, "k3": 3}

        partial0 = wrapt.partial(func0, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_bound_arguments_no_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.partial(func0)

        self.assertEqual(partial0._self_args, ())
        self.assertEqual(partial0._self_kwargs, {})

    def test_bound_arguments_positional(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.partial(func0, 1, 2, 3)

        self.assertEqual(partial0._self_args, (1, 2, 3))
        self.assertEqual(partial0._self_kwargs, {})

    def test_bound_arguments_keyword(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.partial(func0, k1=1, k2=2)

        self.assertEqual(partial0._self_args, ())
        self.assertEqual(partial0._self_kwargs, {"k1": 1, "k2": 2})

    def test_bound_arguments_mixed(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.PartialCallableObjectProxy(func0, 1, 2, k1=1)

        self.assertEqual(partial0._self_args, (1, 2))
        self.assertEqual(partial0._self_kwargs, {"k1": 1})

    def test_bound_arguments_not_forwarded_to_wrapped(self):
        # The attributes must come from the proxy itself and not be
        # forwarded to a same named attribute on the wrapped callable.

        class Callable:
            _self_args = ("wrapped",)
            _self_kwargs = {"wrapped": True}

            def __call__(self, *args, **kwargs):
                return (args, kwargs)

        partial0 = wrapt.partial(Callable(), 1, k1=1)

        self.assertEqual(partial0._self_args, (1,))
        self.assertEqual(partial0._self_kwargs, {"k1": 1})


class TestPartialCallableObjectProxySignature(unittest.TestCase):

    def assertSignatureMatchesPartial(self, func, *args, **kwargs):
        expected = inspect.signature(functools.partial(func, *args, **kwargs))
        actual = inspect.signature(wrapt.partial(func, *args, **kwargs))

        self.assertEqual(actual, expected)

        return actual

    def test_no_bound_arguments(self):
        def func0(a, b, c=1):
            pass

        signature = self.assertSignatureMatchesPartial(func0)

        self.assertEqual(list(signature.parameters), ["a", "b", "c"])

    def test_positional_argument(self):
        def func0(a, b, c=1):
            pass

        signature = self.assertSignatureMatchesPartial(func0, 1)

        self.assertEqual(list(signature.parameters), ["b", "c"])

    def test_method_with_instance_bound(self):
        class Class:
            def method(self, query, *args, column=0, timeout=None):
                pass

        signature = self.assertSignatureMatchesPartial(Class.method, Class())

        self.assertEqual(
            list(signature.parameters), ["query", "args", "column", "timeout"]
        )

    def test_keyword_argument(self):
        class Class:
            def method(self, query, *args, column=0, timeout=None):
                pass

        signature = self.assertSignatureMatchesPartial(Class.method, Class(), column=3)

        self.assertEqual(signature.parameters["column"].default, 3)

    def test_too_many_positional_arguments(self):
        def func0(a, b, c=1):
            pass

        with self.assertRaises(ValueError):
            inspect.signature(functools.partial(func0, 1, 2, 3, 4))

        with self.assertRaises(ValueError):
            inspect.signature(wrapt.partial(func0, 1, 2, 3, 4))

    def test_attribute_on_instance_only(self):
        def func0(a, b, c=1):
            pass

        partial0 = wrapt.partial(func0, 1)

        self.assertTrue(hasattr(partial0, "__signature__"))
        self.assertIsInstance(partial0.__signature__, inspect.Signature)

        # The attribute must not be visible on the class, otherwise
        # inspect.signature() of the class itself would fail on finding
        # something other than a Signature object.

        self.assertFalse(hasattr(wrapt.PartialCallableObjectProxy, "__signature__"))

        try:
            inspect.signature(wrapt.PartialCallableObjectProxy)
        except ValueError:
            # The C extension type has no text signature, so inspect is
            # unable to determine one for the class. This is pre-existing
            # behaviour and unrelated to __signature__ on instances. What
            # matters is that no TypeError is raised due to finding a
            # descriptor object in the __signature__ attribute of the class.
            pass

        # Nor should it have leaked onto the wrapped function.

        self.assertFalse(hasattr(func0, "__signature__"))

    def test_bound_method_limitation(self):
        # When the wrapped callable is an already bound method, inspect
        # decides based on the class of the object, which the proxy reports
        # as being that of the bound method, before it looks for a
        # __signature__ attribute. It therefore reports the signature of the
        # bound method and ignores the arguments bound by the partial. This
        # is documented as a known limitation. The test pins the current
        # behaviour so that a future change in inspect which corrects this
        # is noticed and the documentation can be updated.

        class Class:
            def method(self, query, *args, column=0, timeout=None):
                pass

        instance = Class()

        expected = inspect.signature(functools.partial(instance.method, "query"))
        actual = inspect.signature(wrapt.partial(instance.method, "query"))

        self.assertNotEqual(actual, expected)
        self.assertEqual(actual, inspect.signature(instance.method))

    def test_function_wrapper_called_via_class(self):
        # When a wrapped method is called via the class with the instance
        # passed explicitly, FunctionWrapper passes the wrapper function a
        # PartialCallableObjectProxy with the instance bound, and args
        # without the instance. The signature of the partial must therefore
        # omit the instance so that args and kwargs can be bound against it.

        seen = []

        def wrapper(wrapped, instance, args, kwargs):
            bound = inspect.signature(wrapped).bind(*args, **kwargs)
            seen.append(dict(bound.arguments))
            return wrapped(*args, **kwargs)

        class Class:
            @wrapt.decorator
            def _wrapper(wrapped, instance, args, kwargs):
                return wrapper(wrapped, instance, args, kwargs)

            @_wrapper
            def method(self, query, *args, column=0, timeout=None):
                return (query, args, column, timeout)

        instance = Class()

        self.assertEqual(
            instance.method("SELECT 1", column=1), ("SELECT 1", (), 1, None)
        )
        self.assertEqual(seen[-1], {"query": "SELECT 1", "column": 1})

        self.assertEqual(
            Class.method(instance, "SELECT 2", column=2), ("SELECT 2", (), 2, None)
        )
        self.assertEqual(seen[-1], {"query": "SELECT 2", "column": 2})


if __name__ == "__main__":
    unittest.main()
