from typing import Any, Generic, TypeVar, Callable, Optional

F = TypeVar('F', bound=Callable[..., Any])
A = TypeVar('A', bound=Callable[..., Any])
T = TypeVar("T", bound=Any)

def decorator(wrapper: F, enabled: Optional[bool] = None, adapter: Optional[A] = None) -> F: ...

class ObjectProxy(Generic[T]):
    __wrapped__ : T

    def __init__(self, wrapped: T):
        ...
