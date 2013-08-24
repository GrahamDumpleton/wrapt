__version_info__ = ('0', '9', '0')
__version__ = '.'.join(__version_info__)

from .wrappers import ObjectProxy, FunctionWrapper
from .decorators import decorator, adapter
