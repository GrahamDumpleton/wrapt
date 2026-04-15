Assorted Examples
=================

This document provides practical examples of decorators built using the
**wrapt** module. These range from common patterns such as tracking decorator
state, through to more complex examples like thread synchronization. For
details on the core decorator API and wrapper function signature, see
:doc:`decorators`. For details on the ``FunctionWrapper`` and other proxy
types used in these examples, see :doc:`wrappers`.

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

LRU Cache
---------

.. note::
    The ``lru_cache`` decorator described here is available within the
    **wrapt** package as ``wrapt.lru_cache``.

The ``functools.lru_cache`` decorator from the standard library works well
for plain functions, but has several limitations when applied to instance
methods:

* **Cache pollution** — because ``self`` is included as a cache key, all
  instances share the same ``maxsize`` budget. A cache with ``maxsize=128``
  shared across 100 instances gives roughly one entry per instance.

* **Garbage collection** — the cache holds strong references to ``self``
  through the cache keys, preventing instances from being garbage collected
  as long as they remain in the cache.

* **Hashability** — ``self`` must be hashable for the cache lookup to work.
  If a class defines ``__eq__`` without ``__hash__``, applying
  ``functools.lru_cache`` to its methods will raise a ``TypeError``.

``wrapt.lru_cache`` addresses all three issues by maintaining a separate
per-instance cache stored as an attribute on the instance itself. Each
instance gets its own full ``maxsize`` budget, instances do not need to be
hashable, and caches are automatically cleaned up when the instance is
garbage collected. For plain functions, class methods, and static methods,
a single shared cache is used — the same as ``functools.lru_cache``.

The decorator can be used with or without arguments, just like
``functools.lru_cache``. All keyword arguments are passed through to the
underlying ``functools.lru_cache``.

::

    import wrapt

    @wrapt.lru_cache
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    @wrapt.lru_cache(maxsize=32)
    def factorial(n):
        return n * factorial(n - 1) if n else 1

The decorator works with instance methods, class methods, and static methods.

::

    class MyClass:

        @wrapt.lru_cache
        def compute(self, x):
            return x * 2

        @wrapt.lru_cache(maxsize=32)
        @classmethod
        def class_compute(cls, x):
            return x * 3

        @wrapt.lru_cache
        @staticmethod
        def static_compute(x):
            return x * 4

For instance methods, each instance maintains its own independent cache.

::

    >>> obj1 = MyClass()
    >>> obj2 = MyClass()
    >>> obj1.compute(5)
    10
    >>> obj2.compute(5)
    10

Each instance has its own ``maxsize`` budget, so caching on one instance
does not affect another.

The ``cache_info()``, ``cache_clear()``, and ``cache_parameters()`` methods
are available directly on the decorated function. For instance methods,
these operate on the per-instance cache for the bound instance.

::

    >>> obj = MyClass()
    >>> obj.compute(5)
    10
    >>> obj.compute(5)
    10
    >>> obj.compute.cache_info()
    CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)
    >>> obj.compute.cache_clear()

For plain functions, class methods, and static methods these operate on the
single shared cache.

::

    >>> fibonacci(10)
    55
    >>> fibonacci.cache_info()
    CacheInfo(hits=8, misses=11, maxsize=128, currsize=11)
    >>> fibonacci.cache_parameters()
    {'maxsize': 128, 'typed': False}

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

Thread Synchronization
----------------------

.. note::
    The final variant of the ``synchronized`` decorator described here
    is available within the **wrapt** package as ``wrapt.synchronized``.

Synchronization decorators are a simplified way of adding thread locking to
functions, methods, instances of classes or a class type. They work by
associating a thread mutex with a specific context and when a function is
called the lock is acquired prior to the call and then released once the
function returns.

The simplest example of a decorator for synchronization is one where the
lock is explicitly provided when the decorator is applied to a function. By
being supplied explicitly, it is up to the user of the decorator to
determine what context the lock applies to. For example, a lock may be
applied to a single function, a group of functions, or a class.

As the lock needs to be supplied when the decorator is applied to the
function we need to use a function closure as a means of supplying the
argument to the decorator.

::

    def synchronized(lock):
        @wrapt.decorator
        def _wrapper(wrapped, instance, args, kwargs):
            with lock:
                return wrapped(*args, **kwargs)
        return _wrapper

    import threading

    lock = threading.RLock()

    @synchronized(lock)
    def function():
        pass

    class Class:

        @synchronized(lock)
        def function(self):
            pass

Note that the recursive lock ``threading.RLock`` is used to ensure that
recursive calls, or calls to another synchronized function associated with
the same lock, doesn't cause a deadlock.

