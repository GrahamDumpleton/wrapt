Assorted Examples
=================

This document provides practical examples of decorators and proxy objects
built using the **wrapt** module. The patterns covered include tracking
state across invocations of a decorated function, validating arguments
against type annotations or caller-supplied value constraints, per-instance
thread synchronisation, and serialising proxy objects and decorated
callables with ``pickle`` or ``dill``. For details on the core decorator API and
wrapper function signature, see :doc:`decorators`. For details on the
``FunctionWrapper`` and other proxy types used in these examples, see
:doc:`wrappers`.

Tracking Call State
-------------------

A common requirement is to track state across invocations of a decorated
function. For example, counting how many times a function has been called.

A clean approach is to encapsulate both the state and the wrapper logic in a
class. The wrapper method is decorated with ``@wrapt.function_wrapper`` so
that it follows the standard ``wrapt`` wrapper function signature, with the
addition of ``self`` to access the tracker state. When used as a bound
method, ``wrapt`` will correctly handle the extra ``self`` argument.

The ``@wrapt.bind_state_to_wrapper`` descriptor decorator is applied on top
of ``@wrapt.function_wrapper``. It intercepts descriptor binding so that
when the wrapper method is accessed through an instance, the instance is
automatically stored on the resulting wrapper as a named attribute. The
``name`` keyword argument controls the attribute name (here ``"tracker"``).

By naming the wrapper method ``__call__``, each instance of the class
becomes a callable decorator. An instance is created each time the decorator
is applied, giving each decorated function its own independent state.

::

    import wrapt

    class CallTracker:
        def __init__(self):
            self.call_count = 0

        @wrapt.bind_state_to_wrapper(name="tracker")
        @wrapt.function_wrapper
        def __call__(self, wrapped, instance, args, kwargs):
            try:
                return wrapped(*args, **kwargs)
            finally:
                self.call_count += 1

The decorator can be applied to normal functions, instance methods, class
methods, and static methods. Each use of ``CallTracker()`` creates a fresh
instance with its own state.

::

    @CallTracker()
    def add(x, y):
        return x + y

    class Calculator:

        @CallTracker()
        def compute(self, x, y):
            return x + y

        @CallTracker()
        @classmethod
        def class_compute(cls, x, y):
            return x + y

        @CallTracker()
        @staticmethod
        def static_compute(x, y):
            return x + y

The tracker state can be accessed via the ``tracker`` attribute on the
decorated function.

::

    >>> add(1, 2)
    3
    >>> add(3, 4)
    7
    >>> add.tracker.call_count
    2

For methods on a class, the state can be accessed either via the class or
via an instance. Accessing via an instance works because attribute lookups on
bound function wrappers are delegated to the parent ``FunctionWrapper``.

::

    >>> calc = Calculator()
    >>> calc.compute(1, 2)
    3
    >>> calc.compute(3, 4)
    7
    >>> calc.compute.tracker.call_count
    2
    >>> Calculator.compute.tracker.call_count
    2

Since the tracker is stored on the ``FunctionWrapper`` and not on individual
instances, the call count is shared across all instances of the class.

::

    >>> calc1 = Calculator()
    >>> calc2 = Calculator()
    >>> calc1.compute(1, 2)
    3
    >>> calc2.compute(3, 4)
    7
    >>> calc1.compute.tracker.call_count
    2

The same pattern works for class methods and static methods.

::

    >>> Calculator.class_compute(1, 2)
    3
    >>> Calculator.class_compute.tracker.call_count
    1

    >>> Calculator.static_compute(1, 2)
    3
    >>> Calculator.static_compute.tracker.call_count
    1

For convenience, a static method can be added to provide a decorator that
accepts optional arguments. When called without arguments, the function is
wrapped directly. When called with keyword arguments, a configured
``CallTracker`` instance is returned, which then wraps the function in a
second step.

::

    class CallTracker:
        def __init__(self, *, call_count=0):
            self.call_count = call_count

        @wrapt.bind_state_to_wrapper(name="tracker")
        @wrapt.function_wrapper
        def __call__(self, wrapped, instance, args, kwargs):
            try:
                return wrapped(*args, **kwargs)
            finally:
                self.call_count += 1

        @staticmethod
        def track(func=None, /, *, call_count=0):
            tracker = CallTracker(call_count=call_count)
            if func is None:
                return tracker
            return tracker(func)

