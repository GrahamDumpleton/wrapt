import functools

from . import six

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
        return self._self_wrapped.__module__

    @__module__.setter
    def __module__(self, value):
        self._self_wrapped.__module__ = value

    @property
    def __doc__(self):
        return self._self_wrapped.__doc__

    @__doc__.setter
    def __doc__(self, value):
        self._self_wrapped.__doc__ = value

    # We similar use a property for __dict__. We need __dict__ to be
    # explicit to ensure that vars() works as expected.

    @property
    def __dict__(self):
        return self._self_wrapped.__dict__

class _ObjectProxyMetaType(type):
     def __new__(cls, name, bases, dictionary):
         # Copy our special properties into the class so that they
         # always take precedence over attributes of the same name added
         # during construction of a derived class. This is to save
         # duplicating the implementation for them in all derived classes.

         dictionary.update(vars(_ObjectProxyMethods))

         return type.__new__(cls, name, bases, dictionary)

class ObjectProxy(six.with_metaclass(_ObjectProxyMetaType)):

    def __init__(self, wrapped):
        self._self_wrapped = wrapped

        # Python 3.2+ has the __qualname__ attribute, but it does not
        # allow it to be overridden using a property and it must instead
        # be an actual string object instead.

        try:
            object.__setattr__(self, '__qualname__', wrapped.__qualname__)
        except AttributeError:
            pass

        # Although __name__ can be overridden with a property in all
        # Python versions, updating it writes it back to an internal C
        # structure which can be accessed at C code level, so not sure
        # if overriding it as a property is sufficient in all cases.

        try:
            object.__setattr__(self, '__name__', wrapped.__name__)
        except AttributeError:
            pass

    def __setattr__(self, name, value):
        if name.startswith('_self_'):
            object.__setattr__(self, name, value)
        elif name in ('__name__', '__qualname__'):
            object.__setattr__(self, name, value)
            setattr(self._self_wrapped, name, value)
        else:
            setattr(self._self_wrapped, name, value)

    def __getattr__(self, name):
        return getattr(self._self_wrapped, name)

    @property
    def __class__(self):
        return self._self_wrapped.__class__

    @__class__.setter
    def __class__(self, value):
        self._self_wrapped.__class__ = value

    @property
    def __annotations__(self):
        return self._self_wrapped.__anotations__

    @__annotations__.setter
    def __annotations__(self, value):
        self._self_wrapped.__annotations__ = value

    @property
    def __wrapped__(self):
        try:
            return self._self_wrapped.__wrapped__
        except AttributeError:
            return self._self_wrapped

    @__wrapped__.setter
    def __wrapped__(self, value):
        self._self_wrapped.__wrapped__ = value

    def __dir__(self):
        return dir(self._self_wrapped)

    def __lt__(self, other):
        return self._self_wrapped < other

    def __gt__(self, other):
        return self._self_wrapped > other

    def __le__(self, other):
        return self._self_wrapped <= other

    def __ge__(self, other):
        return self._self_wrapped >= other

    def __eq__(self, other):
        return self._self_wrapped == other

    def __ne__(self, other):
        return self._self_wrapped != other

    def __nonzero__(self):
        return bool(self._self_wrapped)

    def __bool__(self):
        return bool(self._self_wrapped)

    def __hash__(self):
        return hash(self._self_wrapped)

    def __repr__(self):
        return '<%s for %s>' % (type(self).__name__, str(self._self_wrapped))

    def __enter__(self):
        return self._self_wrapped.__enter__()

    def __exit__(self, *args, **kwargs):
        return self._self_wrapped.__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self._self_wrapped)

    def __call__(self, *args, **kwargs):
        return self._self_wrapped(*args, **kwargs)

class _BoundFunctionWrapper(ObjectProxy):

    def __init__(self, wrapped, instance, wrapper, params={}):
        super(_BoundFunctionWrapper, self).__init__(wrapped)
        self._self_instance = instance
        self._self_wrapper = wrapper
        self._self_params = params

    def __call__(self, *args, **kwargs):
        return self._self_wrapper(self._self_wrapped, self._self_instance,
                args, kwargs, **self._self_params)

class _BoundMethodWrapper(ObjectProxy):

    def __init__(self, wrapped, instance, wrapper, params={}):
        super(_BoundMethodWrapper, self).__init__(wrapped)
        self._self_instance = instance
        self._self_wrapper = wrapper
        self._self_params = params

    def __call__(self, *args, **kwargs):
        if self._self_instance is None:
            # This situation can occur where someone is calling the
            # instancemethod via the class type and passing the instance
            # as the first argument. We need to shift the args before
            # making the call to the wrapper and effectively bind the
            # instance to the wrapped function using a partial so the
            # wrapper doesn't see anything as being different.

            instance, args = args[0], args[1:]
            wrapped = functools.partial(self._self_wrapped, instance)
            return self._self_wrapper(wrapped, instance, args, kwargs,
                    **self._self_params)

        return self._self_wrapper(self._self_wrapped, self._self_instance,
                args, kwargs, **self._self_params)

class FunctionWrapper(ObjectProxy):

    def __init__(self, wrapped, wrapper, params={}):
        super(FunctionWrapper, self).__init__(wrapped)
        self._self_wrapper = wrapper
        self._self_params = params

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
        # throw away important information needed to determine it. Some
        # ways that it could be determined in Python 2 are also not
        # possible in Python 3 due to the concept of unbound methods
        # being done away with.
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
        # For the case of a classmethod the class wouldn't be known
        # anyway, as it is only added in by the classmethod decorator
        # later.

        if isinstance(self._self_wrapped, (classmethod, staticmethod)):
            self._self_bound_type = _BoundFunctionWrapper
        else:
            self._self_bound_type = _BoundMethodWrapper

    def __get__(self, instance, owner):
        descriptor = self._self_wrapped.__get__(instance, owner)

        return self._self_bound_type(descriptor, instance, self._self_wrapper,
                self._self_params)

    def __call__(self, *args, **kwargs):
        # This is invoked when the wrapped function is being called as a
        # normal function and is not bound to a class as an instance
        # method. This is also invoked in the case where the wrapped
        # function was a method, but this wrapper was in turn wrapped
        # using the staticmethod decorator.

        return self._self_wrapper(self._self_wrapped, None, args,
                kwargs, **self._self_params)

try:
    from ._wrappers import ObjectProxy as C_ObjectProxy
    from ._wrappers import FunctionWrapper as C_FunctionWrapper
    PY_ObjectProxy = ObjectProxy
    ObjectProxy = C_ObjectProxy
    PY_FunctionWrapper = FunctionWrapper
    FunctionWrapper = C_FunctionWrapper
except ImportError:
    pass
