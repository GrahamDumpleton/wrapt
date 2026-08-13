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

The decorator accepts an optional keyword only ``enabled`` argument which
controls whether the wrapper actually runs. This follows the same rules as the ``enabled``
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
the attribute on it. The factory receives the current value and must return
a replacement.

The descriptor installed on the class is an ``AttributeWrapper``, which
``wrap_object_attribute`` returns. It is an object proxy wrapping whatever
previously occupied the class attribute, or the ``wrapt.MISSING`` sentinel
when nothing did, so the prior definition keeps working beneath the
interception. If the attribute was already implemented by a ``property`` or
other descriptor, reads, writes and deletes delegate to it, with the factory
wrapping the values it serves. If the class defined a plain default, it is
used as the fallback when no instance value exists. Applying
``wrap_object_attribute`` twice to the same attribute stacks the two
interceptions, with the outer factory wrapping the result of the inner one,
rather than the second application replacing the first.

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

When the temporary patch should span a block of code rather than a
function call, ``wrapt.scoped_function_wrapper()`` is the context
manager form. It takes the same arguments as ``wrap_function_wrapper``
and installs the wrapper when the ``with`` statement is entered,
removing it when the block exits.

::

    calls = []

    def capture_info(wrapped, instance, args, kwargs):
        calls.append((args, kwargs))
        return wrapped(*args, **kwargs)

    with wrapt.scoped_function_wrapper("logging", "Logger.info", capture_info):
        logging.getLogger().info("hello")

The context manager is single use, so call ``scoped_function_wrapper``
again for each ``with`` statement. Note that a decorated context
manager factory cannot be substituted for either form: applying
``transient_function_wrapper`` around a ``contextlib.contextmanager``
generator patches only the moment the generator is created, not the
body of the ``with`` block, since calling a generator function does
not run any of its code.

For both forms, removal on exit is deliberately loud about
interference. If code called within the scope of the patch removed or
replaced the temporary wrapper, ``WrapperNotFoundError`` is raised, and
if it wrapped over the top with something other than a wrapt wrapper
and left it there, ``WrapperNotOutermostError`` is raised; a wrapt
wrapper left applied on top is tolerated, with the temporary wrapper
spliced out beneath it. Both errors indicate the surrounding code is
not managing its own patches properly, and are raised so the problem
surfaces at the test responsible rather than as unexplained failures in
later tests.

Inspecting and Removing Patches
-------------------------------

Every wrap function returns the wrapper object it installed:
``wrap_function_wrapper`` and ``wrap_object`` return the wrapper placed
on the attribute, and ``wrap_object_attribute`` returns the descriptor
installed on the class. That returned object is the *handle* for the
patch, and it is the identity used for detecting and removing wrappers.
Code which may later need to check on or remove its patches should keep
the handles it receives, typically in a registry keyed by target and
attribute name.

::

    import wrapt

    registry = {}

    def instrument(module, name, wrapper):
        if (module, name) not in registry:
            registry[(module, name)] = wrapt.wrap_function_wrapper(
                module, name, wrapper)

    def uninstrument():
        while registry:
            (module, name), handle = registry.popitem()
            wrapt.unwrap_object(module, name, handle, missing_ok=True)

``wrapt.is_wrapped_by()`` answers whether the wrapper a handle was
returned for is still installed, and ``wrapt.find_wrapper()`` returns
the matching chain entry itself. Both match by object identity only,
never equality, which proxies delegate to the wrapped object, and both
accept a ``predicate`` function as an alternative to a handle. The
underlying traversal is exposed as ``wrapt.wrapper_chain()``, which
yields the wrapper stack outermost first ending with the original
object, and ``wrapt.unwrapped()``, which returns the original object
directly.

``wrapt.unwrap_object()`` removes the wrapper identified by a handle
and returns it. Several patches may have been applied over one another,
and removal handles each arrangement:

* When the wrapper is outermost, the attribute is restored to the
  object the wrapper wrapped, at the location where the attribute is
  actually defined per ``resolve_owner()``. Removal through a subclass
  therefore restores the defining base class, and if the wrap had
  created a shadowing slot, such as on a subclass, on an instance, or
  over a dynamically served value, the attribute is deleted instead,
  leaving no residue. The wrap functions record whether they created
  the slot on the wrapper itself at installation time, so this
  decision is exact for wrappers they installed.

* When the wrapper is buried beneath other wrapt wrappers, it is
  spliced out of the chain in place. The attribute itself is untouched
  and the wrappers above keep working, so independent parties can
  remove their patches in any order.

* When what sits directly above the wrapper is not a wrapt wrapper,
  for example a plain closure created with ``functools.wraps()``, its
  ``__wrapped__`` attribute is only metadata and updating it would not
  change behaviour, so ``WrapperNotOutermostError`` is raised naming
  what is above.

When the wrapper is not found at all, because the attribute was never
wrapped, the wrapper was already removed, or a third party replaced the
attribute wholesale, ``WrapperNotFoundError`` is raised by default so
that mistakes surface immediately. Cleanup code which must tolerate
such interference passes ``missing_ok=True`` to get ``None`` back
instead.

Note that a wrap deferred with the ``?`` target syntax returns ``None``
rather than a handle, since the wrapper does not exist until the module
is imported. If such a patch may need removing, either use a post
import hook so your own callback receives the handle, or recover the
installed wrapper after the import using ``find_wrapper()`` with a
predicate::

    handle = wrapt.find_wrapper(
        wrapt.resolve_path(module, "function")[2],
        predicate=lambda entry: getattr(
            entry, "_self_wrapper", None) is my_wrapper)

When checking a wrapped method of a class, obtain the object to scan
using ``wrapt.resolve_path()``, not ``getattr()``: accessing the method
on the class triggers descriptor binding and returns a fresh bound
wrapper in which the installed handle will not be found.

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

``wrap_object_attribute`` composes with prior definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The descriptor installed by ``wrap_object_attribute`` wraps whatever
previously occupied the class attribute. A prior ``property`` or other
descriptor keeps executing its own logic beneath the interception, a prior
plain class default serves as the fallback when no instance value exists,
and a second application stacks over the first rather than replacing it.
Earlier versions of wrapt replaced the class attribute outright, could not
be used over a ``property``, and broke class-level access to the attribute;
none of those limitations apply any longer.
