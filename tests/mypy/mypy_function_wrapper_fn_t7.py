"""
This example demonstrates usage of the function_wrapper() function.
"""

from typing import Any, Callable

from wrapt import function_wrapper


@function_wrapper
def wrapper1(
    wrapped: Callable[[int, str], str],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    return wrapped(*args, **kwargs)


@wrapper1
def function1(x: int, y: str = "string") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


# No arguments. (FAIL)
function1()

function1(1, "test")

# Doesn't handle default arguments. (MYPY LIMITATION)
function1(2)

# Doesn't handle keyword arguments. (MYPY LIMITATION)
function1(3, y="override")


class ExampleClass1:
    """A class with methods to be wrapped."""

    def __init__(
        self,
        value: int,
    ) -> None:
        self.value = value

    @wrapper1
    def __call__(self, value: int, name: str) -> str:
        return f"callable: {value}"

    @wrapper1
    def instance_method(self, value: int, name: str) -> str:
        return f"instance: {value}"

    @wrapper1
    @classmethod
    def class_method(cls, value: int, name: str) -> str:
        return f"class: {value}"

    @wrapper1
    @staticmethod
    def static_method(value: int, name: str) -> str:
        return f"static: {value}"


example_instance1 = ExampleClass1(0)

# No arguments. (FAIL)
example_instance1.instance_method()

# No arguments. (FAIL)
example_instance1.class_method()

# No arguments. (FAIL)
example_instance1.static_method()

example_instance1.instance_method(1, "test")
example_instance1.class_method(1, "test")
example_instance1.static_method(1, "test")

example_instance1(1, "test")

# No arguments. (FAIL)
ExampleClass1.class_method()

# No arguments. (FAIL)
ExampleClass1.static_method()

ExampleClass1.class_method(1, "test")
ExampleClass1.static_method(1, "test")


@function_wrapper
def wrapper2(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return wrapped(*args, **kwargs)


@wrapper2
def function2(x: int, y: str | None = None) -> str:
    """A simple function to be wrapped."""
    if y is None:
        y = "default"
    return f"{x}: {y}"


function2()


function2(1, "test")
function2(2)
function2(3, y="override")


class ExampleClass2:
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


example_instance2 = ExampleClass2(0)

example_instance2.instance_method(1)
example_instance2.class_method(1)
example_instance2.static_method(1)

example_instance2(1)


example_instance2.instance_method()
example_instance2.class_method()
example_instance2.static_method()

example_instance2()


class DecoratorClass:
    @function_wrapper
    def wrapper(
        self,
        wrapped: Callable[[int, str], str],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        return wrapped(*args, **kwargs)


decorator_class = DecoratorClass()


@decorator_class.wrapper
def function3(x: int, y: str | None = None) -> str:
    """A simple function to be wrapped."""
    if y is None:
        y = "default"
    return f"{x}: {y}"


# No arguments. (FAIL)
function3()

function3(1, "test")

# Doesn't handle default arguments. (MYPY LIMITATION)
function3(2)

# Doesn't handle keyword arguments. (MYPY LIMITATION)
function3(3, y="override")
