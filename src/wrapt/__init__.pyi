from typing import Callable, TypeVar, Any, Tuple, Dict

try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # Backport for older Python versions

from typing import Callable, TypeVar, Any, Tuple, Dict, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

WrappedFunction = Callable[P, R]
WrapperFunction = Callable[[WrappedFunction, Any, Tuple[Any, ...], Dict[str, Any]], Any]

class FunctionWrapper:
    def __init__(
        self,
        wrapped: WrappedFunction,
        wrapper: WrapperFunction,
    ) -> None: ...
