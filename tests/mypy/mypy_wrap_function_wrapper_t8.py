"""
This example demonstrates the incorrect usage of the wrap_function_wrapper()
function.
"""

from typing import Any, Callable

from wrapt import wrap_function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


def wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


# No string value for attribute path name. (FAIL)
wrapped_function = wrap_function_wrapper(__name__, None, wrapper)
