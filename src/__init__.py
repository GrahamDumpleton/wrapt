__version_info__ = ('1', '2', '1')
__version__ = '.'.join(__version_info__)

from .wrappers import (ObjectProxy, FunctionWrapper, BoundFunctionWrapper,
        WeakFunctionProxy, resolve_path, apply_patch, wrap_object,
        function_wrapper, wrap_function_wrapper, patch_function_wrapper)

from .decorators import decorator, synchronized

from .importer import register_post_import_hook, when_imported
