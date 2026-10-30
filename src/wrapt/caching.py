"""Caching decorators. Currently provides ``lru_cache``, a drop-in
replacement for ``functools.lru_cache`` with correct handling of instance
methods and class methods: a separate cache is maintained per instance or
per class, stored as an attribute on the instance or class itself so it is
cleaned up with that object by the garbage collector. For plain functions
and static methods a single shared cache is used, matching
``functools.lru_cache``.
"""

from functools import lru_cache as _functools_lru_cache
from functools import partial

from .__wrapt__ import BaseObjectProxy, BoundFunctionWrapper, FunctionWrapper
from .decorators import decorator
from .synchronization import synchronized

# Decorator that applies functools.lru_cache to the wrapped function.
# Unlike using functools.lru_cache directly, this works correctly with
# instance methods and class methods by maintaining a separate cache
# per instance or class. Each per-instance cache is stored as an
# attribute on the instance itself, and each per-class cache as an
# attribute on the class the method was bound to when called, so they
# are automatically cleaned up when the instance or class is garbage
# collected. For plain functions and static methods, a single cache is
# stored on the wrapper itself. The underlying caches are created lazily
# on first call, with double-checked locking via synchronized to avoid
# races in multi-threaded code.
#
# Custom FunctionWrapper and BoundFunctionWrapper subclasses are used
# so that cache_info() and cache_clear() are available directly on
# the decorated function. For bound methods, the BoundFunctionWrapper
# uses _self_instance, or the class the method is bound to, to locate
# the per-instance or per-class cache.


class _BoundLRUCacheFunctionWrapper(BoundFunctionWrapper):

    def _cache_owner(self):
        # Return the object the cache for this binding is stored on, or
        # None where the single shared cache on the parent wrapper is
        # used instead.
        #
        # For an instance method this is the instance. For a class method
        # it is the class the method was bound to when accessed, which is
        # the class named in the lookup or the type of the instance it
        # was accessed through. That is not necessarily the class the
        # method was defined on, as a class method inherited by a
        # subclass is bound to the subclass. Each class in a hierarchy
        # therefore has its own cache and the class method always
        # receives the correct cls, in the same way that each instance
        # has its own cache for an instance method. Static methods have
        # no binding and so share a single cache, as do any other
        # callables which could not be identified as methods.

        if self._self_binding == "function":
            return self._self_instance

        if self._self_binding == "classmethod":
            return self.__wrapped__.__self__

        return None

    def _lookup_cache(self, owner):
        cache_attr = self._self_parent._self_cache_attr

        # For a class, only its own __dict__ is consulted. Looking the
        # attribute up normally would find the cache of a base class
        # through inheritance, and a subclass must not share the cache
        # of the class it derives from.

        if self._self_binding == "classmethod":
            return owner.__dict__.get(cache_attr)

        return getattr(owner, cache_attr, None)

    def _store_cache(self, owner, cache):
        cache_attr = self._self_parent._self_cache_attr

        # If the object the method is bound to is a wrapt object proxy, a
        # plain setattr() would fall through and store the cache on the
        # wrapped object rather than the proxy. Use type() rather than
        # isinstance() so the check sees the real proxy type and is not
        # fooled by the proxy overriding __class__ to report the wrapped
        # object's type. Proxies expose __self_setattr__() which stores
        # the attribute on the proxy itself.

        if issubclass(type(owner), BaseObjectProxy):
            owner.__self_setattr__(cache_attr, cache)
        else:
            setattr(owner, cache_attr, cache)

    def _cache(self):
        # Return the cache for this binding, or None if it has not yet
        # been created.

        owner = self._cache_owner()

        if owner is None:
            return self._self_parent._self_cache

        return self._lookup_cache(owner)

    def __call__(self, *args, **kwargs):
        parent = self._self_parent

        owner = self._cache_owner()

        # Static methods and unidentified callables use a single shared
        # cache stored on the parent wrapper. The cache is created from
        # the bound __wrapped__ since the parent's __wrapped__ is the raw
        # staticmethod descriptor.

        if owner is None:
            if parent._self_cache is None:
                with synchronized(parent):
                    if parent._self_cache is None:
                        parent._self_cache = _functools_lru_cache(
                            **parent._self_lru_kwargs
                        )(self.__wrapped__)

            return parent._self_cache(*args, **kwargs)

        # Instance method or class method. The cache is created from the
        # bound __wrapped__, so it calls the method as bound to this
        # instance or class, and is stored as an attribute on that object
        # so it is cleaned up along with it by the garbage collector.

        cache = self._lookup_cache(owner)

        if cache is None:
            with synchronized(parent):
                cache = self._lookup_cache(owner)

                if cache is None:
                    cache = _functools_lru_cache(**parent._self_lru_kwargs)(
                        self.__wrapped__
                    )

                    self._store_cache(owner, cache)

        return cache(*args, **kwargs)

    def cache_info(self):
        """Return the cache statistics for this binding's cache, or
        ``None`` if the cache has not yet been created.
        """

        cache = self._cache()

        if cache is not None:
            return cache.cache_info()

        return None

    def cache_clear(self):
        """Clear this binding's cache."""

        cache = self._cache()

        if cache is not None:
            cache.cache_clear()

    def cache_parameters(self):
        """Return the parameters used to create the cache, or ``None``
        if the cache has not yet been created.
        """

        cache = self._cache()

        if cache is not None:
            return cache.cache_parameters()

        return None


