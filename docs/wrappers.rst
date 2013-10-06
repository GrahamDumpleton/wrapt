Wrappers
========

Underlying the implementation of the decorators created by the **wrapt**
module is a wrapper class which acts as a transparent object proxy. This
document describes the object proxy and the various custom wrappers provided.

Object Proxy
------------

The object proxy class is available as ``wrapt.ObjectProxy``. The class
would not normally be used directly, but as a base class to custom object
proxies or wrappers which add behaviour which overrides that of the
original object. When an object proxy is used, it will pass through any
actions performed on the proxy through to the wrapped object.

::

    >>> table = {}
    >>> proxy = wrapt.ObjectProxy(table)
    >>> proxy['key-1'] = 'value-1'
    >>> proxy['key-2'] = 'value-2'

    >>> proxy.keys()
    ['key-2', 'key-1']
    >>> table.keys()
    ['key-2', 'key-1']

    >>> isinstance(proxy, dict)
    True

    >>> dir(proxy)
    ['__class__', '__cmp__', '__contains__', '__delattr__', '__delitem__',
    '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__',
    '__getitem__', '__gt__', '__hash__', '__init__', '__iter__', '__le__',
    '__len__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__',
    '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__',
    '__subclasshook__', 'clear', 'copy', 'fromkeys', 'get', 'has_key',
    'items', 'iteritems', 'iterkeys', 'itervalues', 'keys', 'pop',
    'popitem', 'setdefault', 'update', 'values']

This ability for a proxy to stand in for the original goes as far as
arithmetic operations, rich comparison and hashing.

::

    >>> value = 1
    >>> proxy = wrapt.ObjectProxy(value)

    >>> proxy + 1
    2

    >>> int(proxy)
    1
    >>> hash(proxy)
    1
    >>> hash(value)
    1

    >>> proxy < 2
    True
    >>> proxy == 0
    False

Do note however, that when wrapping an object proxy around a literal value,
the original value is effectively copied into the proxy object and any
operation which updates the value will only update the value held by the
proxy object.

::

    >>> value = 1
    >>> proxy = wrapt.ObjectProxy(value)
    >>> type(proxy)
    <type 'ObjectProxy'>

    >>> proxy += 1

    >>> type(proxy)
    <type 'ObjectProxy'>

    >>> print(proxy)
    2
    >>> print(value)
    1

Object wrappers may therefore have limited use in conjunction with literal
values.

Type Comparison
---------------

The type of an instance of the object proxy will be ``ObjectProxy``, or that
of any derived class type if creating a custom object proxy.

::

    >>> value = 1
    >>> proxy = wrapt.ObjectProxy(value)
    >>> type(proxy)
    <type 'ObjectProxy'>

    >>> class CustomProxy(wrapt.ObjectProxy):
    ...     pass

    >>> proxy = CustomProxy(1)

    >>> type(proxy)
    <class '__main__.CustomProxy'>

Direct type comparisons in Python are generally frowned upon and allowance
for 'duck typing' preferred. Instead of direct type comparison, the
``isinstance()`` function would therefore be used. Using ``isinstance()``,
comparison of the type of the object proxy will properly evaluate against
the wrapped object.

::

    >>> isinstance(proxy, int)
    True

This works because the ``__class__`` attribute actually returns the class
type for the wrapped object.

::

    >>> proxy.__class__
    <type 'int'>

Note that ``isinstance()`` will still also succeed if comparing to the
``ObjectProxy`` type. It is therefore still possible to use ``isinstance()``
to determine if an object is an object proxy.

::

    >>> isinstance(proxy, wrapt.ObjectProxy)
    True

    >>> class CustomProxy(wrapt.ObjectProxy):
    ...     pass

    >>> proxy = CustomProxy(1)

    >>> isinstance(proxy, wrapt.ObjectProxy)
    True
    >>> isinstance(proxy, CustomProxy)
    True


Custom Proxies
--------------

A custom proxy is where one creates a derived object proxy and overrides
some specific behaviour of the proxy.

