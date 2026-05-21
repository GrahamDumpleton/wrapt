Monkey Patching
===============

Monkey patching is the technique of modifying a function, method or other
attribute on a module or class after it has already been defined, typically to
add behaviour around an existing implementation without changing the original
source. The **wrapt** module provides a small set of helpers that build on
the same ``FunctionWrapper`` and ``ObjectProxy`` machinery used by
``@wrapt.decorator``, so monkey patches benefit from the same correct handling
of instance methods, class methods, static methods and nested descriptors,
and preserve introspection of the underlying target.

This document covers the monkey patching helpers and the related post import
hook mechanism used to defer patching until a target module is actually
imported. For the signature and semantics of the wrapper function used in the
examples below, see :doc:`decorators`. For the object proxy machinery that
wrappers are built on, see :doc:`wrappers`.

Wrapping Functions and Methods
------------------------------

The most common task is replacing a function or method on a module or class
with a version that runs extra behaviour around the original. The
``wrapt.wrap_function_wrapper()`` function performs this in one step.

The first argument is the target holding the attribute. It can be a module, a
class, or an instance of a class. As a convenience it can also be the name of
a module as a string, in which case the module will be imported if it has not
been already. The second argument is a dotted path to the attribute within
that target. The third argument is a wrapper function that follows the same
signature used by ``@wrapt.decorator``.

::

    import wrapt

    def notify(wrapped, instance, args, kwargs):
        print(f"calling {wrapped.__name__}")
        return wrapped(*args, **kwargs)

    wrapt.wrap_function_wrapper("logging", "Logger.info", notify)

The ``wrapped``, ``instance``, ``args`` and ``kwargs`` parameters behave
exactly as they do in a decorator wrapper. In particular, when patching an
instance method, ``instance`` is the bound receiver and ``args`` contains only
the arguments the caller passed, never a separate ``self``.

The ``name`` argument is a dotted path, so attributes reached through a chain
of owners can be patched in a single call. For example,
``"Outer.Inner.method"`` walks from ``Outer`` down to ``Inner`` before
replacing ``method``.

Resolving methods defined on a class is not the same as accessing them via
``getattr()``. Accessing a method on a class triggers the descriptor protocol
and returns a function bound to ``None`` rather than the raw function object
stored in the class namespace. ``wrap_function_wrapper`` avoids this by
looking through the class ``__dict__`` directly, walking the method
resolution order to find where the attribute was actually defined. This is
something you should avoid doing by hand; use ``wrap_function_wrapper`` (or
the lower level ``wrapt.resolve_path()`` described below) rather than chaining
``getattr()`` calls to reach the target.

The ``wrapt.patch_function_wrapper`` Decorator
----------------------------------------------

An equivalent form that reads more naturally at module scope is
``@wrapt.patch_function_wrapper``. It is applied to a wrapper function and
installs the same patch as ``wrap_function_wrapper()``, but the target and
attribute are supplied as decorator arguments.

::

    import wrapt

    @wrapt.patch_function_wrapper("logging", "Logger.info")
    def notify(wrapped, instance, args, kwargs):
        print(f"calling {wrapped.__name__}")
        return wrapped(*args, **kwargs)

The patch is applied as a side effect of evaluating the decorator, so simply
importing the module that contains the decorated wrapper is enough to install
the patch.

The decorator accepts an optional ``enabled`` argument which controls whether
the wrapper actually runs. This follows the same rules as the ``enabled``
argument of ``@wrapt.decorator``. A boolean value is read once: if ``False``,
the wrapper is bypassed and the original function is called directly. A
callable is invoked on every call and its result decides each time whether
the wrapper runs.

::

    DEBUG = False

    @wrapt.patch_function_wrapper("logging", "Logger.info", enabled=DEBUG)
    def notify(wrapped, instance, args, kwargs):
        print(f"calling {wrapped.__name__}")
        return wrapped(*args, **kwargs)

The ``wrapt.function_wrapper`` Decorator
----------------------------------------

``@wrapt.function_wrapper`` is a lighter variant of ``@wrapt.decorator``
intended for use inside monkey patching code. Applied to a wrapper function,
it turns it into a decorator built on ``FunctionWrapper``, with correct
handling of the descriptor protocol for bound methods and class methods, but
without the additional features of ``@wrapt.decorator`` such as the
``adapter`` or ``enabled`` arguments.

::

    import wrapt

    @wrapt.function_wrapper
    def notify(wrapped, instance, args, kwargs):
        print(f"calling {wrapped.__name__}")
        return wrapped(*args, **kwargs)

    class Service:
        def ping(self):
            return "pong"

    Service.ping = notify(Service.ping)

