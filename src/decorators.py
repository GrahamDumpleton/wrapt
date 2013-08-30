"""This module implements decorators for implementing other decorators.

"""

from functools import wraps, partial
from inspect import getargspec, ismethod
from collections import namedtuple

from .wrappers import FunctionWrapper, ObjectProxy

from . import six

# We must use inspect.getfullargspec() in Python 3 because of the
# possibility that decorators can be applied to functions with keyword
# only arguments. Create a version of getfulargspec() for Python 2 so we
# work against the same specification structure.

if six.PY2:
    FullArgSpec = namedtuple('FullArgSpec', 'args, varargs, varkw, ' \
            'defaults, kwonlyargs, kwonlydefaults, annotations')

    def getfullargspec(func):
        argspec = getargspec(func)
        return FullArgSpec(args=argspec.args, varargs=argspec.varargs,
                varkw=argspec.keywords, defaults=argspec.defaults,
                kwonlyargs=[], kwonlydefaults=None, annotations={})

else:
    from inspect import getfullargspec, signature

# Python 3 provides getcallargs() that could be used to validate the
# decorator parameters, but it would not be available in Python 2. Plus,
# we need to fiddle the result from getfullargspec() a bit as we are
# going to be using the argspec from the wrapper and not the decorator,
# so it has our standard wrapper arguments before what would be the
# decorator arguments. So we duplicate the code from Python 3 and tweak
# it a bit.

def _missing_arguments(f_name, argnames, pos, values):
    names = [repr(name) for name in argnames if name not in values]
    missing = len(names)
    if missing == 1:
        s = names[0]
    elif missing == 2:
        s = "{} and {}".format(*names)
    else:
        tail = ", {} and {}".format(names[-2:])
        del names[-2:]
        s = ", ".join(names) + tail
    raise TypeError("%s() missing %i required %s argument%s: %s" %
                    (f_name, missing,
                      "positional" if pos else "keyword-only",
                      "" if missing == 1 else "s", s))

def _too_many(f_name, args, kwonly, varargs, defcount, given, values):
    atleast = len(args) - defcount
    kwonly_given = len([arg for arg in kwonly if arg in values])
    if varargs:
        plural = atleast != 1
        sig = "at least %d" % (atleast,)
    elif defcount:
        plural = True
        sig = "from %d to %d" % (atleast, len(args))
    else:
        plural = len(args) != 1
        sig = str(len(args))
    kwonly_sig = ""
    if kwonly_given:
        msg = " positional argument%s (and %d keyword-only argument%s)"
        kwonly_sig = (msg % ("s" if given != 1 else "", kwonly_given,
                             "s" if kwonly_given != 1 else ""))
    raise TypeError("%s() takes %s positional argument%s but %d%s %s given" %
            (f_name, sig, "s" if plural else "", given, kwonly_sig,
             "was" if given == 1 and not kwonly_given else "were"))

def _validate_parameters(func, spec, *positional, **named):
    args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, ann = spec

    # We throw away the initial leading arguments as they are our
    # special wrapper arguments and not part of the arguments which
    # become the decorator arguments.

    args = args[len(WRAPPER_ARGLIST):]

    f_name = func.__name__
    arg2value = {}

    if ismethod(func) and func.__self__ is not None:
        # implicit 'self' (or 'cls' for classmethods) argument
        positional = (func.__self__,) + positional
    num_pos = len(positional)
    num_args = len(args)
    num_defaults = len(defaults) if defaults else 0

    n = min(num_pos, num_args)
    for i in range(n):
        arg2value[args[i]] = positional[i]
    if varargs:
        arg2value[varargs] = tuple(positional[n:])
    possible_kwargs = set(args + kwonlyargs)
    if varkw:
        arg2value[varkw] = {}
    for kw, value in named.items():
        if kw not in possible_kwargs:
            if not varkw:
                raise TypeError("%s() got an unexpected keyword argument %r" %
                                (f_name, kw))
            arg2value[varkw][kw] = value
            continue
        if kw in arg2value:
            raise TypeError("%s() got multiple values for argument %r" %
                            (f_name, kw))
        arg2value[kw] = value
    if num_pos > num_args and not varargs:
        _too_many(f_name, args, kwonlyargs, varargs, num_defaults,
                   num_pos, arg2value)
    if num_pos < num_args:
        req = args[:num_args - num_defaults]
        for arg in req:
            if arg not in arg2value:
                _missing_arguments(f_name, req, True, arg2value)
        for i, arg in enumerate(args[num_args - num_defaults:]):
            if arg not in arg2value:
                arg2value[arg] = defaults[i]
    missing = 0
    for kwarg in kwonlyargs:
        if kwarg not in arg2value:
            if kwarg in kwonlydefaults:
                arg2value[kwarg] = kwonlydefaults[kwarg]
            else:
                missing += 1
    if missing:
        _missing_arguments(f_name, kwonlyargs, False, arg2value)
    return arg2value

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

