import sys
import unittest

import wrapt


@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


def passthru_wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


# --- Functions with various annotation styles ---


def function_param_annotations(a: int, b: str):
    pass


def function_return_annotation() -> list[int]:
    return []


def function_both_annotations(a: int, b: str) -> list[int]:
    return []


def function_no_annotations(a, b):
    pass


def function_complex_annotations(a: dict[str, list[int]]) -> tuple[str, int]:
    return ("", 0)


def function_default_with_annotations(a: int = 5, b: str = "hello") -> None:
    pass


def function_args_kwargs_annotations(*args: int, **kwargs: str) -> None:
    pass


def function_keyword_only_annotations(*, a: list[int], b: str) -> None:
    pass


class TestAnnotationPreservationFunctionWrapper(unittest.TestCase):
    """Test that annotations are preserved when wrapping with FunctionWrapper."""

    def test_param_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_param_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_param_annotations.__annotations__)
        self.assertEqual(wrapper.__annotations__, {"a": int, "b": str})

    def test_return_annotation(self):
        wrapper = wrapt.FunctionWrapper(function_return_annotation, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_return_annotation.__annotations__)
        self.assertEqual(wrapper.__annotations__, {"return": list[int]})

    def test_both_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_both_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_both_annotations.__annotations__)
        self.assertEqual(
            wrapper.__annotations__,
            {"a": int, "b": str, "return": list[int]},
        )

    def test_no_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_no_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, {})

    def test_complex_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_complex_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_complex_annotations.__annotations__)
        self.assertEqual(
            wrapper.__annotations__,
            {"a": dict[str, list[int]], "return": tuple[str, int]},
        )

    def test_default_with_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_default_with_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_default_with_annotations.__annotations__)

    def test_args_kwargs_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_args_kwargs_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_args_kwargs_annotations.__annotations__)
        self.assertEqual(
            wrapper.__annotations__,
            {"args": int, "kwargs": str, "return": None},
        )

    def test_keyword_only_annotations(self):
        wrapper = wrapt.FunctionWrapper(function_keyword_only_annotations, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, function_keyword_only_annotations.__annotations__)
        self.assertEqual(
            wrapper.__annotations__,
            {"a": list[int], "b": str, "return": None},
        )


class TestAnnotationPreservationDecorator(unittest.TestCase):
    """Test that annotations are preserved when wrapping with @decorator."""

    def test_param_annotations(self):
        @passthru_decorator
        def function(a: int, b: str):
            pass

        self.assertEqual(function.__annotations__, {"a": int, "b": str})

    def test_return_annotation(self):
        @passthru_decorator
        def function() -> list[int]:
            return []

        self.assertEqual(function.__annotations__, {"return": list[int]})

    def test_both_annotations(self):
        @passthru_decorator
        def function(a: int, b: str) -> list[int]:
            return []

        self.assertEqual(
            function.__annotations__,
            {"a": int, "b": str, "return": list[int]},
        )

    def test_no_annotations(self):
        @passthru_decorator
        def function(a, b):
            pass

        self.assertEqual(function.__annotations__, {})

    def test_complex_annotations(self):
        @passthru_decorator
        def function(a: dict[str, list[int]]) -> tuple[str, int]:
            return ("", 0)

        self.assertEqual(
            function.__annotations__,
            {"a": dict[str, list[int]], "return": tuple[str, int]},
        )

    def test_keyword_only_annotations(self):
        @passthru_decorator
        def function(*, a: list[int], b: str) -> None:
            pass

        self.assertEqual(
            function.__annotations__,
            {"a": list[int], "b": str, "return": None},
        )


