"""This module implements decorators for implementing other decorators.

"""

from functools import wraps, partial
from inspect import getargspec

from .wrappers import DynamicWrapper, FunctionWrapper, MethodWrapper
from .exceptions import (UnexpectedDefaultParameters, MissingDefaultParameter,
        UnexpectedParameters)

def _decorator_factory(wrapper_type):
    # This decorator factory serves as a way of parameterising our
    # decorators based on the wrapper type. The wrapper type determines
    # whether or not descriptor behaviour is supported and the number of
    # arguments which are then in turn passed to the wrapper function
    # supplied by the user, which implements their decorator. In other
    # words, it saves us from duplicating all of this code for the
    # different decorator types we provide for constructing the users
    # decorators.

    def _decorator_binder(wrapper=None, target=None, **default_params):
        # The binder works out whether the user decorator will have its
        # own parameters. Parameters for the user decorator must always
        # be specified using keyword arguments and must always have
        # defaults. The user cannot use 'wrapper' or 'adapter' for their
        # own parameters as we use them ourselves and so they are
        # effectively reserved. The 'wrapper' argument being how the
        # user's wrapper function is passed in. The 'adapter' argument
        # is used to optionally denote a function which is an adapter,
        # which changes the effective prototype of the wrapped function.
        # The latter is used to ensure that any function argument
        # specification returned by the final result of any decorator is
        # correct and reflects that of the adapter and not the wrapped
        # function.

        if wrapper is not None:
            # The wrapper has been provided, so we must also have any
            # optional default keyword parameters for the user decorator
            # at this point if they were supplied. Before constructing
            # the decorator we validate if the list of supplied default
            # parameters are actually the same as what the users wrapper
            # function expects.

            expected_arglist = wrapper_type.WRAPPER_ARGLIST
            complete_arglist = getargspec(wrapper).args

            received_names = set(default_params.keys())
            expected_names = complete_arglist[len(expected_arglist):]

            for name in expected_names:
                try:
                    received_names.remove(name)
                except KeyError:
                    raise MissingDefaultParameter('Expected value for '
                            'default parameter %r was not supplied for '
                            'decorator %r.' % (name, wrapper.__name__))
            if received_names:
                raise UnexpectedDefaultParameters('Unexpected default '
                        'parameters %r supplied for decorator %r.' % (
                        list(received_names), wrapper.__name__))

            # If we do have default parameters, the final decorator we
            # create needs to be constructed a bit differently as when
            # that decorator is used, it needs to accept parameters.
            # Those parameters need not be supplied, but at least an
            # empty argument list needs to be used on the decorator at
            # that point. When parameters are supplied, they can be as
            # either positional or keyword arguments.

            if len(complete_arglist) > len(expected_arglist):
                # For the case where the decorator is able to accept
                # parameters, return a partial wrapper to collect the
                # parameters.

                @wraps(wrapper)
                def _partial(*decorator_args, **decorator_kwargs):
                    # Since the supply of parameters is optional due to
                    # having defaults, we need to construct a final set
                    # of parameters by overlaying those finally supplied
                    # to the decorator at the point of use over the
                    # defaults. As we accept positional parameters, we
                    # need to translate those back to keyword parameters
                    # in the process. This allows us to pass just one
                    # dictionary of parameters and we can validate the
                    # set of parameters at the point the decorator is
                    # used and not only let it fail at the time the
                    # wrapped function is called.

                    if len(decorator_args) > len(expected_names):
                        raise UnexpectedParameters('Expected at most %r '
                                'positional parameters for decorator %r, '
                                'but received %r.' % (len(expected_names),
                                 wrapper.__name__, len(decorator_args)))

                    unexpected_params = []
                    for name in decorator_kwargs:
                        if name not in default_params:
                            unexpected_params.append(name)

                    if unexpected_params:
                        raise UnexpectedParameters('Unexpected parameters '
                                '%r supplied for decorator %r.' % (
                                unexpected_params, wrapper.__name__))

                    complete_params = dict(default_params)

                    for i, arg in enumerate(decorator_args):
                        if expected_names[i] in decorator_kwargs:
                            raise UnexpectedParameters('Positional parameter '
                                    '%r also supplied as keyword parameter '
                                    'to decorator %r.' % (expected_names[i],
                                    wrapper.__name__))
                        decorator_kwargs[expected_names[i]] = arg

                    complete_params.update(decorator_kwargs)

                    # Now create and return the final wrapper which
                    # combines the parameters with the wrapped function.

                    def _wrapper(func):
                        return wrapper_type(wrapped=func, wrapper=wrapper,
                                target=target, params=complete_params)
                    return _wrapper

                # Here is where the partial wrapper is returned. This is
                # effectively the users decorator.

                return _partial

            else:
                # No parameters so create and return the final wrapper.
                # This is effectively the users decorator.

                @wraps(wrapper)
                def _wrapper(func):
                    return wrapper_type(wrapped=func, wrapper=wrapper,
                            target=target)
                return _wrapper

        else:
            # The wrapper still has not been provided, so we are just
            # collecting the optional default keyword parameters for the
            # users decorator at this point. Return the binder again as
            # a partial using the collected default parameters and the
            # adapter function if one is being used.

            return partial(_decorator_binder, target=target,
                    **default_params)

    # Override the binder function name to assist debugging.

    _decorator_binder.__name__ = 'decorator(%s)' % wrapper_type.__name__

    return _decorator_binder

decorator = _decorator_factory(DynamicWrapper)
function_decorator = _decorator_factory(FunctionWrapper)
method_decorator = _decorator_factory(MethodWrapper)

def adapter(target):
    @decorator(target=target)
    def wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)
    return wrapper
