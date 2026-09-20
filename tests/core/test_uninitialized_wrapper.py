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

The same applies to reading that state through the ``_self_`` attributes. The
C extension used to substitute ``None``, or an empty tuple or dictionary,
which for most of the attributes is indistinguishable from the state of a
wrapper which had been initialized. As the lookup of a missing attribute on a
proxy falls through to the wrapped object, the ``AttributeError`` is that of
the wrapped object, and where the wrapped object is itself a wrapper it is
the attribute of that wrapper which is returned.
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


FUNCTION_WRAPPER_ATTRIBUTES = (
    "_self_instance",
    "_self_wrapper",
    "_self_enabled",
    "_self_binding",
    "_self_parent",
    "_self_owner",
)

PARTIAL_ATTRIBUTES = ("_self_args", "_self_kwargs")


class TestUninitializedWrapperAttributes(unittest.TestCase):

    def check_attributes_missing(self, wrapper, names):
        for name in names:
            with self.subTest(name=name):
                with self.assertRaises(AttributeError):
                    getattr(wrapper, name)

                self.assertFalse(hasattr(wrapper, name))

    def test_function_wrapper_created_by_new(self):
        wrapper = new_without_init(wrapt.FunctionWrapper)

        self.check_attributes_missing(wrapper, FUNCTION_WRAPPER_ATTRIBUTES)

    def test_function_wrapper_derived_class_not_calling_base_init(self):
        class Wrapper(wrapt.FunctionWrapper):
            def __init__(self, wrapped):
                self.__wrapped__ = wrapped

        self.check_attributes_missing(Wrapper(function), FUNCTION_WRAPPER_ATTRIBUTES)

    def test_bound_function_wrapper_created_by_new(self):
        wrapper = new_without_init(wrapt.BoundFunctionWrapper)

        self.check_attributes_missing(wrapper, FUNCTION_WRAPPER_ATTRIBUTES)

    def test_partial_created_by_new(self):
        wrapper = new_without_init(wrapt.PartialCallableObjectProxy)

        self.check_attributes_missing(wrapper, PARTIAL_ATTRIBUTES)

    def test_partial_derived_class_not_calling_base_init(self):
        class Partial(wrapt.PartialCallableObjectProxy):
            def __init__(self, wrapped):
                self.__wrapped__ = wrapped

        self.check_attributes_missing(Partial(function), PARTIAL_ATTRIBUTES)

    def test_error_is_that_of_the_wrapped_object(self):
        # The lookup falls through to the wrapped object, so the error
        # must be the same one as results from looking up the attribute
        # on the wrapped object directly.

        wrapper = new_without_init(wrapt.FunctionWrapper)

        with self.assertRaises(AttributeError) as direct:
            function._self_instance

        with self.assertRaises(AttributeError) as proxied:
            wrapper._self_instance

        self.assertEqual(str(proxied.exception), str(direct.exception))

    def test_attributes_of_wrapped_wrapper_are_returned(self):
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        inner = wrapt.FunctionWrapper(function, wrapper, enabled=True)

        outer = wrapt.FunctionWrapper.__new__(wrapt.FunctionWrapper)
        outer.__wrapped__ = inner

        self.assertIs(outer._self_wrapper, wrapper)
        self.assertIs(outer._self_enabled, True)
        self.assertIsNone(outer._self_instance)
        self.assertEqual(outer._self_binding, inner._self_binding)

    def test_initialized_function_wrapper_unaffected(self):
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        instance = wrapt.FunctionWrapper(function, wrapper)

        self.assertIsNone(instance._self_instance)
        self.assertIs(instance._self_wrapper, wrapper)
        self.assertIsNone(instance._self_enabled)
        self.assertEqual(instance._self_binding, "function")
        self.assertIsNone(instance._self_parent)
        self.assertIsNone(instance._self_owner)

    def test_initialized_partial_without_keywords_unaffected(self):
        # The captured keyword arguments are legitimately not set in the
        # C extension when none are supplied, which must still be reported
        # as an empty dictionary rather than as a missing attribute.

        wrapper = wrapt.PartialCallableObjectProxy(function, 1)

        self.assertEqual(wrapper._self_args, (1,))
        self.assertEqual(wrapper._self_kwargs, {})

    def test_initialized_partial_with_keywords_unaffected(self):
        wrapper = wrapt.PartialCallableObjectProxy(function, 1, a=2)

        self.assertEqual(wrapper._self_args, (1,))
        self.assertEqual(wrapper._self_kwargs, {"a": 2})


if __name__ == "__main__":
    unittest.main()
