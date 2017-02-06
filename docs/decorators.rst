Function Decorators
===================

The **wrapt** module provides various components, but the main reason that
it would be used is for creating decorators. This document covers the
creation of decorators and all the information needed to cover what you can
do within the wrapper function linked to your decorator.

Creating Decorators
-------------------

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

Decorators With Arguments
-------------------------

If you wish to implement a decorator which accepts arguments, then you can
wrap the definition of the decorator in a function closure. Any arguments
supplied to the outer function when the decorator is applied, will be
available to the inner wrapper when the wrapped function is called.

::

    import wrapt

    def with_arguments(myarg1, myarg2):
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        return wrapper

    @with_arguments(1, 2)
    def function():
        pass

If using Python 3, you can use the keyword arguments only syntax to force
use of keyword arguments when the decorator is used.

::

    import wrapt

    def with_keyword_only_arguments(*, myarg1, myarg2):
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        return wrapper

    @with_keyword_only_arguments(myarg1=1, myarg2=2)
    def function():
        pass

An alternative approach to using a function closure to allow arguments is
to use a class, where the wrapper function is the ``__call__()`` method of
the class.

::

    import wrapt

    class with_arguments(object):

        def __init__(self, myarg1, myarg2):
            self.myarg1 = myarg1
            self.myarg2 = myarg2

        @wrapt.decorator
        def __call__(self, wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

    @with_arguments(1, 2)
    def function():
        pass

In this case the wrapper function should also accept a ``self`` argument as
is normal for instance methods of a class. The arguments to the decorator
would then be accessed by the wrapper function from the class instance
created when the decorator was applied to the target function, via the
``self`` argument.

Using a class in this way has the added benefit that other functions can be
associated with the class providing for better encapsulation. The
alternative would have been to have the class be separate and use it in
conjunction with a function closure, where the class instance would have
been created as a local variable within the outer function when called.

Decorators With Optional Arguments
----------------------------------

Although opinion can be mixed about whether the pattern is a good one, if
the decorator arguments all have default values, it is also possible to
implement decorators which have optional arguments. This allows the
decorator to be applied with or without the arguments, with the brackets
being able to be dropped in the latter.

::

    import wrapt

    def with_optional_arguments(wrapped=None, myarg1=1, myarg2=2):
        if wrapped is None:
            return functools.partial(with_optional_arguments,
                    myarg1=myarg1, myarg2=myarg2)

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        return wrapper(wrapped)

    @with_optional_arguments(myarg1=1, myarg2=2)
    def function():
        pass

    @with_optional_arguments
    def function():
        pass

For this to be used in this way, it is a requirement that the decorator
arguments be supplied as keyword arguments.

If using Python 3, the requirement to use keyword only arguments can again
be enforced using the keyword only argument syntax.

::

    import wrapt

    def with_optional_arguments(wrapped=None, *, myarg1=1, myarg2=2):
        if wrapped is None:
            return functools.partial(with_optional_arguments,
                    myarg1=myarg1, myarg2=myarg2)

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        return wrapper(wrapped)

Processing Function Arguments
-----------------------------

The original set of positional arguments and keyword arguments supplied when
the decorated function is called will be passed in the ``args`` and
``kwargs`` arguments.

Note that these are always passed as their own unique arguments and are not
broken out and bound in any way to the decorator wrapper arguments. In
other words, the decorator wrapper function signature must always be::

    @wrapt.decorator
    def my_decorator(wrapped, instance, args, kwargs): # CORRECT
        return wrapped(*args, **kwargs)

You cannot use::

    @wrapt.decorator
    def my_decorator(wrapped, instance, *args, **kwargs): # WRONG
        return wrapped(*args, **kwargs)

nor can you specify actual named arguments to which ``args`` and ``kwargs``
would be bound.

::

    @wrapt.decorator
    def my_decorator(wrapped, instance, arg1, arg2): # WRONG
        return wrapped(arg1, arg2)

Separate arguments are used and no binding performed to avoid the
possibility of name collisions between the arguments passed to a decorated
function when called, and the names used for the ``wrapped`` and
``instance`` arguments. This can happen for example were ``wrapped`` and
``instance`` also used as keyword arguments by the wrapped function.

If needing to modify certain arguments being supplied to the decorated
function when called, you will thus need to trigger binding of the
arguments yourself. This can be done using a nested function which in turn
then calls the wrapped function::

    @wrapt.decorator
    def my_decorator(wrapped, instance, args, kwargs):
        def _execute(arg1, arg2, *_args, **_kwargs):

            # Do something with arg1 and arg2 and then pass the
            # modified values to the wrapped function. Use 'args'
            # and 'kwargs' on the nested function to mop up any
            # unexpected or non required arguments so they can
            # still be passed through to the wrapped function.

            return wrapped(arg1, arg2, *_args, **_kwargs)

        return _execute(*args, **kwargs)

If you do not need to modify the arguments being passed through to the
wrapped function, but still need to extract them so as to log them or
otherwise use them as input into some process you could instead use.

::

    @wrapt.decorator
    def my_decorator(wrapped, instance, args, kwargs):
        def _arguments(arg1, arg2, *args, **kwargs):
            return (arg1, arg2)

        arg1, arg2 = _arguments(*args, **kwargs)

        # Do something with arg1 and arg2 but still pass through
        # the original arguments to the wrapped function.

        return wrapped(*args, **kwargs)

You should not simply attempt to extract positional arguments from ``args``
directly because this will fail if those positional arguments were actually
passed as keyword arguments, and so were passed in ``kwargs`` with ``args``
being an empty tuple.

Note that in either case, the argument names used in the decorated function
would need to match the names mapped by the wrapper function. This is a
restriction which would need to be documented for the specific decorator to
ensure that users do not use arbitrary argument names which do not match.

Enabling/Disabling Decorators
-----------------------------

A problem with using decorators is that once added into code, the actions
of the wrapper function cannot be readily disabled. The use of the decorator
would have to be removed from the code, or the specific wrapper function
implemented in such a way as to check itself a flag indicating whether it
should do what is required, or simply call the original wrapped function
without doing anything.

To make the task of enabling/disabling the actions of a wrapper function
easier, such functionality is built in to ``wrapt.decorator``. The
feature operates at a couple of levels, but in all cases, the ``enabled``
option is used to ``wrapt.decorator``. This must be supplied as a keyword
argument and cannot be supplied as a positional argument.

In the first way in which this enabling feature can work, if it is supplied
a boolean value, then it will immediately control whether a wrapper is
applied around the function that the decorator was in turn applied to.

In other words, where the ``enabled`` option was ``True``, then the
decorator will still be applied to the target function and will operate as
normal.

::

    ENABLED = True

    @wrapt.decorator(enabled=ENABLED)
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    def function():
        pass

    >>> type(function)
    <type 'FunctionWrapper'>

If however the ``enabled`` option was ``False``, then no wrapper is added
to the target function and the original function returned instead.

::

    ENABLED = False

    @wrapt.decorator(enabled=ENABLED)
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    def function():
        pass

    >>> type(function)
    <type 'function'>

In this scenario, as no wrapper is applied there is no runtime overhead
at the point of call when the decorator had been disabled. This therefore
provides a convenient way of globally disabling a specific decorator
without having to remove all uses of the decorator, or have a special
variant of the decorator function.

Dynamically Disabling Decorators
--------------------------------

Supplying a boolean value for the ``enabled`` option when defining a
decorator provides control over whether the decorator should be applied or
not. This is therefore a global switch and once disabled it cannot be
dynamically re-enabled at runtime while the process is executing.
Similarly, once enabled it cannot be disabled.

An alternative to supplying a literal boolean, is to provide a callable
for ``enabled`` which will yield a boolean value.

::

    def _enabled():
        return True

    @wrapt.decorator(enabled=_enabled)
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

When a callable function is supplied in this way, the callable will be
invoked each time the decorated function is called. If the callable returns
``True``, indicating that the decorator is active, the wrapper function
will then be called. If the callable returns ``False`` however, the wrapper
function will be bypassed and the original wrapped function called directly.

If ``enabled`` is not ``None``, nor a boolean, or a callable, then a
boolean check will be done on the object supplied instead. This allows one
to use a custom object which supports logical operations. If the custom
object evaluates as ``False`` the wrapper function will again be bypassed.

Function Argument Specifications
--------------------------------

To obtain the argument specification of a decorated function the standard
``getargspec()`` function from the ``inspect`` module can be used.

::

    @wrapt.decorator
    def my_decorator(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @my_decorator
    def function(arg1, arg2):
        pass

    >>> print(inspect.getargspec(function))
    ArgSpec(args=['arg1', 'arg2'], varargs=None, keywords=None, defaults=None)

If using Python 3, the ``getfullargspec()`` or ``signature()`` functions
from the ``inspect`` module can also be used.

In other words, applying a decorator created using ``@wrapt.decorator`` to
a function is signature preserving and does not result in the loss of the
original argument specification as would occur when more simplistic
decorator patterns are used.

Wrapped Function Documentation
------------------------------

To obtain documentation for a decorated function which may be specified in
a documentation string of the original wrapped function, the standard
Python help system can be used.

::

    @wrapt.decorator
    def my_decorator(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @my_decorator
    def function(arg1, arg2):
        """Function documentation."""
        pass

    >>> help(function)
    Help on function function in module __main__:

    function(arg1, arg2)
        Function documentation.

Just the documentation string itself can still be obtained by accessing the
``__doc__`` attribute of the decorated function.

::

    >>> print(function.__doc__)
    Function documentation.

Wrapped Function Source Code
----------------------------

To obtain the source code of a decorated function the standard
``getsource()`` function from the ``inspect`` module can be used.

::

    @wrapt.decorator
    def my_decorator(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @my_decorator
    def function(arg1, arg2):
        pass

    >>> print(inspect.getsource(function))
    @my_decorator
    def function(arg1, arg2):
        pass

As with signatures, the use of the decorator does not prevent access to the
original source code for the wrapped function.

Signature Changing Decorators
-----------------------------

When using ``inspect.getargspec()`` the argument specification for the
original wrapped function is returned. If however the decorator is a
signature changing decorator, this is not going to be what is desired.

In this circumstance it is necessary to pass a dummy function to the
decorator via the optional ``adapter`` argument. When this is done, the
argument specification will be sourced from the prototype for this dummy
function.

::

    def _my_adapter_prototype(arg1, arg2): pass

    @wrapt.decorator(adapter=_my_adapter_prototype)
    def my_adapter(wrapped, instance, args, kwargs):
        """Adapter documentation."""

        def _execute(arg1, arg2, *_args, **_kwargs):

            # We actually multiply the first two arguments together
            # and pass that in as a single argument. The prototype
            # exposed by the decorator is thus different to that of
            # the wrapped function.

            return wrapped(arg1*arg2, *_args, **_kwargs)

        return _execute(*args, **kwargs)

    @my_adapter
    def function(arg):
        """Function documentation."""

        pass

    >>> help(function)
    Help on function function in module __main__:

    function(arg1, arg2)
        Function documentation.

As it would not be accidental that you applied such a signature changing
decorator to a function, it would normally be the case that such usage
would be explained within the documentation for the wrapped function. As
such, the documentation for the wrapped function is still what is used for
the ``__doc__`` string and what would appear when using the Python help
system. In the latter, the arguments required of the adapter would though
instead appear.

Decorating Functions
--------------------

When applying a decorator to a normal function, the ``instance`` argument
would always be ``None``.

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    def function(arg1, arg2):
        pass

    function(1, 2)

Decorating Instance Methods
---------------------------

When applying a decorator to an instance method, the ``instance`` argument
will be the instance of the class on which the instance method is called.
That is, it would be the same as ``self`` passed as the first argument to
the actual instance method.

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    class Class(object):

        @pass_through
        def function_im(self, arg1, arg2):
            pass

    c = Class()

    c.function_im(1, 2)

    Class.function_im(c, 1, 2)

Note that the ``self`` argument is only passed via ``instance``, it is not
passed as part of ``args``. Only the arguments following on from the ``self``
argument will be a part of args.

When calling the wrapped function in the decorator wrapper function, the
``instance`` should never be passed explicitly though. This is because the
instance is already bound to ``wrapped`` and will be passed automatically
as the first argument to the original wrapped function.

This is even the situation where the instance method was called via the
class type and the ``self`` pointer passed explicitly. This is the case
as the decorator identifies this specific case and adjusts ``instance``
and ``args`` so that the decorator wrapper function does not see it as
being any different to where it was called directly on the instance.

Decorating Class Methods
------------------------

When applying a decorator to a class method, the ``instance`` argument will
be the class type on which the class method is called. That is, it would be
the same as ``cls`` passed as the first argument to the actual class
method.

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    class Class(object):

        @pass_through
        @classmethod
        def function_cm(cls, arg1, arg2):
            pass

    Class.function_cm(1, 2)

Note that the ``cls`` argument is only passed via ``instance``, it is not
passed as part of ``args``. Only the arguments following on from the ``cls``
argument will be a part of args.

When calling the wrapped function in the decorator wrapper function, the
``instance`` should never be passed explicitly though. This is because the
instance is already bound to ``wrapped`` and will be passed automatically
as the first argument to the original wrapped function.

Note that due to a bug in Python ``classmethod.__get__()``, whereby it does
not apply the descriptor protocol to the function wrapped by ``@classmethod``,
the above only applies where the decorator wraps the ``@classmethod``
decorator. If the decorator is placed inside of the ``@classmethod``
decorator, then ``instance`` will be ``None`` and the decorator wrapper
function will see the call as being the same as a normal function. As a
result, always place any decorator outside of the ``@classmethod``
decorator. Hopefully this issue in Python can be addressed in a future
Python version.

Decorating Static Methods
-------------------------

When applying a decorator to a static method, the ``instance`` argument
will be ``None``. In other words, the decorator wrapper function will not
be able to distinguish a call to a static method from a normal function.

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    class Class(object):

        @pass_through
        @staticmethod
        def function_sm(arg1, arg2):
            pass

    Class.function_sm(1, 2)

Decorating Classes
------------------

When applying a decorator to a class, the ``instance`` argument will be
``None``. In order to distinguish this case from a normal function call,
``inspect.isclass()`` should be used on ``wrapped`` to determine if it
is a class type.

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    class Class(object):
        pass

    c = Class()

Do note that whenever decorating a class, as you are replacing the aliased
name for the class with a wrapper, it will complicate use of the class in
cases where the original type is required.

In particular, if using ``super()``, it is necessary to supply the original
type and the wrapper cannot be used. It will therefore be necessary to use
the ``__wrapped__`` attribute to get access to the original type, as in:

::

    @pass_through
    class Class(BaseClass):
        def __init__(self):
            super(Class.__wrapped__, self).__init__()

In this case one could also use:

::

    @pass_through
    class Class(BaseClass):
        def __init__(self):
            BaseClass.__init__(self)

but in general, use of ``super()`` in conjunction with the ``__wrapped__``
attribute to get access to the original type is still recommended.

If using Python 3, the issue can be avoided by simply using the new magic
``super()`` calling convention whereby the type and ``self`` argument are
not required.

::

    @pass_through
    class Class(BaseClass):
        def __init__(self):
            super().__init__()

The need for the new magic ``super()`` in Python 3 was actually in part
driven by this specific case where the class type can have a decorator
applied.

Universal Decorators
--------------------

A universal decorator is one that can be applied to different types of
functions and can adjust automatically based on what is being decorated.

For example, the decorator may be able to be used on both a normal
function and an instance method, thereby avoiding the need to create two
separate decorators to be used in each case.

A universal decorator can be created by observing what has been stated
above in relation to the expected values/types for ``wrapped`` and
``instance`` passed to the decorator wrapper function.

These rules can be summarised by the following.

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

To be truly robust, if a universal decorator is being applied in a
scenario it does not support, it should raise a runtime exception
at the point it is called.
