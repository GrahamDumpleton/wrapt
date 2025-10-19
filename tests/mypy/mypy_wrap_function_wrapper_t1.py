"""
This example demonstrates the correct usage of the wrap_function_wrapper()
function.

It covers the following cases:
- Wrapping a function
- Wrapping a lambda function
- Wrapping a method of a class
- Wrapping a class method
- Wrapping a static method
- Wrapping an instance method of a class
- Wrapping a class method of an instance
- Wrapping a static method of an instance
- Wrapping a callable class
- Wrapping a callable class instance

Target for wrapping is this module.

These should all pass mypy type checking.
"""

import sys
from typing import Any, Callable

from wrapt import wrap_function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


lambda_function: Callable[[int], int] = lambda x: x + 1


class ExampleClass:
    """A class with methods to be wrapped."""

    def __call__(self, value: int) -> str:
        return f"callable: {value}"

    def instance_method(self, value: int) -> str:
        return f"instance: {value}"

    @classmethod
    def class_method(cls, value: int) -> str:
        return f"class: {value}"

    @staticmethod
    def static_method(value: int) -> str:
        return f"static: {value}"


def wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


example_class = ExampleClass()

this_module = sys.modules[__name__]

wrapped_function = wrap_function_wrapper(this_module, "function", wrapper)

wrapped_lambda = wrap_function_wrapper(this_module, "lambda_function", wrapper)

wrapped_method = wrap_function_wrapper(
    this_module, "ExampleClass.instance_method", wrapper
)
wrapped_classmethod = wrap_function_wrapper(
    this_module, "ExampleClass.class_method", wrapper
)
wrapped_staticmethod = wrap_function_wrapper(
    this_module, "ExampleClass.static_method", wrapper
)

wrapped_method_instance = wrap_function_wrapper(
    this_module, "example_class.instance_method", wrapper
)
wrapped_classmethod_instance = wrap_function_wrapper(
    this_module, "example_class.class_method", wrapper
)
wrapped_staticmethod_instance = wrap_function_wrapper(
    this_module, "example_class.static_method", wrapper
)

wrapped_callable_class = wrap_function_wrapper(this_module, "ExampleClass", wrapper)
wrapped_callable_object = wrap_function_wrapper(this_module, "example_class", wrapper)
