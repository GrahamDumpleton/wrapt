import functools
import unittest

import wrapt


def function_outermost(*args, **kwargs):
    return args, kwargs


def function_buried(*args, **kwargs):
    return args, kwargs


def function_closure(*args, **kwargs):
    return args, kwargs


def function_theirs(*args, **kwargs):
    return args, kwargs


def function_equality(*args, **kwargs):
    return args, kwargs


def function_predicate(*args, **kwargs):
    return args, kwargs


def function_twice(*args, **kwargs):
    return args, kwargs


def function_replaced(*args, **kwargs):
    return args, kwargs


class ClassWithMethod:
    def method(self):
        return "original"


class DerivedFromClassWithMethod(ClassWithMethod):
    pass


def wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


class TestFindWrapper(unittest.TestCase):

    def test_outermost_wrapper(self):
        # The installed wrapper is found by its handle, and the handle
        # of a different wrapper is not matched.

        handle = wrapt.wrap_function_wrapper(__name__, "function_outermost", wrapper)
        other = wrapt.FunctionWrapper(function_outermost, wrapper)

        current = wrapt.resolve_path(__name__, "function_outermost")[2]

        self.assertIs(wrapt.find_wrapper(current, handle), handle)
        self.assertIsNone(wrapt.find_wrapper(current, other))

    def test_buried_wrapper(self):
        # The wrapper is still found when somebody else has since
        # wrapped over the top of it.

        handle = wrapt.wrap_function_wrapper(__name__, "function_buried", wrapper)
        wrapt.wrap_function_wrapper(__name__, "function_buried", wrapper)

        current = wrapt.resolve_path(__name__, "function_buried")[2]

        self.assertIsNot(current, handle)
        self.assertIs(wrapt.find_wrapper(current, handle), handle)

    def test_buried_under_closure(self):
        # The wrapper is found beneath a plain functools.wraps closure,
        # which participates in the __wrapped__ protocol.

        handle = wrapt.wrap_function_wrapper(__name__, "function_closure", wrapper)

        installed = wrapt.resolve_path(__name__, "function_closure")[2]

        @functools.wraps(installed)
        def their_closure(*args, **kwargs):
            return installed(*args, **kwargs)

        wrapt.apply_patch(__import__(__name__), "function_closure", their_closure)

        current = wrapt.resolve_path(__name__, "function_closure")[2]

        self.assertIs(wrapt.find_wrapper(current, handle), handle)

    def test_wrapped_by_someone_else(self):
        # An attribute wrapped only by somebody else does not match a
        # handle which was never installed there.

        wrapt.wrap_function_wrapper(__name__, "function_theirs", wrapper)

        stale = wrapt.FunctionWrapper(function_theirs, wrapper)

        current = wrapt.resolve_path(__name__, "function_theirs")[2]

        self.assertIsNone(wrapt.find_wrapper(current, stale))
        self.assertFalse(wrapt.is_wrapped_by(current, stale))

    def test_class_attribute_getattr_trap(self):
        # Reading a wrapped method off the class with getattr() triggers
        # descriptor binding and yields a fresh BoundFunctionWrapper, in
        # which the handle is not found. Reading with resolve_path()
        # yields the installed wrapper itself, in which it is.

        handle = wrapt.wrap_function_wrapper(ClassWithMethod, "method", wrapper)

        bound = getattr(ClassWithMethod, "method")

        self.assertIsNone(wrapt.find_wrapper(bound, handle))

        unbound = wrapt.resolve_path(ClassWithMethod, "method")[2]

        self.assertIs(wrapt.find_wrapper(unbound, handle), handle)

        # Resolution through a subclass finds the same wrapper via the
        # method resolution order.

        via_subclass = wrapt.resolve_path(DerivedFromClassWithMethod, "method")[2]

        self.assertIs(wrapt.find_wrapper(via_subclass, handle), handle)

    def test_equality_is_not_identity(self):
        # An object which merely compares equal to a chain entry, as
        # proxies delegate __eq__ to the wrapped object, is not matched;
        # the scan is identity only.

        wrapt.wrap_function_wrapper(__name__, "function_equality", wrapper)

        current = wrapt.resolve_path(__name__, "function_equality")[2]
        lookalike = wrapt.ObjectProxy(function_equality)

        self.assertEqual(current, lookalike)
        self.assertIsNone(wrapt.find_wrapper(current, lookalike))

    def test_predicate(self):
        # A predicate finds a wrapper without a handle, and the entry
        # returned is itself usable as a handle thereafter.

        handle = wrapt.wrap_function_wrapper(__name__, "function_predicate", wrapper)

        current = wrapt.resolve_path(__name__, "function_predicate")[2]

        found = wrapt.find_wrapper(
            current,
            predicate=lambda entry: getattr(entry, "_self_wrapper", None) is wrapper,
        )

        self.assertIs(found, handle)

        self.assertTrue(
            wrapt.is_wrapped_by(
                current,
                predicate=lambda entry: getattr(entry, "_self_wrapper", None)
                is wrapper,
            )
        )

    def test_handle_and_predicate_both_match(self):
        handle = wrapt.FunctionWrapper(function_outermost, wrapper)

        self.assertIs(
            wrapt.find_wrapper(
                handle, handle, predicate=lambda entry: entry is handle
            ),
            handle,
        )
        self.assertIsNone(
            wrapt.find_wrapper(handle, handle, predicate=lambda entry: False)
        )

    def test_no_criteria_raises(self):
        with self.assertRaises(TypeError):
            wrapt.find_wrapper(function_outermost)

        with self.assertRaises(TypeError):
            wrapt.is_wrapped_by(function_outermost)

    def test_wrapped_call_still_works(self):
        # Detection does not disturb the installed wrapper.

        current = wrapt.resolve_path(__name__, "function_outermost")[2]

        self.assertEqual(current(1, one=1), ((1,), {"one": 1}))

    def test_same_wrapper_function_twice(self):
        # The same wrapper function applied twice produces two distinct
        # handles, each finding exactly its own installed instance.

        first = wrapt.wrap_function_wrapper(__name__, "function_twice", wrapper)
        second = wrapt.wrap_function_wrapper(__name__, "function_twice", wrapper)

        self.assertIsNot(first, second)

        current = wrapt.resolve_path(__name__, "function_twice")[2]

        self.assertIs(wrapt.find_wrapper(current, first), first)
        self.assertIs(wrapt.find_wrapper(current, second), second)

    def test_wholesale_replacement(self):
        # After a third party blindly restores the original with
        # setattr(), the handle is no longer found. The original must be
        # captured before wrapping, since the module global is rebound
        # to the wrapper once the patch is applied.

        original = wrapt.resolve_path(__name__, "function_replaced")[2]

        handle = wrapt.wrap_function_wrapper(__name__, "function_replaced", wrapper)

        wrapt.apply_patch(__import__(__name__), "function_replaced", original)

        current = wrapt.resolve_path(__name__, "function_replaced")[2]

        self.assertIsNone(wrapt.find_wrapper(current, handle))
        self.assertFalse(wrapt.is_wrapped_by(current, handle))

    def test_deep_chain_raises(self):
        # An indeterminate scan raises rather than reporting a false
        # negative, which would defeat the double install guard.

        deep = function_outermost
        for _ in range(200):
            deep = wrapt.ObjectProxy(deep)

        handle = wrapt.FunctionWrapper(function_outermost, wrapper)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            wrapt.find_wrapper(deep, handle)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            wrapt.is_wrapped_by(deep, handle)