The result of applying ``@wrapt.function_wrapper`` is itself a ``wrapt``
wrapper, so it can be used either as an in place decorator as shown above,
or passed directly as the ``wrapper`` argument to ``wrap_function_wrapper``
and friends. For user facing decorators, prefer ``@wrapt.decorator``. For
wrappers you intend to apply through the monkey patching helpers,
``@wrapt.function_wrapper`` is the lower overhead option.

Wrapping Arbitrary Attributes
-----------------------------

Not every monkey patch replaces a function. When the target is some other
kind of object, or the replacement is a custom proxy rather than a
``FunctionWrapper``, the lower level helper ``wrapt.wrap_object()`` takes any
factory callable.

The factory is called with the original attribute value followed by any
positional and keyword arguments supplied through ``args`` and ``kwargs``.
Its return value replaces the attribute on the parent. ``wrap_object`` then
returns the replacement for convenience.

::

    import wrapt

    class CountingProxy(wrapt.ObjectProxy):
        def __init__(self, wrapped):
            super().__init__(wrapped)
            self._self_count = 0

        def __call__(self, *args, **kwargs):
            self._self_count += 1
            return self.__wrapped__(*args, **kwargs)

    counter = wrapt.wrap_object("math", "sqrt", CountingProxy)

For cases where ``wrap_object`` is still too high level, ``wrapt.resolve_path``
and ``wrapt.apply_patch`` expose the two steps it performs. ``resolve_path``
returns a three tuple of ``(parent, attribute, original)`` for a dotted path,
taking the same kind of target argument as ``wrap_function_wrapper``.
``apply_patch`` is a thin wrapper around ``setattr`` that sets the replacement
back on the parent.

::

    parent, attribute, original = wrapt.resolve_path("math", "sqrt")
    wrapt.apply_patch(parent, attribute, CountingProxy(original))

This is the same sequence that ``wrap_object`` performs internally. Use
``resolve_path`` directly when you need access to the original value for
purposes other than wrapping, for example to capture it in a closure or to
restore it later.

Wrapping Instance Attributes
----------------------------

``wrap_function_wrapper`` and ``wrap_object`` replace attributes on the owner
(a module, class or instance). That works well for functions and methods
because methods live on the class. It does not work for instance attributes
that live in ``self.__dict__``, because those values are set by each instance
individually, typically in ``__init__``.

``wrapt.wrap_object_attribute()`` handles this case by installing a descriptor
on the class rather than the instance. On every attribute read, the
descriptor fetches the real value from ``instance.__dict__`` and passes it
through a factory, letting the factory return a wrapper around the current
value each time.

::

    import wrapt

    class LoggedValue(wrapt.ObjectProxy):
        def __repr__(self):
            return f"LoggedValue({self.__wrapped__!r})"

    class Widget:
        def __init__(self, name):
            self.name = name

    wrapt.wrap_object_attribute(__name__, "Widget.name", LoggedValue)

    >>> Widget("spinner").name
    LoggedValue('spinner')

The attribute name must be a dotted path that identifies the owning class and
the attribute on it. The factory receives the current value stored in the
instance dictionary and must return a replacement.

Because the hook is a descriptor installed on the class, it cannot be
applied to an attribute that is already implemented by a ``property`` or
other data descriptor on the same class: the original descriptor would take
precedence and the value would never be read from the instance dictionary.
Apply ``wrap_object_attribute`` only to plain instance attributes.

Deferring Patches Until Import
------------------------------

A monkey patch can only wrap an attribute that already exists, so the target
module must have been imported by the time the patch is applied. Applying a
patch too early fails with an import error, and applying it too late misses
any code that has already been executed.

Deferring with the ``?`` shortcut
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both ``wrap_function_wrapper`` and ``patch_function_wrapper`` support a
convenience form where the target module name ends with a question mark.
When this form is used, the patch is applied immediately if the module is
already imported; otherwise, application is deferred until the module is
imported for the first time.

::

    import wrapt

    @wrapt.patch_function_wrapper("requests?", "Session.get")
    def notify(wrapped, instance, args, kwargs):
        print("GET", args, kwargs)
        return wrapped(*args, **kwargs)

This form is convenient when you know the patch file may be loaded either
before or after the target module, and you do not need any logic beyond
"apply as soon as possible".

Post import hooks
~~~~~~~~~~~~~~~~~

For more general deferred behaviour, ``wrapt`` provides a post import hook
mechanism styled after PEP 369. ``wrapt.register_post_import_hook()``
registers a callback to be invoked once a module with a given name has been
imported. If the module is already imported at the time of registration,
the callback fires immediately.

