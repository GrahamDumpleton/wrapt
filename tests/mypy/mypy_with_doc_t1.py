"""
This example demonstrates the correct usage of with_doc() and of the doc
argument to with_signature(), along with a factory returning a tuple.
"""

import inspect
from typing import Callable

import wrapt


def prototype(user: str, count: int = 1) -> bool:
    raise NotImplementedError()


# Supplying the docstring directly
@wrapt.with_doc(doc="Look up a user.")
def function1(*args: object, **kwargs: object) -> bool:
    return True


# Deriving the docstring from the wrapped function, stacked above
# with_signature so the overridden signature is what the factory sees
def describe(wrapped: Callable[..., object]) -> str:
    return f"{wrapped.__name__}{inspect.signature(wrapped)}"


@wrapt.with_doc(factory=describe)
@wrapt.with_signature(prototype=prototype)
def function2(*args: object, **kwargs: object) -> bool:
    return True


# Overriding the signature and docstring together
@wrapt.with_signature(prototype=prototype, doc="Look up a user.")
def function3(*args: object, **kwargs: object) -> bool:
    return True


# A single factory deriving both the signature and the docstring
def derive(wrapped: Callable[..., object]) -> tuple[inspect.Signature, str]:
    return inspect.signature(prototype), f"Documentation for {wrapped.__name__}."


@wrapt.with_signature(factory=derive)
def function4(*args: object, **kwargs: object) -> bool:
    return True


# The wrappers are called as the wrapped function was
result1: bool = function1("user")
result2: bool = function2("user", 2)
result3: bool = function3("user", 2)
result4: bool = function4("user", 2)


# Supplying something other than a string as the docstring (FAIL)
@wrapt.with_doc(doc=42)
def function5() -> None: ...


# A factory returning something other than a string (FAIL)
def bad_factory(wrapped: Callable[..., object]) -> int:
    return 42


@wrapt.with_doc(factory=bad_factory)
def function6() -> None: ...


# A with_signature factory returning a tuple with a non-string docstring (FAIL)
def bad_derive(wrapped: Callable[..., object]) -> tuple[inspect.Signature, int]:
    return inspect.signature(prototype), 42


@wrapt.with_signature(factory=bad_derive)
def function7() -> None: ...


# Supplying no docstring at all (FAIL at runtime, but accepted by the stubs
# since the arguments default to None)
@wrapt.with_doc()
def function8() -> None: ...
