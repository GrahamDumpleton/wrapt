"""
This example demonstrates the correct usage of the FunctionWrapper type.

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

from wrapt import FunctionWrapper


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


lambda_function: Callable[[int], int] = lambda x: x + 1


class ExampleClass:
    """A class with methods to be wrapped."""

    def __init__(self, value: int) -> None:
        self.value = value

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


def standard_wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    try:
        print(f"Before calling {wrapped.__name__}")
        return wrapped(*args, **kwargs)
    finally:
        print(f"After calling {wrapped.__name__}")


wrapped_function = FunctionWrapper(function, standard_wrapper)

wrapped_lambda = FunctionWrapper(lambda_function, standard_wrapper)

wrapped_method = FunctionWrapper(ExampleClass.instance_method, standard_wrapper)
wrapped_classmethod = FunctionWrapper(ExampleClass.class_method, standard_wrapper)
wrapped_staticmethod = FunctionWrapper(ExampleClass.static_method, standard_wrapper)

wrapped_method_instance = FunctionWrapper(
    ExampleClass(0).instance_method, standard_wrapper
)
wrapped_classmethod_instance = FunctionWrapper(
    ExampleClass(0).class_method, standard_wrapper
)
wrapped_staticmethod_instance = FunctionWrapper(
    ExampleClass(0).static_method, standard_wrapper
)

wrapped_callable_class = FunctionWrapper(ExampleClass, standard_wrapper)
wrapped_callable_object = FunctionWrapper(ExampleClass(0), standard_wrapper)

wrapped_function(1)
wrapped_lambda(2)
wrapped_method(ExampleClass(0), 3)
wrapped_classmethod(4)
wrapped_staticmethod(5)
wrapped_method_instance(6)
wrapped_classmethod_instance(7)
wrapped_staticmethod_instance(8)

wrapped_callable_class(9)
wrapped_callable_object(10)
