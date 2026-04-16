Bundled Decorators
==================

The **wrapt** package ships a small number of ready-made decorators built on
top of the ``wrapt.decorator`` / ``FunctionWrapper`` machinery. This document
is a usage reference for those bundled decorators. For worked examples of how
decorators of this kind can be constructed from scratch using **wrapt**, see
:doc:`examples`.

LRU Cache
---------

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
a single shared cache is used, the same as ``functools.lru_cache``.

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

Thread Synchronization
----------------------

The ``wrapt.synchronized`` decorator associates a lock with the callable or
context it is applied to, so that the decorated function runs with the lock
held. It can also be used as a context manager, and it understands both
threading locks and ``asyncio`` locks. The same ``synchronized`` name serves
all of these roles.

Synchronous usage
~~~~~~~~~~~~~~~~~

Applied to a plain function, a ``threading.RLock`` is created lazily and
attached to the wrapper on first call. The same lock is reused on every
subsequent call, so concurrent callers are serialised.

::

    import wrapt

    @wrapt.synchronized
    def function():
        ...

Applied to methods of a class, the lock is associated with the appropriate
context for each form of method. The decorator detects whether it is bound
to an instance, a class, or an unbound callable and stores the lock on the
corresponding object.

::

    @wrapt.synchronized  # lock bound to the class itself
    class Service:

        @wrapt.synchronized  # per-instance lock
        def instance_method(self):
            ...

        @wrapt.synchronized  # lock bound to the class
        @classmethod
        def class_method(cls):
            ...

        @wrapt.synchronized  # lock bound to the decorated function
        @staticmethod
        def static_method():
            ...

For an instance method each separate instance of the class gets its own lock,
so two different instances may execute concurrently but two callers using the
same instance are serialised against each other. For a class method, and for
the case where the class itself is decorated, the lock is shared at the class
level. For a static method, a single lock is stored on the decorated function.

``synchronized`` can also be used as a context manager inside an undecorated
method, which allows synchronising a block of code rather than a whole
function. When used this way the object passed to ``synchronized`` is the
synchronisation context; a lock is created lazily and attached to it.

::

    class Service:

        def instance_block(self):
            with wrapt.synchronized(self):
                ...

        @classmethod
        def class_block(cls):
            with wrapt.synchronized(cls):
                ...

Any object that accepts attribute assignment can serve as a synchronisation
context, including a completely separate data object that has nothing to do
with where ``synchronized`` is used. Multiple unrelated callers passing the
same object to ``synchronized`` share the same lock.

::

    class Resource:
        pass

    shared = Resource()

    def function_one():
        with wrapt.synchronized(shared):
            ...

    def function_two():
        with wrapt.synchronized(shared):
            ...

Built-in immutable types such as ``int``, ``str``, ``tuple`` and plain
``dict`` instances cannot be used as a context, because they do not accept
attribute assignment. Use a dedicated sentinel object instead.

The decorator form and the context-manager form share the same auto-created
lock whenever they name the same context object. An ``@wrapt.synchronized``
method and a ``with wrapt.synchronized(self):`` block in a sibling
(undecorated) method of the same class both resolve to the per-instance
``_synchronized_lock`` attribute, so they are mutually exclusive on any
given instance.

::

    class Service:

        @wrapt.synchronized          # acquires per-instance lock
        def update(self, value):
            ...

        def read(self):
            with wrapt.synchronized(self):  # acquires the same lock
                ...

The same applies at the class level: ``@wrapt.synchronized`` on a class
method and ``with wrapt.synchronized(cls):`` inside another method share
the per-class lock. Decorator-form and context-manager-form usage can
therefore be mixed freely, and each object (instance, class, or arbitrary
sentinel) carries at most one auto-created synchronous lock.

The lock created automatically is a ``threading.RLock``, so a synchronised
callable is reentrant: a synchronised method calling another synchronised
method on the same instance, or a synchronised function calling itself
recursively, does not deadlock.

An explicit lock can be supplied instead of relying on the automatically
created one. Any object with ``acquire()`` and ``release()`` methods is
accepted, including ``threading.Lock``, ``threading.RLock``,
``threading.Semaphore`` and custom primitives. The same form works as both
a decorator and a context manager.

