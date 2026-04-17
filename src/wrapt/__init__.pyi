import sys

if sys.version_info >= (3, 10):
    from inspect import FullArgSpec, Signature
    from types import ModuleType, TracebackType
    from typing import (
        Any,
        AsyncIterator,
        Callable,
        Concatenate,
        Generator,
        Generic,
        Iterator,
        ParamSpec,
        Protocol,
        TypeVar,
        overload,
    )

    P = ParamSpec("P")
    R = TypeVar("R", covariant=True)

    T = TypeVar("T", bound=Any)

    # Need two sets of ParamSpec/TypeVar for generics in some cases to ensure
    # that mypy, pyrefly and ty all work correctly. More specifically need a
    # separate set for cases where extracting the type or instance from the
    # first argument of a callable where binding is involved.

    P1 = ParamSpec("P1")
    R1 = TypeVar("R1", covariant=True)

    T1 = TypeVar("T1", bound=Any)

    P2 = ParamSpec("P2")
    R2 = TypeVar("R2", covariant=True)

    T2 = TypeVar("T2", bound=Any)

    class Boolean(Protocol):
        def __bool__(self) -> bool: ...

    # ObjectProxy
    #
    # BaseObjectProxy mirrors the dunder surface of the runtime class
    # (wrappers.ObjectProxy / _wrappers.ObjectProxy). Every protocol/operator
    # dunder that the runtime defines unconditionally is declared here so
    # static type checkers accept `len(proxy)`, `with proxy: ...`,
    # `proxy + x`, etc. without complaint. Dunders that the runtime only
    # attaches dynamically per wrapped object (__iter__ lives on
    # ObjectProxy for backward compatibility; __next__, __aiter__,
    # __anext__, __await__ and __length_hint__ are added per-instance by
    # AutoObjectProxy based on the wrapped interface) are intentionally
    # NOT claimed statically on BaseObjectProxy.
    #
    # `__enter__`/`__aenter__` return `T` rather than `Any` because the
    # runtime forwards to the wrapped object's `__enter__`, which for the
    # common "wrap a context manager" use case returns the wrapped object
    # itself -- this preserves type information through `with proxy as x`.
    # Other operator dunders return `Any` since the result depends on the
    # wrapped type.

    class BaseObjectProxy(Generic[T]):
        __wrapped__: T
        def __init__(self, wrapped: T) -> None: ...
        def __getattr__(self, name: str) -> Any: ...

        # Context managers.
        def __enter__(self) -> T: ...
        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None: ...
        async def __aenter__(self) -> T: ...
        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None: ...

        # Container protocol.
        def __len__(self) -> int: ...
        def __contains__(self, item: object) -> bool: ...
        def __getitem__(self, key: Any) -> Any: ...
        def __setitem__(self, key: Any, value: Any) -> None: ...
        def __delitem__(self, key: Any) -> None: ...
        def __reversed__(self) -> Iterator[Any]: ...

        # Numeric conversions.
        def __bool__(self) -> bool: ...
        def __int__(self) -> int: ...
        def __float__(self) -> float: ...
        def __complex__(self) -> complex: ...
        def __bytes__(self) -> bytes: ...
        def __index__(self) -> int: ...
        def __round__(self, ndigits: int = ...) -> Any: ...

        # Unary arithmetic.
        def __neg__(self) -> Any: ...
        def __pos__(self) -> Any: ...
        def __abs__(self) -> Any: ...
        def __invert__(self) -> Any: ...

        # Binary arithmetic.
        def __add__(self, other: Any) -> Any: ...
        def __sub__(self, other: Any) -> Any: ...
        def __mul__(self, other: Any) -> Any: ...
        def __matmul__(self, other: Any) -> Any: ...
        def __truediv__(self, other: Any) -> Any: ...
        def __floordiv__(self, other: Any) -> Any: ...
        def __mod__(self, other: Any) -> Any: ...
        def __divmod__(self, other: Any) -> Any: ...
        def __pow__(self, other: Any, modulo: Any = ...) -> Any: ...
        def __lshift__(self, other: Any) -> Any: ...
        def __rshift__(self, other: Any) -> Any: ...
        def __and__(self, other: Any) -> Any: ...
        def __or__(self, other: Any) -> Any: ...
        def __xor__(self, other: Any) -> Any: ...

        # Reflected binary arithmetic.
        def __radd__(self, other: Any) -> Any: ...
        def __rsub__(self, other: Any) -> Any: ...
        def __rmul__(self, other: Any) -> Any: ...
        def __rmatmul__(self, other: Any) -> Any: ...
        def __rtruediv__(self, other: Any) -> Any: ...
        def __rfloordiv__(self, other: Any) -> Any: ...
        def __rmod__(self, other: Any) -> Any: ...
        def __rdivmod__(self, other: Any) -> Any: ...
        def __rpow__(self, other: Any, modulo: Any = ...) -> Any: ...
        def __rlshift__(self, other: Any) -> Any: ...
        def __rrshift__(self, other: Any) -> Any: ...
        def __rand__(self, other: Any) -> Any: ...
        def __ror__(self, other: Any) -> Any: ...
        def __rxor__(self, other: Any) -> Any: ...

        # In-place arithmetic.
        def __iadd__(self, other: Any) -> Any: ...
        def __isub__(self, other: Any) -> Any: ...
        def __imul__(self, other: Any) -> Any: ...
        def __imatmul__(self, other: Any) -> Any: ...
        def __itruediv__(self, other: Any) -> Any: ...
        def __ifloordiv__(self, other: Any) -> Any: ...
        def __imod__(self, other: Any) -> Any: ...
        def __ipow__(self, other: Any) -> Any: ...  # type: ignore[misc]
        def __ilshift__(self, other: Any) -> Any: ...
        def __irshift__(self, other: Any) -> Any: ...
        def __iand__(self, other: Any) -> Any: ...
        def __ior__(self, other: Any) -> Any: ...
        def __ixor__(self, other: Any) -> Any: ...

        # Copy / pickle.
        def __copy__(self) -> Any: ...
        def __deepcopy__(self, memo: dict[int, Any]) -> Any: ...
        def __reduce__(self) -> Any: ...

    class ObjectProxy(BaseObjectProxy[T]):
        def __init__(self, wrapped: T) -> None: ...
        def __iter__(self) -> Iterator[Any]: ...

    class AutoObjectProxy(BaseObjectProxy[T]):
        # AutoObjectProxy attaches the dunders below to a per-instance
        # subclass at construction time, based on what the wrapped object
        # exposes (see proxies.AutoObjectProxy.__new__). We statically
        # claim all of them here so type checkers accept code that uses
        # them -- AutoObjectProxy's contract is "take on the interface
        # of the wrapped object", so the stub reflects that intent at
        # the cost of being permissive for proxies whose wrapped value
        # doesn't actually support a given dunder (a runtime
        # AttributeError, which mirrors the wrapt design).

        def __init__(self, wrapped: T) -> None: ...
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
        def __iter__(self) -> Iterator[Any]: ...
        def __next__(self) -> Any: ...
        def __aiter__(self) -> AsyncIterator[Any]: ...
        async def __anext__(self) -> Any: ...
        def __length_hint__(self) -> int: ...
        def __await__(self) -> Generator[Any, Any, Any]: ...

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

    class BoundFunctionWrapper(_FunctionWrapperBase[P1, R1]):
        def __call__(self, *args: P1.args, **kwargs: P1.kwargs) -> R1: ...

        # Note that for following overloads, testing with mypy and ty they still do
        # not handle static methods being decorated but to best knowledge this is
        # a limitation in those type checkers. Testing with pyrefly fails on any
        # type of bound method. Testing with pyright handles case correctly.
        #
        # Also, note that use of T2, P2 and R2 in first two cases is also required
        # to ensure correct handling by mypy and ty, so do not change to use of T1,
        # P1 and R1.

        @overload
        def __get__(  # Required to ensure mypy, pyrefly and ty works correctly
            self: BoundFunctionWrapper[Concatenate[T2, P2], R2],
            instance: T2,
            owner: type[T2] | None = None,
        ) -> BoundFunctionWrapper[P2, R2]: ...
        @overload
        def __get__(  # Required to ensure mypy, pyrefly and ty works correctly
            self: BoundFunctionWrapper[Concatenate[T2, P2], R2],
            instance: T2,
            owner: type[Any] | None = None,
        ) -> BoundFunctionWrapper[P2, R2]: ...
        @overload
        def __get__(  # Required to ensure mypy, pyrefly and ty works correctly
            self, instance: None, owner: type[T1] | None = None
        ) -> BoundFunctionWrapper[P1, R1]: ...
        @overload
        def __get__(  # Required to ensure pyright works correctly
            self, instance: T1, owner: type[T1] | None = None
        ) -> BoundFunctionWrapper[P1, R1]: ...

    class FunctionWrapper(_FunctionWrapperBase[P1, R1]):
        def __init__(
            self,
            wrapped: WrappedFunction[P1, R1],
            wrapper: WrapperFunction[P1, R1],
            enabled: bool | Boolean | Callable[[], bool] | None = None,
        ) -> None: ...
        def __call__(self, *args: P1.args, **kwargs: P1.kwargs) -> R1: ...

        # Note that for following overloads, testing with mypy and ty they still do
        # not handle static methods being decorated but to best knowledge this is
        # a limitation in those type checkers. Testing with pyrefly fails on any
        # type of bound method. Testing with pyright handles case correctly.
        #
        # Also, note that use of T2, P2 and R2 in first two cases is also required
        # to ensure correct handling by mypy and ty, so do not change to use of T1,
        # P1 and R1.

        @overload
        def __get__(  # Required to ensure mypy, pyrefly and ty works correctly
            self: FunctionWrapper[Concatenate[T2, P2], R2],
            instance: T2,
            owner: type[Any] | None = None,
        ) -> BoundFunctionWrapper[P2, R2]: ...
        @overload
        def __get__(  # Required to ensure mypy, pyrefly and ty works correctly
            self: FunctionWrapper[Concatenate[T2, P2], R2],
            instance: T2,
            owner: type[T2] | None = None,
        ) -> BoundFunctionWrapper[P2, R2]: ...
        @overload
        def __get__(  # Required to ensure mypy, pyrefly and ty works correctly
            self, instance: None, owner: type[T1] | None = None
        ) -> BoundFunctionWrapper[P1, R1]: ...
        @overload
        def __get__(  # Required to ensure pyright works correctly
            self, instance: T1, owner: type[T1] | None = None
        ) -> BoundFunctionWrapper[P1, R1]: ...

    # AdapterFactory/adapter_factory()

    class AdapterFactory(Protocol):
        def __call__(
            self, wrapped: Callable[..., Any]
        ) -> str | FullArgSpec | Callable[..., Any]: ...

    def adapter_factory(factory: Callable[..., Any]) -> AdapterFactory: ...

    # decorator()

    class Descriptor(Protocol):
        def __get__(self, instance: Any, owner: type[Any] | None = None) -> Any: ...

    class FunctionDecorator:
        @overload
        def __call__(
            self,
            callable: (
                Callable[P, R]
                | Callable[Concatenate[type[T], P], R]  # Required for pylance
                # | Callable[Concatenate[Any, P], R]  # Breaks mypy, pyrefly and ty
                | Callable[[type[T]], R]  # Required for pylance
            ),
        ) -> FunctionWrapper[P, R]: ...
        @overload
        def __call__(self, callable: Descriptor) -> FunctionWrapper[P, Any]: ...

    class PartialFunctionDecorator:
        @overload
        def __call__(
            self, wrapper: GenericCallableWrapperFunction[P, R], /
        ) -> FunctionDecorator: ...
        @overload
        def __call__(
            self, wrapper: ClassMethodWrapperFunction[P, R], /
        ) -> FunctionDecorator: ...
        @overload
        def __call__(
            self, wrapper: InstanceMethodWrapperFunction[P, R], /
        ) -> FunctionDecorator: ...

    # ... Decorator applied to class type.

    @overload
    def decorator(wrapper: type[T], /) -> FunctionDecorator: ...

    # ... Decorator applied to function or method.

    @overload
    def decorator(
        wrapper: GenericCallableWrapperFunction[P, R], /
    ) -> FunctionDecorator: ...
    @overload
    def decorator(
        wrapper: ClassMethodWrapperFunction[P, R], /
    ) -> FunctionDecorator: ...
    @overload
    def decorator(
        wrapper: InstanceMethodWrapperFunction[P, R], /
    ) -> FunctionDecorator: ...

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
    def function_wrapper(wrapper: type[Any]) -> FunctionDecorator: ...
    @overload
    def function_wrapper(
        wrapper: GenericCallableWrapperFunction[P, R],
    ) -> FunctionDecorator: ...
    @overload
    def function_wrapper(
        wrapper: ClassMethodWrapperFunction[P, R],
    ) -> FunctionDecorator: ...
    @overload
    def function_wrapper(
        wrapper: InstanceMethodWrapperFunction[P, R],
    ) -> FunctionDecorator: ...
    # @overload
    # def function_wrapper(wrapper: Any) -> FunctionDecorator: ... # Don't use, breaks stuff.

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
        def __call__(self, wrapper: WrapperFunction[P, R]) -> FunctionDecorator: ...

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
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any: ...

    # wrap_object_attribute()

    def wrap_object_attribute(
        module: ModuleType | type[Any] | Any | str,
        name: str,
        factory: WrapperFactory | type[ObjectProxy[Any]],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
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
        async def __aenter__(self) -> Any: ...
        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None: ...

    @overload
    def synchronized(wrapped: Callable[P, R]) -> Callable[P, R]: ...
    @overload
    def synchronized(wrapped: Any) -> SynchronizedObject: ...

    # mark_as_sync(), mark_as_async(), async_to_sync(), sync_to_async()

    @overload
    def mark_as_sync(wrapped: Callable[P, R], /) -> Callable[P, R]: ...
    @overload
    def mark_as_sync(
        *, generator: bool | None = None
    ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
    @overload
    def mark_as_async(wrapped: Callable[P, R], /) -> Callable[P, R]: ...
    @overload
    def mark_as_async(
        *, generator: bool | None = None
    ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
    def async_to_sync(wrapped: Callable[P, R]) -> Callable[P, R]: ...
    def sync_to_async(wrapped: Callable[P, R]) -> Callable[P, R]: ...

    # bind_state_to_wrapper()

    class _StateBindingWrapper:
        name: str
        wrapper_factory: Descriptor | None
        def __init__(self, *, name: str = "state") -> None: ...
        def __call__(self, wrapper_factory: Descriptor) -> _StateBindingWrapper: ...
        def __get__(
            self, instance: Any, owner: type[Any] | None = None
        ) -> (
            _StateBindingWrapper
            | Callable[[Callable[..., Any]], FunctionWrapper[..., Any]]
        ): ...

    bind_state_to_wrapper = _StateBindingWrapper

    # lru_cache()

    class _BoundLRUCacheFunctionWrapper(BoundFunctionWrapper[P1, R1]):
        def cache_info(self) -> Any | None: ...
        def cache_clear(self) -> None: ...
        def cache_parameters(self) -> dict[str, Any] | None: ...

    class _LRUCacheFunctionWrapper(FunctionWrapper[P1, R1]):
        __bound_function_wrapper__: type[_BoundLRUCacheFunctionWrapper[P1, R1]]
        def cache_info(self) -> Any | None: ...
        def cache_clear(self) -> None: ...
        def cache_parameters(self) -> dict[str, Any] | None: ...

    @overload
    def lru_cache(func: Callable[P, R], /) -> _LRUCacheFunctionWrapper[P, R]: ...
    @overload
    def lru_cache(
        func: None = None, /, **kwargs: Any
    ) -> Callable[[Callable[P, R]], _LRUCacheFunctionWrapper[P, R]]: ...

    # with_signature()

    def with_signature(
        *,
        prototype: Callable[..., Any] | None = None,
        signature: Signature | None = None,
        factory: (
            Callable[[Callable[..., Any]], Signature | Callable[..., Any]] | None
        ) = None,
    ) -> Callable[[Callable[P, R]], FunctionWrapper[P, R]]: ...