class TestAnnotationPreservationObjectProxy(unittest.TestCase):
    """Test that annotations are preserved when wrapping with ObjectProxy."""

    def test_param_annotations(self):
        proxy = wrapt.ObjectProxy(function_param_annotations)
        self.assertEqual(proxy.__annotations__, function_param_annotations.__annotations__)
        self.assertEqual(proxy.__annotations__, {"a": int, "b": str})

    def test_return_annotation(self):
        proxy = wrapt.ObjectProxy(function_return_annotation)
        self.assertEqual(proxy.__annotations__, function_return_annotation.__annotations__)

    def test_no_annotations(self):
        proxy = wrapt.ObjectProxy(function_no_annotations)
        self.assertEqual(proxy.__annotations__, {})

    def test_complex_annotations(self):
        proxy = wrapt.ObjectProxy(function_complex_annotations)
        self.assertEqual(proxy.__annotations__, function_complex_annotations.__annotations__)


class TestAnnotationMutation(unittest.TestCase):
    """Test setting and deleting annotations on wrappers."""

    def test_set_annotations_on_wrapper_propagates(self):
        def function(a: int) -> str:
            return ""

        wrapper = wrapt.FunctionWrapper(function, passthru_wrapper)

        new_annotations = {"a": float, "return": bytes}
        wrapper.__annotations__ = new_annotations

        self.assertEqual(function.__annotations__, new_annotations)
        self.assertEqual(wrapper.__annotations__, new_annotations)

    def test_set_annotations_on_decorator_wrapped(self):
        @passthru_decorator
        def function(a: int) -> str:
            return ""

        new_annotations = {"a": float, "return": bytes}
        function.__annotations__ = new_annotations

        self.assertEqual(function.__wrapped__.__annotations__, new_annotations)
        self.assertEqual(function.__annotations__, new_annotations)

    def test_delete_annotations_on_wrapper(self):
        def function(a: int) -> str:
            return ""

        wrapper = wrapt.FunctionWrapper(function, passthru_wrapper)

        del wrapper.__annotations__

        # After deletion, accessing __annotations__ should return empty dict
        # as Python functions recreate __annotations__ when accessed.
        self.assertEqual(function.__annotations__, {})
        self.assertEqual(wrapper.__annotations__, {})

    def test_delete_annotations_on_decorator_wrapped(self):
        @passthru_decorator
        def function(a: int) -> str:
            return ""

        del function.__annotations__

        self.assertEqual(function.__annotations__, {})

    def test_set_annotations_on_object_proxy(self):
        proxy = wrapt.ObjectProxy(function_param_annotations)

        new_annotations = {"x": float}
        proxy.__annotations__ = new_annotations

        self.assertEqual(function_param_annotations.__annotations__, new_annotations)
        self.assertEqual(proxy.__annotations__, new_annotations)

        # Restore original annotations.
        function_param_annotations.__annotations__ = {"a": int, "b": str}


class TestAnnotationWrappedReassignment(unittest.TestCase):
    """Test that annotations update when __wrapped__ is changed."""

    def test_reassign_wrapped_updates_annotations(self):
        def function1(a: int) -> str:
            return ""

        def function2(x: float, y: float) -> bool:
            return True

        wrapper = wrapt.FunctionWrapper(function1, passthru_wrapper)

        self.assertEqual(
            wrapper.__annotations__,
            {"a": int, "return": str},
        )

        wrapper.__wrapped__ = function2

        self.assertEqual(
            wrapper.__annotations__,
            {"x": float, "y": float, "return": bool},
        )

    def test_reassign_wrapped_no_annotations_to_annotations(self):
        def function1(a, b):
            pass

        def function2(a: int) -> str:
            return ""

        wrapper = wrapt.FunctionWrapper(function1, passthru_wrapper)
        self.assertEqual(wrapper.__annotations__, {})

        wrapper.__wrapped__ = function2

        self.assertEqual(
            wrapper.__annotations__,
            {"a": int, "return": str},
        )

    def test_reassign_wrapped_annotations_to_no_annotations(self):
        def function1(a: int) -> str:
            return ""

        def function2(a, b):
            pass

        wrapper = wrapt.FunctionWrapper(function1, passthru_wrapper)

        self.assertEqual(
            wrapper.__annotations__,
            {"a": int, "return": str},
        )

        wrapper.__wrapped__ = function2

        self.assertEqual(wrapper.__annotations__, {})