This allows both styles of usage.

::

    @CallTracker.track
    def add(x, y):
        return x + y

    @CallTracker.track(call_count=10)
    def add_starting_at_ten(x, y):
        return x + y

Checking Argument Types
-----------------------

The same state class pattern can be used to build a decorator that validates
the types of arguments passed to a wrapped function against the function's
type annotations. The state class here holds the decorated function's
signature, so that it is computed only once and reused on every call.

A key choice is *when* the signature is computed. Rather than deriving it
from the raw function at decoration time, it is derived from ``wrapped`` on
the first call and cached on the state instance. When ``wrapped`` is an
instance method, class method or static method, it has already been bound
by the descriptor protocol before the wrapper runs, so its signature does
not include ``self`` or ``cls``. Using ``wrapped`` removes the need for any
special handling of methods: the wrapper can bind ``args`` and ``kwargs``
to the signature directly.

::

    import inspect
    import wrapt

    class TypeChecker:
        def __init__(self):
            self.signature = None

        @wrapt.function_wrapper
        def __call__(self, wrapped, instance, args, kwargs):
            if self.signature is None:
                self.signature = inspect.signature(wrapped)
            bound = self.signature.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, value in bound.arguments.items():
                annotation = self.signature.parameters[name].annotation
                if annotation is inspect.Parameter.empty:
                    continue
                if not isinstance(value, annotation):
                    raise TypeError(
                        f"Argument {name!r} must be {annotation.__name__}, "
                        f"got {type(value).__name__}"
                    )
            return wrapped(*args, **kwargs)

        @staticmethod
        def check(func):
            return TypeChecker()(func)

    type_checker = TypeChecker.check

The static ``check`` method creates a fresh ``TypeChecker`` instance for
each decoration and uses it to wrap the function. A module level alias
``type_checker = TypeChecker.check`` lets callers write ``@type_checker``
without referring to the class. Unlike the ``CallTracker`` example, there
is no need for ``@wrapt.bind_state_to_wrapper`` because the state class
does not need to be accessible from outside the wrapper.

The decorator can be applied to normal functions, instance methods, class
methods and static methods. Arguments without an annotation are skipped, so
only those parameters that have been annotated are checked.

::

    @type_checker
    def add(x: int, y: int) -> int:
        return x + y

    class Calculator:

        @type_checker
        def compute(self, x: int, y: int) -> int:
            return x + y

        @type_checker
        @classmethod
        def class_compute(cls, x: int, y: int) -> int:
            return x + y

        @type_checker
        @staticmethod
        def static_compute(x: int, y: int) -> int:
            return x + y

A valid call returns the result as normal. A call whose argument type does
not match the annotation raises ``TypeError``.

::

    >>> add(1, 2)
    3
    >>> add(1, "2")
    Traceback (most recent call last):
      ...
    TypeError: Argument 'y' must be int, got str

Validating Argument Values
--------------------------

A related decorator validates argument *values* rather than their types.
Instead of relying on type annotations, the caller supplies a callable for
each parameter that should be checked. Each callable is a constraint that
must return a truthy value for the supplied argument, otherwise the
decorator raises ``ValueError``.

The implementation mirrors ``TypeChecker`` but takes its configuration from
the decoration site, so the static ``validate`` method uses the same
optional arguments pattern as ``CallTracker.track``. When called with
constraint keyword arguments, it returns a configured ``ValueChecker``
instance which then wraps the function.

::

    import inspect
    import wrapt

    class ValueChecker:
        def __init__(self, constraints):
            self.constraints = constraints
            self.signature = None

        @wrapt.function_wrapper
        def __call__(self, wrapped, instance, args, kwargs):
            if self.signature is None:
                self.signature = inspect.signature(wrapped)
            bound = self.signature.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, constraint in self.constraints.items():
                if name not in bound.arguments:
                    continue
                value = bound.arguments[name]
                if not constraint(value):
                    raise ValueError(
                        f"Argument {name!r} with value {value!r} failed "
                        f"constraint "
                        f"{getattr(constraint, '__name__', constraint)!s}"
                    )
            return wrapped(*args, **kwargs)

        @staticmethod
        def validate(func=None, /, **constraints):
            checker = ValueChecker(constraints=constraints)
            if func is None:
                return checker
            return checker(func)

    value_checker = ValueChecker.validate