An alternative to requiring the lock be supplied when the decorator is
applied to a function, is to associate a lock automatically with the
wrapped function. That is, rather than require the lock be passed in
explicitly, create one on demand and attach it to the wrapped function.

::

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        # Retrieve the lock from the wrapped function.

        lock = vars(wrapped).get('_synchronized_lock', None)

        if lock is None:
            # There was no lock yet associated with the function so we
            # create one and associate it with the wrapped function.
            # We use ``dict.setdefault()`` as a means of ensuring that
            # only one thread gets to set the lock if multiple threads
            # do this at the same time. This may mean redundant lock
            # instances will get thrown away if there is a race to set
            # it, but all threads would still get back the same one lock.

            lock = vars(wrapped).setdefault('_synchronized_lock',
                    threading.RLock())

        with lock:
            return wrapped(*args, **kwargs)

    @synchronized
    def function():
        pass

This avoids the need for an instance of a lock to be passed in explicitly
when the decorator is being applied to a function, but it now means that
all decorated methods of a class will have a distinct lock.

A more severe issue in both these approaches is that locks on each method
work across all instances of the class where as what we really want is a
lock per instance of a class for all methods of the class decorated with
the ``@synchronized`` decorator.

To address this, we can use the fact that the decorator wrapper function
is passed the ``instance`` and so can determine when the function is being
invoked on an instance of a class and that it is not a normal function
call. In this case we can associate the lock with the instance instead.

::

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        # Use the instance as the context if function was bound.

        if instance is not None:
            context = vars(instance)
        else:
            context = vars(wrapped)

        # Retrieve the lock for the specific context.

        lock = context.get('_synchronized_lock', None)

        if lock is None:
            # There was no lock yet associated with the function so we
            # create one and associate it with the wrapped function.
            # We use ``dict.setdefault()`` as a means of ensuring that
            # only one thread gets to set the lock if multiple threads
            # do this at the same time. This may mean redundant lock
            # instances will get thrown away if there is a race to set
            # it, but all threads would still get back the same one lock.

            lock = context.setdefault('_synchronized_lock',
                    threading.RLock())

        with lock:
            return wrapped(*args, **kwargs)

    @synchronized
    def function():
        pass

Now we actually have two scenarios that match for where ``instance`` is not
``None``. One will be where an instance method is being called on a class,
which is what we are targeting in this case. We will also have ``instance``
being a value other than ``None`` for the case where a class method is
called. For this case ``instance`` will be a reference to the class type.

Having the lock being associated with the class type for class methods is
entirely reasonable, but a problem presents. That is that
``vars(instance)`` where ``instance`` is a class type, actually returns a
``dictproxy`` and not a ``dict``. As a ``dictproxy`` is effectively read
only, it is not possible to associate the lock with it.

A similar problem also occurs where ``instance`` is ``None`` but ``wrapped``
is a class type. That is, if the decorator was applied to a class. The result
is that the above technique will not work in these two cases.

The only way that it is possible to add attributes to a class type is to use
``setattr``, either explicitly or via direct attribute assignment. Although
this allows us to add attributes to a class, there is no equivalent to
``dict.setdefault()``, so we loose the ability to add the attribute which will
hold the lock atomically.

To get around this problem, we need to use an intermediary meta lock which
gates the attempt to associate a lock with a specific context. This meta
lock itself still needs to be created somehow, so what we do now is use
the ``dict.setdefault()`` trick against the decorator itself and use it as
the place to store the meta lock.

::

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        # Use the instance as the context if function was bound.

        if instance is not None:
            context = instance
        else:
            context = wrapped

        # Retrieve the lock for the specific context.

        lock = vars(context).get('_synchronized_lock', None)

        if lock is None:
            # There is no existing lock defined for the context we
            # are dealing with so we need to create one. This needs
            # to be done in a way to guarantee there is only one
            # created, even if multiple threads try and create it at
            # the same time. We can't always use the setdefault()
            # method on the __dict__ for the context. This is the
            # case where the context is a class, as __dict__ is
            # actually a dictproxy. What we therefore do is use a
            # meta lock on this wrapper itself, to control the
            # creation and assignment of the lock attribute against
            # the context.

            meta_lock = vars(synchronized).setdefault(
                    '_synchronized_meta_lock', threading.Lock())

            with meta_lock:
                # We need to check again for whether the lock we want
                # exists in case two threads were trying to create it
                # at the same time and were competing to create the
                # meta lock.

                lock = vars(context).get('_synchronized_lock', None)

                if lock is None:
                    lock = threading.RLock()
                    setattr(context, '_synchronized_lock', lock)

        with lock:
            return wrapped(*args, **kwargs)

