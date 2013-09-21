__version_info__ = ('1', '1', '3')
__version__ = '.'.join(__version_info__)

from .wrappers import ObjectProxy, FunctionWrapper, WeakFunctionProxy
from .decorators import decorator, synchronized