Binding the arguments to the function signature serves two purposes. It
resolves positional arguments to their parameter names, so constraints
written in terms of parameter names work regardless of whether the caller
passed arguments positionally or by keyword. It also applies defaults, so
a constraint is still enforced when the caller omits an argument that has
a default value.

Constraints are ordinary callables that return true or false for a given
value.

::

    def is_positive(value):
        return value > 0

    @value_checker(x=is_positive, y=is_positive)
    def multiply(x, y):
        return x * y

    >>> multiply(2, 3)
    6
    >>> multiply(-1, 3)
    Traceback (most recent call last):
      ...
    ValueError: Argument 'x' with value -1 failed constraint is_positive

As with ``TypeChecker``, the decorator works on instance methods, class
methods and static methods without any special handling, because the
signature is taken from the already-bound ``wrapped`` on the first call.

The two decorators can be stacked on the same function, but only in one
order. ``type_checker`` must be applied as the outer (top) decorator so
that type validation runs before value validation. If the order is
reversed, a wrong-typed argument reaches the constraint callable first
and the constraint itself fails in whatever way it fails on unexpected
input. For example, comparing a string against zero raises ``TypeError``
from the ``>`` operator rather than a clear "must be ``int``" message
from ``TypeChecker``. With ``type_checker`` on top, type errors short
circuit the value checks and the intended error message is reported.

::

    @type_checker
    @value_checker(x=is_positive, y=is_positive)
    def scale(x: int, y: int) -> int:
        return x * y

    >>> scale(2, 3)
    6
    >>> scale(-1, 3)
    Traceback (most recent call last):
      ...
    ValueError: Argument 'x' with value -1 failed constraint is_positive
    >>> scale("a", 3)
    Traceback (most recent call last):
      ...
    TypeError: Argument 'x' must be int, got str

Serialising an Object Proxy
---------------------------

By default an instance of ``wrapt.ObjectProxy`` (or ``wrapt.BaseObjectProxy``)
cannot be pickled. The object proxy base classes define ``__reduce__`` such
that it raises ``NotImplementedError``. This is because there is no generic
way to pickle a proxy that would correctly capture both the wrapped object
and any additional state a proxy subclass may add on top of it. It is
therefore up to the user to define ``__reduce__`` on a proxy subclass to
indicate how its data should be saved and restored.

The same requirement applies to third party serialisers such as ``dill``
which extend and build on top of the standard library pickle protocol.
They rely on ``__reduce__`` in exactly the same way, and the base proxy
class's ``__reduce__`` raising ``NotImplementedError`` is not bypassed
by them. Defining ``__reduce__`` on a proxy subclass therefore makes it
serialisable with ``pickle``, ``dill`` and any other serialiser that
follows the pickle protocol.

Consider a proxy subclass which wraps a dict of computed statistics and
adds a ``label`` attribute alongside it.

::

    import wrapt

    class StatsProxy(wrapt.BaseObjectProxy):

        def __init__(self, wrapped, label):
            super().__init__(wrapped)
            self._self_label = label

        @property
        def label(self):
            return self._self_label

Proxy-local state is conventionally held in attributes named with a
``_self_`` prefix. Such attributes are stored on the proxy instance itself
rather than being forwarded to the wrapped object. Here ``_self_label``
holds the label that is specific to the proxy, while ``__wrapped__``
holds the dict being proxied.

Attempting to pickle an instance of ``StatsProxy`` as defined above will
fail with ``NotImplementedError`` coming from the base class. To make
the proxy pickleable, override ``__reduce__``.

::

    import pickle

    class StatsProxy(wrapt.BaseObjectProxy):

        def __init__(self, wrapped, label):
            super().__init__(wrapped)
            self._self_label = label

        @property
        def label(self):
            return self._self_label

        def __reduce__(self):
            return (type(self), (self.__wrapped__, self._self_label))

The ``__reduce__`` method returns a two-tuple. The first element is a
callable that pickle will invoke to recreate the object. In this case
that is the proxy class itself. The second element is the tuple of
arguments that will be passed to that callable. Here those arguments are
the wrapped object and the proxy-local ``label`` state, matching the
signature of ``__init__``. When the pickle stream is loaded, pickle will
reconstruct the wrapped dict first, then call
``StatsProxy(wrapped_dict, label)`` to rebuild the proxy around it.

