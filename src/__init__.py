__version_info__ = ('1', '2', '0')
__version__ = '.'.join(__version_info__)

from .wrappers import ObjectProxy, FunctionWrapper, WeakFunctionProxy
from .decorators import decorator, synchronized
from .importer import register_post_import_hook, when_imported
