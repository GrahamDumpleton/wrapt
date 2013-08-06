import functools

from . import six

class WrapperOverrideMethods(object):

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

class WrapperBaseMetaType(type):
     def __new__(cls, name, bases, dictionary):
         # We use properties to override the values of __module__ and
         # __doc__. If we add these in WrapperBase, the derived class
         # __dict__ will still be setup to have string variants of these
         # attributes and the rules of descriptors means that they
         # appear to take precedence over the properties in the base
         # class. To avoid that, we copy the properties into the derived
         # class type itself via a meta class. In that way the
         # properties will always take precedence.

         dictionary.update(vars(WrapperOverrideMethods))
         return type.__new__(cls, name, bases, dictionary)

class WrapperBase(six.with_metaclass(WrapperBaseMetaType)):

    def __init__(self, wrapped, wrapper, adapter=None, params={}):
        self._self_wrapped = wrapped
        self._self_wrapper = wrapper
        self._self_params = params

        # Python 3.2+ has the __wrapped__ attribute which is meant to
        # hold a reference to the inner most wrapped object when there
        # are multiple decorators. We handle __wrapped__ and also
        # duplicate that functionality for Python 2, although it will
        # only go as far as what is below our own wrappers when there is
        # more than one for Python 2.

        if adapter is None:
            try:
                self._self_target = wrapped.__wrapped__
            except AttributeError:
                self._self_target = wrapped
        else:
            self._self_target = adapter

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
        return self._self_target

    @__wrapped__.setter
    def __wrapped__(self, value):
        self._self_wrapped.__wrapped__ = value

    def __self__(self):
        return self._self_wrapped.__self__

    def __dir__(self):
        return dir(self._self_wrapped)

    def __eq__(self, other):
        return self._self_target == other

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash(self._self_target)

    def __repr__(self):
        return '<%s for %s>' % (type(self).__name__, str(self._self_target))

    def __enter__(self):
        return self._self_wrapped.__enter__()

    def __exit__(self, *args, **kwargs):
        return self._self_wrapped.__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self._self_wrapped)

class BoundGenericWrapper(WrapperBase):

    def __init__(self, wrapped, obj, cls, wrapper, adapter=None,
            params={}):
        self._self_object = obj
        self._self_class = cls
        super(BoundGenericWrapper, self).__init__(wrapped=wrapped,
                wrapper=wrapper, adapter=adapter, params=params)

    def __call__(self, *args, **kwargs):
        if self._self_object is None:
            # We need to try and identify the specific circumstances
            # this occurs under. There are two possibilities. The first
            # is that someone is calling an instance method via the
            # class type and passing the instance as the first argument.
            # The second is that a class method is being called via the
            # class type, in which case there is no instance.
            #
            # There isn't strictly a fool proof method of knowing which
            # is occuring, because if our decorator wraps another
            # decorator that uses a descriptor and it isn't implemented
            # properly so as to provide __self__, then information by
            # which it can be determined can be lost.

            try:
                if self._self_wrapped.__self__ is None:
                    # Where __self__ is None, this indicates that an
                    # instance method is being called via the class type
                    # and the instance is passed in as the first
                    # argument. We need to shift the args before making
                    # the call to the wrapper and effectively bind the
                    # instance to the wrapped function using a partial
                    # so the wrapper doesn't see anything as being
                    # different when invoking the wrapped function.

                    obj, args = args[0], args[1:]
                    wrapped = functools.partial(self._self_wrapped, obj)
                    return self._self_wrapper(wrapped, obj, self._self_class,
                            args, kwargs, **self._self_params)

            except AttributeError, IndexError:
                pass

        return self._self_wrapper(self._self_wrapped,
                self._self_object, self._self_class, args, kwargs,
                **self._self_params)

class GenericWrapper(WrapperBase):

    WRAPPER_ARGLIST = ('wrapped', 'obj', 'cls', 'args', 'kwargs')

    def __get__(self, obj, cls):
        descriptor = self._self_wrapped.__get__(obj, cls)
        return BoundGenericWrapper(wrapped=descriptor, obj=obj, cls=cls,
                wrapper=self._self_wrapper, adapter=self._self_target,
                params=self._self_params)
        return result

    def __call__(self, *args, **kwargs):
        # This is invoked when the wrapped function is being called as a
        # normal function and is not bound to a class as a instance
        # method. This is also invoked in the case where the wrapped
        # function was a method, but this wrapper was in turn wrapped
        # using the staticmethod decorator.

        return self._self_wrapper(self._self_wrapped, None, None,
                args, kwargs, **self._self_params)

class FunctionWrapper(WrapperBase):

    WRAPPER_ARGLIST = ('wrapped', 'args', 'kwargs')

    def __call__(self, *args, **kwargs):
        return self._self_wrapper(self._self_wrapped, args, kwargs,
                **self._self_params)

class BoundInstanceMethodWrapper(WrapperBase):

    def __init__(self, wrapped, obj, cls, wrapper, adapter=None,
            params={}):
        self._self_object = obj
        self._self_class = cls
        super(BoundInstanceMethodWrapper, self).__init__(wrapped=wrapped,
                wrapper=wrapper, adapter=adapter, params=params)

    def __call__(self, *args, **kwargs):
        if self._self_object is None:
            # This situation can occur where someone is calling the
            # instancemethod via the class type and passing the instance
            # as the first argument. We need to shift the args before
            # making the call to the wrapper and effectively bind the
            # instance to the wrapped function using a partial so the
            # wrapper doesn't see anything as being different.

            obj, args = args[0], args[1:]
            wrapped = functools.partial(self._self_wrapped, obj)
            return self._self_wrapper(wrapped, obj, self._self_class,
                    args, kwargs, **self._self_params)

        else:
            return self._self_wrapper(self._self_wrapped, self._self_object,
                    self._self_class, args, kwargs, **self._self_params)

class InstanceMethodWrapper(WrapperBase):

    WRAPPER_ARGLIST = ('wrapped', 'obj', 'cls', 'args', 'kwargs')

    def __get__(self, obj, cls):
        descriptor = self._self_wrapped.__get__(obj, cls)
        return BoundInstanceMethodWrapper(wrapped=descriptor, obj=obj,
                cls=cls, wrapper=self._self_wrapper,
                adapter=self._self_target, params=self._self_params)
        return result
