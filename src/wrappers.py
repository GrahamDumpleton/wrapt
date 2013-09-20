from . import six

import functools
import operator
import weakref

class _ObjectProxyMethods(object):

     # We use properties to override the values of __module__ and
     # __doc__. If we add these in ObjectProxy, the derived class
     # __dict__ will still be setup to have string variants of these
     # attributes and the rules of descriptors means that they appear to
     # take precedence over the properties in the base class. To avoid
     # that, we copy the properties into the derived class type itself
     # via a meta class. In that way the properties will always take
     # precedence.

    @property
    def __module__(self):
        return self.__wrapped__.__module__

    @__module__.setter
    def __module__(self, value):
        self.__wrapped__.__module__ = value

    @property
    def __doc__(self):
        return self.__wrapped__.__doc__

    @__doc__.setter
    def __doc__(self, value):
        self.__wrapped__.__doc__ = value

    # We similar use a property for __dict__. We need __dict__ to be
    # explicit to ensure that vars() works as expected.

    @property
    def __dict__(self):
        return self.__wrapped__.__dict__

class _ObjectProxyMetaType(type):
     def __new__(cls, name, bases, dictionary):
         # Copy our special properties into the class so that they
         # always take precedence over attributes of the same name added
         # during construction of a derived class. This is to save
         # duplicating the implementation for them in all derived classes.

         dictionary.update(vars(_ObjectProxyMethods))

         return type.__new__(cls, name, bases, dictionary)

