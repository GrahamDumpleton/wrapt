Proxies and Wrappers
====================

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


Custom Object Proxies
---------------------

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

Proxy Object Attributes
-----------------------

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
that then being overridden if necessary, with a specific value in the
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

Function Wrappers
-----------------

Although an ``ObjectProxy`` can be used to wrap a function, it doesn't do
anything special in respect of bound methods. If attempting to use a custom
object proxy to wrap instance methods, class methods or static methods, it
would be necessary to override the appropriate descriptor protocol methods
in order to be able to intercept and modify in any way the execution of the
wrapped function.

::

    class BoundCallableWrapper(wrapt.ObjectProxy):

        def __init__(self, wrapped, wrapper):
            super(BoundCallableWrapper, self).__init__(wrapped)
            self._self_wrapper = wrapper

        def __get__(self, instance, owner):
            return self

        def __call__(self, *args, **kwargs):
            return self._self_wrapper(self.__wrapped__, args, kwargs)

    class CallableWrapper(wrapt.ObjectProxy):

        def __init__(self, wrapped, wrapper):
            super(CallableWrapper, self).__init__(wrapped)
            self._self_wrapper = wrapper

        def __get__(self, instance, owner):
            function = self.__wrapped__.__get__(instance, owner)
            return BoundCallableWrapper(function, self._self_wrapper)

        def __call__(self, *args, **kwargs):
            return self._self_wrapper(self.__wrapped__, args, kwargs)

The ``CallableWrapper.__call__()`` method would therefore be invoked when
``CallableWrapper`` is used around a regular function. The
``BoundCallableWrapper.__call__()`` would instead be what is invoked for a
bound method, the instance of ``BoundCallableWrapper`` having being created
when the original wrapped method was bound to the class instance.

This specific pattern is actually the basis of what is required to
implement a robust function wrapper for use in implementing a decorator.
Because it is a fundamental pattern, a predefined version is available as
``wrapt.FunctionWrapper``.

As with the illustrative example above, ``FunctionWrapper`` class accepts
two key arguments:

* ``wrapped`` - The function being wrapped.
* ``wrapper`` - A wrapper function to be called when the wrapped function is invoked.

Although in prior examples the wrapper function was shown as accepting three
positional arguments of the wrapped function and the args and kwargs for when
the wrapped function was called, when using ``FunctionWrapper``, it is
expected that the wrapper function accepts four arguments. These are:

* ``wrapped`` - The wrapped function which in turns needs to be called by your wrapper function.
* ``instance`` - The object to which the wrapped function was bound when it was called.
* ``args`` - The list of positional arguments supplied when the decorated function was called.
* ``kwargs`` - The dictionary of keyword arguments supplied when the decorated function was called.

When ``FunctionWrapper`` is applied to a normal function or static method,
the wrapper function when called will be passed ``None`` as the
``instance`` argument.

When applied to an instance method, the wrapper function when called will
be passed the instance of the class the method is being called on as the
``instance`` argument. This will be the case even when the instance method
was called explicitly via the class and the instance passed as the first
argument. That is, the instance will never be passed as part of ``args``.

When applied to a class method, the wrapper function when called will be
passed the class type as the ``instance`` argument.

When applied to a class, the wrapper function when called will be passed
``None`` as the ``instance`` argument. The ``wrapped`` argument in this
case will be the class.

The above rules can be summarised with the following example.

::

    import inspect
    
    def wrapper(wrapped, instance, args, kwargs):
        if instance is None:
            if inspect.isclass(wrapped):
                # Decorator was applied to a class.
                return wrapped(*args, **kwargs)
            else:
                # Decorator was applied to a function or staticmethod.
                return wrapped(*args, **kwargs)
        else:
            if inspect.isclass(instance):
                # Decorator was applied to a classmethod.
                return wrapped(*args, **kwargs)
            else:
                # Decorator was applied to an instancemethod.
                return wrapped(*args, **kwargs)

