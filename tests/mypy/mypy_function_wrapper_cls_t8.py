"""
This example demonstrates the usage of the FunctionWrapper type.

It covers the following cases:
- Default to enabled. (OKAY)
- Passing None to enabled. (OKAY)
- Passing bool to enabled. (OKAY)
- Passing a callable to enabled. (OKAY)
- Passing incorrect types to enabled. (FAIL)
"""

from typing import Any, Callable
from wrapt import FunctionWrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


def standard_wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    try:
        print(f"Before calling {wrapped.__name__}")
        return wrapped(*args, **kwargs)
    finally:
        print(f"After calling {wrapped.__name__}")


enabled_default = FunctionWrapper(function, standard_wrapper)
enabled_none = FunctionWrapper(function, standard_wrapper, None)
enabled_true = FunctionWrapper(function, standard_wrapper, True)
enabled_false = FunctionWrapper(function, standard_wrapper, False)
enabled_callable = FunctionWrapper(function, standard_wrapper, lambda: True)

enabled_string = FunctionWrapper(function, standard_wrapper, "string")
