from typing import Callable, TypeVar, Any, Tuple, Dict, Union

WrappedFunction = TypeVar("WrappedFunction", bound=Callable)

# Standard signature for wrappers
StandardWrapper = Callable[[WrappedFunction, Any, Tuple[Any, ...], Dict[str, Any]], Any]

# Catch-all wrapper signature
CatchAllWrapper = Callable[..., Any]

# Union type to accept either wrapper style
WrapperFunction = Union[StandardWrapper, CatchAllWrapper]

def FunctionWrapper(
    wrapped: WrappedFunction, wrapper: WrapperFunction
) -> WrappedFunction: ...
