import sys

if sys.version_info >= (3, 10):
    from inspect import FullArgSpec
    from types import ModuleType, TracebackType
    from typing import Any, Callable, Generic, ParamSpec, Protocol, TypeVar, overload

    P = ParamSpec("P")
    R = TypeVar("R", covariant=True)

    T = TypeVar("T", bound=Any)

    class Boolean(Protocol):
        def __bool__(self) -> bool: ...

    # ObjectProxy

    class ObjectProxy(Generic[T]):
        __wrapped__: T
        def __init__(self, wrapped: T) -> None: ...

    # CallableObjectProxy

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

    WrappedFunction = Callable[P, R]

    GenericCallableWrapperFunction = Callable[
        [WrappedFunction[P, R], Any, tuple[Any, ...], dict[str, Any]], R
    ]

    InstanceMethodWrapperFunction = Callable[
        [Any, WrappedFunction[P, R], Any, tuple[Any, ...], dict[str, Any]], R
    ]

    ClassMethodWrapperFunction = Callable[
        [type[Any], WrappedFunction[P, R], Any, tuple[Any, ...], dict[str, Any]], R
    ]

    WrapperFunction = (
        GenericCallableWrapperFunction[P, R]
        | InstanceMethodWrapperFunction[P, R]
        | ClassMethodWrapperFunction[P, R]
    )

    class _FunctionWrapperBase(ObjectProxy[WrappedFunction[P, R]]):
        _self_instance: Any
        _self_wrapper: WrapperFunction[P, R]
        _self_enabled: bool | Boolean | Callable[[], bool] | None
        _self_binding: str
        _self_parent: Any
        _self_owner: Any

    class BoundFunctionWrapper(_FunctionWrapperBase[P, R]):
        def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
        def __get__(
            self, instance: Any, owner: type[Any] | None = None
        ) -> "BoundFunctionWrapper[P, R]": ...

    class FunctionWrapper(_FunctionWrapperBase[P, R]):
        def __init__(
            self,
            wrapped: WrappedFunction[P, R],
            wrapper: WrapperFunction[P, R],
            enabled: bool | Boolean | Callable[[], bool] | None = None,
        ) -> None: ...
        def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
        def __get__(
            self, instance: Any, owner: type[Any] | None = None
        ) -> BoundFunctionWrapper[P, R]: ...

    # decorator()

    P1 = ParamSpec("P1")
    R1 = TypeVar("R1", covariant=True)

    P2 = ParamSpec("P2")
    R2 = TypeVar("R2", covariant=True)

    class AdapterFactory:
        def __call__(
            self, wrapped: WrappedFunction[P1, R1]
        ) -> WrappedFunction[P2, R2]: ...

    def adapter_factory(wrapped: WrappedFunction[P1, R1]) -> AdapterFactory: ...

    class FunctionDecorator(Generic[P1, R1]):
        def __call__(self, callable: Callable[..., R1]) -> FunctionWrapper[P1, R1]: ...

    @overload
    def decorator(
        wrapper: type[T] | None = None,
        /,
        *,
        enabled: bool | Boolean | Callable[[], bool] | None = None,
        adapter: None = None,
        proxy: type[FunctionWrapper[Any, Any]] = ...,
    ) -> FunctionDecorator[Any, Any]: ...
    @overload
    def decorator(
        wrapper: WrapperFunction[P1, R1] | None = None,
        /,
        *,
        enabled: bool | Boolean | Callable[[], bool] | None = None,
        adapter: None = None,
        proxy: type[FunctionWrapper[P1, R1]] = ...,
    ) -> FunctionDecorator[P1, R1]: ...
    @overload
    def decorator(
        wrapper: WrapperFunction[P1, R1] | None = None,
        /,
        *,
        enabled: bool | Boolean | Callable[[], bool] | None = None,
        adapter: str | FullArgSpec | Callable[[Callable[P1, R1]], Callable[P2, R2]],
        proxy: type[FunctionWrapper[P2, R2]] = ...,
    ) -> FunctionDecorator[P2, R2]: ...

    # function_wrapper()

    @overload
    def function_wrapper(
        wrapper: GenericCallableWrapperFunction[P, R],
    ) -> FunctionDecorator[P, R]: ...
    @overload
    def function_wrapper(
        wrapper: InstanceMethodWrapperFunction[P, R],
    ) -> FunctionDecorator[P, R]: ...
    @overload
    def function_wrapper(
        wrapper: ClassMethodWrapperFunction[P, R],
    ) -> FunctionDecorator[P, R]: ...

    # wrap_function_wrapper()

    def wrap_function_wrapper(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        wrapper: WrapperFunction[P, R],
    ) -> FunctionWrapper[P, R]: ...

    # patch_function_wrapper()

    class WrapperDecorator:
        def __call__(self, wrapper: WrapperFunction[P, R]) -> FunctionWrapper[P, R]: ...

    def patch_function_wrapper(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        enabled: bool | Boolean | Callable[[], bool] | None = None,
    ) -> WrapperDecorator: ...

    # transient_function_wrapper()

    class TransientDecorator:
        def __call__(
            self, wrapper: WrapperFunction[P, R]
        ) -> FunctionDecorator[P, R]: ...

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
        [Callable[..., Any], tuple[Any, ...], dict[str, Any]], type[ObjectProxy[Any]]
    ]

    def wrap_object(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        factory: WrapperFactory | type[ObjectProxy[Any]],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any: ...

    # wrap_object_attribute()

    def wrap_object_attribute(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        factory: WrapperFactory | type[ObjectProxy[Any]],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] = {},
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
        def __call__(self, wrapped: Callable[P, R]) -> Callable[P, R]: ...
        def __enter__(self) -> Any: ...
        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None: ...

    @overload
    def synchronized(wrapped: Callable[P, R]) -> Callable[P, R]: ...  # type: ignore
    @overload
    def synchronized(wrapped: Any) -> SynchronizedObject: ...