# Decorators for creating other decorators. These decorators and the
# wrappers which they use are designed to properly preserve any name
# attributes, function signatures etc, in addition to the wrappers
# themselves acting like a transparent proxy for the original wrapped
# function so the wrapper is effectively indistinguishable from the
# original wrapped function.

WRAPPER_ARGLIST = ('wrapped', 'instance', 'args', 'kwargs')

def decorator(wrapper=None, adapter=None, validate=True):
    # The decorator takes some optional keyword parameters to change its
    # behaviour. The decorator works out whether parameters have been
    # passed based on whether the first positional argument, which is
    # the wrapper which implements the user decorator, has been
    # supplied. The 'adapter' argument is used to optionally denote a
    # separate function which is notionally used by an adapter
    # decorator. In that case parts of the function '__code__' and
    # '__defaults__' attributes are used from the adapter function
    # rather than those of the wrapped function. This allows for the
    # argument specification from inspect.getargspec() to be overridden
    # with a prototype for a different function than what was wrapped.
    # The 'validate' argument, which defaults to True, indicates whether
    # validation of decorator parameters should be validated at the time
    # the decorator is applied, or whether a failure is allow to occur
    # only when the wrapped function is later called and the user
    # wrapper function thus called.

    if wrapper is not None:
        # We now need to work out whether the users decorator is
        # to take any arguments. If there are parameters, the
        # final decorator we create needs to be constructed a bit
        # differently, as when that decorator is used it needs to
        # accept parameters. Those parameters do not need to be
        # supplied if they have defaults, but at least an empty
        # argument list needs to be used on the decorator at that
        # point. When the users decorator parameters are
        # supplied, they can be as either positional or keyword
        # arguments.

        wrapper_argspec = getfullargspec(wrapper)

        if (len(wrapper_argspec.args) > len(WRAPPER_ARGLIST) or
                wrapper_argspec.varargs or wrapper_argspec.varkw or
                wrapper_argspec.kwonlyargs):

            # For the case where the user decorator is able to accept
            # parameters, return a partial wrapper to collect the
            # parameters.

            @wraps(wrapper)
            def _partial(*decorator_args, **decorator_kwargs):
                # Validate the set of decorator parameters at
                # this point so that an error occurs when the
                # decorator is used and not only when the
                # function is later called.

                if validate:
                    _validate_parameters(wrapper, wrapper_argspec,
                            *decorator_args, **decorator_kwargs)

                # Now create and return the final wrapper which
                # combines the parameters with the wrapped function.

                def _wrapper(func):
                    _adapter = adapter and _AdapterFunction(func, adapter)
                    result = FunctionWrapper(wrapped=func,
                            wrapper=wrapper, wrapper_args=decorator_args,
                            wrapper_kwargs=decorator_kwargs,
                            adapter=_adapter)
                    return result
                _wrapper.__wrapped__ = wrapper
                return _wrapper

            # Here is where the partial wrapper is returned. This is
            # effectively the users decorator.

            return _partial

        else:
            # No parameters so create and return the final wrapper.
            # This is effectively the users decorator.

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
        # collecting the optional default keyword parameters for the
        # users decorator at this point. Return the decorator again as
        # a partial using the collected default parameters and the
        # adapter function if one is being used.

        return partial(decorator, adapter=adapter, validate=validate)