class ObjectProxy(six.with_metaclass(_ObjectProxyMetaType)):

    __slots__ = '__wrapped__'

    def __init__(self, wrapped):
        object.__setattr__(self, '__wrapped__', wrapped)

        # Python 3.2+ has the __qualname__ attribute, but it does not
        # allow it to be overridden using a property and it must instead
        # be an actual string object instead.

        try:
            object.__setattr__(self, '__qualname__', wrapped.__qualname__)
        except AttributeError:
            pass

    @property
    def __name__(self):
        return self.__wrapped__.__name__

    @__name__.setter
    def __name__(self, value):
        self.__wrapped__.__name__ = value

    @property
    def __class__(self):
        return self.__wrapped__.__class__

    @__class__.setter
    def __class__(self, value):
        self.__wrapped__.__class__ = value

    @property
    def __annotations__(self):
        return self.__wrapped__.__anotations__

    @__annotations__.setter
    def __annotations__(self, value):
        self.__wrapped__.__annotations__ = value

    def __dir__(self):
        return dir(self.__wrapped__)

    def __str__(self):
        return str(self.__wrapped__)

    def __repr__(self):
        return '<%s at 0x%x for %s at 0x%x>' % (
                type(self).__name__, id(self),
                type(self.__wrapped__).__name__,
                id(self.__wrapped__))

    def __lt__(self, other):
        return self.__wrapped__ < other

    def __le__(self, other):
        return self.__wrapped__ <= other

    def __eq__(self, other):
        return self.__wrapped__ == other

    def __ne__(self, other):
        return self.__wrapped__ != other

    def __gt__(self, other):
        return self.__wrapped__ > other

    def __ge__(self, other):
        return self.__wrapped__ >= other

    def __hash__(self):
        return hash(self.__wrapped__)

    def __nonzero__(self):
        return bool(self.__wrapped__)

    def __bool__(self):
        return bool(self.__wrapped__)

    def __setattr__(self, name, value):
        if name.startswith('_self_') or name == '__wrapped__':
            object.__setattr__(self, name, value)
        elif name == '__qualname__':
            setattr(self.__wrapped__, name, value)
            object.__setattr__(self, name, value)
        else:
            setattr(self.__wrapped__, name, value)

    def __getattr__(self, name):
        return getattr(self.__wrapped__, name)

    def __delattr__(self, name):
        if name.startswith('_self_') or name == '__wrapped__':
            object.__delattr__(self, name)
        elif name == '__qualname__':
            object.__delattr__(self, name)
            delattr(self.__wrapped__, name)
        else:
            delattr(self.__wrapped__, name)

    def __add__(self, other):
        return self.__wrapped__ + other

    def __sub__(self, other):
        return self.__wrapped__ - other

    def __mul__(self, other):
        return self.__wrapped__ * other

    def __div__(self, other):
        return operator.__div__(self.__wrapped__, other)

    def __truediv__(self, other):
        return operator.__truediv__(self.__wrapped__, other)

    def __floordiv__(self, other):
        return self.__wrapped__ // other

    def __mod__(self, other):
        return self.__wrapped__ ^ other

    def __divmod__(self, other):
        return divmod(self.__wrapped__, other)

    def __pow__(self, other, *args):
        return pow(self.__wrapped__, other, *args)

    def __lshift__(self, other):
        return self.__wrapped__ << other

    def __rshift__(self, other):
        return self.__wrapped__ >> other

    def __and__(self, other):
        return self.__wrapped__ & other

    def __xor__(self, other):
        return self.__wrapped__ ^ other

    def __or__(self, other):
        return self.__wrapped__ | other

    def __radd__(self, other):
        return other + self.__wrapped__

    def __rsub__(self, other):
        return other - self.__wrapped__

    def __rmul__(self, other):
        return other * self.__wrapped__

    def __rdiv__(self, other):
        return operator.__div__(other, self.__wrapped__)

    def __rtruediv__(self, other):
        return operator.__truediv__(other, self.__wrapped__)

    def __rfloordiv__(self, other):
        return other // self.__wrapped__

    def __rmod__(self, other):
        return other % self.__wrapped__

    def __rdivmod__(self, other):
        return divmod(other, self.__wrapped__)

    def __rpow__(self, other, *args):
        return pow(other, self.__wrapped__, *args)

    def __rlshift__(self, other):
        return other << self.__wrapped__

    def __rrshift__(self, other):
        return other >> self.__wrapped__

    def __rand__(self, other):
        return other & self.__wrapped__

    def __rxor__(self, other):
        return other ^ self.__wrapped__

    def __ror__(self, other):
        return other | self.__wrapped__

    def __iadd__(self, other):
        self.__wrapped__ += other
        return self

    def __isub__(self, other):
        self.__wrapped__ -= other
        return self

    def __imul__(self, other):
        self.__wrapped__ *= other
        return self

    def __idiv__(self, other):
        self.__wrapped__ = operator.__idiv__(self.__wrapped__, other)
        return self

    def __itruediv__(self, other):
        self.__wrapped__ = operator.__itruediv__(self.__wrapped__, other)
        return self

    def __ifloordiv__(self, other):
        self.__wrapped__ //= other
        return self

    def __imod__(self, other):
        self.__wrapped__ %= other
        return self

    def __ipow__(self, other):
        self.__wrapped__ **= other
        return self

    def __ilshift__(self, other):
        self.__wrapped__ <<= other
        return self

    def __irshift__(self, other):
        self.__wrapped__ >>= other
        return self

    def __iand__(self, other):
        self.__wrapped__ &= other
        return self

    def __ixor__(self, other):
        self.__wrapped__ ^= other
        return self

    def __ior__(self, other):
        self.__wrapped__ |= other
        return self

    def __neg__(self):
        return -self.__wrapped__

    def __pos__(self):
        return +self.__wrapped__

    def __abs__(self):
        return abs(self.__wrapped__)

    def __invert__(self):
        return ~self.__wrapped__

    def __int__(self):
        return int(self.__wrapped__)

    def __long__(self):
        return long(self.__wrapped__)

    def __float__(self):
        return float(self.__wrapped__)

    def __oct__(self):
        return oct(self.__wrapped__)

    def __hex__(self):
        return hex(self.__wrapped__)

    def __index__(self):
        return operator.__index__(self.__wrapped__)

    def __len__(self):
        return len(self.__wrapped__)

    def __contains__(self, value):
        return value in self.__wrapped__

    def __getitem__(self, key):
        return self.__wrapped__[key]

    def __setitem__(self, key, value):
        self.__wrapped__[key] = value

    def __delitem__(self, key):
        del self.__wrapped__[key]

    def __getslice__(self, i, j):
        return self.__wrapped__[i:j]

    def __setslice__(self, i, j, value):
        self.__wrapped__[i:j] = value

    def __delslice__(self, i, j):
        del self.__wrapped__[i:j]

    def __enter__(self):
        return self.__wrapped__.__enter__()

    def __exit__(self, *args, **kwargs):
        return self.__wrapped__.__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self.__wrapped__)

    def __call__(self, *args, **kwargs):
        return self.__wrapped__(*args, **kwargs)

