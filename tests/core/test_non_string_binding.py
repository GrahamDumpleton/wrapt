"""Tests for function wrappers where the binding is not a string.

The binding of a function wrapper is normally one of the strings produced
internally, such as "function" or "classmethod", but a wrapper can be
constructed directly with any object as the binding. A non-string binding
can also be inherited when a function wrapper wraps an existing wrapper.

The pure Python implementation compares the binding against the known
names and, as a non-string never matches, takes the fallback path in each
case. The C extension previously passed the binding to string-only C API
functions, crashing the interpreter. See issue #368.
"""

import unittest

import wrapt
from wrapt.__wrapt__ import _FunctionWrapperBase

# Values used as the binding. Not all of these crashed the C extension
# reliably, as the result depended on the memory layout of the object,
# but object() and float did.

NON_STRING_BINDINGS = (object(), 1.5, 0, None, b"function", [])

# Values used as the binding where it is inherited from a wrapped wrapper.
# Falsy values are excluded as the pure Python implementation discards a
# falsy inherited binding and works out the binding itself.

TRUTHY_NON_STRING_BINDINGS = (object(), 1.5, b"function", [1])


def function(*args, **kwargs):
    return "function", args, kwargs


class Class:

    def method(self, *args, **kwargs):
        return "method", args, kwargs

    @classmethod
    def class_method(cls, *args, **kwargs):
        return "class_method", args, kwargs


class _BaseWrapper(_FunctionWrapperBase):
    # A minimal unbound wrapper which accepts an explicit binding.

    __bound_function_wrapper__ = wrapt.BoundFunctionWrapper


def recording_wrapper(calls):
    def wrapper(wrapped, instance, args, kwargs):
        calls.append((wrapped, instance, args, kwargs))
        return "wrapper"

    return wrapper


def binding_name(binding):
    return type(binding).__name__


class TestBoundFunctionWrapperCall(unittest.TestCase):

    def test_issue_reproducer(self):
        def wrapper(wrapped, instance, args, kwargs):
            return "ok"

        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                bound = wrapt.BoundFunctionWrapper(
                    function, None, wrapper, None, binding
                )
                self.assertEqual(bound(), "ok")

    def test_function_uses_fallback(self):
        # A non-string binding takes the fallback path, which passes the
        # __self__ of the wrapped function as instance, which for a plain
        # function is None, ignoring the instance the wrapper holds.

        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                calls = []
                bound = wrapt.BoundFunctionWrapper(
                    function, object(), recording_wrapper(calls), None, binding
                )

                self.assertEqual(bound(1, flag=True), "wrapper")
                self.assertEqual(calls, [(function, None, (1,), {"flag": True})])

    def test_class_method_uses_fallback(self):
        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                calls = []
                bound = wrapt.BoundFunctionWrapper(
                    Class.class_method,
                    None,
                    recording_wrapper(calls),
                    None,
                    binding,
                    None,
                    Class,
                )

                self.assertEqual(bound(1), "wrapper")
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0], Class.class_method)
                self.assertIs(calls[0][1], Class)
                self.assertEqual(calls[0][2], (1,))

    def test_disabled_wrapper_calls_wrapped(self):
        def wrapper(wrapped, instance, args, kwargs):
            raise AssertionError("disabled wrapper must not be called")

        for enabled in (False, lambda: False):
            with self.subTest(enabled=enabled):
                bound = wrapt.BoundFunctionWrapper(
                    function, None, wrapper, enabled, object()
                )
                self.assertEqual(bound(1), ("function", (1,), {}))


class TestFunctionWrapperBaseCall(unittest.TestCase):

    def test_call_uses_wrapped_instance(self):
        # Calling an unbound wrapper with no instance looks for __self__ on
        # the wrapped object only for the known function bindings. For a
        # non-string binding the wrapper is called with instance as None.

        instance = Class()

        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                calls = []
                unbound = _BaseWrapper(
                    instance.method, None, recording_wrapper(calls), None, binding
                )

                self.assertEqual(unbound(1), "wrapper")
                self.assertEqual(calls, [(instance.method, None, (1,), {})])

    def test_call_with_instance(self):
        instance = Class()

        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                calls = []
                unbound = _BaseWrapper(
                    function, instance, recording_wrapper(calls), None, binding
                )

                self.assertEqual(unbound(1), "wrapper")
                self.assertEqual(calls, [(function, instance, (1,), {})])


