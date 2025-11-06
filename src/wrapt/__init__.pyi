import sys

if sys.version_info >= (3, 10):
    from inspect import FullArgSpec
    from types import ModuleType, TracebackType
    from typing import (
        Any,
        Callable,
        Concatenate,
        Generic,
        ParamSpec,
        Protocol,
        TypeVar,
        overload,
    )

    P = ParamSpec("P")
    R = TypeVar("R", covariant=True)

    T = TypeVar("T", bound=Any)

    class Boolean(Protocol):
        def __bool__(self) -> bool: ...

    # ObjectProxy

    class BaseObjectProxy(Generic[T]):
        __wrapped__: T
        def __init__(self, wrapped: T) -> None: ...

    class ObjectProxy(BaseObjectProxy[T]):
        def __init__(self, wrapped: T) -> None: ...

    class AutoObjectProxy(BaseObjectProxy[T]):
        def __init__(self, wrapped: T) -> None: ...

    # LazyObjectProxy

    class LazyObjectProxy(AutoObjectProxy[T]):
        def __init__(
            self, callback: Callable[[], T] | None, *, interface: Any = ...
        ) -> None: ...

    @overload
    def lazy_import(name: str) -> LazyObjectProxy[ModuleType]: ...
    @overload
    def lazy_import(
        name: str, attribute: str, *, interface: Any = ...
    ) -> LazyObjectProxy[Any]: ...

    # CallableObjectProxy

    class CallableObjectProxy(BaseObjectProxy[T]):
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

    ClassMethodWrapperFunction = Callable[
        [type[Any], WrappedFunction[P, R], Any, tuple[Any, ...], dict[str, Any]], R
    ]

    InstanceMethodWrapperFunction = Callable[
        [Any, WrappedFunction[P, R], Any, tuple[Any, ...], dict[str, Any]], R
    ]

    WrapperFunction = (
        GenericCallableWrapperFunction[P, R]
        | ClassMethodWrapperFunction[P, R]
        | InstanceMethodWrapperFunction[P, R]
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

    # AdapterFactory/adapter_factory()

    class AdapterFactory(Protocol):
        def __call__(
            self, wrapped: Callable[..., Any]
        ) -> str | FullArgSpec | Callable[..., Any]: ...

    def adapter_factory(wrapped: Callable[..., Any]) -> AdapterFactory: ...

    # decorator()

    class Descriptor(Protocol):
        def __get__(self, instance: Any, owner: type[Any] | None = None) -> Any: ...

    class FunctionDecorator(Generic[P, R]):
        def __call__(
            self,
            callable: (
                Callable[P, R]
                | Callable[Concatenate[type[T], P], R]
                | Callable[Concatenate[Any, P], R]
                | Callable[[type[T]], R]
                | Descriptor
            ),
        ) -> FunctionWrapper[P, R]: ...

    class PartialFunctionDecorator:
        @overload
        def __call__(
            self, wrapper: GenericCallableWrapperFunction[P, R], /
        ) -> FunctionDecorator[P, R]: ...
        @overload
        def __call__(
            self, wrapper: ClassMethodWrapperFunction[P, R], /
        ) -> FunctionDecorator[P, R]: ...
        @overload
        def __call__(
            self, wrapper: InstanceMethodWrapperFunction[P, R], /
        ) -> FunctionDecorator[P, R]: ...

    # ... Decorator applied to class type.

    @overload
    def decorator(wrapper: type[T], /) -> FunctionDecorator[Any, Any]: ...

    # ... Decorator applied to function or method.

    @overload
    def decorator(
        wrapper: GenericCallableWrapperFunction[P, R], /
    ) -> FunctionDecorator[P, R]: ...
    @overload
    def decorator(
        wrapper: ClassMethodWrapperFunction[P, R], /
    ) -> FunctionDecorator[P, R]: ...
    @overload
    def decorator(
        wrapper: InstanceMethodWrapperFunction[P, R], /
    ) -> FunctionDecorator[P, R]: ...

    # ... Positional arguments.

    @overload
    def decorator(
        *,
        enabled: bool | Boolean | Callable[[], bool] | None = None,
        adapter: str | FullArgSpec | AdapterFactory | Callable[..., Any] | None = None,
        proxy: type[FunctionWrapper[Any, Any]] | None = None,
    ) -> PartialFunctionDecorator: ...

    # function_wrapper()

    @overload
    def function_wrapper(wrapper: type[Any]) -> FunctionDecorator[Any, Any]: ...
    @overload
    def function_wrapper(
        wrapper: GenericCallableWrapperFunction[P, R],
    ) -> FunctionDecorator[P, R]: ...
    @overload
    def function_wrapper(
        wrapper: ClassMethodWrapperFunction[P, R],
    ) -> FunctionDecorator[P, R]: ...
    @overload
    def function_wrapper(
        wrapper: InstanceMethodWrapperFunction[P, R],
    ) -> FunctionDecorator[P, R]: ...
    # @overload
    # def function_wrapper(wrapper: Any) -> FunctionDecorator[Any, Any]: ... # Don't use, breaks stuff.

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
    def synchronized(wrapped: Callable[P, R]) -> Callable[P, R]: ...
    @overload
    def synchronized(wrapped: Any) -> SynchronizedObject: ...
