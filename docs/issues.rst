Known Issues
============

The following known issues exist.

@classmethod.\_\_get\_\_()
--------------------------

Prior to Python 3.9 the ``@classmethod`` decorator assumes in the
implementation of its ``__get__()`` method that the wrapped function
is always a normal function. It doesn't entertain the idea that the
wrapped function could actually be a descriptor, the result of a
nested decorator. This is an issue because it means that the complete
descriptor binding protocol is not performed on anything which is
wrapped by the ``@classmethod`` decorator.

The consequence of this is that when ``@classmethod`` is used to wrap a
decorator implemented using ``@wrapt.decorator``, that ``__get__()`` isn't
called on the latter. The result is that it is not possible in the latter
to properly identify the decorator as being bound to a class method and
it will instead be identified as being associated with a normal function,
with the class type being passed as the first argument.

The behaviour of the Python ``@classmethod`` was reported in the issue
(http://bugs.python.org/issue19072). Prior to Python 3.9, which is where
the Python interpreter was fixed, the only solution is the recommendation
that decorators implemented using ``@wrapt.decorator`` always be placed
outside of ``@classmethod`` and never inside.

Unfortunately, in Python 3.13 this change in Python was reverted back to the
old behaviour because various third party code relied on the broken behaviour
and even though technically not correct, it was deemed safer to revert the fix.
The original warning thus applies.

Using decorated class with super()
----------------------------------

In the implementation of a decorated class, if needing to use a reference
to the class type with super, it is necessary to access the original
wrapped class and use it instead of the decorated class.

::

    @mydecorator
    class Derived(Base):

        def __init__(self):
            super(Derived.__wrapped__, self).__init__()

If using Python 3, one can simply use ``super()`` with no arguments and
everything will work fine.

::

    @mydecorator
    class Derived(Base):

        def __init__(self):
            super().__init__()


Deriving from decorated class
-----------------------------

If deriving from a decorated class, it is necessary to access the original
wrapped class and use it as the base class.

::

    @mydecorator
    class Base:
        pass

    class Derived(Base.__wrapped__):
        pass

In doing this, the functionality of any decorator on the base class is not
inherited. If creation of a derived class needs to also be mediated via the
decorator, the decorator would need to be applied to the derived class also.

In this case of trying to decorate a base class in a class hierarchy, it
may turn out to be more appropriate to use a meta class instead of trying
to decorate the base class.

Note that as of Python 3.7 and wrapt 1.12.0, accessing the true type of the
base class using ``__wrapped__`` is not required. Such code though will not
work for versions of Python older than Python 3.7.

Using issubclass() on abstract classes
--------------------------------------

If a class hierarchy has a base class which uses the ``abc.ABCMeta``
metaclass, and a decorator is applied to a class in the hierarchy, use of
``issubclass()`` with classes where the decorator is applied will result in
an exception of:

::

    TypeError: issubclass() arg 1 must be a class

This is due to what can be argued as being a bug in The Python standard
library and has been reported (https://bugs.python.org/issue44847).

Using issubclass() and isinstance() with proxied types
-------------------------------------------------------

When wrapping a class (type) object with ``ObjectProxy``, the
``issubclass()`` and ``isinstance()`` checks work correctly when the
proxy appears on the **right** side of the check:

::

    import wrapt

    class Base:
        pass

    class Child(Base):
        pass

    proxy = wrapt.ObjectProxy(Base)

    issubclass(Child, proxy)       # True
    isinstance(Child(), proxy)     # True

This works because Python calls ``__subclasscheck__`` or
``__instancecheck__`` on the proxy, and ``ObjectProxy`` delegates these
to the wrapped type.

There are several cases that **cannot** be fixed when the proxy appears
on the **left** side of the check:

1. ``issubclass(proxy, WrappedClass)`` returns ``False`` when testing
   against the same class the proxy wraps. This is because CPython's
   ``issubclass()`` first performs an identity check (``proxy is
   WrappedClass``), which fails since the proxy is not the actual class.
   It then walks ``proxy.__bases__`` looking for the class, but a class
   is not in its own ``__bases__``. Checking against *ancestors* of the
   wrapped class works correctly since they are found via the
   ``__bases__`` walk.

   ::

       proxy = wrapt.ObjectProxy(Child)

       issubclass(proxy, Base)    # True — Base is in Child.__bases__
       issubclass(proxy, Child)   # False — identity check fails

2. ``issubclass(proxy, ABCClass)`` raises ``TypeError`` when the
   right-hand class uses ``abc.ABCMeta`` as its metaclass. The C-level
   ``__subclasscheck__`` in ``ABCMeta`` strictly requires its argument
   to be a real class. This is the same limitation described in the
   `Using issubclass() on abstract classes`_ section above.

3. ``isinstance(proxy, typing.Dict)`` and other ``typing`` generic
   aliases return ``False`` when the proxy wraps a matching value. This
   happens because ``typing._BaseGenericAlias.__instancecheck__`` is
   implemented using ``type(obj)`` rather than ``obj.__class__``.
   Because ``type()`` returns the concrete C-level type, it sees
   ``ObjectProxy`` instead of the wrapped object's class, and the check
   fails. This is a known CPython issue
   (https://github.com/python/cpython/issues/89949).

   ::

       from typing import Dict
       import wrapt

       proxy = wrapt.ObjectProxy({1: 2})

       isinstance(proxy, dict)    # True — default __instancecheck__ uses __class__
       isinstance(proxy, Dict)    # False — typing uses type(obj)

   The workaround is to check against the origin type instead::

       import typing

       isinstance(proxy, typing.get_origin(Dict))    # True

   Note that the newer parameterised generic syntax (``dict[str, int]``)
   does not support ``isinstance()`` checks at all — with or without a
   proxy — and raises ``TypeError``.

More generally, any ``__instancecheck__`` or ``__subclasscheck__``
implementation that calls ``type(obj)`` instead of inspecting
``obj.__class__`` will see ``ObjectProxy`` rather than the wrapped
type. The same applies to C-level type-check macros such as
``PyTuple_Check`` or ``PyDict_Check``, which inspect the internal
``ob_type`` field directly. Code paths that rely on these C-level
checks — for example, the C-accelerated JSON encoder in the standard
library — will not recognise a proxied object as the type it wraps::

    import json
    import wrapt

    proxy = wrapt.ObjectProxy((1, 2, 3))

    json.dumps(proxy)    # TypeError — C encoder does not see a tuple

This is an inherent limitation of the transparent proxy pattern: the
proxy can override ``__class__`` at the Python level, but it cannot
change the object's C-level type.

hasattr() on ObjectProxy and pre-defined dunder methods
-------------------------------------------------------

Although ``ObjectProxy`` is described as a transparent object proxy, in
practice it always defines a large number of Python "dunder" (double
underscore) methods on the proxy class itself, regardless of whether the
wrapped object defines the equivalent method. As a result, ``hasattr()``
checks for these dunder methods on the proxy always return ``True``,
even when the same check against the wrapped object directly would
return ``False``::

    import wrapt

    hasattr(wrapt.ObjectProxy(1), "__contains__")    # True
    hasattr(1, "__contains__")                       # False

This is a deliberate design trade-off rather than a bug.

For most Python special methods, the interpreter looks up the method on
the **type** of the object, not on the instance. That is how operators
such as ``x in obj``, ``len(obj)``, ``-obj``, ``obj + 1`` and so on are
dispatched internally. For these operations to delegate correctly to
the wrapped object, the corresponding dunder method must be defined on
the proxy class. A proxy class that did not define ``__contains__``,
``__len__``, ``__add__`` and the rest could not forward those
operations at all, regardless of what the wrapped object supports.

The obvious alternative, generating a custom proxy class per wrapped
object whose dunder methods exactly mirror those of the wrapped type,
is not free. Constructing a fresh class for every proxy instance adds
meaningful memory and construction-time overhead, which is a problem
when proxies are used pervasively (for example, when decorating every
function and method in a large codebase). ``ObjectProxy`` is intended
to be cheap enough to use in that setting, so it instead defines a
fixed set of dunder methods on a single shared class.

For the dunder methods that ``ObjectProxy`` pre-defines, this is
usually harmless in practice. Code that wants to use one of these
features, such as arithmetic, containment, length, comparison, hashing,
attribute access, subscripting or the context-manager protocol, almost
always just *uses* the feature directly. If the wrapped object does
not implement the corresponding dunder method, the shim on
``ObjectProxy`` will delegate through to ``self.__wrapped__`` and an
``AttributeError`` will be raised from there, which is the same
exception Python would raise for an object that didn't define the
method in the first place. Code that simply does ``len(obj)``,
``a in b`` or ``x + y`` therefore behaves correctly whether or not the
argument is a proxy.

The cases where this becomes a problem are the dunder methods whose
*existence* is itself meaningful, typically methods that Python
introspection APIs or user code probe for explicitly rather than just
invoking. The most common examples are:

* ``__call__``, probed by ``callable(obj)``.
* ``__iter__`` and ``__next__``, probed by code that distinguishes
  iterables from iterators, or that wants to decide whether an object
  can be iterated.
* ``__aiter__``, ``__anext__`` and ``__await__``, the async
  counterparts of the above, probed by async frameworks when deciding
  how to drive an object.
* Descriptor protocol methods ``__get__``, ``__set__``, ``__delete__``
  and ``__set_name__``, whose mere presence on a class attribute
  changes how Python treats that attribute.
* ``__length_hint__``, consulted by built-ins as an optimisation hint;
  its presence implies the object can cheaply estimate its length.

If ``ObjectProxy`` defined these unconditionally, ``callable(proxy)``
would always be ``True`` even when wrapping a non-callable, every
proxy would appear to be iterable, and every proxy attribute on a
class body would silently behave as a descriptor. To avoid those
incorrect answers, these specific methods are **not** defined on
``ObjectProxy`` by default. The trade-off is that if you want a proxy
around a callable (or an iterable, or an awaitable, and so on) to
itself be recognised as callable/iterable/awaitable, you have to opt
in.

There are two ways to opt in:

1. Define a derived proxy class that implements the required dunder
   methods explicitly. This is the preferred approach when you know at
   the point of wrapping what kind of object you are wrapping, and is
   the cheapest in terms of runtime cost. For example, to wrap a
   callable so that ``callable(proxy)`` returns ``True``::

       class CallableProxy(wrapt.ObjectProxy):
           def __call__(self, *args, **kwargs):
               return self.__wrapped__(*args, **kwargs)

   Equivalent subclasses can be defined for iterators, async
   iterators, awaitables and descriptors, adding only the dunder
   methods actually required.

2. Use ``AutoObjectProxy`` when the type of the wrapped object is not
   known statically, or varies. ``AutoObjectProxy`` inspects the
   wrapped object at construction time and dynamically creates a
   subclass that defines exactly those problematic dunder methods
   (``__call__``, ``__iter__``, ``__next__``, ``__aiter__``,
   ``__anext__``, ``__await__``, ``__length_hint__``, ``__get__``,
   ``__set__``, ``__delete__``, ``__set_name__``) that the wrapped
   object actually supports::

       import wrapt

       proxy = wrapt.AutoObjectProxy(lambda: 42)
       callable(proxy)    # True

       proxy = wrapt.AutoObjectProxy(42)
       callable(proxy)    # False

   The cost is that ``AutoObjectProxy`` generates a **new class per
   wrapped object**. That is significantly more expensive, in both
   time and memory, than using a pre-defined proxy class, and the
   generated classes are not deduplicated. ``AutoObjectProxy`` is
   therefore intended for situations where the flexibility is genuinely
   needed, typically a small number of long-lived proxies over objects
   of varying types, rather than as a drop-in replacement for
   ``ObjectProxy``.

The short version is that ``ObjectProxy`` chooses a fixed set of
pre-defined dunder methods as a compromise between transparency and
efficiency. The dunder methods whose presence is benign in practice
are defined unconditionally; the dunder methods whose presence would
give incorrect answers to introspection are left off, and opt-in is
provided via subclassing or ``AutoObjectProxy``. Code that relies on
``hasattr(proxy, "__some_dunder__")`` producing the same answer as
``hasattr(wrapped, "__some_dunder__")`` will therefore see mismatches
for the pre-defined set, and should either test the wrapped object
directly (via ``proxy.__wrapped__``) or use the feature and handle any
resulting ``AttributeError`` rather than probing for it.

\_\_qualname\_\_ snapshot vs live-read divergence
--------------------------------------------------

The Python and C implementations of ``ObjectProxy`` handle the
``__qualname__`` attribute differently. CPython does not allow
``__qualname__`` to be overridden via a Python property — it must be an
actual string object stored on the instance. To work around this, the
pure-Python ``ObjectProxy.__init__`` copies the wrapped object's
``__qualname__`` into the proxy's instance dictionary at construction
time using ``object.__setattr__()``. This creates a *snapshot* of the
value.

The C extension, by contrast, uses a ``PyGetSetDef`` descriptor to
live-read ``__qualname__`` from the wrapped object on every access.
C-level getset descriptors operate below the layer where CPython
enforces the "must be a real string" restriction, so this works without
issue.

The practical consequence is that if the wrapped object's ``__qualname__``
is mutated *directly* (not through the proxy) after wrapping, the two
implementations diverge::

    import wrapt

    def foo(): pass

    proxy = wrapt.ObjectProxy(foo)
    foo.__qualname__ = "Changed"

    # Pure-Python: proxy.__qualname__ returns the original value (snapshot)
    # C extension: proxy.__qualname__ returns "Changed" (live-read)

This only matters when code mutates ``__qualname__`` on the wrapped
object after the proxy has been constructed. Setting ``__qualname__``
*through* the proxy (``proxy.__qualname__ = "new"``) updates both the
wrapped object and the local snapshot in the Python implementation, so
both implementations agree in that case.

Free-threaded Python (PEP 703)
------------------------------

The C extension declares ``Py_mod_gil = Py_MOD_GIL_NOT_USED`` on Python
3.13 and later, which allows it to be loaded into a free-threaded build
without the runtime re-enabling the GIL on import. This declaration is
sound for the way **wrapt** is used in the overwhelming majority of
applications: a decorator is applied to a function or class at import
time, the resulting wrapper or proxy is published once, and from then on
it is only *read* (called, introspected, used as a descriptor) from
multiple threads. That pattern is safe on free-threaded builds.

The current implementation does **not**, however, guarantee safety when
a single proxy or wrapper instance is **mutated** from one thread while
another thread concurrently reads from or calls it. In particular, the
following operations are not race-free on free-threaded builds when the
same instance is shared across threads:

* Assigning to ``__wrapped__`` (or any other proxy attribute) on an
  ``ObjectProxy`` while another thread is calling, iterating, or
  performing attribute access on the same proxy.

* Reassigning fields on a ``FunctionWrapper`` (such as the ``enabled``
  callable, the ``wrapper`` function, or the bound instance) after
  construction, while another thread is invoking the wrapper.

* Replacing the captured ``args`` or ``kwargs`` on a
  ``PartialCallableObjectProxy`` while another thread is calling it.

In each case the writer's update is not atomic with respect to a
concurrent reader. A reader may observe a torn view of multiple proxy
fields, or, in the worst case, a use-after-free of an object that the
writer has just released. The same hazards exist in the pure-Python
implementation — Python attribute assignment is not atomic with respect
to readers in any meaningful sense — so the limitation is a property of
the proxy model, not specifically of the C extension.

The recommended pattern on free-threaded builds is therefore the same
as the pattern on GIL builds: construct the proxy or wrapper once,
publish it, and treat it as immutable thereafter. Concurrent readers
and concurrent calls are supported; concurrent mutation of a shared
instance is not.

More robust support for free-threaded Python — covering the
shared-mutation case via atomic field access and per-instance critical
sections — is being investigated for a future release. Until then,
applications that genuinely need to mutate a shared proxy from multiple
threads should serialise those mutations externally (for example, with
a ``threading.Lock`` held across both the write and any concurrent
read).

Introspecting the ObjectProxy instance \_\_dict\_\_
----------------------------------------------------

``ObjectProxy`` replaces ``__dict__`` with a property that delegates to
the wrapped object. This means that ``vars(proxy)`` returns the wrapped
object's ``__dict__`` rather than the proxy's own instance dictionary::

    import wrapt

    class Target:
        def __init__(self, name):
            self.name = name

    class MyProxy(wrapt.ObjectProxy):
        def __init__(self, wrapped):
            super().__init__(wrapped)
            self._self_tag = "example"

    target = Target("test")
    proxy = MyProxy(target)

    vars(proxy)       # {'name': 'test'} — no '_self_tag'

This is by design — the proxy is meant to be transparent — but it makes
it difficult to introspect what attributes are stored on the proxy
instance itself.

To allow introspection of the proxy's own instance dictionary,
``ObjectProxy`` exposes it as ``__self_dict__``::

    proxy.__self_dict__    # {'_self_tag': 'example', ...}

This returns the live instance dictionary of the proxy, so any
``_self_`` attributes set on the proxy will appear there. Mutations to
the returned dictionary are reflected on the proxy.

If the combined view of the wrapped object's ``__dict__`` together with
the proxy's own ``_self_`` attributes is desired as the result of
``vars()``, a derived ``ObjectProxy`` can override ``__dict__`` with its
own property::

    class IntrospectableProxy(wrapt.ObjectProxy):
        def __init__(self, wrapped):
            super().__init__(wrapped)
            self._self_tag = "example"
            self._self_count = 0

        @property
        def __dict__(self):
            result = self.__wrapped__.__dict__.copy()
            result.update(self.__self_dict__)
            return result

    target = Target("test")
    proxy = IntrospectableProxy(target)

    vars(proxy)       # includes 'name' from target and '_self_tag', '_self_count'

Note that because the result is a copy, modifying the dictionary returned
by ``vars()`` in this case will not affect either the proxy or the
wrapped object.

pytest setup_class/teardown_class hooks
----------------------------------------

Decorators implemented using ``@wrapt.decorator`` are silently bypassed
when applied to the ``setup_class`` or ``teardown_class`` xunit-style
hooks that ``pytest`` recognises on test classes. The decorator is never
invoked when ``pytest`` runs the hook, even though the same decorator
applied to a regular test method, or to ``setup_method`` /
``teardown_method``, works correctly.

The following test illustrates the problem::

    import wrapt

    @wrapt.decorator
    def pass_through(wrapped, instance, args, kwargs):
        return wrapped(*args, foo=1, **kwargs)

    class TestMyClass:
        @pass_through
        @classmethod
        def setup_class(cls, **kwargs):
            cls.kwargs = kwargs

        def test_something(self):
            assert self.kwargs == {'foo': 1}

When this is run under ``pytest``, ``test_something`` fails with
``kwargs`` equal to ``{}`` rather than ``{'foo': 1}``. The
``pass_through`` decorator is never called. Replacing its body with a
``raise`` confirms that the wrapper is not entered at all.

The cause is specific to how ``pytest`` invokes the class-level xunit
hooks. For these hooks, ``pytest`` does not use normal attribute access
on the class. Instead, it retrieves the attribute statically, then
extracts the underlying function object by reading ``__func__`` directly
(via an internal helper ``_pytest.compat.getimfunc``), and finally calls
that function with the class as an explicit first argument. The
equivalent of::

    cls.setup_class()        # normal, goes through descriptor protocol

is replaced by::

    func = setup_class.__func__    # reach past the descriptor
    func(cls)                       # call the raw function directly

Reading ``__func__`` off a ``@classmethod`` (or ``@staticmethod``)
returns the underlying plain function, that is, the original function
supplied to the method decorator. When a ``@wrapt.decorator`` has been applied
on top of the ``@classmethod``, ``wrapt``'s wrapper object sits between
the classmethod descriptor and the caller, and its behaviour is
delivered via the descriptor binding protocol. By reading ``__func__``
and calling the result directly, ``pytest`` bypasses the descriptor
binding protocol entirely, and with it any decorator that relies on
that protocol to inject itself into the call.

The same shortcut is taken for ``teardown_class``, and analogous
behaviour applies to the ``setup_class`` / ``teardown_class`` forms
whether the method is declared with ``@classmethod``, as a plain
function taking ``cls``, or as a zero-argument function. By contrast,
``setup_method`` and ``teardown_method`` are invoked by ``pytest`` via
normal attribute access on the instance, so the descriptor protocol is
honoured and ``@wrapt.decorator`` wrappers on those hooks work
correctly.

This is believed to be an issue in ``pytest`` rather than in ``wrapt``.
The Python descriptor binding protocol is the language-defined mechanism
for invoking methods, including ``@classmethod`` and ``@staticmethod``,
and decorators, proxies and other wrappers legitimately rely on it to
interpose on calls. Code that reaches past that protocol by extracting
``__func__`` and calling it directly will skip any wrapping applied via
the descriptor protocol, regardless of whether the wrapper is from
``wrapt`` or implemented by some other means. If ``pytest`` were to
follow normal Python practice, invoking the hook via attribute access on
the class and allowing the descriptor protocol to deliver the correctly
bound callable, the problem would not arise.

It is likely that the ``__func__`` extraction in ``pytest`` is a
historical shortcut rather than a considered design decision. Pytest
supports three different ways of declaring the class-level xunit hooks,
namely as a ``@classmethod``, as a plain function taking ``cls``, or as
a zero-argument function, and the ``__func__`` trick normalises all
three into a single uniform dispatch: always call the underlying plain
function with ``cls`` as an explicit argument. This was probably the
shortest path that worked across older versions of Python, and it has
remained in place ever since because it handles the common cases. The
same uniformity could be achieved today without reaching past the
descriptor protocol, for example by dispatching through normal
attribute access and using ``inspect.signature`` to decide how many
arguments to pass, but the original code has never been revisited to
match more current practice.

Until this is addressed upstream in ``pytest``, the practical workaround
is to avoid applying ``@wrapt.decorator`` directly on top of
``@classmethod`` or ``@staticmethod`` for the ``setup_class`` and
``teardown_class`` hooks. The decorated behaviour can instead be moved
into an ordinary helper method that the hook calls, or into a
``setup_method`` / ``teardown_method`` hook, both of which are dispatched
through normal attribute access and therefore honour decorators applied
via ``@wrapt.decorator``.
