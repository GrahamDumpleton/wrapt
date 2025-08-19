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

from typing import Any, Callable, ParamSpec, TypeVar

from wrapt import function_wrapper

P = ParamSpec("P")
R = TypeVar("R", covariant=True)


def function(x: int, y: int = 0) -> int:
    """A simple function to be wrapped."""
    return x + y


class ExampleClass1:
    """A class with methods to be wrapped."""

    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, x: int, y: int = 0) -> int:
        return x + y

    def instance_method(self, x: int, y: int = 0) -> int:
        return x + y

    @classmethod
    def class_method(cls, x: int, y: int = 0) -> int:
        return x + y

    @staticmethod
    def static_method(x: int, y: int = 0) -> int:
        return x + y


@function_wrapper
def wrapper(
    wrapped: Callable[P, R],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> R:
    return wrapped(*args, **kwargs)


wrapped_function = wrapper(function)

wrapped_method = wrapper(ExampleClass1.instance_method)
wrapped_classmethod = wrapper(ExampleClass1.class_method)
wrapped_staticmethod = wrapper(ExampleClass1.static_method)

wrapped_method_instance = wrapper(ExampleClass1(0).instance_method)
wrapped_classmethod_instance = wrapper(ExampleClass1(0).class_method)
wrapped_staticmethod_instance = wrapper(ExampleClass1(0).static_method)

wrapped_callable_class = wrapper(ExampleClass1)
wrapped_callable_object = wrapper(ExampleClass1(0))

wrapped_function(1)
wrapped_method(ExampleClass1(0), 3)
wrapped_classmethod(4)
wrapped_staticmethod(5)
wrapped_method_instance(6)
wrapped_classmethod_instance(7)
wrapped_staticmethod_instance(8)

wrapped_callable_class(9)
wrapped_callable_object(10)


@wrapper
class ExampleClass2:
    """A class with methods to be wrapped."""

    def __init__(self, value: int) -> None:
        self.value = value

    @wrapper
    def __call__(self, x: int, y: int = 0) -> int:
        return x + y

    @wrapper
    def instance_method(self, x: int, y: int = 0) -> int:
        return x + y

    @wrapper
    @classmethod
    def class_method(cls, x: int, y: int = 0) -> int:
        return x + y

    @wrapper
    @staticmethod
    def static_method(x: int, y: int = 0) -> int:
        return x + y


example_instance = ExampleClass2(0)

example_instance.instance_method(1)
example_instance.class_method(2)
example_instance.static_method(3)

example_instance(4)
