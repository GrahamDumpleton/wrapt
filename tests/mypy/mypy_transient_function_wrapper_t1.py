"""
This example demonstrates the usage of the transient_wrapper_function() function.

It covers the following cases:
- Patch function of module directly. (OKAY)
- Patch function of module by module __name__. (OKAY)
- Incorrect type for attribute path. (FAIL)
- Incorrect prototype for wrapper function. (FAIL)
"""

import sys
from typing import Any, Callable
from wrapt import transient_function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


this_module = sys.modules[__name__]


@transient_function_wrapper(this_module, "function")
def patch_module_direct(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@patch_module_direct
def patch_module_direct_fn(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


@transient_function_wrapper(__name__, "function")
def patch_module_by_name(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@patch_module_by_name
def patch_module_by_name_fn(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


@transient_function_wrapper(this_module, None)
def incorrect_type_for_attribute_path(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@transient_function_wrapper(this_module, "function")
def incorrect_prototype_for_wrapper(
    wrapped: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> Any:
    return wrapped(*args, **kwargs)
