Quick Start
===========

To implement your decorator you need to first define a wrapper function.
This will be called each time a decorated function is called. The wrapper
function needs to take four positional arguments:

* ``wrapped`` - The wrapped function which in turns needs to be called by your wrapper function.
* ``instance`` - The object to which the wrapped function was bound when it was called.
* ``args`` - The list of positional arguments supplied when the decorated function was called.
* ``kwargs`` - The dictionary of keyword arguments supplied when the decorated function was called.

The wrapper function would do whatever it needs to, but would usually in
turn call the wrapped function that is passed in via the ``wrapped``
argument.

The decorator ``@wrapt.decorator`` then needs to be applied to the wrapper
function to convert it into a decorator which can in turn be applied to
other functions.

::

    import wrapt
    
    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    def function():
        pass

If you wish to implement a decorator which accepts arguments, then list the
arguments after the existing four arguments of the wrapper function.

::

    import wrapt
    
    @wrapt.decorator
    def with_arguments(wrapped, instance, args, kwargs, myarg1, myarg2):
        return wrapped(*args, **kwargs)

    @with_arguments(1, 2)
    def function():
        pass

It is possible to use positional arguments, with or without default values,
a variable arguments list or a keyword argument dictionary.

Any arguments given to your decorator when it is used to decorate a
function, will be passed to the wrapper via the arguments added to the
wrapper function, when the wrapper is invoked upon the call of the
decorated function.

Note that even if all your decorator arguments have default values, or you
only have a variable arguments list or keyword argument dictionary, you
must still provide the parentheses to the decorator when used. Once you opt
to have the decorator be able to accept arguments the use of the
parentheses is not optional.

If using Python 3, you can use the keyword arguments only syntax to force
use of keyword arguments when the decorator is used.

::

    import wrapt
    
    @wrapt.decorator
    def with_keyword_only_arguments(wrapped, instance, args, kwargs, *, myarg1, myarg2):
        return wrapped(*args, **kwargs)

    @with_keyword_only_arguments(myarg1=1, myarg2=2)
    def function():
        pass
 
Any decorator you create can be applied to normal functions, instance
methods, class methods, static methods or classes.

When applied to a normal function or static method, the wrapper function
when called will be passed ``None`` as the ``instance`` argument.

When applied to an instance method, the wrapper function when called will
be passed the instance of the class the method is being called on as the
``instance`` argument. This will be the case even when the instance method
was called explicitly via the class and the instance passed as the first
argument. That is, the instance will never be passed as part of ``args``.

When applied to a class method, the wrapper function when called will be
passed the class type as the ``instance`` argument.

When applied to a class, the wrapper function when called will be passed
``None`` as the ``instance`` argument. The ``wrapped`` argument in this
case will be the class.

The above rules can be summarised with the following example.

::

    import inspect
    
    @wrapt.decorator
    def universal(wrapped, instance, args, kwargs):
        if instance is None:
            if inspect.isclass(wrapped):
                # Decorator was applied to a class.
                return wrapped(*args, **kwargs)
            else:
                # Decorator was applied to a function or staticmethod.
                return wrapped(*args, **kwargs)
        else:
            if inspect.isclass(instance):
                # Decorator was applied to a classmethod.
                return wrapped(*args, **kwargs)
            else:
                # Decorator was applied to an instancemethod.
                return wrapped(*args, **kwargs)

Using these checks it is therefore possible to create a universal decorator
that can be applied in all situations. It is no longer necessary to create
different variants of decorators for normal functions and instance methods,
or use additional wrappers to convert a function decorator into one that
will work for instance methods.

In all cases, the wrapped function passed to the wrapper function is called
in the same way, with ``args`` and ``kwargs`` being passed. The
``instance`` argument doesn't need to be used in calling the wrapped
function.
