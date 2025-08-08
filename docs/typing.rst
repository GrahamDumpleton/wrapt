Type Hinting
============

As of version 2.0.0, **wrapt** provides inline type hints for its public APIs to
improve interoperability with static type checkers (e.g. ``mypy``). The type
metadata is available when running on Python 3.10 or later (the minimum version
the annotations target).

The annotations aim to be as precise as practical in order to maximise
inference quality and surface errors early. In some situations you may still
need to add explicit annotations yourself, sometimes by introducing small
helper wrapper functions to guide the type checker.

Certain advanced decorator and wrapper patterns enabled by **wrapt** are simply
too dynamic to express exactly in today's static type systems, so exhaustive
type checking cannot be applied there. The principal categories of limitations,
their underlying causes, and recommended workarounds are described in the
sections which follow.

Function Decorators
-------------------

The **wrapt** module exposes two helpers for authoring function decorators:
``@decorator`` and ``@function_wrapper``. ``@function_wrapper`` is a lightweight
subset of ``@decorator`` intended for straightforward function wrapping; it
omits the advanced extension points in exchange for a smaller, simpler
surface. We will use ``@decorator`` in this discussion of type hints, but
``@function_wrapper`` is also fully type hinted and can be used in a similar way.

The most basic example of a function decorator is:

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    def add(a, b):
        return a + b

    result = add(2, 3)

In this example, because no type hints are provided, the type checker will not
be able to infer the types of the function's parameters or return value.

Adding type hints, the example becomes:

