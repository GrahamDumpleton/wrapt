"""
This example demonstrates usage of the decorator() function.
"""

from typing import Any, Callable, ParamSpec, TypeVar

import wrapt

P = ParamSpec("P")
R = TypeVar("R")


@wrapt.decorator
def wrapper1(
    wrapped: Callable[[int], int],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> int:
    return wrapped(*args, **kwargs)

@wrapper1
def function1(x: int) -> int:
    """A function that takes an integer and returns it."""
    return x


result1a: int = function1(1)

# Mismatch return type. (FAIL)
result1b: str = function1(1)

# No arguments provided. (FAIL)
function1()

function1(1)

# Provide incorrect argument type. (FAIL)
function1("x")

# Wrong number of arguments provided. (FAIL)
function1(1, 2)


@wrapt.decorator(enabled=True)
def wrapper2(
    wrapped: Callable[[int], int],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> int:
    return wrapped(*args, **kwargs)


@wrapper2
def function2(x: int) -> int:
    """A function that takes an integer and returns it."""
    return x


# No arguments provided. (FAIL)
function2()

function2(1)

# Provide incorrect argument type. (FAIL)
function2("x")

# Wrong number of arguments provided. (FAIL)
function2(1, 2)


def adapter1(i: int) -> str:
    return str(i)


def wrapper3(wrapped: Callable[[int], int]) -> Callable[[int], str]:
    @wrapt.decorator(adapter=adapter1)
    def _wrapper3(
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        return adapter1(wrapped(*args, **kwargs))

    return _wrapper3(wrapped)


@wrapper3
def function3(x: int) -> int:
    """A function that takes an integer and returns it."""
    return x


result3a: str = function3(1)

# Mismatch return type. (FAIL)
result3b: int = function3(1)

# No arguments provided. (FAIL)
function3()

function3(1)

# Provide incorrect argument type. (FAIL)
function3("x")

# Wrong number of arguments provided. (FAIL)
function3(1, 2)


@wrapt.decorator(adapter=adapter1)
def wrapper4(
    wrapped: Callable[[int], int],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    return adapter1(wrapped(*args, **kwargs))


@wrapper4
def function4(x: int) -> int:
    """A function that takes an integer and returns it."""
    return x


result4a: str = function4(1)

# Allowed since return Any.
result4b: int = function4(1)

# No arguments provided. (FAIL)
function4()

function4(1)

# Provide incorrect argument type. (FAIL)
function4("x")

# Wrong number of arguments provided. (FAIL)
function4(1, 2)


def adapter2(a: int, b: int) -> str:
    return str(a + b)


def wrapper5(wrapped: Callable[[int], int]) -> Callable[[int, int], str]:
    @wrapt.decorator(adapter=adapter2)
    def _wrapper5(
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        def bind(a: int, b: int) -> tuple[int, int]:
            return a, b

        a, b = bind(*args, **kwargs)

        return str(wrapped(a + b))

    return _wrapper5(wrapped)


@wrapper5
def function5(x: int) -> int:
    """A function that takes an integer and returns it."""
    return x


result5: str = function5(1, 2)


class Example:
    @wrapt.decorator
    def pass_through_im(
        self: Any,
        wrapped: Callable[P, R],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> R:
        return wrapped(*args, **kwargs)

    @wrapt.decorator
    @classmethod
    def pass_through_cm(
        cls: Any,
        wrapped: Callable[P, R],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> R:
        return wrapped(*args, **kwargs)

    @wrapt.decorator
    @staticmethod
    def pass_through_sm(
        wrapped: Callable[P, R],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> R:
        return wrapped(*args, **kwargs)


example_instance = Example()


@example_instance.pass_through_im
def function6(a: int, b: int = 0) -> int:
    return a + b


result6: int = function6(1, 2)

function6(1)
function6(1, b=2)


@example_instance.pass_through_cm
def function7(a: int, b: int = 0) -> int:
    return a + b


result7: int = function7(1, 2)

function7(1)
function7(1, b=2)


@example_instance.pass_through_sm
def function8(a: int, b: int = 0) -> int:
    return a + b


result8: int = function8(1, 2)

function8(1)
function8(1, b=2)
