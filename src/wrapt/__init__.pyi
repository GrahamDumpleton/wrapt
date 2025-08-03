import sys

if sys.version_info >= (3, 10):
    from types import ModuleType
    from typing import Any, Callable

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
            enabled: bool | Callable[[], bool] | None = None,
        ) -> None: ...
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # function_wrapper()

    class FunctionDecorator:
        def __call__(self, callable: Callable[..., Any]) -> FunctionWrapper: ...

    def function_wrapper(wrapper: WrapperFunction) -> FunctionDecorator: ...

    # wrap_function_wrapper()

    def wrap_function_wrapper(
        target: ModuleType | type[Any] | Any | str, name: str, wrapper: WrapperFunction
    ) -> FunctionWrapper: ...

    # patch_function_wrapper()

    class WrapperDecorator:
        def __call__(self, wrapper: WrapperFunction) -> FunctionWrapper: ...

    def patch_function_wrapper(
        target: ModuleType | type[Any] | Any | str,
        name: str,
        enabled: bool | Callable[[], bool] | None = None,
    ) -> WrapperDecorator: ...

    # transient_function_wrapper()

    class TransientDecorator:
        def __call__(self, wrapper: WrapperFunction) -> FunctionDecorator: ...

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