::

    from typing import Any, Callable

    @wrapt.decorator  # <-- Type checking applied here.
    def pass_through(
        wrapped: Callable[[int, int], int],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> int:
        return wrapped(*args, **kwargs)

    @pass_through  # <-- Type checking not applied here (see below).
    def add(a: int, b: int) -> int:
        return a + b

    result: int = add(2, 3)  # <-- Type checking applied here.

Annotate ``wrapped`` with a ``Callable`` whose signature matches the functions you
intend to decorate. Leave ``instance`` as ``Any`` in most cases; if you need to be
stricter you can use ``Any | type[Any] | None``. You can narrow ``args`` / ``kwargs``
based on the accepted parameter types, but doing so rarely improves type
checking and usually adds noise, so the generic ``tuple[Any, ...]`` and
``dict[str, Any]`` forms are normally sufficient.

The wrapper's return type annotation should mirror the return type of the
wrapped function.

With the type hints added, the type checker can now validate both the
arguments supplied to the decorated function and its return value at the point
it is being called. For example, the type checker will flag incorrect argument
types or an incompatible assigned result as in the following.

::

    result: str = add("hello", "world")  # Error: incompatible types

Because a single **wrapt** decorator can be applied to both plain functions
and bound or class methods, there are practical limits to how precisely we can
match the call signatures. In particular, the implicit ``self`` / ``cls`` binding
for methods cannot be reconciled reliably with the standalone function
signature you must supply for ``wrapped``. While partial workarounds are
possible, they introduce fragility and false positives, so for now type
checking has been disabled at the point where the decorator is being applied
to a method or function.

Argument Matching
-----------------

Functions being decorated can have default arguments, and so long as the
decorator is aware of them, it can handle them correctly at runtime.
Unfortunately due to limitations in the type system, a type checker doesn't
recognise the default arguments of the wrapped function and so will indicate
an error when you don't still explicitly provide the argument, even though the
call will work fine at runtime.

::

    from typing import Any, Callable

    @wrapt.decorator
    def pass_through(
        wrapped: Callable[[int, int], int],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> int:
        return wrapped(*args, **kwargs)

    @pass_through
    def add(a: int, b: int = 0) -> int:
        return a + b

    result1: int = add(2, 3)

    # Error: type checker doesn't recognise default arguments.

    result2: int = add(2) # <-- Invalid error warning.

Type checkers also have issue with using keyword parameters, thus they will
wrongly flag use of keyword arguments even though at runtime it still works.

::

     # Error: type checker doesn't recognise keyword arguments.

    result3: int = add(2, b=3) # <-- Invalid error warning.

If using these patterns and you don't like see the errors, you will need to
flag the type checker to ignore them. For example, with ``mypy`` you can use
``# type: ignore`` comments to suppress the warnings:

Signature Adapters
------------------

Sometimes you want the decorated callable to present a different public
signature from the underlying implementation (for example, to narrow the
parameters, rename them, or enforce keyword-only usage). You can express this
using a signature adapter: a small prototype function whose only purpose is
to declare the outward-facing signature the wrapped function should appear to
have after decoration.

For instance, imagine the original function returns an integer, but you want
the decorated function to return a string. You would define a signature adapter
like this:

::

    def adapter_prototype(i: int) -> str: ...

    @wrapt.decorator(adapter=wrapt.adapter_factory(adapter_prototype))
    def int_to_str(wrapped, instance, args, kwargs):
        return str(wrapped(*args, **kwargs))

    @int_to_str
    def function(x) -> int:
        """A function that takes an integer and returns it."""
        return x

    result = function(1)

In this example we passed the prototype function itself via the ``adapter``
argument. **wrapt** also supports alternative forms: you can supply the
prototype as a string, or return a pre-formatted argument spec instead of a
callable.

Declaring the adapter explicitly ensures that runtime introspection
(``inspect.signature``, ``help()``, IDE tooling, etc.) reports the adapted
signature rather than the underlying implementation detail. Because the
adaptation is applied dynamically (and the prototype may itself be generated
at runtime), **wrapt** cannot reliably infer the target signature from the
wrapped function alone, and so you must provide it if you want accurate type
checking.

::

    def adapter_prototype(i: int) -> str: ...

    def int_to_str(wrapped: Callable[[int], int]) -> Callable[[int], str]:
        @wrapt.decorator(adapter=wrapt.adapter_factory(adapter_prototype))
        def wrapper(
            wrapped: Callable[..., Any],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return str(wrapped(*args, **kwargs))

        return wrapper(wrapped)

    @int_to_str
    def function(x: int) -> int:
        """A function that takes an integer and returns it."""
        return x

    result: str = function(1)

In this version we introduced an outer helper that constructs the decorator and
added explicit type hints to its parameters and return type. This allows the
type checker to validate calls to the decorated function and propagate the
correct return type.

Note that inside the decorator body the ``wrapped`` callable is annotated
as accepting any arguments and returning ``Any``. You could just as well omit
those inner annotations as what matters for most static checking is the
user facing signature exposed by the outer wrapper.

Decorating Classes
------------------

Decorators can be applied to classes as well as functions and methods. when
applied to a class, the decorator object effectively replaces the original.
With the way the **wrapt** decorator works, it is still possible to use the
decorated class as a base class in an inheritance hierarchy, however, this
confuses the type checker.

::

    @pass_through
    class BaseClass:
        def __init__(self): ...

    # Error: type checker doesn't recognise the class as a base class.

    class DerivedClass(BaseClass):  # <-- Invalid error warning.
        def __init__(self): ...

The type checker can also give invalid error warnings when using functions
such as `issubclass()` due to not recognising the decorated class as a
class type.

::

    # Error: type checker doesn't recognise the class as a base class.

    issubclass(DerivedClass, BaseClass) # <-- Invalid error warning.

Class as Decorator
------------------

Normally decorators are functions, but it is also possible to use a class as a
decorator. In this situation the wrapper function (``__call__()`` method of class)
is not type checked as it would be if the ``@decorator`` were being applied to it
directly. Further, the type checker cannot match the arguments for the
constructor of the class at the point it it is being created.

::

    @wrapt.decorator
    class ClassDecorator:
        def __init__(self, arg: str): ...

        # Error: type checker will not check arguments of wrapper function.

        def __call__(self, wrapped, instance, args, kwargs): ... # <-- Not checked.

    # Error: type checker doesn't recognise arguments correctly.

    @ClassDecorator("string") # <-- Invalid error warning.
    def function(): ...

Object Proxy
------------

Due to the magic of how the ``ObjectProxy`` class in **wrapt** works, you may find
that the type checker will generate errors about using it and the above are not
all the possible issues you may encounter. To allow for further investigation
and improvement of the type hints, please report any issues you find with
using **wrapt**. For more notable cases we can add at least add additional
documentation here with warnings or workarounds.
