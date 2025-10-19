"""
This example demonstrates the incorrect usage of the function_wrapper() function.

It covers the following cases:
- A wrapper function returning wrong type

Should fail mypy type checking for incorrect cases.
"""

from typing import Any, Callable

from wrapt import function_wrapper


@function_wrapper
def wrapper(
    wrapped: Callable[[int, int], int], instance: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> str:
    return "string"


wrapped_function = wrapper(function)