::

    import threading

    lock = threading.RLock()

    @wrapt.synchronized(lock)
    def function_one():
        ...

    @wrapt.synchronized(lock)
    def function_two():
        ...

    def function_three():
        with wrapt.synchronized(lock):
            ...

    semaphore = threading.Semaphore(2)

    @wrapt.synchronized(semaphore)
    def limited():
        ...

Note that supplying a non-reentrant primitive such as ``threading.Lock``
loses the reentrancy guarantee that the auto-created ``threading.RLock``
provides, and can deadlock on recursive or nested calls.

Asynchronous usage
~~~~~~~~~~~~~~~~~~

``synchronized`` detects when the callable being decorated is an ``async def``
function and switches over to creating an ``asyncio.Lock`` per context,
awaiting acquisition, and awaiting the wrapped coroutine. No change in
syntax is needed on the user's side — the same ``@wrapt.synchronized`` is
used.

::

    import asyncio
    import wrapt

    @wrapt.synchronized
    async def fetch():
        ...

    class Service:

        @wrapt.synchronized
        async def work(self):
            ...

The object returned by ``synchronized`` also exposes ``__aenter__`` and
``__aexit__``, so it can be used with ``async with`` to guard a block of
code. The block-form usage mirrors the synchronous version and applies to
``self``, ``cls``, or any arbitrary shared object.

::

    class Service:

        async def instance_block(self):
            async with wrapt.synchronized(self):
                ...

        @classmethod
        async def class_block(cls):
            async with wrapt.synchronized(cls):
                ...

    shared = Resource()

    async def function_one():
        async with wrapt.synchronized(shared):
            ...

As with the synchronous side, the decorator form and the ``async with``
context-manager form share the same auto-created ``asyncio.Lock`` whenever
they name the same context object. An ``@wrapt.synchronized`` async method
and an ``async with wrapt.synchronized(self):`` block in a sibling
(undecorated) async method of the same class both resolve to the
per-instance ``_synchronized_async_lock`` attribute and are mutually
exclusive on any given instance.

Passing an ``asyncio.Lock`` (or any object whose ``acquire`` is a coroutine
function) to ``synchronized`` routes through the async code path
automatically. The returned object supports ``async with`` but not ``with``.

::

    lock = asyncio.Lock()

    @wrapt.synchronized(lock)
    async def work():
        ...

    async def block():
        async with wrapt.synchronized(lock):
            ...

Non-reentrancy
^^^^^^^^^^^^^^

Unlike the ``threading.RLock`` used by the synchronous auto-lock path,
``asyncio.Lock`` is not reentrant. A synchronised async method that calls
another synchronised async method on the same context will deadlock, because
the second call waits for the lock that the first call still holds.

The idiomatic way to deal with this is to split the locking layer from the
logic: the public coroutines acquire the lock, and a private shadow
coroutine (conventionally named with a leading underscore) carries the
actual logic and assumes the lock is already held. Callers that need to
reuse the logic from inside another already-locked coroutine call the
private form directly.

::

    class Cache:

        def __init__(self):
            self._store = {}

        @wrapt.synchronized
        async def get(self, key):
            return await self._get(key)

        @wrapt.synchronized
        async def refresh(self, key, source):
            value = await source(key)
            self._store[key] = value
            return await self._get(key)

        async def _get(self, key):
            # Assumes the caller is holding the per-instance async lock.
            return self._store.get(key)

The public ``get`` and ``refresh`` acquire the per-instance ``asyncio.Lock``
on entry; ``_get`` runs inside whichever caller already holds it and never
tries to re-acquire the lock itself.

If true reentrancy is required, the auto-lock form cannot provide it.
Supply your own task-reentrant async lock via the explicit-lock form
instead.

Mixing synchronous and asynchronous use of the same context
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The synchronous and asynchronous auto-lock paths store their locks under
different attribute names on the context object (``_synchronized_lock`` and
``_synchronized_async_lock`` respectively). They are independent primitives.
A synchronous ``with wrapt.synchronized(obj):`` block and an asynchronous
``async with wrapt.synchronized(obj):`` block targeting the same ``obj`` do
not mutually exclude each other — each protocol only serialises against
itself.

