"""
This example demonstrates usage of the function_wrapper() function.

It demonstrates how mypy can not correctly infer the type of the wrapped
function when the function_wrapper() is used as a decorator. It also shows
however that by using a helper function that returns a function_wrapper()
decorator, mypy can correctly infer the type of the wrapped function.
"""

from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

from wrapt import function_wrapper


@function_wrapper
def wrapper1(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@wrapper1
def function1(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


function1()

function1(1, "test")
function1(2)
function1(3, y="override")

P = ParamSpec("P")
R = TypeVar("R", covariant=True)


def wrapper2(
    callable: Callable[Concatenate[Any, P], R],
) -> Callable[Concatenate[Any, P], R]:
    @function_wrapper
    def _wrapper(
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        return wrapped(*args, **kwargs)

    return _wrapper(callable)


@wrapper2
def function2(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


function2()


function2(1, "test")
function2(2)
function2(3, y="override")


class ExampleClass:
    """A class with methods to be wrapped."""

    def __init__(self, value: int) -> None:
        self.value = value

    @wrapper2
    def __call__(self, value: int) -> str:
        return f"callable: {value}"

    @wrapper2
    def instance_method(self, value: int) -> str:
        return f"instance: {value}"

    @wrapper2
    @classmethod
    def class_method(cls, value: int) -> str:
        return f"class: {value}"

    @wrapper2
    @staticmethod
    def static_method(value: int) -> str:
        return f"static: {value}"


example_instance1 = ExampleClass()
example_instance2 = ExampleClass(0)

example_instance2.instance_method(1)
example_instance2.class_method(1)
example_instance2.static_method(1)

example_instance2(1)


example_instance2.instance_method()
example_instance2.class_method()
example_instance2.static_method()

example_instance2()
