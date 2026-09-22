"""Weak reference proxy for functions and bound methods."""

import functools
import weakref

from .__wrapt__ import BaseObjectProxy, _FunctionWrapperBase

# A weak function proxy. This will work on instance methods, class
# methods, static methods and regular functions. Special treatment is
# needed for the method types because the bound method is effectively a
# transient object and applying a weak reference to one will immediately
# result in it being destroyed and the weakref callback called. The weak
# reference is therefore applied to the instance the method is bound to
# and the original function. The function is then rebound at the point
# of a call via the weak function proxy.
#
# Where the function is a wrapt function wrapper, such as results from
# applying a decorator, the same applies but there may be no instance,
# either because the wrapper was never bound, as for a decorated free
# function, or because the method was accessed via the class rather
# than an instance. In that case a weak reference to the class the
# wrapper was accessed through, the owner, is retained as well so that
# the function can still be rebound correctly at the point of a call.


def _weak_function_proxy_callback(ref, proxy, callback):
    if proxy._self_expired:
        return

    proxy._self_expired = True

    # This could raise an exception. We let it propagate back and let
    # the weakref.proxy() deal with it, at which point it generally
    # prints out a short error message direct to stderr and keeps going.

    if callback is not None:
        callback(proxy)


class WeakFunctionProxy(BaseObjectProxy):
    """A weak function proxy."""

    def __init__(self, wrapped, callback=None):
        """Create a proxy to object which uses a weak reference. This is
        similar to the `weakref.proxy` but is designed to work with functions
        and methods. It will automatically rebind the function to the instance
        when called if the function was originally a bound method. This is
        necessary because bound methods are transient objects and applying a
        weak reference to one will immediately result in it being destroyed
        and the weakref callback called. The weak reference is therefore
        applied to the instance the method is bound to and the original
        function. The function is then rebound at the point of a call via the
        weak function proxy.
        """

        # We need to determine if the wrapped function is actually a
        # bound method. In the case of a bound method, we need to keep a
        # reference to the original unbound function and the instance.
        # This is necessary because if we hold a reference to the bound
        # function, it will be the only reference and given it is a
        # temporary object, it will almost immediately expire and
        # the weakref callback triggered. So what is done is that we
        # hold a reference to the instance and unbound function and
        # when called bind the function to the instance once again and
        # then call it. Note that we avoid using a nested function for
        # the callback here so as not to cause any odd reference cycles.

        _callback = callback and functools.partial(
            _weak_function_proxy_callback, proxy=self, callback=callback
        )

        self._self_expired = False
        self._self_owner = None

        if isinstance(wrapped, _FunctionWrapperBase):
            # A function wrapper may have no instance, either because it
            # was never bound, as for a decorated free function, or
            # because the method was accessed via the class rather than
            # an instance. Only take a weak reference to the instance
            # where there is one. The owner is the class the wrapper was
            # accessed through, and is retained so the function can be
            # rebound with it when called. Without it a classmethod
            # accessed via the class could not be rebound at all, and an
            # instance method accessed via the class would not be able
            # to identify an instance passed as the first argument.

            instance = wrapped._self_instance
            self._self_instance = (
                weakref.ref(instance, _callback) if instance is not None else None
            )
            owner = wrapped._self_owner
            if owner is not None:
                self._self_owner = weakref.ref(owner, _callback)

            if wrapped._self_parent is not None:
                # Explicit class in super() is used because the proxy
                # overrides __class__ and MRO-related methods to delegate
                # to the wrapped object, which can interfere with bare
                # super().
                super(WeakFunctionProxy, self).__init__(
                    weakref.proxy(wrapped._self_parent, _callback)
                )

            else:
                super(WeakFunctionProxy, self).__init__(
                    weakref.proxy(wrapped, _callback)
                )

            return

        try:
            self._self_instance = weakref.ref(wrapped.__self__, _callback)

            super(WeakFunctionProxy, self).__init__(
                weakref.proxy(wrapped.__func__, _callback)
            )

        except AttributeError:
            self._self_instance = None

            super(WeakFunctionProxy, self).__init__(weakref.proxy(wrapped, _callback))

    def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        # We perform a boolean check here on the instance and wrapped
        # function as that will trigger the reference error prior to
        # calling if the reference had expired.

        instance = self._self_instance and self._self_instance()
        function = self.__wrapped__ and self.__wrapped__

        # If the wrapped function was originally a bound method but the
        # instance it was bound to has been garbage collected, raise a
        # ReferenceError rather than silently calling it as unbound.

        if self._self_instance is not None and instance is None:
            raise ReferenceError("weakly-referenced object no longer exists")

        # If the wrapped function was a function wrapper for which the
        # owner was retained, rebind the function against the instance,
        # which may be None, and that owner. This is what a classmethod
        # accessed via the class needs to be rebound at all, and what an
        # instance method accessed via the class needs to recognise an
        # instance passed as the first argument. If the owner has been
        # garbage collected, raise a ReferenceError as for the instance.

        if self._self_owner is not None:
            owner = self._self_owner()
            if owner is None:
                raise ReferenceError("weakly-referenced object no longer exists")
            return function.__get__(instance, owner)(*args, **kwargs)

        # Otherwise, if the wrapped function was originally a bound
        # function, for which we retained a reference to the instance and
        # the unbound function, we need to rebind the function and then
        # call it. If not just call the wrapped function.

        if instance is None:
            return self.__wrapped__(*args, **kwargs)

        return function.__get__(instance, type(instance))(*args, **kwargs)
