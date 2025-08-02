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

A catch all wrapper is a function that accepts any arguments.

These should all pass mypy type checking.
"""

from typing import Any, Callable, Dict, Tuple
from wrapt import FunctionWrapper


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


def catch_all_wrapper(*args: Any, **kwargs: Any) -> Any:
    def _bind(
        wrapped: Callable[[Any], Any], instance: Any, *args: Any, **kwargs: Any
    ) -> Tuple[Callable[[Any], Any], Any, Tuple[Any, ...], Dict[str, Any]]:
        return wrapped, instance, args, kwargs

    _wrapped, _instance, _args, _kwargs = _bind(*args, **kwargs)

    try:
        print(f"Before calling {_wrapped.__name__}")
        return _wrapped(*_args, **_kwargs)
    finally:
        print(f"After calling {_wrapped.__name__}")


wrapped_function = FunctionWrapper(function, catch_all_wrapper)

wrapped_lambda = FunctionWrapper(lambda_function, catch_all_wrapper)

wrapped_method = FunctionWrapper(ExampleClass.instance_method, catch_all_wrapper)
wrapped_classmethod = FunctionWrapper(ExampleClass.class_method, catch_all_wrapper)
wrapped_staticmethod = FunctionWrapper(ExampleClass.static_method, catch_all_wrapper)

wrapped_method_instance = FunctionWrapper(
    ExampleClass().instance_method, catch_all_wrapper
)
wrapped_classmethod_instance = FunctionWrapper(
    ExampleClass().class_method, catch_all_wrapper
)
wrapped_staticmethod_instance = FunctionWrapper(
    ExampleClass().static_method, catch_all_wrapper
)

wrapped_callable_class = FunctionWrapper(ExampleClass, catch_all_wrapper)
wrapped_callable_object = FunctionWrapper(ExampleClass(), catch_all_wrapper)
