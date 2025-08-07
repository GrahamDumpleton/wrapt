"""
This example demonstrates the usage of the patch_wrapper_function() function.
"""

import sys
from typing import Any, Callable

from wrapt import patch_function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


this_module = sys.modules[__name__]


@patch_function_wrapper(this_module, "function")
def patch_module_direct(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@patch_function_wrapper(this_module, "function")
def patch_module_using_name(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


# Incorrect type for attribute path. (FAIL)
@patch_function_wrapper(this_module, None)
def incorrect_type_for_attribute_path(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


# Incorrect prototype for wrapper function. (FAIL)
@patch_function_wrapper(this_module, "function")
def incorrect_prototype_for_wrapper(
    wrapped: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> Any:
    return wrapped(*args, **kwargs)


@patch_function_wrapper(this_module, "function", enabled=True)
def boolean_for_enabled_argument(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@patch_function_wrapper(this_module, "function", enabled=lambda: True)
def callable_for_enabled_argument(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@patch_function_wrapper(this_module, "function", enabled=None)
def none_for_enabled_argument(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


# Incorrect type for enabled argument. (FAIL)
@patch_function_wrapper(this_module, "function", enabled="string")
def incorrect_type_for_enabled_argument(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)
