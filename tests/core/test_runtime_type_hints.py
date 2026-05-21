"""Runtime behaviour of the generic type hints declared in the wrapt
stubs (src/wrapt-stubs/__init__.pyi).

The stubs declare ``BaseObjectProxy``, ``ObjectProxy``, ``AutoObjectProxy``,
``LazyObjectProxy``, ``CallableObjectProxy``, ``FunctionWrapper`` and
``BoundFunctionWrapper`` as generic, so users can write annotations like
``proxy: BaseObjectProxy[int] = BaseObjectProxy(5)``. The mypy tests under
``tests/mypy`` only cover static type checking; these tests exercise the
same patterns at runtime to ensure ``cls[T]`` subscripting, subclassing
with a subscripted base and ``typing.get_type_hints()`` resolution all
succeed.
"""

from __future__ import annotations

import unittest
from typing import Any, get_type_hints

from wrapt import (
    AutoObjectProxy,
    BaseObjectProxy,
    BoundFunctionWrapper,
    CallableObjectProxy,
    FunctionWrapper,
    LazyObjectProxy,
    ObjectProxy,
)


def _passthrough(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


def _target(x: int) -> int:
    return x + 1


class TestDirectSubscripting(unittest.TestCase):
    """Subscripting the class directly (e.g. ``BaseObjectProxy[int]``)
    must not raise. This is the most direct exercise of
    ``__class_getitem__``.
    """

    def test_base_object_proxy(self):
        _ = BaseObjectProxy[int]

    def test_object_proxy(self):
        _ = ObjectProxy[int]

    def test_auto_object_proxy(self):
        _ = AutoObjectProxy[int]

    def test_lazy_object_proxy(self):
        _ = LazyObjectProxy[int]

    def test_callable_object_proxy(self):
        _ = CallableObjectProxy[Any]

    def test_function_wrapper(self):
        _ = FunctionWrapper[Any, int]

    def test_bound_function_wrapper(self):
        _ = BoundFunctionWrapper[Any, int]


class TestAnnotatedAssignment(unittest.TestCase):
    """Variable annotations that reference a subscripted proxy class must
    round-trip through ``typing.get_type_hints`` without raising. This
    covers the user-visible pattern ``proxy: ObjectProxy[int] = ...``,
    which on Python < 3.14 evaluates the annotation eagerly and on
    Python >= 3.14 evaluates it lazily (e.g. via ``get_type_hints``).
    """

    def test_base_object_proxy(self):
        def f(p: BaseObjectProxy[int]) -> BaseObjectProxy[int]:
            return p

        get_type_hints(f)

    def test_object_proxy(self):
        def f(p: ObjectProxy[int]) -> ObjectProxy[int]:
            return p

        get_type_hints(f)

    def test_auto_object_proxy(self):
        def f(p: AutoObjectProxy[int]) -> AutoObjectProxy[int]:
            return p

        get_type_hints(f)

    def test_lazy_object_proxy(self):
        def f(p: LazyObjectProxy[int]) -> LazyObjectProxy[int]:
            return p

        get_type_hints(f)

    def test_callable_object_proxy(self):
        def f(p: CallableObjectProxy[Any]) -> CallableObjectProxy[Any]:
            return p

        get_type_hints(f)

    def test_function_wrapper(self):
        def f(p: FunctionWrapper[Any, int]) -> FunctionWrapper[Any, int]:
            return p

        get_type_hints(f)

    def test_bound_function_wrapper(self):
        def f(
            p: BoundFunctionWrapper[Any, int],
        ) -> BoundFunctionWrapper[Any, int]:
            return p

        get_type_hints(f)


class TestSubclassWithSubscriptedBase(unittest.TestCase):
    """Subclassing with a subscripted generic base (e.g.
    ``class MyProxy(ObjectProxy[int]): ...``) must not raise. This is the
    pattern used by libraries such as smart_open to specialise a proxy
    for a concrete wrapped type.
    """

    def test_base_object_proxy(self):
        class Sub(BaseObjectProxy[int]):
            pass

        self.assertEqual(Sub(5), 5)

    def test_object_proxy(self):
        class Sub(ObjectProxy[int]):
            pass

        self.assertEqual(Sub(5), 5)

    def test_auto_object_proxy(self):
        class Sub(AutoObjectProxy[list[int]]):
            pass

        self.assertEqual(len(Sub([1, 2, 3])), 3)

    def test_lazy_object_proxy(self):
        class Sub(LazyObjectProxy[int]):
            pass

        self.assertEqual(Sub(lambda: 5), 5)

    def test_callable_object_proxy(self):
        class Sub(CallableObjectProxy[Any]):
            pass

        self.assertEqual(Sub(len)([1, 2, 3]), 3)

    def test_function_wrapper(self):
        class Sub(FunctionWrapper[Any, int]):
            pass

        wrapped = Sub(_target, _passthrough)
        self.assertEqual(wrapped(1), 2)


class TestConstructionAfterSubscripting(unittest.TestCase):
    """Sanity check that once subscripting is supported, construction via
    the generic alias still produces a working proxy. ``Cls[T](...)``
    should be equivalent to ``Cls(...)`` at runtime.
    """

    def test_base_object_proxy_instance(self):
        proxy = BaseObjectProxy[int](5)
        self.assertEqual(proxy, 5)
        self.assertIsInstance(proxy, BaseObjectProxy)

    def test_object_proxy_instance(self):
        proxy = ObjectProxy[int](5)
        self.assertEqual(proxy, 5)
        self.assertIsInstance(proxy, ObjectProxy)

    def test_function_wrapper_instance(self):
        fw = FunctionWrapper[Any, int](_target, _passthrough)
        self.assertEqual(fw(1), 2)
        self.assertIsInstance(fw, FunctionWrapper)


if __name__ == "__main__":
    unittest.main()
