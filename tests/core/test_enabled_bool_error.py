"""Tests that an exception raised while evaluating the truthiness of the
``enabled`` argument of a function wrapper is propagated to the caller
rather than being silently swallowed.

The C extension implementation in ``src/wrapt/_wrappers.c`` evaluates
``enabled`` using ``PyObject_Not``, which is a tri-valued function returning
``1`` (false), ``0`` (true) or ``-1`` (error). Four call sites currently use
the result as a plain C boolean::

    if (PyObject_Not(object))
        return PyObject_Call(self->object_proxy.wrapped, args, kwds);

In C, ``-1`` is non-zero and so the "wrapper disabled" branch is taken when
``__bool__`` raises. This silently bypasses the wrapper and calls the wrapped
function with a pending Python exception.

The four affected sites are:

* ``WraptFunctionWrapperBase_call`` - callable ``enabled`` branch
* ``WraptFunctionWrapperBase_call`` - non-callable ``enabled`` branch
* ``WraptBoundFunctionWrapper_call`` - callable ``enabled`` branch
* ``WraptBoundFunctionWrapper_call`` - non-callable ``enabled`` branch

The pure-Python implementation in ``src/wrapt/wrappers.py`` uses ``if not
self.enabled`` which propagates ``__bool__`` exceptions correctly, so the
same tests pass against the pure-Python implementation today and will pass
against the C extension once the four sites are fixed.
"""

import unittest

import wrapt
import wrapt.__wrapt__

USING_C_EXTENSION = wrapt.__wrapt__._using_c_extension


CANARY_MESSAGE = "enabled_bool_canary"


class _BoolCanary(RuntimeError):
    """Distinct exception type so the assertions cannot accidentally match an
    unrelated ``RuntimeError`` raised by surrounding machinery."""


class BoolRaiser:
    """An object whose ``__bool__`` raises ``_BoolCanary``. Used as either the
    ``enabled`` value itself, or as the return value of a callable ``enabled``,
    to drive the four ``PyObject_Not`` sites under test."""

    def __bool__(self):
        raise _BoolCanary(CANARY_MESSAGE)


class TestEnabledBoolErrorFunctionWrapper(unittest.TestCase):
    """Exercises ``WraptFunctionWrapperBase_call`` - the wrapper is attached
    to a plain function and called directly."""

    def test_callable_enabled_returning_object_whose_bool_raises(self):
        """Callable-``enabled`` branch: the callable returns successfully but
        the returned value's ``__bool__`` raises. The wrapper must propagate
        the exception and must not call the wrapped function or wrapper body.
        """

        wrapper_calls = []
        wrapped_calls = []

        def enabled():
            return BoolRaiser()

        @wrapt.decorator(enabled=enabled)
        def _wrapper(wrapped, instance, args, kwargs):
            wrapper_calls.append(1)
            return wrapped(*args, **kwargs)

        @_wrapper
        def function():
            wrapped_calls.append(1)

        with self.assertRaises(_BoolCanary) as cm:
            function()

        self.assertEqual(str(cm.exception), CANARY_MESSAGE)
        self.assertEqual(wrapper_calls, [])
        self.assertEqual(wrapped_calls, [])

    def test_noncallable_enabled_whose_bool_raises(self):
        """Non-callable-``enabled`` branch: ``enabled`` itself is an object
        whose ``__bool__`` raises. The wrapper must propagate the exception."""

        wrapper_calls = []
        wrapped_calls = []

        @wrapt.decorator(enabled=BoolRaiser())
        def _wrapper(wrapped, instance, args, kwargs):
            wrapper_calls.append(1)
            return wrapped(*args, **kwargs)

        @_wrapper
        def function():
            wrapped_calls.append(1)

        with self.assertRaises(_BoolCanary) as cm:
            function()

        self.assertEqual(str(cm.exception), CANARY_MESSAGE)
        self.assertEqual(wrapper_calls, [])
        self.assertEqual(wrapped_calls, [])


class TestEnabledBoolErrorBoundFunctionWrapper(unittest.TestCase):
    """Exercises ``WraptBoundFunctionWrapper_call`` - the wrapper is attached
    to an instance method and called via an instance, so descriptor binding
    routes the call through the bound-wrapper code path."""

    def test_callable_enabled_returning_object_whose_bool_raises(self):
        wrapper_calls = []
        wrapped_calls = []

        def enabled():
            return BoolRaiser()

        @wrapt.decorator(enabled=enabled)
        def _wrapper(wrapped, instance, args, kwargs):
            wrapper_calls.append(1)
            return wrapped(*args, **kwargs)

        class Class:
            @_wrapper
            def method(self):
                wrapped_calls.append(1)

        instance = Class()
        self.assertIsInstance(instance.method, wrapt.BoundFunctionWrapper)

        with self.assertRaises(_BoolCanary) as cm:
            instance.method()

        self.assertEqual(str(cm.exception), CANARY_MESSAGE)
        self.assertEqual(wrapper_calls, [])
        self.assertEqual(wrapped_calls, [])

    def test_noncallable_enabled_whose_bool_raises(self):
        wrapper_calls = []
        wrapped_calls = []

        @wrapt.decorator(enabled=BoolRaiser())
        def _wrapper(wrapped, instance, args, kwargs):
            wrapper_calls.append(1)
            return wrapped(*args, **kwargs)

        class Class:
            @_wrapper
            def method(self):
                wrapped_calls.append(1)

        instance = Class()
        self.assertIsInstance(instance.method, wrapt.BoundFunctionWrapper)

        with self.assertRaises(_BoolCanary) as cm:
            instance.method()

        self.assertEqual(str(cm.exception), CANARY_MESSAGE)
        self.assertEqual(wrapper_calls, [])
        self.assertEqual(wrapped_calls, [])


class TestEnabledFalsyControl(unittest.TestCase):
    """Positive control: confirms that a normal falsy result from a callable
    ``enabled`` still skips the wrapper body and calls the wrapped function
    directly. The fix to the ``PyObject_Not`` sites must not regress this."""

    def test_callable_enabled_returning_false_skips_wrapper(self):
        wrapper_calls = []
        wrapped_calls = []

        def enabled():
            return False

        @wrapt.decorator(enabled=enabled)
        def _wrapper(wrapped, instance, args, kwargs):
            wrapper_calls.append(1)
            return wrapped(*args, **kwargs)

        @_wrapper
        def function():
            wrapped_calls.append(1)

        function()

        self.assertEqual(wrapper_calls, [])
        self.assertEqual(wrapped_calls, [1])


if __name__ == "__main__":
    unittest.main()