In practice this means you should pick one synchronisation protocol per
context. Do not mix ``@wrapt.synchronized`` on a regular method and
``@wrapt.synchronized`` on an ``async def`` method of the same class and
expect them to serialise against one another.

Calling Convention Markers and Adapters
---------------------------------------

The ``synchronized`` decorator decides between its synchronous and asynchronous
paths by consulting ``inspect.iscoroutinefunction()`` on the callable it is
applied to. That works whenever the calling convention exposed by the decorator
stack matches the underlying function definition. In more elaborate stacks the
two can diverge: an inner decorator might call an ``async def`` via
``asyncio.run()`` and present a synchronous callable to the outside, or a
decorator around a plain ``def`` might return a coroutine. In either case
auto-detection based on the inner function definition alone gives the wrong
answer.

To make the effective calling convention explicit, **wrapt** provides four
small decorators. ``mark_as_sync`` and ``mark_as_async`` are pass-through
markers that leave the calling behaviour untouched; ``async_to_sync`` and ``sync_to_async``
actually bridge between the two conventions.

All four are wrapt function wrappers that adjust ``__code__.co_flags`` so that
``inspect.iscoroutinefunction()`` (and therefore any stdlib or third-party code
that consults it, including ``synchronized``) reports the intended convention.
The underlying wrapped callable is left unchanged and is still reachable via
``__wrapped__``.

Marking without converting
~~~~~~~~~~~~~~~~~~~~~~~~~~

``wrapt.mark_as_sync`` and ``wrapt.mark_as_async`` are pass-through wrappers.
They do not change how the callable is invoked; they only record the convention
that the surrounding stack has established.

Use ``mark_as_sync`` when an inner decorator has already collapsed an
``async def`` into a synchronous callable (for example by running it to
completion with ``asyncio.run()``) but the outer introspection would still
see the inner ``async def``:

::

    import wrapt

    @wrapt.synchronized
    @wrapt.mark_as_sync
    @some_third_party_run_to_completion
    async def work(...):
        ...

Use ``mark_as_async`` for the symmetric case where a plain ``def`` wrapper
actually returns a coroutine and should be treated as an async callable:

::

    @wrapt.synchronized
    @wrapt.mark_as_async
    @some_third_party_coroutine_returning_wrapper
    def work(...):
        ...

Because the marker wrappers do not alter the calling convention themselves,
applying them directly to an ``async def`` (with no intermediate decorator to
collapse it) does not make the result actually callable synchronously; it only
changes what ``iscoroutinefunction()`` reports. The marker wrappers are for
annotating stacks whose effective convention has already been established by
other decorators.

Marking generator convention
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both ``mark_as_sync`` and ``mark_as_async`` accept an optional
``generator`` keyword to control the reported generator-ness of the
wrapper. This is the modifier on top of the primary sync/async axis, and
lets the markers address all four realistic callable kinds: plain
function, sync generator, coroutine function, and async generator.

The parameter is tri-state:

- ``None`` (default): auto. Preserve generator-ness from the input. For
  ``mark_as_sync``, an async generator input becomes a sync generator;
  other inputs keep their ``CO_GENERATOR`` bit as-is. For
  ``mark_as_async``, any generator input (sync or async) becomes an
  async generator; non-generator input becomes a coroutine function.
- ``True``: force generator reporting on. ``mark_as_sync(generator=True)``
  sets ``CO_GENERATOR``; ``mark_as_async(generator=True)`` sets
  ``CO_ASYNC_GENERATOR`` (and clears ``CO_COROUTINE`` since the two
  are mutually exclusive at the CPython code-object level).
- ``False``: force generator reporting off. ``mark_as_sync(generator=False)``
  clears ``CO_GENERATOR``; ``mark_as_async(generator=False)`` sets
  ``CO_COROUTINE`` and clears ``CO_ASYNC_GENERATOR`` and ``CO_GENERATOR``.

::

    # An upstream decorator collects items from an async generator into
    # a list and returns it synchronously. Mark the resulting callable
    # as a plain sync function (default auto would flip
    # CO_ASYNC_GENERATOR into CO_GENERATOR and the wrapper would report
    # as a sync generator, which is wrong here -- the real return is a
    # list).

    @wrapt.mark_as_sync(generator=False)
    @collect_async_generator_to_list
    async def stream(...):
        yield ...

