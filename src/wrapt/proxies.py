"""Variants of ObjectProxy for different use cases."""

from .__wrapt__ import BaseObjectProxy
from .decorators import synchronized

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


def __wrapped_await__(self):
    return (yield from self.__wrapped__.__await__())


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

        if "__await__" in wrapped_attrs and "__await__" not in class_attrs:
            namespace["__await__"] = __wrapped_await__

        name = cls.__name__

        if cls is AutoObjectProxy:
            name = BaseObjectProxy.__name__

        return super().__new__(type(name, (cls,), namespace))

    def __wrapped_setattr_fixups__(self):
        """Adjusts special dunder methods on the class as needed based on the
        wrapped object, when `__wrapped__` is changed.
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


class LazyObjectProxy(AutoObjectProxy):
    """An object proxy which can generate/create the wrapped object on demand
    when it is first needed.
    """

    def __new__(cls, callback=None):
        return super().__new__(cls, None)

    def __init__(self, callback=None):
        """Initialize the object proxy with wrapped object as `None` but due
        to presence of special `__wrapped_factory__` attribute addded first,
        this will actually trigger the deferred creation of the wrapped object
        when first needed.
        """

        if callback is not None:
            self.__wrapped_factory__ = callback

        super().__init__(None)

    def __wrapped_factory__(self):
        return None

    def __wrapped_get__(self):
        """Gets the wrapped object, creating it if necessary."""

        # We synchronize on the class type, which will be unique to this instance
        # since we inherit from `AutoObjectProxy` which creates a new class
        # for each instance. If we synchronize on `self` or the method then
        # we can end up in infinite recursion via `__getattr__()`.

        with synchronized(type(self)):
            # We were called because `__wrapped__` was not set, but because of
            # multiple threads we may find that it has been set by the time
            # we get the lock. So check again now whether `__wrapped__` is set.
            # If it is then just return it, otherwise call the factory to
            # create it.

            try:
                return object.__getattribute__(self, "__wrapped__")
            except AttributeError:
                pass

            self.__wrapped__ = self.__wrapped_factory__()

            return self.__wrapped__
