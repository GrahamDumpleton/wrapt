"""
This example demonstrates the incorrect usage of the function_wrapper() function.

It covers the following cases:
- Wrapping a non callable object
- Wrapping a None object

Should fail mypy type checking for incorrect cases.
"""

from typing import Any, Callable

from wrapt import function_wrapper


@function_wrapper
def wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


wrapped_function = wrapper("string")
wrapped_function = wrapper(None)
