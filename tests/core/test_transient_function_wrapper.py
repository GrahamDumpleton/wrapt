import functools
import types
import unittest

import wrapt


def global_function(*args, **kwargs):
    return "original"


class TestTransientFunctionWrapper(unittest.TestCase):

    def _test_transient_function_wrapper(self, *args, **kwargs):
        return args, kwargs

    def test_transient_function_wrapper(self):

        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        called = []

        @wrapt.transient_function_wrapper(
            __name__, "TestTransientFunctionWrapper._test_transient_function_wrapper"
        )
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(wrapped, self._test_transient_function_wrapper)
            self.assertEqual(instance, self)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @wrapper
        def function(*args, **kwargs):
            return self._test_transient_function_wrapper(*args, **kwargs)

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_transient_function_wrapper_instance_method(self):

        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        called = []

        _self = self

        class wrapper:
            @wrapt.transient_function_wrapper(
                __name__,
                "TestTransientFunctionWrapper._test_transient_function_wrapper",
            )
            def __call__(self, wrapped, instance, args, kwargs):
                called.append((args, kwargs))
                _self.assertEqual(wrapped, _self._test_transient_function_wrapper)
                _self.assertEqual(instance, _self)
                _self.assertEqual(args, _args)
                _self.assertEqual(kwargs, _kwargs)
                return wrapped(*args, **kwargs)

        @wrapper()
        def function(*args, **kwargs):
            return self._test_transient_function_wrapper(*args, **kwargs)

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_module_function_restored_exactly(self):
        original = global_function

        @wrapt.transient_function_wrapper(__name__, "global_function")
        def apply_patch(wrapped, instance, args, kwargs):
            return ("patched", wrapped(*args, **kwargs))

        @apply_patch
        def invoke():
            return global_function()

        self.assertEqual(invoke(), ("patched", "original"))

        self.assertIs(global_function, original)
        self.assertEqual(global_function(), "original")

    def test_class_method_restored_exactly(self):
        class Target:
            def method(self):
                return "original"

        original = vars(Target)["method"]

        @wrapt.transient_function_wrapper(Target, "method")
        def apply_patch(wrapped, instance, args, kwargs):
            return ("patched", wrapped(*args, **kwargs))

        @apply_patch
        def invoke():
            return Target().method()

        self.assertEqual(invoke(), ("patched", "original"))

        self.assertIs(vars(Target)["method"], original)
        self.assertEqual(Target().method(), "original")

    def test_inherited_method_scope_and_no_shadow(self):
        class Base:
            def method(self):
                return "original"

        class Derived(Base):
            pass

        class Sibling(Base):
            pass

        @wrapt.transient_function_wrapper(Derived, "method")
        def apply_patch(wrapped, instance, args, kwargs):
            return ("patched", wrapped(*args, **kwargs))

        @apply_patch
        def invoke():
            # Patching via the subclass only affects the subclass. The
            # base class and other subclasses are not patched.

            return Derived().method(), Base().method(), Sibling().method()

        self.assertEqual(invoke(), (("patched", "original"), "original", "original"))

        # Restoration must not leave a shadowing copy of the inherited
        # method behind in the subclass dictionary.

        self.assertEqual(Derived().method(), "original")
        self.assertNotIn("method", vars(Derived))

        # A shadowing copy would cause later patching of the base class
        # to be silently invisible through the subclass.

        Base.method = lambda self: "repatched"
        self.assertEqual(Derived().method(), "repatched")

    def test_instance_target_scope_and_no_shadow(self):
        class Target:
            def method(self):
                return "original"

        target1 = Target()
        target2 = Target()

        @wrapt.transient_function_wrapper(target1, "method")
        def apply_patch(wrapped, instance, args, kwargs):
            return ("patched", wrapped(*args, **kwargs))

        @apply_patch
        def invoke():
            # Patching via an instance only affects that instance.

            return target1.method(), target2.method()

        self.assertEqual(invoke(), (("patched", "original"), "original"))

        # Restoration must not leave the bound method behind in the
        # instance dictionary shadowing the class attribute.

        self.assertEqual(target1.method(), "original")
        self.assertNotIn("method", vars(target1))

    def test_dynamic_module_attribute_no_shadow(self):
        module = types.ModuleType("xyz_transient_dynamic")

        def __getattr__(name):
            if name == "function":
                return global_function
            raise AttributeError(name)

        module.__getattr__ = __getattr__

        @wrapt.transient_function_wrapper(module, "function")
        def apply_patch(wrapped, instance, args, kwargs):
            return ("patched", wrapped(*args, **kwargs))

        @apply_patch
        def invoke():
            return module.function()

        self.assertEqual(invoke(), ("patched", "original"))

        # Restoration must not leave a static attribute behind which
        # would shadow the dynamic module level __getattr__ lookup.

        self.assertNotIn("function", vars(module))
        self.assertIs(module.function, global_function)

    def test_exception_restores_without_shadow(self):
        class Base:
            def method(self):
                return "original"

        class Derived(Base):
            pass

        @wrapt.transient_function_wrapper(Derived, "method")
        def apply_patch(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @apply_patch
        def invoke():
            raise RuntimeError("error")

        with self.assertRaises(RuntimeError):
            invoke()

        self.assertEqual(Derived().method(), "original")
        self.assertNotIn("method", vars(Derived))

    def test_nested_application(self):
        original = global_function

        labels = []

        @wrapt.transient_function_wrapper(__name__, "global_function")
        def apply_outer(wrapped, instance, args, kwargs):
            labels.append("outer")
            return wrapped(*args, **kwargs)

        @wrapt.transient_function_wrapper(__name__, "global_function")
        def apply_inner(wrapped, instance, args, kwargs):
            labels.append("inner")
            return wrapped(*args, **kwargs)

        @apply_outer
        @apply_inner
        def invoke():
            return global_function()

        self.assertEqual(invoke(), "original")

        # The innermost patch is applied last so sits on top and is
        # called first, with each level unwound in reverse order.

        self.assertEqual(labels, ["inner", "outer"])

        self.assertIs(global_function, original)


if __name__ == "__main__":
    unittest.main()


class TestTransientFunctionWrapperInterference(unittest.TestCase):

    # Restoration on exit is deliberately loud about interference from
    # code called within the scope of the patch, since leaked patch
    # state in a test harness surfaces as hard to diagnose failures in
    # later tests.

    def _make_module(self):
        module = types.ModuleType("transient_interference_target")
        module.function = lambda: "original"
        return module

    def test_removed_during_call_raises(self):
        module = self._make_module()

        @wrapt.transient_function_wrapper(module, "function")
        def patch(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @patch
        def run():
            module.function = lambda: "replaced"

        with self.assertRaises(wrapt.WrapperNotFoundError):
            run()

    def test_removed_during_call_with_exception_in_flight(self):
        # The restoration error supersedes an in-flight exception from
        # the wrapped call, which remains visible as the chained
        # __context__.

        module = self._make_module()

        @wrapt.transient_function_wrapper(module, "function")
        def patch(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @patch
        def run():
            module.function = lambda: "replaced"
            raise ZeroDivisionError("failure from the call itself")

        with self.assertRaises(wrapt.WrapperNotFoundError) as cm:
            run()

        self.assertIsInstance(cm.exception.__context__, ZeroDivisionError)

    def test_wrapt_wrapper_left_on_top_spliced(self):
        # A wrapt wrapper applied over the temporary wrapper and left in
        # place is tolerated: the temporary wrapper is spliced out from
        # beneath it, with the other wrapper left wrapping the original.

        module = self._make_module()
        original = module.function

        handles = []

        def their_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @wrapt.transient_function_wrapper(module, "function")
        def patch(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @patch
        def run():
            handles.append(
                wrapt.wrap_function_wrapper(module, "function", their_wrapper)
            )

        run()

        self.assertIs(module.function, handles[0])
        self.assertIs(module.function.__wrapped__, original)

    def test_non_wrapt_wrapper_left_on_top_raises(self):
        module = self._make_module()

        @wrapt.transient_function_wrapper(module, "function")
        def patch(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @patch
        def run():
            inner = module.function

            @functools.wraps(inner)
            def closure():
                return inner()

            module.function = closure

        with self.assertRaises(wrapt.WrapperNotOutermostError):
            run()
