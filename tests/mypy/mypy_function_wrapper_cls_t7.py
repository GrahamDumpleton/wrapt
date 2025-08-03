"""
This example demonstrates the incorrect usage of the FunctionWrapper type.

It covers the following cases:
- A wrapper function returning wrong type

Should fail mypy type checking for incorrect cases.
"""

from typing import Any

from wrapt import FunctionWrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


def standard_wrapper(
    wrapped: str, instance: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> str:
    return "string"


wrapped_function = FunctionWrapper(function, standard_wrapper)
