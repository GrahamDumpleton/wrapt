"""
This example demonstrates the correct usage of the wrap_function_wrapper()
function.

It covers the following cases:
- Wrapping an instance method of a class

Target for wrapping is the instance of a class.

These should all pass mypy type checking.
"""

from typing import Any, Callable

from wrapt import wrap_function_wrapper


class ExampleClass:
    """A class with methods to be wrapped."""

    def instance_method(self, value: int) -> str:
        return f"instance: {value}"


def wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


example_class = ExampleClass()

wrapped_method = wrap_function_wrapper(example_class, "instance_method", wrapper)