::

    import wrapt

    def install_patches(module):
        wrapt.wrap_function_wrapper(module, "Session.get", notify)

    wrapt.register_post_import_hook(install_patches, "requests")

The callback receives the imported module as its only argument, so the patch
code is free to pass it straight back to ``wrap_function_wrapper`` or any
other wrapt helper.

The ``hook`` argument may also be supplied as a string of the form
``"package.module:function"``. In that case, the registration does not import
the named module until the target is itself imported, which is useful when
the patch code lives in a module that you do not want loaded unless it is
actually needed.

The decorator form ``@wrapt.when_imported()`` is equivalent to
``register_post_import_hook`` with the decorated function as the callback.

::

    @wrapt.when_imported("requests")
    def install_patches(module):
        wrapt.wrap_function_wrapper(module, "Session.get", notify)

Post import hooks address a subtle ordering problem. If a monkey patch is
applied after the target module has already been imported, any code that has
already executed a binding like ``from target import function`` will still be
using the original, unpatched reference. Registering a post import hook from
the earliest point in the application ensures that the patch is in place
before other modules have had a chance to cache references.

Discovering patches via entry points
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Patching code can be packaged and distributed as a plugin, with the target
module names declared as entry points in the package metadata.
``wrapt.discover_post_import_hooks()`` loads every entry point in a named
group and registers it as a post import hook, using the entry point name as
the target module name.

::

    wrapt.discover_post_import_hooks("my_app.patches")

A plugin package then declares entries in that group in its package
configuration, for example in ``pyproject.toml``::

    [project.entry-points."my_app.patches"]
    requests = "my_patches.requests_patches:apply"

Each entry point target is a callable which accepts the imported module and
is free to call any of the monkey patching helpers on it. This approach keeps
the decision of *which* patches to apply in the hands of the application,
while the patches themselves live in separately installable packages.

Temporary Patches for Tests
---------------------------

Some monkey patches only need to be in force for the duration of a particular
call, typically a test. ``@wrapt.transient_function_wrapper()`` creates a
decorator that, when applied to a function, installs the patch before each
call to that function and removes it afterwards.

::

    import wrapt

    @wrapt.transient_function_wrapper("logging", "Logger.info")
    def capture_info(wrapped, instance, args, kwargs):
        calls.append((args, kwargs))
        return wrapped(*args, **kwargs)

    calls = []

    @capture_info
    def run():
        logging.getLogger().info("hello")

    run()

The patch is installed on entry to ``run`` and removed on exit, even if the
decorated call raises. This makes ``transient_function_wrapper`` well suited
to replacing ``unittest.mock.patch`` in cases where you want the richer wrapt
wrapper signature and the correct handling of bound methods. A fuller
testing example that builds on this pattern is covered in :doc:`examples`.

Pitfalls and Guidelines
-----------------------

The monkey patching helpers hide most of the subtleties, but a few recurring
issues are worth keeping in mind.

Reach methods through the class, not ``getattr``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Accessing a method on a class via ``getattr()`` invokes the descriptor
protocol and returns a function bound to ``None``, which is not the same
object stored in the class namespace. Code that tries to save the original
method by reading it this way, patch the class, and then restore it later,
will fail to restore the correct object. Use ``wrapt.resolve_path()`` (or the
higher level helpers that call it) to obtain the raw attribute in a way that
walks the MRO and reads from ``__dict__`` directly.

Watch out for cached references
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a module has executed ``from other_module import name``, the importing
module has its own binding for ``name``. Patching ``other_module.name`` after
that point does not affect callers that reached the function through the
alias. The safest approaches are to apply the patch before any consumer of
the target has been imported (which is exactly what post import hooks are
for), or to apply the patch at the module where the alias lives as well as
at the original owner.

Respect the ``instance`` argument rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a monkey patch targets a method, the wrapper function receives
``instance`` as the bound receiver (the instance for instance methods, or
the class for class methods) and ``instance`` is ``None`` for normal
functions and static methods. The ``wrapped`` callable passed in has already
been bound, so always call it as ``wrapped(*args, **kwargs)``, without
inserting ``instance`` yourself. These rules match the decorator wrapper
rules described in :doc:`decorators`.

Do not use ``wrap_object_attribute`` over a ``property``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``wrap_object_attribute`` installs a descriptor that reads from
``instance.__dict__``. If the class already defines a data descriptor such as
a ``property`` for the same attribute, the existing descriptor will take
precedence and the wrap will have no effect. Apply it only to plain instance
attributes.
