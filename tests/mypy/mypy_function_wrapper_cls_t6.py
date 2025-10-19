"""
This example demonstrates the incorrect usage of the FunctionWrapper type.

It covers the following cases:
- Wrapper as non callable object
- Wrapper as None object

Should fail mypy type checking for incorrect cases.
"""

from wrapt import FunctionWrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


wrapped_function = FunctionWrapper(function, "string")
wrapped_function = FunctionWrapper(function, None)