class TestDescriptorBinding(unittest.TestCase):

    def test_get_on_unbound_wrapper(self):
        # Binding an unbound wrapper checks for the "builtin" and "class"
        # bindings before binding the wrapped function.

        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                calls = []
                unbound = _BaseWrapper(
                    Class.method, None, recording_wrapper(calls), None, binding
                )

                instance = Class()
                bound = unbound.__get__(instance, Class)

                self.assertIsInstance(bound, wrapt.BoundFunctionWrapper)
                self.assertIs(bound._self_parent, unbound)
                self.assertIs(bound._self_binding, binding)

                # The bound wrapper also has a non-string binding and so
                # takes the fallback path, passing __self__ of the bound
                # method through as instance.

                self.assertEqual(bound(1), "wrapper")
                self.assertEqual(len(calls), 1)
                self.assertIs(calls[0][1], instance)
                self.assertEqual(calls[0][2], (1,))

    def test_get_on_bound_wrapper_with_no_instance(self):
        # Binding again a bound wrapper with no instance rebinds via the
        # parent only for the known function bindings. For a non-string
        # binding the bound wrapper is returned unchanged.

        def wrapper(wrapped, instance, args, kwargs):
            return "wrapper"

        parent = wrapt.FunctionWrapper(Class.method, wrapper)

        for binding in NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                bound = wrapt.BoundFunctionWrapper(
                    Class.method, None, wrapper, None, binding, parent, Class
                )

                self.assertIs(bound.__get__(Class(), Class), bound)


class TestInheritedBinding(unittest.TestCase):

    def test_function_wrapper_inherits_binding(self):
        def wrapper(wrapped, instance, args, kwargs):
            return "inner"

        for binding in TRUTHY_NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                inner = wrapt.BoundFunctionWrapper(
                    function, None, wrapper, None, binding
                )
                outer = wrapt.FunctionWrapper(inner, wrapper)

                self.assertIs(outer._self_binding, binding)

    def test_function_wrapper_call(self):
        def inner_wrapper(wrapped, instance, args, kwargs):
            return "inner", wrapped(*args, **kwargs)

        for binding in TRUTHY_NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                calls = []
                inner = wrapt.BoundFunctionWrapper(
                    function, None, inner_wrapper, None, binding
                )
                outer = wrapt.FunctionWrapper(inner, recording_wrapper(calls))

                self.assertEqual(outer(1), "wrapper")
                self.assertEqual(calls, [(inner, None, (1,), {})])

                self.assertEqual(inner(1), ("inner", ("function", (1,), {})))

    def test_function_wrapper_get(self):
        def wrapper(wrapped, instance, args, kwargs):
            return "wrapper"

        for binding in TRUTHY_NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                inner = _BaseWrapper(Class.method, None, wrapper, None, binding)
                outer = wrapt.FunctionWrapper(inner, wrapper)

                instance = Class()
                bound = outer.__get__(instance, Class)

                self.assertIsInstance(bound, wrapt.BoundFunctionWrapper)
                self.assertIs(bound._self_parent, outer)
                self.assertIs(bound._self_binding, binding)
                self.assertEqual(bound(), "wrapper")

    def test_decorator_applied_to_wrapper(self):
        @wrapt.decorator
        def decorator(wrapped, instance, args, kwargs):
            return "decorator", wrapped(*args, **kwargs)

        def wrapper(wrapped, instance, args, kwargs):
            return "inner"

        for binding in TRUTHY_NON_STRING_BINDINGS:
            with self.subTest(binding=binding_name(binding)):
                inner = wrapt.BoundFunctionWrapper(
                    function, None, wrapper, None, binding
                )
                outer = decorator(inner)

                self.assertEqual(outer(), ("decorator", "inner"))


class TestStringBindings(unittest.TestCase):

    def test_unknown_string_uses_fallback(self):
        calls = []
        bound = wrapt.BoundFunctionWrapper(
            function, object(), recording_wrapper(calls), None, "unknown"
        )

        self.assertEqual(bound(1), "wrapper")
        self.assertEqual(calls, [(function, None, (1,), {})])

    def test_str_subclass_matches_known_binding(self):
        # A str subclass with the same value as a known binding must still
        # be treated as that binding, so the type check must not be limited
        # to exact str instances.

        class Binding(str):
            pass

        for binding in (Binding("function"), Binding("callable")):
            with self.subTest(binding=binding):
                calls = []
                bound = wrapt.BoundFunctionWrapper(
                    Class.method,
                    None,
                    recording_wrapper(calls),
                    None,
                    binding,
                    None,
                    Class,
                )

                # Calling via the class with an instance as the first
                # argument binds the instance, which only happens for the
                # "function" and "callable" bindings.

                instance = Class()

                self.assertEqual(bound(instance, 1), "wrapper")
                self.assertEqual(len(calls), 1)
                self.assertIsInstance(calls[0][0], wrapt.PartialCallableObjectProxy)
                self.assertIs(calls[0][1], instance)
                self.assertEqual(calls[0][2], (1,))

    def test_str_subclass_matches_known_binding_on_get(self):
        class Binding(str):
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return "wrapper"

        unbound = _BaseWrapper(len, None, wrapper, None, Binding("builtin"))

        self.assertIs(unbound.__get__(Class(), Class), unbound)


if __name__ == "__main__":
    unittest.main()
