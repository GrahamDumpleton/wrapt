"""
This example demonstrates the incorrect usage of the FunctionWrapper type.

It covers the following cases:
- Wrapping a non callable object
- Wrapping a None object

Should fail mypy type checking for incorrect cases.
"""

from typing import Any, Callable, Dict, Tuple

from wrapt import FunctionWrapper


def standard_wrapper(
    wrapped: Callable[[Any], Any],
    instance: Any,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


wrapped_function = FunctionWrapper("string", standard_wrapper)
wrapped_function = FunctionWrapper(None, standard_wrapper)
