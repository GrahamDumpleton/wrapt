API Reference
=============

This page lists everything that the **wrapt** package exposes as part of
its public API, with a short description of each item and pointers into
the rest of the documentation for further detail.

Public API Contract
-------------------

Everything that **wrapt** considers part of its public API is re-exported
from the top-level ``wrapt`` module and listed in ``wrapt.__all__``. The
intended way to use the package is to import these names from ``wrapt``
directly.

::

    import wrapt

    @wrapt.synchronized
    def function():
        ...

The submodules of the ``wrapt`` package (for example ``wrapt.wrappers``,
``wrapt.decorators``, ``wrapt.synchronization``, ``wrapt.proxies``,
``wrapt.patches``, ``wrapt.importer``, ``wrapt.caching``,
``wrapt.signature``, ``wrapt.weakrefs``) are private implementation
detail. The internal layout of these modules, and the location of any
individual name within them, can change between releases without notice.
If a name is not listed below, or is not exposed from the top-level
``wrapt`` module, do not import it.

A practical example of why this matters: in version 2.2.0 the
``synchronized`` decorator was moved from ``wrapt.decorators`` to a new
``wrapt.synchronization`` submodule as part of a code reorganisation.
Code that was importing ``wrapt.synchronized`` continued to work
unchanged. Code that had reached in and imported
``wrapt.decorators.synchronized`` directly broke. The first form is
supported; the second form was never part of the public API.

Public API Surface
------------------

The names below are everything currently exported from ``wrapt``. They
are grouped by area of functionality rather than by submodule. Each
entry has a short description and, where applicable, a pointer to the
relevant section of the rest of the documentation.

Decorator Factories
~~~~~~~~~~~~~~~~~~~

``wrapt.decorator``
    The primary decorator factory for building well-behaved decorators.
    Applied to a wrapper function of the form
    ``wrapper(wrapped, instance, args, kwargs)``, it produces a
    decorator that preserves introspection, descriptor binding,
    signatures, and applies correctly to plain functions, instance
    methods, class methods, static methods, and classes. Supports
    optional ``enabled``, ``adapter`` and ``proxy`` keyword arguments.
    See :doc:`decorators` for the full guide.

``wrapt.function_wrapper``
    A lightweight subset of ``wrapt.decorator`` intended for the
    straightforward case of wrapping a function with a wrapper of the
    same shape, with no need for ``enabled``, ``adapter`` or a custom
    ``proxy``. Commonly used together with ``wrapt.wrap_function_wrapper``
    and ``wrapt.patch_function_wrapper`` for monkey patching. See
    :doc:`monkey` for usage in patching scenarios.

``wrapt.AdapterFactory``
    Base class for factory objects that compute a signature adapter at
    decoration time from the function being wrapped. Used as the
    ``adapter`` argument to ``wrapt.decorator``. The newer
    ``wrapt.with_signature`` mechanism is the recommended replacement;
    see :doc:`bundled` for details.

``wrapt.adapter_factory``
    Convenience callable that wraps a plain function as an
    ``AdapterFactory``. Equivalent to a factory that returns whatever
    its argument returns when called with the wrapped function.
    Superseded by ``wrapt.with_signature(factory=...)``.

``wrapt.bind_state_to_wrapper``
    Descriptor decorator that supports the pattern of implementing a
    decorator as a method on a state-holding class. When the wrapper
    method is accessed through an instance, the instance is automatically
    attached as a named attribute on the resulting wrapper, making
    per-decoration state reachable from the decorated function. See the
    "Binding State to a Wrapper" section of :doc:`bundled`.

Bundled Decorators
~~~~~~~~~~~~~~~~~~

``wrapt.synchronized``
    Decorator and context manager that associates a lock with a
    callable or context. Detects synchronous versus asynchronous use
    automatically and creates either a ``threading.RLock`` or an
    ``asyncio.Lock`` as appropriate. May also be supplied with an
    explicit lock primitive. See the "Thread Synchronization" section
    of :doc:`bundled`.

``wrapt.mark_as_sync``
    Pass-through wrapper that asserts the effective calling convention
    of its target is synchronous, so that
    ``inspect.iscoroutinefunction()`` (and code that consults it,
    including ``wrapt.synchronized``) reports it that way. Useful when
    an inner decorator has collapsed an ``async def`` into a sync
    callable. See "Calling Convention Markers and Adapters" in
    :doc:`bundled`.

