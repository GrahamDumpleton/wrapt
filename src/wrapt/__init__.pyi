from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)

def FunctionWrapper(wrapped: F, wrapper: Callable) -> F: ...
