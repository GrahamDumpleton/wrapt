import sys

if sys.version_info >= (3, 10):
    from typing import Callable, Any

    # FunctionWrapper

    WrappedFunction = Callable[..., Any]
    WrapperFunction = Callable[
        [WrappedFunction, Any, tuple[Any, ...], dict[str, Any]], Any
    ]

    class FunctionWrapper:
        def __init__(
            self,
            wrapped: WrappedFunction,
            wrapper: WrapperFunction,
        ) -> None: ...
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # function_wrapper()

    class FunctionDecorator:
        def __call__(self, callable: Callable[..., Any]) -> FunctionWrapper: ...

    def function_wrapper(wrapper: WrapperFunction) -> FunctionDecorator: ...
