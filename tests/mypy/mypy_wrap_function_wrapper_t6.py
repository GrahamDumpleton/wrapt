"""
This example demonstrates the incorrect usage of the wrap_function_wrapper()
function.
"""

from typing import Any, Callable

from wrapt import wrap_function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


def wrapper(wrapped: Any) -> Any:
    return


# A wrapper function with incorrect number of arguments. (FAIL)
wrapped_function = wrap_function_wrapper(__name__, "function", wrapper)
