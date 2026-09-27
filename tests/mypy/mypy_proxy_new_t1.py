"""
Type-check coverage for derived proxies which override __new__() and pass
their arguments through to the base class, and which add arguments to
__init__(). The stubs declare __new__() on BaseObjectProxy, AutoObjectProxy
and LazyObjectProxy as accepting extra arguments and returning Self, to
match the runtime, so both patterns type check.
"""

from typing import Any, Callable

import wrapt


class LabelledProxy(wrapt.BaseObjectProxy[int]):
    def __new__(cls, wrapped: int, label: str) -> "LabelledProxy":
        return super().__new__(cls, wrapped, label)

    def __init__(self, wrapped: int, label: str) -> None:
        super().__init__(wrapped)
        self._self_label = label


labelled: LabelledProxy = LabelledProxy(1, "one")
labelled_value: int = labelled.__wrapped__


class ExtraInitProxy(wrapt.BaseObjectProxy[int]):
    def __init__(self, wrapped: int, label: str) -> None:
        super().__init__(wrapped)
        self._self_label = label


extra: ExtraInitProxy = ExtraInitProxy(1, "one")


class LabelledAutoProxy(wrapt.AutoObjectProxy[Any]):
    def __new__(cls, wrapped: Any, label: str) -> "LabelledAutoProxy":
        return super().__new__(cls, wrapped, label)

    def __init__(self, wrapped: Any, label: str) -> None:
        super().__init__(wrapped)
        self._self_label = label


auto: LabelledAutoProxy = LabelledAutoProxy([1, 2, 3], "list")


class LabelledLazyProxy(wrapt.LazyObjectProxy[Any]):
    def __init__(
        self, callback: Callable[[], Any], label: str, *, interface: Any = ...
    ) -> None:
        super().__init__(callback, interface=interface)
        self._self_label = label


lazy: LabelledLazyProxy = LabelledLazyProxy(lambda: [1, 2, 3], "list", interface=list)

# Construction of the base classes themselves still infers the wrapped type
# from __init__ rather than from the permissive __new__.

base: wrapt.BaseObjectProxy[int] = wrapt.BaseObjectProxy(1)
compat: wrapt.ObjectProxy[int] = wrapt.ObjectProxy(1)
auto_base: wrapt.AutoObjectProxy[list[int]] = wrapt.AutoObjectProxy([1, 2, 3])