``wrapt.mark_as_async``
    Symmetric to ``mark_as_sync``. Marks the target as asynchronous
    (or as an async generator, via the ``generator`` keyword) without
    altering how it is called. See "Calling Convention Markers and
    Adapters" in :doc:`bundled`.

``wrapt.async_to_sync``
    Adapts an async callable so it can be invoked synchronously. Each
    call runs the coroutine to completion via ``asyncio.run()`` and
    marks the resulting wrapper as synchronous for introspection
    purposes. See "Bridging between conventions" in :doc:`bundled`.

``wrapt.sync_to_async``
    Adapts a synchronous callable so it can be awaited. Each call
    schedules the work on the default executor via
    ``loop.run_in_executor()`` and marks the resulting wrapper as
    asynchronous for introspection purposes. See "Bridging between
    conventions" in :doc:`bundled`.

``wrapt.with_signature``
    Overrides the signature reported by introspection tools
    (``inspect.signature()``, ``help()``, IDE tooling) for a wrapped
    callable without mutating the wrapped function itself. Accepts a
    prototype function, an ``inspect.Signature`` object, or a factory
    callable. The modern replacement for the ``adapter`` argument of
    ``wrapt.decorator``. See the "Signature Override" section of
    :doc:`bundled`.

``wrapt.lru_cache``
    A drop-in replacement for ``functools.lru_cache`` that handles
    instance methods correctly. Each instance maintains its own cache
    stored as an attribute on the instance, so instances do not need
    to be hashable, each instance gets its own ``maxsize`` budget, and
    caches are released when the instance is garbage collected. For
    plain functions, class methods, and static methods, behaves the
    same as ``functools.lru_cache``. See the "LRU Cache" section of
    :doc:`bundled`.

Monkey Patching
~~~~~~~~~~~~~~~

``wrapt.resolve_path``
    Resolves a dotted attribute path on a target object (which may be
    a module, class, instance, or the name of a module to import) and
    returns a ``(parent, attribute, original)`` tuple suitable for
    subsequent patching. See :doc:`monkey`.

``wrapt.apply_patch``
    Thin convenience over ``setattr`` for setting a replacement
    attribute on a parent object as the final step of a patch. Pairs
    with ``wrapt.resolve_path``.

``wrapt.wrap_object``
    Replaces an attribute on a target object with the result of calling
    a factory function on the original attribute value. The typical
    factory is ``wrapt.FunctionWrapper`` or a subclass.

``wrapt.wrap_object_attribute``
    Variant of ``wrap_object`` that wraps an instance attribute by
    installing a descriptor on the owning class. Useful when the
    attribute is not defined at the class level itself.

``wrapt.wrap_function_wrapper``
    Convenience wrapper that combines ``resolve_path`` and
    ``wrap_object`` with ``FunctionWrapper`` to patch a function
    attribute with a wrapper of the
    ``wrapper(wrapped, instance, args, kwargs)`` form. If the target
    module name is suffixed with ``?``, the patch is deferred via a
    post-import hook until the module is imported.

``wrapt.patch_function_wrapper``
    Decorator form of ``wrap_function_wrapper``. Apply it to a wrapper
    function and the wrapper will be installed on the named attribute
    of the target. Supports the same deferred ``?`` syntax and an
    optional ``enabled`` flag.

``wrapt.transient_function_wrapper``
    Decorator that installs a wrapper on a target attribute only for
    the duration of a single call to the decorated function. Useful
    for scoped test fixtures and similar narrow patches.

Post Import Hooks
~~~~~~~~~~~~~~~~~

``wrapt.register_post_import_hook``
    Registers a callback to be invoked when a named module is imported,
    or immediately if the module is already loaded. The first
    registration installs an import hook into ``sys.meta_path``
    automatically. See :doc:`monkey`.

``wrapt.when_imported``
    Decorator form of ``register_post_import_hook``. Apply it to a
    function with a single ``module`` argument to have the function
    invoked when the named module is imported.

``wrapt.notify_module_loaded``
    Manually fires any post-import hooks registered against the given
    module. The import hook finder calls this automatically; this
    function exists for cases where modules are loaded by other means.

``wrapt.discover_post_import_hooks``
    Registers post-import hooks declared as entry points under a given
    group name in package metadata. Allows third-party packages to
    register hooks declaratively.

