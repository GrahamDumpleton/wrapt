"""
This example demonstrates the incorrect usage of the wrap_function_wrapper()
function.

It covers the following cases:
- A wrapper function with incorrect number of arguments

Target for wrapping is this module, referenced by name.

Should fail mypy type checking for incorrect cases.
"""

from typing import Any, Callable

from wrapt import wrap_function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


def wrapper(wrapped: Any) -> Any:
    return


wrapped_function = wrap_function_wrapper(__name__, "function", wrapper)
