"""
This example demonstrates the incorrect usage of the function_wrapper() function.

It covers the following cases:
- A wrapper function with incorrect number of arguments

Should fail mypy type checking for incorrect cases.
"""

from typing import Any

from wrapt import function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


@function_wrapper
def wrapper(wrapped: Any) -> Any:
    return


wrapped_function = wrapper(function)