Object Proxies
~~~~~~~~~~~~~~

``wrapt.BaseObjectProxy``
    The transparent object proxy base class. Forwards attribute access,
    descriptor binding, equality, hashing, and most special methods to
    the wrapped object stored on ``__wrapped__``. The recommended base
    for custom proxy subclasses. See :doc:`wrappers` and the "Object
    Proxies" section of :doc:`typing`.

``wrapt.ObjectProxy``
    A thin subclass of ``BaseObjectProxy`` retained for backward
    compatibility. The only behavioural difference from
    ``BaseObjectProxy`` is that it also forwards ``__iter__``. New code
    that does not need this can use ``BaseObjectProxy`` directly.

``wrapt.AutoObjectProxy``
    A proxy that dynamically adds the appropriate special dunder methods
    (``__call__``, ``__iter__``, ``__await__``, descriptor methods, and
    so on) for the wrapped object at construction time. Has higher
    per-instance overhead than ``BaseObjectProxy`` because a fresh
    subclass is generated for each instance. Useful when the set of
    methods needed cannot be known up front.

``wrapt.LazyObjectProxy``
    A proxy whose wrapped object is created lazily on first use, via a
    callback supplied at construction time. Builds on
    ``AutoObjectProxy`` and accepts an optional ``interface`` keyword
    to declare the set of dunder methods to forward without having to
    instantiate the wrapped object first.

``wrapt.CallableObjectProxy``
    A proxy subclass that adds ``__call__`` forwarding for cases where
    the wrapped object is known to be callable but the rest of
    ``AutoObjectProxy``'s flexibility is not needed.

``wrapt.PartialCallableObjectProxy``
    A proxy that combines a callable with a set of pre-bound positional
    and keyword arguments, analogous to ``functools.partial`` but
    implemented as an object proxy.

``wrapt.partial``
    Factory function that returns a ``PartialCallableObjectProxy``,
    providing a drop-in replacement for ``functools.partial`` with
    better introspection.

``wrapt.lazy_import``
    Returns a ``LazyObjectProxy`` configured to import a named module
    (and optionally retrieve a specific attribute from it) the first
    time the proxy is used.

Function Wrappers
~~~~~~~~~~~~~~~~~

``wrapt.FunctionWrapper``
    The runtime wrapper class produced by ``@wrapt.decorator`` and
    ``@wrapt.function_wrapper`` when applied to a function. Handles
    descriptor binding, the ``enabled`` predicate, and dispatch to the
    user-supplied wrapper. May be constructed directly when more
    control is needed. See :doc:`wrappers` and the "Function Wrappers"
    section of :doc:`typing`.

``wrapt.BoundFunctionWrapper``
    The bound counterpart of ``FunctionWrapper``, produced when a
    decorated method is accessed via the descriptor protocol on an
    instance or class. Rarely constructed directly; appears in type
    annotations and during introspection of bound decorated methods.

Weak References
~~~~~~~~~~~~~~~

``wrapt.WeakFunctionProxy``
    A proxy that holds a weak reference to a function or bound method.
    Unlike ``weakref.proxy``, it correctly handles bound methods, which
    are transient objects, by holding weak references to the underlying
    instance and unbound function separately and rebinding on call.
    Accepts an optional callback invoked when the underlying object is
    garbage collected.

Type Hints and the Public API
-----------------------------

Type hints for **wrapt** are shipped as a single ``__init__.pyi`` stub
file in the ``wrapt-stubs`` distribution. The stub declares only the
names that the top-level ``wrapt`` module exposes. There are no
``.pyi`` files for the implementation submodules.

This has a direct, practical consequence: if you import a name from one
of the submodules instead of from ``wrapt``, static type checkers will
not see any annotations for it, even if there is an equivalent
annotated name available from ``wrapt``. The two forms below behave
the same at runtime but differ for the type checker:

::

    import wrapt
    from wrapt.synchronization import synchronized  # not type-hinted

    @wrapt.synchronized        # type-checked
    def good():
        ...

    @synchronized              # not type-checked
    def bad():
        ...

For type inference to work, always import from ``wrapt``. See
:doc:`typing` for a full discussion of how the type hints work and
what they do and do not propagate.

C Extension and Pure Python Implementations
-------------------------------------------