class _LRUCacheFunctionWrapper(FunctionWrapper):

    __bound_function_wrapper__ = _BoundLRUCacheFunctionWrapper

    def __init__(self, wrapped, wrapper, **kwargs):
        super().__init__(wrapped, wrapper, **kwargs)

        # Extract the LRU cache configuration that was attached to the
        # wrapper function before it was passed to the decorator.

        self._self_lru_kwargs = wrapper._self_lru_kwargs
        self._self_cache = None

        # Use __func__ to get the name for classmethod/staticmethod
        # descriptors which lack __name__ on Python < 3.10.

        name = getattr(wrapped, "__name__", None)

        if name is None:
            name = wrapped.__func__.__name__

        # The cache attribute name must be unique per decorated method so
        # that a method overridden in a subclass does not share the same
        # per-instance cache slot as the method it overrides. If they shared
        # a slot, a subclass method calling super() would find the subclass
        # cache and re-enter its own body, recursing forever. The owning
        # class is not known here, since the decorator runs on the raw
        # function before the class exists, but each decorated method has its
        # own wrapper instance, so id(self) is a stable discriminator unique
        # to this method definition.

        self._self_cache_attr = "_lru_cache_" + name + "_" + str(id(self))

    def __call__(self, *args, **kwargs):
        # Plain function or static method, single cache stored on the
        # wrapper itself.

        if self._self_cache is None:
            with synchronized(self):
                if self._self_cache is None:
                    self._self_cache = _functools_lru_cache(**self._self_lru_kwargs)(
                        self.__wrapped__
                    )

        return self._self_cache(*args, **kwargs)

    def cache_info(self):
        """Return the cache statistics, or ``None`` if the cache has
        not yet been created.
        """

        if self._self_cache is not None:
            return self._self_cache.cache_info()

        return None

    def cache_clear(self):
        """Clear the cache and reset the statistics."""

        if self._self_cache is not None:
            self._self_cache.cache_clear()

    def cache_parameters(self):
        """Return the parameters used to create the cache, or ``None``
        if the cache has not yet been created.
        """

        if self._self_cache is not None:
            return self._self_cache.cache_parameters()

        return None


def lru_cache(func=None, /, **kwargs):
    """A decorator that applies ``functools.lru_cache`` to the wrapped
    function, with correct handling for instance methods, class methods,
    and static methods.

    For instance methods, a separate ``functools.lru_cache`` is
    maintained per instance. The cache is stored as an attribute on the
    instance itself, so it is automatically cleaned up when the instance
    is garbage collected. This means instances do not need to be
    hashable, each instance gets its own full ``maxsize`` budget, and
    no external mapping prevents garbage collection.

    For class methods, a separate cache is likewise maintained per class,
    stored as an attribute on the class the method was bound to when
    called. A class method inherited by a subclass is bound to the
    subclass, so each class in a hierarchy has its own cache and the
    method always receives the class it was called through as ``cls``.

    For plain functions and static methods, a single shared cache is
    used.

    All keyword arguments are passed through to ``functools.lru_cache``.

    Cache management methods ``cache_info()`` and ``cache_clear()`` are
    available directly on the decorated function. For bound methods,
    these operate on the cache for the bound instance or class.
    """

    if func is None:
        return partial(lru_cache, **kwargs)

    def _wrapper(wrapped, instance, args, _kwargs):
        return wrapped(*args, **_kwargs)

    _wrapper._self_lru_kwargs = kwargs

    return decorator(_wrapper, proxy=_LRUCacheFunctionWrapper)(func)
