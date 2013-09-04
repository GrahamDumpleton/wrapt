"""This module implements decorators for implementing other decorators.

"""

from . import six

from functools import wraps, partial
from inspect import getargspec, ismethod
from collections import namedtuple

if not six.PY2:
    from inspect import signature

from .wrappers import FunctionWrapper, ObjectProxy

# Object proxy for the wrapped function which will overlay certain
# properties from the adapter function onto the wrapped function so that
# functions such as inspect.getargspec(), inspect.getfullargspec(),
# inspect.signature() and inspect.getsource() return the correct results
# one would expect.

class _AdapterFunctionCode(ObjectProxy):

    def __init__(self, wrapped_code, adapter_code):
        super(_AdapterFunctionCode, self).__init__(wrapped_code)
        self._self_adapter_code = adapter_code

    @property
    def co_argcount(self):
        return self._self_adapter_code.co_argcount

    @property
    def co_code(self):
        return self._self_adapter_code.co_code

    @property
    def co_flags(self):
        return self._self_adapter_code.co_flags

    @property
    def co_kwonlyargcount(self):
        return self._self_adapter_code.co_kwonlyargcount

    @property
    def co_varnames(self):
        return self._self_adapter_code.co_varnames

class _AdapterFunction(ObjectProxy):

    def __init__(self, wrapped, adapter):
        super(_AdapterFunction, self).__init__(wrapped)
        self._self_adapter = adapter

    @property
    def __code__(self):
        return _AdapterFunctionCode(self._self_wrapped.__code__,
                self._self_adapter.__code__)

    @property
    def __defaults__(self):
        return self._self_adapter.__defaults__

    @property
    def __kwdefaults__(self):
        return self._self_adapter.__kwdefaults__

    @property
    def __signature__(self):
        if six.PY2:
            return self._self_adapter.__signature__
        else:
            # Can't allow this to fail on Python 3 else it falls
            # through to using __wrapped__, but that will be the
            # wrong function we want to derive the signature
            # from. Thus generate the signature ourselves.

            return signature(self._self_adapter)

    if six.PY2:
        func_code = __code__
        func_defaults = __defaults__

# Decorator for creating other decorators. This decorator and the
# wrappers which they use are designed to properly preserve any name
# attributes, function signatures etc, in addition to the wrappers
# themselves acting like a transparent proxy for the original wrapped
# function so the wrapper is effectively indistinguishable from the
# original wrapped function.

def decorator(wrapper=None, adapter=None):
    # The decorator should be supplied with a single positional argument
    # which is the wrapper function to be used to implement the
    # decorator. This may be preceded by a step whereby the keyword
    # arguments are supplied to customise the behaviour of the
    # decorator. The 'adapter' argument is currently the only such
    # keyword argument and is used to optionally denote a separate
    # function which is notionally used by an adapter decorator. In that
    # case parts of the function '__code__' and '__defaults__'
    # attributes are used from the adapter function rather than those of
    # the wrapped function. This allows for the argument specification
    # from inspect.getargspec() to be overridden with a prototype for a
    # different function than what was wrapped.

    if wrapper is not None:
        # The wrapper has been provided so return the final decorator.

        @wraps(wrapper)
        def _wrapper(func):
            _adapter = adapter and _AdapterFunction(func, adapter)
            result = FunctionWrapper(wrapped=func, wrapper=wrapper,
                    adapter=_adapter)
            return result
        _wrapper.__wrapped__ = wrapper
        return _wrapper

    else:
        # The wrapper still has not been provided, so we are just
        # collecting the optional keyword arguments. Return the
        # decorator again wrapped in a partial using the collected
        # arguments.

        return partial(decorator, adapter=adapter)