Using these checks it is therefore possible to create a universal function
wrapper that can be applied in all situations. It is no longer necessary to
create different variants of function wrappers for normal functions and
instance methods.

In all cases, the wrapped function passed to the wrapper function is called
in the same way, with ``args`` and ``kwargs`` being passed. The
``instance`` argument doesn't need to be used in calling the wrapped
function.

A simple decorator factory implementation which makes use of
``FunctionWrapper`` to delegate execution of the wrapped function to
the wrapper function  would be:

::

    def function_wrapper(wrapper):
        @functools.wraps(wrapper)
        def _wrapper(wrapped):
            return FunctionWrapper(wrapped, wrapper)
        return _wrapper

It would be used like:

::

    @function_wrapper
    def wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @wrapper
    def function():
        pass

This example of a simplified decorator factory is made available as
``wrapt.function_wrapper``. Although it is usable in its own right, it is
preferable that ``wrapt.decorator`` be used to create decorators as it
provides additional features. The ``@function_wrapper`` decorator would
generally be used more when performing monkey patching and needing to
dynamically create function wrappers.

::

    @function_wrapper
    def wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    callback = wrapper(fetch_callback())

Custom Function Wrappers
------------------------

If it is necessary to implement a custom function wrapper in order to
override the behaviour of a wrapped function, it is possible to still
derive from the ``wrapt.FunctionWrapper`` class. That binding of functions
can occur, does however complicate this. This is because the bound function
is a separate object implemented as a different type.

The type of the separate bound function wrapper is
``wrapt.BoundFunctionWrapper``. If the behaviour for the bound function
also needs to be overridden, a derived version of this class will also
need to be created. The derived custom function wrapper will then need
to indicate that this second type should be used when creating the bound
function wrapper, rather than the default. This is done via the
``__bound_function_wrapper__`` attribute of the class.

::

    class CustomBoundFunctionWrapper(wrapt.BoundFunctionWrapper):

        def __init__(self, *args, **kwargs):
            self._self_attribute = self._self_parent._self_attribute
            super(CustomBoundFunctionWrapper, self).__init__(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            if self._self_attribute:
                ...
            return super(CustomBoundFunctionWrapper, self).__call__(*args, **kwargs)

    class CustomFunctionWrapper(wrapt.FunctionWrapper):

        __bound_function_wrapper__ = CustomBoundFunctionWrapper

        def __init__(self, wrapped, wrapper, attribute):
            super(CustomFunctionWrapper, self).__init__(wrapped, wrapper)
            self._self_attribute = attribute

The set of arguments used to initialize an instance of a bound function
wrapper object should be treated as a private implementation detail. This
means that if a custom bound function wrapper needs to implement an
``__init__()`` method, it should pass through all arguments as ``*args``
and ``**kwargs``. It should not use specific named parameters.

If the instance of the custom bound function wrapper needs to access any
special attributes originally supplied to the custom function wrapper when
created, it should use ``self._self_parent`` to access the parent object
to retrieve them.

Alternatively, it would be necessary to define the custom bound function
wrapper type in a function closure and assign ``__bound_function_wrapper__``
dynamically against the instance of the custom bound function wrapper.

::

    def custom_bound_function_wrapper(attribute):

        class CustomBoundFunctionWrapper(wrapt.BoundFunctionWrapper):

            def __init__(self, *args, **kwargs):
                self._self_attribute = attribute
                super(CustomBoundFunctionWrapper, self).__init__(*args, **kwargs)

            def __call__(self, *args, **kwargs):
                if self._self_attribute:
                    ...
                return super(CustomBoundFunctionWrapper, self).__call__(*args, **kwargs)

    class CustomFunctionWrapper(wrapt.FunctionWrapper):

        def __init__(self, wrapped, wrapper, attribute):
            super(CustomFunctionWrapper, self).__init__(wrapped, wrapper)
            self._self_attribute = attribute
            self.__bound_function_wrapper__ = custom_bound_function_wrapper(attribute)
