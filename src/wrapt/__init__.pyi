import sys

if sys.version_info >= (3, 10):
    from types import ModuleType, TracebackType
    from typing import Any, Callable, Generic, ParamSpec, TypeVar, overload

    # ObjectProxy

    T = TypeVar("T", bound=Any)

    class ObjectProxy(Generic[T]):
        __wrapped__: T

    class CallableObjectProxy(ObjectProxy[T]):
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # PartialCallableObjectProxy

    class PartialCallableObjectProxy:
        def __init__(
            self, func: Callable[..., Any], *args: Any, **kwargs: Any
        ) -> None: ...
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    def partial(
        func: Callable[..., Any], /, *args: Any, **kwargs: Any
    ) -> Callable[..., Any]: ...

    # WeakFunctionProxy

    class WeakFunctionProxy:
        def __init__(
            self,
            wrapped: Callable[..., Any],
            callback: Callable[..., Any] | None = None,
        ) -> None: ...
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # FunctionWrapper

    P1 = ParamSpec("P1")
    R1 = TypeVar("R1", covariant=True)

    WrappedFunction = Callable[P1, R1]
    WrapperFunction = Callable[
        [WrappedFunction[P1, R1], Any, tuple[Any, ...], dict[str, Any]], Any
    ]

    class BoundFunctionWrapper(Generic[P1, R1]):
        def __call__(self, *args: P1.args, **kwargs: P1.kwargs) -> R1: ...
        def __get__(
            self, instance: Any, owner: type[Any] | None = None
        ) -> "BoundFunctionWrapper[P1, R1]": ...

    class FunctionWrapper(Generic[P1, R1]):
        __wrapped__: WrappedFunction[P1, R1]
        def __init__(
            self,
            wrapped: WrappedFunction[P1, R1],
            wrapper: WrapperFunction[P1, R1],
            enabled: bool | Callable[[], bool] | None = None,
        ) -> None: ...
        def __call__(self, *args: P1.args, **kwargs: P1.kwargs) -> R1: ...
        def __get__(
            self, instance: Any, owner: type[Any] | None = None
        ) -> BoundFunctionWrapper[P1, R1]: ...

    # function_wrapper()

    class FunctionDecorator(Generic[P1, R1]):
        def __call__(self, callable: Callable[P1, R1]) -> FunctionWrapper[P1, R1]: ...

    def function_wrapper(
        wrapper: WrapperFunction[P1, R1],
    ) -> FunctionDecorator[P1, R1]: ...

    # wrap_function_wrapper()

    def wrap_function_wrapper(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        wrapper: WrapperFunction[P1, R1],
    ) -> FunctionWrapper[P1, R1]: ...

    # patch_function_wrapper()

    class WrapperDecorator:
        def __call__(
            self, wrapper: WrapperFunction[P1, R1]
        ) -> FunctionWrapper[P1, R1]: ...

    def patch_function_wrapper(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        enabled: bool | Callable[[], bool] | None = None,
    ) -> WrapperDecorator: ...

    # transient_function_wrapper()

    class TransientDecorator:
        def __call__(
            self, wrapper: WrapperFunction[P1, R1]
        ) -> FunctionDecorator[P1, R1]: ...

    def transient_function_wrapper(
        target: ModuleType | type[Any] | Any | str, name: str
    ) -> TransientDecorator: ...

    # resolve_path()

    def resolve_path(
        target: ModuleType | type[Any] | Any | str, name: str
    ) -> tuple[ModuleType | type[Any] | Any, str, Callable[..., Any]]: ...

    # apply_patch()

    def apply_patch(
        parent: ModuleType | type[Any] | Any,
        attribute: str,
        replacement: Any,
    ) -> None: ...

    # wrap_object()

    WrapperFactory = Callable[
        [Callable[..., Any], tuple[Any, ...], dict[str, Any]], Any
    ]

    def wrap_object(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        factory: WrapperFactory,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any: ...

    # register_post_import_hook()

    def register_post_import_hook(
        hook: Callable[[ModuleType], Any] | str, name: str
    ) -> None: ...

    # discover_post_import_hooks()

    def discover_post_import_hooks(group: str) -> None: ...

    # notify_module_loaded()

    def notify_module_loaded(module: ModuleType) -> None: ...

    # when_imported()

    class ImportHookDecorator:
        def __call__(self, hook: Callable[[ModuleType], Any]) -> Callable[..., Any]: ...

    def when_imported(name: str) -> ImportHookDecorator: ...

    # synchronized()

    class SynchronizedObject:
        def __call__(self, wrapped: Callable[P1, R1]) -> Callable[P1, R1]: ...
        def __enter__(self) -> Any: ...
        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None: ...

    @overload
    def synchronized(wrapped: Callable[P1, R1]) -> Callable[P1, R1]: ...
    @overload
    def synchronized(wrapped: Any) -> SynchronizedObject: ...
