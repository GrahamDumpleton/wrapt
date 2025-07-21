import sys
from typing import Any, Callable, TypeVar

R = TypeVar("R")

if sys.version_info >= (3, 10):
    from typing import ParamSpec

    P = ParamSpec("P")

    def FunctionWrapper(wrapped: Callable[P, R], wrapper: Callable) -> Callable[P, R]: ...
else:
    def FunctionWrapper(wrapped: Callable[..., R], wrapper: Callable) -> Callable[..., R]: ...
