Type Hinting
============

As of version 2.0.0, **wrapt** includes type hints for its public APIs to
improve interoperability with static type checkers (e.g. ``pyright``, ``mypy``).
The type metadata is available when running on Python 3.10 or later (the minimum
version the annotations target).

The type annotations aim to ensure type inference works correctly in the common
cases, but the dynamic nature of decorators and wrappers means that some
patterns cannot be expressed precisely. The type hints are designed to be
broadly compatible with the major type checkers, but there are some differences
in how they interpret certain constructs, so you may find that some things work
in one type checker but not another. In some situations you may still
need to add explicit annotations yourself, sometimes by introducing small
helper functions to guide the type checker.

Of the type checkers, ``pyright`` used within VS Code Pylance extension gives
the best experience, and ``mypy`` fails to work correctly in many situations.
This appears to be due to limitations in ``mypy`` rather than issues with the
**wrapt** type hints.

Always ensure you are using the most up to date version of a type checking tool.
If you encounter any issues, please report them on the **wrapt** issue tracker
so they can be investigated and suggested workarounds or fixes can be provided.

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

    from typing import Any, Callable, ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")

    @wrapt.decorator
    def pass_through(
        wrapped: Callable[P, R],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> R:
        return wrapped(*args, **kwargs)

    @pass_through
    def add(a: int, b: int) -> int:
        return a + b

    result: int = add(2, 3)

In this example, because the decorator simply passes through the call to the
wrapped function and is intended to be generic, it is necessary to use
``ParamSpec`` and ``TypeVar`` to express that the decorator can be applied to
functions with any signature and return type. The ``wrapped`` parameter is
annotated with ``Callable[P, R]`` to indicate that it accepts the same parameters
as the decorated function and returns the same type. The ``instance``, ``args``,
and ``kwargs`` parameters are annotated with appropriate generic types. The
return type of the decorator is annotated as ``R`` to match the return type of
the wrapped function.

With the type hints as shown, the type checker should be able to validate both the
arguments supplied to the decorated function and its return value at the point
it is being called. For example, the type checker will flag incorrect argument
types or an incompatible assigned result as in the following.

::

    result: str = add("hello", "world")  # Error: incompatible types

When ``@decorator`` or ``@function_wrapper`` are applied to a wrapper function,
the type checker should give an error when the return type of the wrapper
function is incompatible with the returned type given for the wrapped function.

The type checker will in some circumstances not appear to correctly verify that
the number and type of arguments of the wrapper function itself are what is
expected because of the decorators being able to be applied to a class, a class
instance, instance methods, class methods and normal functions. Thus there are
multiple valid signatures for the wrapper function depending on the context in
which the decorator is applied. As such, it may look like it does not flag
incorrect arguments as it matches a different but still valid signature.
    
No type checking is performed when the custom decorator is applied to a
function. This is because the decorator can be applied to any callable with
any signature, and the type checker cannot determine the correct signature
to use for the decorated function.

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
at runtime), the **wrapt** type hints will not work, and so you must use a
helper function.

::

    def adapter_prototype(i: int) -> str: ...

    def int_to_str(wrapped: Callable[[int], int]) -> Callable[[int], str]:
        @wrapt.decorator(adapter=adapter_prototype)
        def wrapper(
            wrapped: Callable[[int], int],
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

In this version the outer helper function constructs the decorator and
added explicit type hints to its parameters and return type. This allows the
type checker to validate calls to the decorated function and propagate the
correct return type.

Note that inside the decorator body the ``wrapped`` callable is annotated
with signature of the functions to be wrapped. The return type of the wrapper
function does however need to be ``Any``. You could just as well omit
those inner annotations as what matters for most static checking is the
user facing signature exposed by the outer helper function.

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
such as ``issubclass()`` due to not recognising the decorated class as a
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
