"""
This example demonstrates the correct usage of the function_wrapper() function.

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

These should all pass mypy type checking.
"""

from typing import Any, Callable

from wrapt import function_wrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


lambda_function: Callable[[int], int] = lambda x: x + 1


class ExampleClass1:
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


@function_wrapper
def wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


wrapped_function = wrapper(function)

wrapped_lambda = wrapper(lambda_function)

wrapped_method = wrapper(ExampleClass1.instance_method)
wrapped_classmethod = wrapper(ExampleClass1.class_method)
wrapped_staticmethod = wrapper(ExampleClass1.static_method)

wrapped_method_instance = wrapper(ExampleClass1().instance_method)
wrapped_classmethod_instance = wrapper(ExampleClass1().class_method)
wrapped_staticmethod_instance = wrapper(ExampleClass1().static_method)

wrapped_callable_class = wrapper(ExampleClass1)
wrapped_callable_object = wrapper(ExampleClass1())

wrapped_function(1)
wrapped_lambda(2)
wrapped_method(ExampleClass1(), 3)
wrapped_classmethod(4)
wrapped_staticmethod(5)
wrapped_method_instance(6)
wrapped_classmethod_instance(7)
wrapped_staticmethod_instance(8)


@wrapper
class ExampleClass2:
    """A class with methods to be wrapped."""

    def __init__(self, value: int) -> None:
        self.value = value

    @wrapper
    def __call__(self, value: int) -> str:
        return f"callable: {value}"

    @wrapper
    def instance_method(self, value: int) -> str:
        return f"instance: {value}"

    @wrapper
    @classmethod
    def class_method(cls, value: int) -> str:
        return f"class: {value}"

    @wrapper
    @staticmethod
    def static_method(value: int) -> str:
        return f"static: {value}"


example_instance = ExampleClass2(0)

example_instance.instance_method(1)
example_instance.class_method(2)
example_instance.static_method(3)

example_instance(4)