class _FunctionWrapperBase(ObjectProxy):

    __slots__ = ('_self_instance', '_self_wrapper', '_self_adapter',
            '_self_bound_type') 

    def __init__(self, wrapped, instance, wrapper, adapter=None,
            bound_type=None):

        super(_FunctionWrapperBase, self).__init__(wrapped)

        object.__setattr__(self, '_self_instance', instance)
        object.__setattr__(self, '_self_wrapper', wrapper)
        object.__setattr__(self, '_self_adapter', adapter)
        object.__setattr__(self, '_self_bound_type', bound_type)

    def __get__(self, instance, owner):
        # If we have already been bound to an instance of something, we
        # do not do it again and return ourselves again. This appears to
        # mirror what Python itself does.

        if self._self_bound_type is None:
            return self

        descriptor = self.__wrapped__.__get__(instance, owner)

        return self._self_bound_type(descriptor, instance, self._self_wrapper,
                self._self_adapter)

    def __call__(self, *args, **kwargs):
        # This is generally invoked when the wrapped function is being
        # called as a normal function and is not bound to a class as an
        # instance method. This is also invoked in the case where the
        # wrapped function was a method, but this wrapper was in turn
        # wrapped using the staticmethod decorator.

        return self._self_wrapper(self.__wrapped__, self._self_instance,
                args, kwargs)

    # If an adapter function was provided we want to return certain
    # attributes of the function from the adapter rather than the
    # wrapped function so things like inspect.getargspec() will reflect
    # the prototype of the adapter and not the wrapped function.

    @property
    def __code__(self):
        if self._self_adapter:
            return self._self_adapter.__code__
        return self.__wrapped__.__code__

    @property
    def __defaults__(self):
        if self._self_adapter:
            return self._self_adapter.__defaults__
        return self.__wrapped__.__defaults__

    @property
    def __kwdefaults__(self):
        if self._self_adapter:
            return self._self_adapter.__kwdefaults__
        return self.__wrapped__.__kwdefaults__

    if six.PY2:
        func_code = __code__
        func_defaults = __defaults__

    # If an adapter function was provided, we also want to override the
    # __signature__ attribute introduced in Python 3 so that we get the
    # correct result when using inspect.signature().

    @property
    def __signature__(self):
        if self._self_adapter:
            return self._self_adapter.__signature__
        return self.__wrapped__.__signature__

class _BoundFunctionWrapper(_FunctionWrapperBase):

    def __call__(self, *args, **kwargs):
        # As in this case we would be dealing with a classmethod or
        # staticmethod, then _self_instance will only tell us whether
        # when calling the classmethod or staticmethod they did it via an
        # instance of the class it is bound to and not the case where
        # done by the class type itself. We thus ignore _self_instance
        # and use the __self__ attribute of the bound function instead.
        # For a classmethod, this means instance will be the class type
        # and for a staticmethod it will be None. This is probably the
        # more useful thing we can pass through even though we loose
        # knowledge of whether they were called on the instance vs the
        # class type, as it reflects what they have available in the
        # decoratored function.

        instance = getattr(self.__wrapped__, '__self__', None)

        return self._self_wrapper(self.__wrapped__, instance, args, kwargs)