Overriding ``__reduce__`` alone is sufficient. Pickle first calls
``__reduce_ex__``, and the default implementation inherited from
``object`` delegates to ``__reduce__`` whenever a subclass has overridden
it. There is therefore no need to override ``__reduce_ex__`` as well.

.. note::
    Prior to **wrapt** 2.2.0 this was not the case. Earlier versions of
    the object proxy base classes incorrectly overrode both
    ``__reduce__`` and ``__reduce_ex__`` to raise ``NotImplementedError``.
    Because the base class override of ``__reduce_ex__`` ran before the
    subclass's ``__reduce__`` could be consulted, a proxy subclass had
    to override both methods, with ``__reduce_ex__`` typically just
    delegating to ``__reduce__``::

        def __reduce_ex__(self, protocol):
            return self.__reduce__()

    This was fixed in **wrapt** 2.2.0 by removing the ``__reduce_ex__``
    override from the base classes, bringing the behaviour in line with
    the standard Python pickle contract where overriding ``__reduce__``
    alone is enough. Code that needs to work with both older and newer
    versions of **wrapt** should continue to define both methods, as
    defining ``__reduce_ex__`` in addition to ``__reduce__`` is harmless
    on the newer versions.

Note that the wrapped object must itself be pickleable, since pickle will
recursively pickle the arguments returned from ``__reduce__``. The same
applies to any proxy-local state included in the returned arguments.

With ``__reduce__`` defined, instances of ``StatsProxy`` can be pickled
and unpickled in the normal way, and the restored proxy will retain both
the wrapped object and the proxy-local state.

::

    >>> original = StatsProxy({"count": 3, "sum": 6}, label="demo")
    >>> data = pickle.dumps(original)
    >>> restored = pickle.loads(data)
    >>> restored.label
    'demo'
    >>> dict(restored)
    {'count': 3, 'sum': 6}

The same ``StatsProxy`` works unchanged with ``dill`` in place of
``pickle``. This is useful when the wrapped object contains values
that the standard library pickle module cannot handle, such as
lambdas, closures or nested functions. ``dill`` uses the same pickle
protocol for user defined types, so the ``__reduce__`` method defined
on the proxy is all that is needed to make the proxy serialisable.

There is however one extra consideration when using ``dill`` with a
proxy subclass. By default ``dill`` attempts to serialise classes and
functions by value, embedding their source in the output stream, rather
than by reference to their import path the way ``pickle`` does. This
does not work for a subclass of ``wrapt.BaseObjectProxy`` because the
proxy base class is ultimately backed by a C extension type and cannot
be reconstructed from a serialised class body. The ``dill.dump()`` (and
``dill.dumps()``) call must therefore be passed ``byref=True`` so that
``dill`` references the proxy class by its import path instead of
attempting to serialise it by value.

::

    import dill

    original = StatsProxy({"count": 3, "sum": 6}, label="demo")

    data = dill.dumps(original, byref=True)
    restored = dill.loads(data)

The same consideration applies at the module level via
``dill.settings["byref"] = True`` if ``byref`` is to be the default for
all ``dill`` operations in the process. Without ``byref=True`` the dump
step will fail.

Serialising a Decorator
-----------------------

The same technique used to make a subclass of ``BaseObjectProxy``
serialisable can be applied to ``FunctionWrapper``, which is the proxy
class ``wrapt`` uses to implement decorators. Making a decorated
function serialisable therefore comes down to defining ``__reduce__``
on a subclass of ``FunctionWrapper`` and using that subclass in a
decorator factory of your own.

``FunctionWrapper`` stores the wrapped callable at ``__wrapped__`` and
the user supplied wrapper function on the proxy itself as the
``_self_wrapper`` attribute. The rebuild recipe returned from
``__reduce__`` is therefore simply the same pair of arguments
``FunctionWrapper`` was constructed with in the first place.

::

    import wrapt

    class SerialisableFunctionWrapper(wrapt.FunctionWrapper):

        def __reduce__(self):
            return (type(self), (self.__wrapped__, self._self_wrapper))

    def serialisable_decorator(wrapper):
        def _decorator(wrapped):
            return SerialisableFunctionWrapper(wrapped, wrapper)
        return _decorator