::

    # A sync generator is being exposed through an adapter that wraps
    # each yielded item in an async future. Mark it as an async
    # generator so consumers using ``async for`` see the expected
    # introspection.

    @wrapt.mark_as_async(generator=True)
    @async_wrap_yielded_items
    def produce(...):
        yield ...

Both markers always clear ``CO_ITERABLE_COROUTINE`` (the legacy
``@types.coroutine`` flag), regardless of ``generator``, since that
flag's meaning is incompatible with either marker's assertion.

Bridging between conventions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``wrapt.async_to_sync`` adapts an async callable so that callers can invoke it
synchronously. Each call runs the coroutine to completion via
``asyncio.run()`` and returns the result.

::

    @wrapt.async_to_sync
    async def add(a, b):
        return a + b

    add(2, 3)  # returns 5

``wrapt.sync_to_async`` adapts a synchronous callable so that callers can
``await`` it. Each call schedules the synchronous work on the default
executor using ``loop.run_in_executor()``.

::

    @wrapt.sync_to_async
    def mul(a, b):
        return a * b

    await mul(4, 5)  # returns 20

Both adapters also take care of marking the result with the appropriate
``iscoroutinefunction()`` reporting, so they can be stacked directly under
``@wrapt.synchronized`` with no additional marker required:

::

    @wrapt.synchronized
    @wrapt.async_to_sync
    async def fetch(...):
        # ``synchronized`` sees this as synchronous and uses the
        # ``threading.RLock`` path.
        ...

    @wrapt.synchronized
    @wrapt.sync_to_async
    def compute(...):
        # ``synchronized`` sees this as asynchronous and uses the
        # ``asyncio.Lock`` path.
        ...

Relationship to third-party equivalents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tools similar to ``async_to_sync`` and ``sync_to_async`` are available in a number of
third-party packages. The versions provided here are primarily a convenience:
they are set up so that ``wrapt.synchronized`` sees the correct calling
convention automatically, without needing to interpose ``mark_as_sync`` or
``mark_as_async`` between the adapter and ``synchronized``.

If you prefer a third-party ``async_to_sync`` / ``sync_to_async`` (for example because it
offers features such as explicit executor selection, loop reuse, or structured
concurrency hooks), use ``mark_as_sync`` or ``mark_as_async`` to declare the
resulting calling convention to ``wrapt.synchronized``:

::

    @wrapt.synchronized
    @wrapt.mark_as_sync
    @third_party_to_sync
    async def work(...):
        ...

    @wrapt.synchronized
    @wrapt.mark_as_async
    @third_party_to_async
    def work(...):
        ...

Signature Override
------------------

``wrapt.with_signature`` overrides the signature that introspection tools
see for a wrapped callable, without mutating the wrapped function itself.
The wrapper still calls through to the wrapped function normally; only the
signature reported by ``inspect.signature()``, ``inspect.getfullargspec()``,
``help()``, and equivalent tools is substituted. Annotations, defaults,
keyword defaults, and the argument-related attributes of ``__code__`` are
all derived from the supplied signature so that tools which read these
attributes directly stay consistent with ``inspect.signature()``.

This is the modern replacement for the ``adapter`` argument of
``wrapt.decorator`` (see :doc:`decorators`). The older ``adapter``
mechanism remains available but is planned for deprecation.

Exactly one of the keyword arguments ``prototype=``, ``signature=``, or
``factory=`` must be supplied. Supplying none, or more than one, raises
``TypeError``.

Providing a prototype function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common form is to pass a prototype function whose signature is
to be presented. The prototype's body is not executed; only its signature
(including annotations) is used.

::

    import wrapt

    def _prototype(user: str, count: int = 1) -> bool: ...

    @wrapt.with_signature(prototype=_prototype)
    def function(*args, **kwargs):
        # The real implementation accepts (*args, **kwargs), but
        # introspection sees (user: str, count: int = 1) -> bool.
        ...

The wrapped function is not modified. ``inspect.signature(function)``
returns the prototype's signature, while
``inspect.signature(function.__wrapped__)`` still returns the wrapped
function's own ``(*args, **kwargs)``.

Providing a Signature object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the signature is built programmatically, an ``inspect.Signature`` object
can be supplied directly via ``signature=``.

