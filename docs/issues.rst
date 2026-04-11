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
