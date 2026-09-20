"""Tests for use of a function wrapper or partial which was never initialized.

The additional state of a ``FunctionWrapper``, ``BoundFunctionWrapper`` or
``PartialCallableObjectProxy`` is only set by ``__init__()``. If that is never
called, but ``__wrapped__`` is assigned directly, the check for an
uninitialized wrapper passes as it only considers ``__wrapped__``. That can
occur where a derived class overrides ``__init__()`` and sets ``__wrapped__``
itself rather than calling ``__init__()`` of the base class, or where an
instance is created using ``__new__()`` alone.

The C extension used to crash the interpreter when such a wrapper was called,
as it used the fields for that state without checking they had been set. Both
implementations must instead raise ``AttributeError``, which is what the pure
Python implementation yields as the instance attributes do not exist.
"""

import unittest

import wrapt


def function(*args, **kwargs):
    return args, kwargs


def new_without_init(cls):
    wrapper = cls.__new__(cls)
    wrapper.__wrapped__ = function
    return wrapper


class TestUninitializedFunctionWrapper(unittest.TestCase):

    def test_call_created_by_new(self):
        wrapper = new_without_init(wrapt.FunctionWrapper)

        with self.assertRaises(AttributeError):
            wrapper()

    def test_call_with_arguments_created_by_new(self):
        wrapper = new_without_init(wrapt.FunctionWrapper)

        with self.assertRaises(AttributeError):
            wrapper(1, 2, key="value")

    def test_call_derived_class_not_calling_base_init(self):
        class Wrapper(wrapt.FunctionWrapper):
            def __init__(self, wrapped):
                self.__wrapped__ = wrapped

        wrapper = Wrapper(function)

        with self.assertRaises(AttributeError):
            wrapper()

    def test_descriptor_access_via_instance(self):
        class Class:
            method = new_without_init(wrapt.FunctionWrapper)

        with self.assertRaises(AttributeError):
            Class().method

    def test_descriptor_access_via_class(self):
        class Class:
            method = new_without_init(wrapt.FunctionWrapper)

        with self.assertRaises(AttributeError):
            Class.method

    def test_descriptor_access_derived_class_not_calling_base_init(self):
        class Wrapper(wrapt.FunctionWrapper):
            def __init__(self, wrapped):
                self.__wrapped__ = wrapped

        class Class:
            method = Wrapper(function)

        with self.assertRaises(AttributeError):
            Class().method()

    def test_initialized_wrapper_unaffected(self):
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            method = wrapt.FunctionWrapper(function, wrapper)

        self.assertEqual(
            wrapt.FunctionWrapper(function, wrapper)(1, a=2), ((1,), {"a": 2})
        )

        instance = Class()

        self.assertEqual(instance.method(1, a=2), ((instance, 1), {"a": 2}))


class TestUninitializedBoundFunctionWrapper(unittest.TestCase):

    def test_assign_wrapped_created_by_new(self):
        # The pure Python implementation used to fail with RecursionError
        # here, before the wrapper could even be called.

        wrapper = new_without_init(wrapt.BoundFunctionWrapper)

        self.assertIs(wrapper.__wrapped__, function)

    def test_call_created_by_new(self):
        wrapper = new_without_init(wrapt.BoundFunctionWrapper)

        with self.assertRaises(AttributeError):
            wrapper()

    def test_call_with_arguments_created_by_new(self):
        wrapper = new_without_init(wrapt.BoundFunctionWrapper)

        with self.assertRaises(AttributeError):
            wrapper(1, 2, key="value")


class TestUninitializedPartialCallableObjectProxy(unittest.TestCase):

    def test_call_created_by_new(self):
        wrapper = new_without_init(wrapt.PartialCallableObjectProxy)

        with self.assertRaises(AttributeError):
            wrapper()

    def test_call_with_arguments_created_by_new(self):
        wrapper = new_without_init(wrapt.PartialCallableObjectProxy)

        with self.assertRaises(AttributeError):
            wrapper(1, 2, key="value")

    def test_call_derived_class_not_calling_base_init(self):
        class Partial(wrapt.PartialCallableObjectProxy):
            def __init__(self, wrapped):
                self.__wrapped__ = wrapped

        wrapper = Partial(function)

        with self.assertRaises(AttributeError):
            wrapper()

    def test_initialized_partial_without_keywords_unaffected(self):
        # The captured keyword arguments are legitimately not set in the
        # C extension when none are supplied, so must not be required.

        wrapper = wrapt.PartialCallableObjectProxy(function, 1)

        self.assertEqual(wrapper(2, a=3), ((1, 2), {"a": 3}))


if __name__ == "__main__":
    unittest.main()