class _BoundMethodWrapper(_FunctionWrapperBase):

    def __call__(self, *args, **kwargs):
        if self._self_instance is None:
            # This situation can occur where someone is calling the
            # instancemethod via the class type and passing the instance
            # as the first argument. We need to shift the args before
            # making the call to the wrapper and effectively bind the
            # instance to the wrapped function using a partial so the
            # wrapper doesn't see anything as being different.

            instance, args = args[0], args[1:]
            wrapped = functools.partial(self.__wrapped__, instance)
            return self._self_wrapper(wrapped, instance, args, kwargs)

        return self._self_wrapper(self.__wrapped__, self._self_instance,
                args, kwargs)

class FunctionWrapper(_FunctionWrapperBase):

    def __init__(self, wrapped, wrapper, adapter=None):
        # We need to do special fixups on the args in the case of an
        # instancemethod where called via the class and the instance is
        # passed explicitly as the first argument. Defer to the
        # _BoundMethodWrapper for these specific fixups when we believe
        # it is likely an instancemethod. That is, anytime it isn't
        # classmethod or staticmethod.
        #
        # Note that there isn't strictly a fool proof method of knowing
        # which is occuring because if a decorator using this code wraps
        # other decorators and they are poorly implemented they can
        # throw away important information needed to determine it.
        #
        # Anyway, the best we can do is look at the original type of the
        # object which was wrapped prior to any binding being done and
        # see if it is an instance of classmethod or staticmethod. In
        # the case where other decorators are between us and them, if
        # they do not propagate the __class__  attribute so that the
        # isinstance() checks works, then likely this will do the wrong
        # thing where classmethod and staticmethod are used.
        #
        # Since it is likely to be very rare that anyone even puts
        # decorators around classmethod and staticmethod, likelihood of
        # that being an issue is very small, so we accept it and suggest
        # that those other decorators be fixed. It is also only an issue
        # if a decorator wants to actually do things with the arguments.

        if isinstance(wrapped, (classmethod, staticmethod)):
            bound_type = _BoundFunctionWrapper
        else:
            bound_type = _BoundMethodWrapper

        super(FunctionWrapper, self).__init__(wrapped, None, wrapper,
                adapter, bound_type)

try:
    from ._wrappers import (ObjectProxy, FunctionWrapper,
            _FunctionWrapperBase, _BoundFunctionWrapper, _BoundMethodWrapper)
except ImportError:
    pass

def _weak_function_proxy_callback(ref, proxy, callback):
    if proxy._self_expired:
        return

    proxy._self_expired = True

    # This could raise an exception. We let it propagate back and let
    # the weakref.proxy() deal with it, at which point it generally
    # prints out a short error message direct to stderr and keeps going.

    if callback is not None:
        callback(proxy)

class WeakFunctionProxy(ObjectProxy):

    __slots__ = ('_self_expired', '_self_instance')

    def __init__(self, wrapped, callback=None):
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
                _weak_function_proxy_callback, proxy=self,
                callback=callback)

        self._self_expired = False

        try:
            self._self_instance = weakref.ref(wrapped.__self__, _callback)

            super(WeakFunctionProxy, self).__init__(
                    weakref.proxy(wrapped.__func__, _callback))

        except AttributeError:
            self._self_instance = None

            super(WeakFunctionProxy, self).__init__(
                    weakref.proxy(wrapped, _callback))

    def __call__(self, *args, **kwargs):
        # We perform a boolean check here on the instance and wrapped
        # function as that will trigger the reference error prior to
        # calling if the reference had expired.

        instance = self._self_instance and self._self_instance()
        function = self.__wrapped__ and self.__wrapped__

        # If the wrapped function was originally a bound function, for
        # which we retained a reference to the instance and the unbound
        # function we need to rebind the function and then call it. If
        # not just called the wrapped function.

        if instance is None:
            return self.__wrapped__(*args, **kwargs)

        return function.__get__(instance, type(instance))(*args, **kwargs)
