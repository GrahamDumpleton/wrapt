Known Issues
============

The following known issues exist.

@classmethod.\_\_get\_\_()
--------------------------

The Python ``@classmethod`` decorator assumes in the implementation of its
``__get__()`` method that the wrapped function is always a normal function.
It doesn't entertain the idea that the wrapped function could actually be a
descriptor, the result of a nested decorator. This is an issue because it
means that the complete descriptor binding protocol is not performed on
anything which is wrapped by the ``@classmethod`` decorator.

The consequence of this is that when ``@classmethod`` is used to wrap a
decorator implemented using ``@wrapt.decorator``, that ``__get__()`` isn't
called on the latter. The result is that it is not possible in the latter
to properly identify the decorator as being bound to a class method and
it will instead be identified as being associated with a normal function,
with the class type being passed as the first argument.

The behaviour of the Python ``@classmethod`` is arguably wrong and a fix to
Python for this issue is being pursued (http://bugs.python.org/issue19072).
The only solution is the recommendation that decorators implemented using
``@wrapt.decorator`` always be placed outside of ``@classmethod`` and never
inside.

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
    class Base(object):
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

If a class heirarchy has a base class which uses the ``abc.ABCMeta``
metaclass, and a decorator is applied to a class in the heirarchy, use of
``issubclass()`` with classes where the decorator is applied will result in
an exception of:

::

    TypeError: issubclass() arg 1 must be a class

This is due to what can be argued as being a bug in The Python standard
library and has been reported (https://bugs.python.org/issue44847).