This is all that is needed to plug a serialisable variant into the same
place ``@wrapt.decorator`` would be used. The decorator factory
returned from ``serialisable_decorator`` is used identically to a
factory built with ``@wrapt.decorator``, and a function or method
decorated with it can be serialised with ``dill`` (using ``byref=True``
for the reason described in the preceding section).

::

    import dill

    @serialisable_decorator
    def trace(wrapped, instance, args, kwargs):
        print(f"[trace] {wrapped.__name__}({args}, {kwargs})")
        return wrapped(*args, **kwargs)

    @trace
    def add(a, b):
        return a + b

    data = dill.dumps(add, byref=True)
    restored = dill.loads(data)

    restored(2, 3)    # works the same as add(2, 3)

The restored callable is an instance of ``SerialisableFunctionWrapper``
again, retains the same wrapper behaviour, and participates in the
descriptor binding protocol just like the original. This means the
same approach works for decorated instance methods, class methods and
static methods on a class: restoring an instance of the class also
restores any decorated methods reachable through it.

Before adopting this pattern, consider carefully whether serialising
decorators is actually what you need. Most applications of decorators
do not need them to survive serialisation. Wrappers are typically
rebuilt from source at import time, and the things that *do* need to
travel through a serialisation boundary (data, configuration, results)
are usually plain values rather than decorated callables. If
serialising decorated functions is not a core requirement of the
system, the simplest thing is not to try.

When decorator serialisation genuinely is a requirement, it is
strongly recommended to build a small decorator factory of your own
along the lines of the one above, rather than trying to make
``@wrapt.decorator`` or ``wrapt.FunctionWrapper`` themselves
serialisable. ``wrapt`` offers a number of features beyond the minimum
needed to implement a decorator, including adapter functions that
reshape the apparent signature of the wrapper, enabled and disabled
flags that can toggle wrapping on and off dynamically, descriptor
protocol integration for bound methods, and careful handling of edge
cases such as classmethods, staticmethods and nested classes. All of
this state lives on the proxy in ways that make a fully general
``__reduce__`` implementation substantially more involved than the
one shown here. A hand-rolled decorator factory that only supports
what your application actually uses keeps the pickle surface small
and the rebuild recipe obvious, and avoids inheriting serialisation
responsibility for parts of ``wrapt`` that are not relevant to your
use case.

Synchronization Locks
---------------------

A thread synchronisation decorator acquires a lock before calling the
wrapped function and releases it afterwards, so that concurrent callers
run the body one at a time. When the decorated target is a method, a
useful refinement is to keep a separate lock *per instance of the class*
so that calls on different instances do not serialise against each
other.

The ``instance`` argument of the wrapper function is the way in. When
**wrapt** invokes the wrapper for a bound method call, ``instance`` is the
bound receiver: the object for an instance method, or the class for a
class method. For a normal function call, ``instance`` is ``None``. Using
``instance`` as the storage location when it is not ``None``, and falling
back to ``wrapped`` when it is, selects the right context for each kind
of call.

The lock is stored on the chosen context on first call, using
``dict.setdefault`` so that concurrent callers cannot create two locks
by accident.

::

    import threading
    import wrapt

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        context = instance if instance is not None else wrapped
        lock = vars(context).get('_synchronized_lock')
        if lock is None:
            lock = vars(context).setdefault(
                '_synchronized_lock', threading.RLock())
        with lock:
            return wrapped(*args, **kwargs)

    @synchronized
    def function():
        pass

    class Class:

        @synchronized
        def method(self):
            pass

For a normal function, ``instance`` is ``None`` and the lock is attached
to the wrapped function, so every caller of ``function`` shares a single
lock. For an instance method, ``instance`` is the object on which the
method was called and the lock is stored on that object, so each instance
of ``Class`` gets its own independent lock. ``threading.RLock`` is used
so that a thread which already holds the lock can call into another
synchronized function protected by the same lock without deadlocking.

The example above is a minimal illustration. It is not a production
quality synchronisation decorator. **wrapt** already ships a fully
featured ``wrapt.synchronized`` that handles the cases this simple
version does not, such as class methods and classes decorated directly
where ``vars()`` returns a read-only ``mappingproxy``, along with a dual
role as both decorator and context manager, and transparent support for
``async def`` functions and ``async with`` blocks backed by an
``asyncio.Lock``. See :doc:`bundled` for the full description.