This means lock creation is all automatic, with an appropriate lock created
for the different contexts the decorator is used in.

::

    @synchronized # lock bound to function1
    def function1():
        pass

    @synchronized # lock bound to function2
    def function2():
        pass

    @synchronized # lock bound to Class
    class Class:

        @synchronized # lock bound to instance of Class
        def function_im(self):
            pass

        @synchronized # lock bound to Class
        @classmethod
        def function_cm(cls):
            pass

        @synchronized # lock bound to function_sm
        @staticmethod
        def function_sm():
            pass

Specifically, when the decorator is used on a normal function or static
method, a unique lock will be associated with each function. For the case
of instance methods, the lock will be against the instance. Finally, for
class methods and a decorator against an actual class, the lock will be
against the class type.

One requirement with this approach though is that only the execution of a
whole function can be synchronized. In Java where a similar mechanism
exists, it is also possible to have synchronized statements. In Python one
can emulate synchronized statements by using the 'with' statement in
conjunction with a lock. The trick with that is that if using it within a
method of a class, we want to be able to use the same lock as that which is
being applied to synchronized methods of the class. In effect we want to be
able to do the following.

::

    class Class:

        @synchronized
        def function_im_1(self):
            pass

        def function_im_2(self):
            with synchronized(self):
                pass

In other words we want the decorator function to serve a dual role of being
able to decorate a function to make it synchronized, but also return a
context manager for the lock for a specific context so that it can be used
with the 'with' statement.

Because of this dual requirement, we actually need to partly side step
``wrapt.decorator`` and drop down to using the underlying ``FunctionWrapper``
class that it uses to implement decorators. Specifically, we need to create
a derived version of ``FunctionWrapper`` which converts it into a context
manager, but at the same time can still be used as a decorator as before.

::

    def synchronized(wrapped):
        def _synchronized_lock(context):
            # Attempt to retrieve the lock for the specific context.

            lock = vars(context).get('_synchronized_lock', None)

            if lock is None:
                # There is no existing lock defined for the context we
                # are dealing with so we need to create one. This needs
                # to be done in a way to guarantee there is only one
                # created, even if multiple threads try and create it at
                # the same time. We can't always use the setdefault()
                # method on the __dict__ for the context. This is the
                # case where the context is a class, as __dict__ is
                # actually a dictproxy. What we therefore do is use a
                # meta lock on this wrapper itself, to control the
                # creation and assignment of the lock attribute against
                # the context.

                meta_lock = vars(synchronized).setdefault(
                        '_synchronized_meta_lock', Lock())

                with meta_lock:
                    # We need to check again for whether the lock we want
                    # exists in case two threads were trying to create it
                    # at the same time and were competing to create the
                    # meta lock.

                    lock = vars(context).get('_synchronized_lock', None)

                    if lock is None:
                        lock = RLock()
                        setattr(context, '_synchronized_lock', lock)

            return lock

        def _synchronized_wrapper(wrapped, instance, args, kwargs):
            # Execute the wrapped function while the lock for the
            # desired context is held. If instance is None then the
            # wrapped function is used as the context.

            with _synchronized_lock(instance or wrapped):
                return wrapped(*args, **kwargs)

        class _FinalDecorator(FunctionWrapper):

            def __enter__(self):
                self._self_lock = _synchronized_lock(self.__wrapped__)
                self._self_lock.acquire()
                return self._self_lock

            def __exit__(self, *args):
                self._self_lock.release()

        return _FinalDecorator(wrapped=wrapped, wrapper=_synchronized_wrapper)

When used in this way, the more typical use case would be to synchronize
against the class instance, but if needing to synchronize with the work of
a class method from an instance method, it could also be done against the
class itself.

::

    class Class:

        @synchronized
        @classmethod
        def function_cm(cls):
            pass

        def function_im(self):
            with synchronized(Class):
                pass

If wishing to have more than one normal function synchronize on the same
object, then it is possible to have the synchronization be against a data
structure which they all manipulate.

::

    class Data:
        pass

    data = Data()

    def function_1():
        with synchronized(data):
            pass

    def function_2():
        with synchronized(data):
            pass

In doing this you would be restricted to using a data structure to which
new attributes can be added, such that the hidden lock can be added. This
means for example, you could not do this with a dictionary. It also means
you can't just decorate the whole function.

What would perhaps be better is to return back to having the ``synchronized``
decorator allow an actual lock object to be supplied when the decorator is
being applied to a function. Being able to do this though would be
optional and if not done the lock would be associated with the appropriate
context of the wrapped function.

