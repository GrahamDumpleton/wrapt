Bundled Decorators
==================

The **wrapt** package ships a small number of ready-made decorators built on
top of the ``wrapt.decorator`` / ``FunctionWrapper`` machinery. This document
is a usage reference for those bundled decorators. For worked examples of how
decorators of this kind can be constructed from scratch using **wrapt**, see
:doc:`examples`.

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