A small number of the most performance-sensitive classes in **wrapt**
have two implementations: a C extension module compiled from
``src/wrapt/_wrappers.c``, and an equivalent pure Python implementation
in ``wrapt.wrappers``. The classes that have a C implementation are:

* ``BaseObjectProxy`` (the C extension exposes this as ``ObjectProxy``;
  **wrapt** imports it under the ``BaseObjectProxy`` name)
* ``CallableObjectProxy``
* ``PartialCallableObjectProxy``
* ``FunctionWrapper``
* ``BoundFunctionWrapper``

When you import these from the top-level ``wrapt`` module, the C
extension version is used whenever it is available. The pure Python
implementation is used only as a fallback when the C extension cannot
be imported.

All of the other names listed above (``AutoObjectProxy``,
``LazyObjectProxy``, ``ObjectProxy``, the decorator factories, the
bundled decorators, the monkey-patching helpers, the post-import hook
machinery, ``WeakFunctionProxy``, and so on) are pure Python code
built on top of those core classes. They transparently use whichever
implementation of the core classes is active.

How the choice is made
~~~~~~~~~~~~~~~~~~~~~~

The **wrapt** package on PyPI ships binary wheels with the C extension
pre-compiled for the common Python versions and platforms. If
**wrapt** is installed from one of those wheels (which is what ``pip``
or ``uv`` will normally select), the C extension is present and is used
by default.

When **wrapt** is installed from the source distribution (the
``.tar.gz`` on PyPI), the build system attempts to compile the C
extension. If a working C compiler is not available, the extension is
silently omitted from the install and the package falls back to the
pure Python implementation at import time.

So in a normal installation you will be using the C extension. The
pure Python implementation only comes into play when no wheel is
available for your platform and your environment has no compiler, or
when you deliberately disable the extension.

Forcing the pure Python implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are three escalating ways to make **wrapt** use the pure Python
implementation. Pick the least invasive one that fits your situation.

**1. Disable the C extension at runtime.** Set
``WRAPT_DISABLE_EXTENSIONS=true`` in the environment before **wrapt**
is imported. The C extension may be installed, but **wrapt** will not
import it and will use the pure Python implementation instead. This
is the simplest option and is reversible without touching the install.

**2. Disable the C extension at install time.** Force installation
from the source distribution and set ``WRAPT_INSTALL_EXTENSIONS=false``
in the environment for the build, so that the extension is not built
even if a compiler is available. For example, with ``pip``:

::

    WRAPT_INSTALL_EXTENSIONS=false pip install --no-binary=wrapt wrapt

**3. Install from source with no compiler available.** Force
installation from the source distribution; if no C compiler is
present, the build of the extension is treated as optional and the
package is installed with only the pure Python implementation.

::

    pip install --no-binary=wrapt wrapt

Using pure Python core classes while keeping the C extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need the C extension to remain active for the rest of the
package but specifically want the pure Python implementation of
``BaseObjectProxy`` or ``FunctionWrapper`` (for example to subclass
them in a way that depends on Python-level implementation details that
the C extension does not expose), the only way to do this is to
import them directly from the private ``wrapt.wrappers`` submodule:

::

    from wrapt.wrappers import ObjectProxy as BaseObjectProxy
    from wrapt.wrappers import FunctionWrapper

This sidesteps the normal public API contract and comes with several
caveats. You should be aware of all of them before relying on this
approach:

* These names live in a private submodule. The module path
  ``wrapt.wrappers`` is not part of the public API and may be
  reorganised in a future release.
* Type hints are not available for names imported this way (see the
  "Type Hints and the Public API" section above).
* Only these two specific classes can be replaced with their pure
  Python variants in this way. Everything else that **wrapt** exposes
  -- including ``wrapt.ObjectProxy``, ``wrapt.AutoObjectProxy``,
  ``wrapt.LazyObjectProxy``, ``wrapt.decorator``,
  ``wrapt.function_wrapper``, ``wrapt.synchronized``, and the
  monkey-patching helpers -- is built on top of the C extension
  versions of the core classes and will continue to use them.

If you find yourself needing this, consider whether disabling the C
extension entirely via ``WRAPT_DISABLE_EXTENSIONS`` would actually
serve you better. The case for the targeted import is narrow: it is
appropriate only when you genuinely need both implementations to be
present in the same process.