::

    lock = threading.RLock()

    @synchronized(lock)
    def function_1():
        pass

    @synchronized(lock)
    def function_2():
        pass

This requires what the decorator accepts to be overloaded and so may be
frowned on by some, but the implementation would be as follows.

::

    def synchronized(wrapped):
        # Determine if being passed an object which is a synchronization
        # primitive. We can't check by type for Lock, RLock, Semaphore etc,
        # as the means of creating them isn't the type. Therefore use the
        # existence of acquire() and release() methods. This is more
        # extensible anyway as it allows custom synchronization mechanisms.

        if hasattr(wrapped, 'acquire') and hasattr(wrapped, 'release'):
            # We remember what the original lock is and then return a new
            # decorator which accesses and locks it. When returning the new
            # decorator we wrap it with an object proxy so we can override
            # the context manager methods in case it is being used to wrap
            # synchronized statements with a 'with' statement.

            lock = wrapped

            @decorator
            def _synchronized(wrapped, instance, args, kwargs):
                # Execute the wrapped function while the original supplied
                # lock is held.

                with lock:
                    return wrapped(*args, **kwargs)

            class _PartialDecorator(ObjectProxy):

                def __enter__(self):
                    lock.acquire()
                    return lock

                def __exit__(self, *args):
                    lock.release()

            return _PartialDecorator(wrapped=_synchronized)

        # Following only apply when the lock is being created
        # automatically based on the context of what was supplied. In
        # this case we supply a final decorator, but need to use
        # FunctionWrapper directly as we want to derive from it to add
        # context manager methods in case it is being used to wrap
        # synchronized statements with a 'with' statement.

        def _synchronized_lock(context):
            # Attempt to retrieve the lock for the specific context.

            lock = vars(context).get('_synchronized_lock', None)

            if lock is None:
                # There is no existing lock defined for the context we
                # are dealing with so we need to create one. This needs
                # to be done in a way to guarantee there is only one
                # created, even if multiple threads try and create it at
                # the same time. We can't always use the setdefault()
                # method on the __dict__ for the context. This is the
                # case where the context is a class, as __dict__ is
                # actually a dictproxy. What we therefore do is use a
                # meta lock on this wrapper itself, to control the
                # creation and assignment of the lock attribute against
                # the context.

                meta_lock = vars(synchronized).setdefault(
                        '_synchronized_meta_lock', Lock())

                with meta_lock:
                    # We need to check again for whether the lock we want
                    # exists in case two threads were trying to create it
                    # at the same time and were competing to create the
                    # meta lock.

                    lock = vars(context).get('_synchronized_lock', None)

                    if lock is None:
                        lock = RLock()
                        setattr(context, '_synchronized_lock', lock)

            return lock

        def _synchronized_wrapper(wrapped, instance, args, kwargs):
            # Execute the wrapped function while the lock for the
            # desired context is held. If instance is None then the
            # wrapped function is used as the context.

            with _synchronized_lock(instance or wrapped):
                return wrapped(*args, **kwargs)

        class _FinalDecorator(FunctionWrapper):

            def __enter__(self):
                self._self_lock = _synchronized_lock(self.__wrapped__)
                self._self_lock.acquire()
                return self._self_lock

            def __exit__(self, *args):
                self._self_lock.release()

        return _FinalDecorator(wrapped=wrapped, wrapper=_synchronized_wrapper)

As well as normal functions, this can be used with methods of classes as
well. Because though the lock object has to be available at the time the
class definition is being created, it can only be used to refer to a lock
which is the same across the whole class, or one which is at global scope.

::

    class Class:
        lock1 = threading.RLock()
        lock2 = threading.RLock()

        @synchronized(lock1)
        @classmethod
        def function_cm_1(cls):
            pass

        @synchronized(lock1)
        def function_im_1(self):
            pass

        @synchronized(lock2)
        @classmethod
        def function_cm_2(cls):
            pass

The alternative is to use ``synchronized`` as a context manager and pass the
lock in at that time.

::

    class Class:

        def __init__(self):
            self.lock1 = threading.RLock()

        def function_im(self):
            with synchronized(self.lock1):
                pass

This is actually the same as using the 'with' statement directly on the lock,
but it you want to get carried away and have all the code look more or less
uniform, it is possible.

One benefit of being able to pass the lock in explicitly, is that you can
override the default lock type used, which is ``threading.RLock``. Any
synchronization primitive can be supplied so long as it provides a
``acquire()`` and ``release()`` method. This includes being able to pass
in your own custom class objects with such methods which do something
appropriate.

::

    semaphore = threading.Semaphore(2)

    @synchronized(semaphore)
    def function():
        pass
