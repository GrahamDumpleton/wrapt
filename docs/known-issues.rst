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
Python 3.4 for this issue is being pursued. The only solution is the
recommendation that decorators implemented using ``@wrapt.decorator``
always be placed outside of ``@classmethod`` and never inside.