::

    def function():
        print('executing', function.__name__)
    
    class CallableWrapper(wrapt.ObjectProxy):

        def __call__(self, *args, **kwargs):
            print('entering', self.__wrapped__.__name__)
            try:
                return self.__wrapped__(*args, **kwargs)
            finally:
                print('exiting', self.__wrapped__.__name__)

    >>> proxy = CallableWrapper(function)

    >>> proxy()
    ('entering', 'function')
    ('executing', 'function')
    ('exiting', 'function')

Any method of the original wrapped object can be overridden, including
special Python methods such as ``__call__()``. If it is necessary to change
what happens when a specific attribute of the wrapped object is accessed,
then properties can be used.

If it is necessary to access the original wrapped object from within an
overridden method or property, then ``self.__wrapped__`` is used.

Proxy Attributes
----------------

When an attempt is made to access an attribute from the proxy, the same
named attribute would in normal circumstances be accessed from the wrapped
object. When updating an attributes value, or deleting the attribute, that
change will also be reflected in the wrapped object.

::

    >>> proxy = CallableWrapper(function)

    >>> hasattr(function, 'attribute')
    False
    >>> hasattr(proxy, 'attribute')
    False

    >>> proxy.attribute = 1

    >>> hasattr(function, 'attribute')
    True
    >>> hasattr(proxy, 'attribute')
    True

    >>> function.attribute
    1
    >>> proxy.attribute 
    1

If an attribute was updated on the wrapped object directly, that change is
still reflected in what is available via the proxy.

::

    >>> function.attribute = 2

    >>> function.attribute
    2
    >>> proxy.attribute
    2

If creating a custom proxy and it needs to keep attributes of its own which
should not be saved through to the wrapped object, those attributes should
be prefixed with ``_self_``.

::

    def function():
        print('executing', function.__name__)

    class CallableWrapper(wrapt.ObjectProxy):

        def __init__(self, wrapped, wrapper):
            super(CallableWrapper, self).__init__(wrapped)
            self._self_wrapper = wrapper

        def __call__(self, *args, **kwargs):
            return self._self_wrapper(self.__wrapped__, args, kwargs)

    def wrapper(wrapped, args, kwargs):
          print('entering', wrapped.__name__)
          try:
              return wrapped(*args, **kwargs)
          finally:
              print('exiting', wrapped.__name__)
        
    >>> proxy = CallableWrapper(function, wrapper)

    >>> proxy._self_wrapper
    <function wrapper at 0x1005961b8>

    >>> function._self_wrapper
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    AttributeError: 'function' object has no attribute '_self_wrapper'

If an attribute local to the proxy must be available under a name without
this special prefix, then a ``@property`` can be used in the class
definition.

::

    class CustomProxy(wrapt.ObjectProxy):

        def __init__(self, wrapped):
            super(CustomProxy, self).__init__(wrapped)
            self._self_attribute = 1

        @property
        def attribute(self):
            return self._self_attribute

        @attribute.setter
        def attribute(self, value):
            self._self_attribute = value

        @attribute.deleter
        def attribute(self):
           del self._self_attribute
     
    >>> proxy = CustomProxy(1)
    >>> print proxy.attribute
    1
    >>> proxy.attribute = 2 
    >>> print proxy.attribute
    2
    >>> del proxy.attribute
    >>> print proxy.attribute
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    AttributeError: 'int' object has no attribute 'attribute'

Alternatively, the attribute can be specified as a class attribute, with
that then being overidden if necessary, with a specific value in the
``__init__()`` method of the class.

::

    class CustomProxy(wrapt.ObjectProxy):
        attribute = None
        def __init__(self, wrapped):
            super(CustomProxy, self).__init__(wrapped)
            self.attribute = 1

    >>> proxy = CustomProxy(1)
    >>> print proxy.attribute
    1
    >>> proxy.attribute = 2
    >>> print proxy.attribute
    2
    >>> del proxy.attribute
    >>> print proxy.attribute
    None

Just be aware that although the attribute can be deleted from the instance
of the custom proxy, lookup will then fallback to using the class attribute.
