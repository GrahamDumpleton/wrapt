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