::

    import inspect
    import wrapt

    sig = inspect.Signature(
        [
            inspect.Parameter(
                "user",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=str,
            ),
        ],
        return_annotation=bool,
    )

    @wrapt.with_signature(signature=sig)
    def function(*args, **kwargs):
        ...

Deriving the signature from the wrapped function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A factory callable can be supplied via ``factory=``. It is called at
decoration time with the function being wrapped, and must return either
an ``inspect.Signature`` or a prototype callable from which a signature
will be derived. This form is the equivalent of ``wrapt.adapter_factory``
in the legacy mechanism.

::

    def prepend_request_id(wrapped):
        s = inspect.signature(wrapped)
        return s.replace(
            parameters=[
                inspect.Parameter(
                    "request_id",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ),
                *s.parameters.values(),
            ]
        )

    @wrapt.with_signature(factory=prepend_request_id)
    def function(a, b):
        ...

Methods
~~~~~~~

``with_signature`` handles instance methods, class methods, and static
methods. For an instance method the prototype should include ``self``; the
bound view has it stripped automatically, matching Python's built-in
behaviour for ``inspect.signature(instance.method)``.

::

    def _method_proto(self, value: int) -> int: ...

    class C:

        @wrapt.with_signature(prototype=_method_proto)
        def scale(self, *args, **kwargs):
            return args[0] * 10

    # inspect.signature(C.scale)   reports (self, value: int) -> int
    # inspect.signature(c.scale)   reports (value: int) -> int

For class methods and static methods, ``with_signature`` can be stacked
either above or below ``@classmethod`` / ``@staticmethod``; both orders
produce correct introspection results. The conventional ordering is to
place ``@with_signature`` on top.

::

    class C:

        @wrapt.with_signature(prototype=_cm_proto)
        @classmethod
        def build(cls, *args, **kwargs):
            ...

        @wrapt.with_signature(prototype=_sm_proto)
        @staticmethod
        def twice(*args, **kwargs):
            ...

Stacking under other decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When another **wrapt** decorator is placed on top of ``@with_signature``,
the overridden signature is still reported by introspection on the outer
wrapper. Annotations, defaults, keyword defaults, and the argument
attributes of ``__code__`` all propagate upward through the wrapper
chain.

::

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @pass_through
    @wrapt.with_signature(prototype=_prototype)
    def function(*args, **kwargs):
        ...

    # inspect.signature(function) still reports the prototype's signature.

Combining with calling-convention markers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``with_signature`` controls *what the arguments look like*, but it does
not assert anything about the *calling convention* of the resulting
wrapper -- whether it is a coroutine function, a generator, an async
generator, or a plain sync function. Those concerns are expressed by
``mark_as_sync`` and ``mark_as_async``, described in the "Calling
Convention Markers and Adapters" section above. The two concerns are
deliberately orthogonal: ``with_signature`` only modifies the
argument-related ``co_flags`` bits (``CO_VARARGS`` and
``CO_VARKEYWORDS``, derived from the signature), while the markers only
modify the calling-convention bits (``CO_COROUTINE``,
``CO_ASYNC_GENERATOR``, ``CO_GENERATOR``, ``CO_ITERABLE_COROUTINE``).

Because the two decorators touch disjoint bits, they compose cleanly
when stacked. The conventional ordering is the marker on top, the
signature override underneath, but both orders produce the same
result:

::

    @wrapt.mark_as_sync
    @wrapt.with_signature(prototype=_prototype)
    async def real(*args, **kwargs):
        # inspect.iscoroutinefunction(real) -> False (from mark_as_sync)
        # inspect.signature(real)           -> prototype's signature
        ...

When the underlying callable is a generator of some kind and the
surrounding stack has changed that convention, the ``generator``
keyword on the markers is the right modifier:

::

    @wrapt.mark_as_async(generator=True)
    @wrapt.with_signature(prototype=_prototype)
    def real(*args, **kwargs):
        # inspect.isasyncgenfunction(real) -> True
        # inspect.signature(real)          -> prototype's signature
        yield ...

Use ``with_signature`` alone when only the signature needs correcting;
stack with a marker when the calling convention also needs to be
asserted independently of the wrapped function's own declaration.
