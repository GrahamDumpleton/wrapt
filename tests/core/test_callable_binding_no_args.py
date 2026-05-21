"""Tests for BoundFunctionWrapper with binding="callable" and instance=None.

When a callable descriptor (an object with both __call__ and __get__) is
wrapped with FunctionWrapper and assigned as a class attribute, accessing
it via the class (not an instance) produces a BoundFunctionWrapper with
binding="callable" and instance=None. In this state, the dispatch logic
should behave the same as the "function" path: only extract the instance
from the first argument if it is an instance of the owner class, and
otherwise call the wrapper with instance=None.
"""

import unittest

import wrapt


class CallableDescriptor:
    """A descriptor that is also callable, producing binding='callable'."""

    def __call__(self, *args, **kwargs):
        return ("called", args, kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        import functools

        return functools.partial(self, instance)


class TestCallableBindingNoArgs(unittest.TestCase):
    """BoundFunctionWrapper(binding='callable', instance=None) called with no args."""

    def setUp(self):
        def wrapper(wrapped, instance, args, kwargs):
            self._last_instance = instance
            self._last_args = args
            return wrapped(*args, **kwargs)

        cd = CallableDescriptor()
        fw = wrapt.FunctionWrapper(cd, wrapper)

        class Host:
            method = fw

        self._Host = Host
        self._last_instance = None
        self._last_args = None

    def test_unbound_access_produces_callable_binding(self):
        """Accessing via the class should give binding='callable', instance=None."""
        unbound = self._Host.method
        self.assertIsInstance(unbound, wrapt.BoundFunctionWrapper)
        self.assertEqual(unbound._self_binding, "callable")
        self.assertIsNone(unbound._self_instance)

    def test_callable_binding_no_args_calls_wrapper(self):
        """Calling with no args should call the wrapper with instance=None."""
        unbound = self._Host.method
        result = unbound()
        self.assertEqual(result, ("called", (), {}))
        self.assertIsNone(self._last_instance)
        self.assertEqual(self._last_args, ())

    def test_callable_binding_with_instance_arg_succeeds(self):
        """Calling via the class with an explicit instance arg should work."""
        host = self._Host()
        result = self._Host.method(host, "hello")
        self.assertEqual(result, ("called", (host, "hello"), {}))
        self.assertIs(self._last_instance, host)
        self.assertEqual(self._last_args, ("hello",))

    def test_bound_access_succeeds(self):
        """Calling via an instance should work normally."""
        host = self._Host()
        result = host.method("hello")
        self.assertEqual(result, ("called", (host, "hello"), {}))
