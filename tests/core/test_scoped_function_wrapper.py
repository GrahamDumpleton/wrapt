import functools
import sys
import types
import unittest

import wrapt


class TestScopedFunctionWrapper(unittest.TestCase):

    def setUp(self):
        self.module = types.ModuleType("scoped_wrapper_target")
        self.module.function = lambda *args, **kwargs: (args, kwargs)
        sys.modules["scoped_wrapper_target"] = self.module

    def tearDown(self):
        del sys.modules["scoped_wrapper_target"]

    def test_patch_scoped_to_block(self):
        original = self.module.function

        calls = []

        def capture(wrapped, instance, args, kwargs):
            calls.append((args, kwargs))
            return wrapped(*args, **kwargs)

        with wrapt.scoped_function_wrapper(self.module, "function", capture):
            result = self.module.function(1, one=1)

        self.assertEqual(result, ((1,), {"one": 1}))
        self.assertEqual(calls, [((1,), {"one": 1})])

        # The patch is removed on exit, with the identical original
        # restored, and the wrapper no longer invoked.

        self.assertIs(self.module.function, original)

        self.module.function(2)

        self.assertEqual(len(calls), 1)

    def test_yields_nothing(self):
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with wrapt.scoped_function_wrapper(
            self.module, "function", passthrough
        ) as value:
            self.assertIsNone(value)

    def test_removed_on_exception(self):
        original = self.module.function

        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with self.assertRaises(ZeroDivisionError):
            with wrapt.scoped_function_wrapper(self.module, "function", passthrough):
                raise ZeroDivisionError("failure from the block")

        self.assertIs(self.module.function, original)

    def test_nested_scopes(self):
        original = self.module.function

        def wrapper_a(wrapped, instance, args, kwargs):
            return ("a", wrapped(*args, **kwargs))

        def wrapper_b(wrapped, instance, args, kwargs):
            return ("b", wrapped(*args, **kwargs))

        with wrapt.scoped_function_wrapper(self.module, "function", wrapper_a):
            with wrapt.scoped_function_wrapper(self.module, "function", wrapper_b):
                self.assertEqual(self.module.function(), ("b", ("a", ((), {}))))

            self.assertEqual(self.module.function(), ("a", ((), {})))

        self.assertIs(self.module.function, original)

    def test_class_method_target(self):
        class MyClass:
            def method(self):
                return "original"

        original = wrapt.resolve_path(MyClass, "method")[2]

        def wrapper(wrapped, instance, args, kwargs):
            return ("wrapped", wrapped(*args, **kwargs))

        with wrapt.scoped_function_wrapper(MyClass, "method", wrapper):
            self.assertEqual(MyClass().method(), ("wrapped", "original"))

        self.assertIs(wrapt.resolve_path(MyClass, "method")[2], original)
        self.assertEqual(MyClass().method(), "original")

    def test_deferred_target_rejected(self):
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with self.assertRaises(ValueError):
            with wrapt.scoped_function_wrapper(
                "scoped_wrapper_target?", "function", passthrough
            ):
                pass

    def test_removed_during_block_raises(self):
        # As for transient_function_wrapper(), interference with the
        # patch during the block is loud on exit.

        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            with wrapt.scoped_function_wrapper(self.module, "function", passthrough):
                self.module.function = lambda: "replaced"

    def test_wrapt_wrapper_left_on_top_spliced(self):
        # A wrapt wrapper applied over the temporary wrapper during the
        # block and left there is tolerated, with the temporary wrapper
        # spliced out beneath it on exit.

        original = self.module.function

        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        def their_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        handles = []

        with wrapt.scoped_function_wrapper(self.module, "function", passthrough):
            handles.append(
                wrapt.wrap_function_wrapper(self.module, "function", their_wrapper)
            )

        self.assertIs(self.module.function, handles[0])
        self.assertIs(self.module.function.__wrapped__, original)

    def test_non_wrapt_wrapper_left_on_top_raises(self):
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with self.assertRaises(wrapt.WrapperNotOutermostError):
            with wrapt.scoped_function_wrapper(self.module, "function", passthrough):
                inner = self.module.function

                @functools.wraps(inner)
                def closure():
                    return inner()

                self.module.function = closure
