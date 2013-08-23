"""This module implements decorators for implementing other decorators.

"""

from functools import wraps, partial
from inspect import getargspec

from .wrappers import FunctionWrapper
from .exceptions import (MissingParameter, UnexpectedParameters)

# Copy name attributes from a wrapped function onto an wrapper. This is
# only used in mapping the name from the final wrapped function to which
# an adapter is applied onto the adapter itself. All other details come
# from the adapter function via the function wrapper so we don't update
# __dict__ or __wrapped__.

def _update_adapter(wrapper, target):
    for attr in ('__module__', '__name__', '__qualname__'):
        try:
            value = getattr(target, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapper, attr, value)

# Decorators for creating other decorators. These decorators and the
# wrappers which they use are designed to properly preserve any name
# attributes, function signatures etc, in addition to the wrappers
# themselves acting like a transparent proxy for the original wrapped
# function so the wrapper is effectively indistinguishable from the
# original wrapped function.

WRAPPER_ARGLIST = ('wrapped', 'instance', 'args', 'kwargs')

def decorator(wrapper=None, target=None):
    # The decorator takes some optional keyword parameters to change its
    # behaviour. The decorator works out whether parameters have been
    # passed based on whether the first positional argument, which is
    # the wrapper which implements the user decorator, has been
    # supplied. The 'target' argument is used to optionally denote a
    # function which is wrapped by an adapter decorator. In that case
    # the name attributes are copied from the target function rather
    # than those of the adapter function.

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

        wrapper_argspec = getargspec(wrapper)

        wrapper_arglist = wrapper_argspec.args
        wrapper_defaults = (wrapper_argspec.defaults and
                wrapper_arglist[-len(wrapper_argspec.defaults):] or [])

        if len(wrapper_arglist) > len(WRAPPER_ARGLIST):
            # For the case where the user decorator is able to accept
            # parameters, return a partial wrapper to collect the
            # parameters.

            @wraps(wrapper)
            def _partial(*decorator_args, **decorator_kwargs):
                # We need to construct a final set of parameters
                # by merging positional parameters with the
                # keyword parameters. This allows us to pass just
                # one dictionary of parameters. We can also
                # validate the set of parameters at this point so
                # that an error occurs when the decorator is used
                # and not only let it fail at the time the
                # wrapped function is called.

                expected_names = wrapper_arglist[len(WRAPPER_ARGLIST):]

                if len(decorator_args) > len(expected_names):
                    raise UnexpectedParameters('Expected at most %r '
                            'positional parameters for decorator %r, '
                            'but received %r.' % (len(expected_names),
                             wrapper.__name__, len(decorator_args)))

                unexpected_params = []
                for name in decorator_kwargs:
                    if name not in expected_names:
                        unexpected_params.append(name)

                if unexpected_params:
                    raise UnexpectedParameters('Unexpected parameters '
                            '%r supplied for decorator %r.' % (
                            unexpected_params, wrapper.__name__))

                for i, arg in enumerate(decorator_args):
                    if expected_names[i] in decorator_kwargs:
                        raise UnexpectedParameters('Positional parameter '
                                '%r also supplied as keyword parameter '
                                'to decorator %r.' % (expected_names[i],
                                wrapper.__name__))
                    decorator_kwargs[expected_names[i]] = arg

                received_names = set(wrapper_defaults)
                received_names.update(decorator_kwargs.keys())

                for name in expected_names:
                    if name not in received_names:
                        raise MissingParameter('Expected value for '
                                'parameter %r was not supplied for '
                                'decorator %r.' % (name, wrapper.__name__))

                # Now create and return the final wrapper which
                # combines the parameters with the wrapped function.

                def _wrapper(func):
                    result = FunctionWrapper(wrapped=func,
                            wrapper=wrapper, kwargs=decorator_kwargs)
                    if target:
                        _update_adapter(result, target)
                    return result
                return _wrapper

            # Here is where the partial wrapper is returned. This is
            # effectively the users decorator.

            return _partial

        else:
            # No parameters so create and return the final wrapper.
            # This is effectively the users decorator.

            @wraps(wrapper)
            def _wrapper(func):
                result = FunctionWrapper(wrapped=func, wrapper=wrapper)
                if target:
                    _update_adapter(result, target)
                return result
            return _wrapper

    else:
        # The wrapper still has not been provided, so we are just
        # collecting the optional default keyword parameters for the
        # users decorator at this point. Return the decorator again as
        # a partial using the collected default parameters and the
        # adapter function if one is being used.

        return partial(decorator, target=target)

def adapter(target):
    @decorator(target=target)
    def wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)
    return wrapper
