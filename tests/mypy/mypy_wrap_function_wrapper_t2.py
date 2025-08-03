"""
This example demonstrates the correct usage of the wrap_function_wrapper()
function.

It covers the following cases:
- Wrapping a function

Target for wrapping is this module, referenced by name.

These should all pass mypy type checking.
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


wrapped_function = wrap_function_wrapper(__name__, "function", wrapper)