class TestDeferredAnnotationEvaluation(unittest.TestCase):
    """Test deferred annotation evaluation (Python 3.14+ PEP 649/749).

    On Python 3.14+, annotations are evaluated lazily via __annotate__.
    Wrapping a function should not trigger eager evaluation which could
    fail if names referenced in annotations have been shadowed.
    """

    @unittest.skipIf(
        sys.version_info < (3, 14),
        "Deferred annotation evaluation requires Python 3.14+",
    )
    def test_shadowed_builtin_function_wrapper(self):
        """Wrapping a function after shadowing a builtin used in annotations
        should not raise TypeError."""

        def f(*, a: list[int]) -> list[int]:
            return a

        # Shadow the builtin 'list' with a non-subscriptable function.
        # On Python 3.14+, if annotations are eagerly evaluated at wrap
        # time, this would cause: TypeError: 'function' object is not
        # subscriptable.
        def list():  # noqa: F841
            return

        # This should not raise TypeError.
        wrapper = wrapt.FunctionWrapper(f, passthru_wrapper)

        # The wrapper should still be callable.
        result = wrapper(a=[1, 2, 3])
        self.assertEqual(result, [1, 2, 3])

    @unittest.skipIf(
        sys.version_info < (3, 14),
        "Deferred annotation evaluation requires Python 3.14+",
    )
    def test_shadowed_builtin_function_wrapper_decorator(self):
        """Same test using @wrapt.function_wrapper as in the bug report."""

        @wrapt.function_wrapper
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        def f(*, a: list[int]) -> list[int]:
            return a

        def list():  # noqa: F841
            return

        # This should not raise TypeError.
        f = passthrough(f)

        result = f(a=[1, 2, 3])
        self.assertEqual(result, [1, 2, 3])

    @unittest.skipIf(
        sys.version_info < (3, 14),
        "Deferred annotation evaluation requires Python 3.14+",
    )
    def test_shadowed_builtin_object_proxy(self):
        """ObjectProxy should also not trigger eager annotation evaluation."""

        def f(*, a: list[int]) -> list[int]:
            return a

        def list():  # noqa: F841
            return

        # This should not raise TypeError during construction.
        proxy = wrapt.ObjectProxy(f)

        self.assertEqual(proxy.__name__, "f")

    @unittest.skipIf(
        sys.version_info < (3, 14),
        "Deferred annotation evaluation requires Python 3.14+",
    )
    def test_annotate_preserved_on_wrapper(self):
        """Wrapper should preserve __annotate__ from the wrapped function."""

        def f(a: int, b: str) -> list[int]:
            return []

        self.assertTrue(hasattr(f, "__annotate__"))

        wrapper = wrapt.FunctionWrapper(f, passthru_wrapper)

        self.assertTrue(hasattr(wrapper, "__annotate__"))

    @unittest.skipIf(
        sys.version_info < (3, 14),
        "Deferred annotation evaluation requires Python 3.14+",
    )
    def test_annotate_preserved_on_object_proxy(self):
        """ObjectProxy should preserve __annotate__ from the wrapped object."""

        def f(a: int) -> str:
            return ""

        self.assertTrue(hasattr(f, "__annotate__"))

        proxy = wrapt.ObjectProxy(f)

        self.assertTrue(hasattr(proxy, "__annotate__"))

    @unittest.skipIf(
        sys.version_info < (3, 14),
        "Deferred annotation evaluation requires Python 3.14+",
    )
    def test_annotations_still_accessible_after_wrapping(self):
        """Even with deferred evaluation, annotations should be accessible
        on the wrapper when the names are still valid."""

        def f(a: int, b: str) -> list[int]:
            return []

        wrapper = wrapt.FunctionWrapper(f, passthru_wrapper)

        self.assertEqual(
            wrapper.__annotations__,
            {"a": int, "b": str, "return": list[int]},
        )
