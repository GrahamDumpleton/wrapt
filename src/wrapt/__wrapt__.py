"""This module is used to switch between C and Python implementations of the
wrappers.
"""

import os

from .wrappers import BoundFunctionWrapper, CallableObjectProxy, FunctionWrapper
from .wrappers import ObjectProxy as BaseObjectProxy
from .wrappers import PartialCallableObjectProxy, _FunctionWrapperBase

# Try to use C extensions if not disabled.

_use_extensions = not os.environ.get("WRAPT_DISABLE_EXTENSIONS")

if _use_extensions:
    try:
        from ._wrappers import (  # type: ignore[no-redef,import-not-found]
            BoundFunctionWrapper,
            CallableObjectProxy,
            FunctionWrapper,
        )
        from ._wrappers import (
            ObjectProxy as BaseObjectProxy,  # type: ignore[no-redef,import-not-found]
        )
        from ._wrappers import (  # type: ignore[no-redef,import-not-found]
            PartialCallableObjectProxy,
            _FunctionWrapperBase,
        )
    except ImportError:
        # C extensions not available, using Python implementations
        pass


def partial(*args, **kwargs):
    """Create a callable object proxy with partial application of the given
    arguments and keywords. This behaves the same as `functools.partial`, but
    implemented using the `ObjectProxy` class to provide better support for
    introspection.
    """
    return PartialCallableObjectProxy(*args, **kwargs)


# Define variant of ObjectProxy which can automatically adjust to the wrapped
# object and add special dunder methods.


def __wrapper_call__(self, *args, **kwargs):
    return self.__wrapped__(*args, **kwargs)


def __wrapper_iter__(self):
    return iter(self.__wrapped__)


def __wrapper_next__(self):
    return self.__wrapped__.__next__()


def __wrapper_aiter__(self):
    return self.__wrapped__.__aiter__()


def __wrapper_anext__(self):
    return self.__wrapped__.__anext__()


class AutoObjectProxy(BaseObjectProxy):
    """An object proxy which can automatically adjust to the wrapped object
    and add special dunder methods as needed.
    """

    def __new__(cls, wrapped):
        """Injects special dunder methods into a dynamically created subclass
        as needed based on the wrapped object.
        """

        namespace = {}

        wrapped_attrs = dir(wrapped)
        class_attrs = dir(cls)

        if callable(wrapped) and "__call__" not in class_attrs:
            namespace["__call__"] = __wrapper_call__

        if "__iter__" in wrapped_attrs and "__iter__" not in class_attrs:
            namespace["__iter__"] = __wrapper_iter__

        if "__next__" in wrapped_attrs and "__next__" not in class_attrs:
            namespace["__next__"] = __wrapper_next__

        if "__aiter__" in wrapped_attrs and "__aiter__" not in class_attrs:
            namespace["__aiter__"] = __wrapper_aiter__

        if "__anext__" in wrapped_attrs and "__anext__" not in class_attrs:
            namespace["__anext__"] = __wrapper_anext__

        name = cls.__name__

        if cls is AutoObjectProxy:
            name = BaseObjectProxy.__name__

        return super().__new__(type(name, (cls,), namespace))

    def __wrapped_setattr_fixups__(self):
        """Adjusts special dunder methods on the class as needed based on the
        wrapped object, when ``__wrapped__`` is changed.
        """

        cls = type(self)
        class_attrs = dir(cls)

        if callable(self.__wrapped__):
            if "__call__" not in class_attrs:
                cls.__call__ = __wrapper_call__
        elif getattr(cls, "__call__", None) is __wrapper_call__:
            delattr(cls, "__call__")

        if hasattr(self.__wrapped__, "__iter__"):
            if "__iter__" not in class_attrs:
                cls.__iter__ = __wrapper_iter__
        elif getattr(cls, "__iter__", None) is __wrapper_iter__:
            delattr(cls, "__iter__")

        if hasattr(self.__wrapped__, "__next__"):
            if "__next__" not in class_attrs:
                cls.__next__ = __wrapper_next__
        elif getattr(cls, "__next__", None) is __wrapper_next__:
            delattr(cls, "__next__")

        if hasattr(self.__wrapped__, "__aiter__"):
            if "__aiter__" not in class_attrs:
                cls.__aiter__ = __wrapper_aiter__
        elif getattr(cls, "__aiter__", None) is __wrapper_aiter__:
            delattr(cls, "__aiter__")

        if hasattr(self.__wrapped__, "__anext__"):
            if "__anext__" not in class_attrs:
                cls.__anext__ = __wrapper_anext__
        elif getattr(cls, "__anext__", None) is __wrapper_anext__:
            delattr(cls, "__anext__")
