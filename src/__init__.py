__version_info__ = ('1', '9', '0')
__version__ = '.'.join(__version_info__)

from .wrappers import (ObjectProxy, CallableObjectProxy, FunctionWrapper,
        BoundFunctionWrapper, WeakFunctionProxy, resolve_path, apply_patch,
        wrap_object, wrap_object_attribute, function_wrapper,
        wrap_function_wrapper, patch_function_wrapper,
        transient_function_wrapper)

from .decorators import decorator, synchronized

from .importer import (register_post_import_hook, when_imported,
        discover_post_import_hooks)

try:
    from inspect import getcallargs
except ImportError:
    from .arguments import getcallargs
