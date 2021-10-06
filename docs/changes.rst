Release Notes
=============

Version 1.14.0
--------------

**Bugs Fixed**

* Drop support for Python 2.7 and 3.5, which are past their end of lifetime.


Version 1.13.1
--------------

**Bugs Fixed**

* Fix Python version constraint so PyPi classifier for ``pip`` requires
  Python 2.7 or Python 3.5+.

Version 1.13.0
--------------

**Bugs Fixed**

* When a reference to a class method was taken out of a class, and then
  wrapped in a function wrapper, and called, the class type was not being
  passed as the instance argument, but as the first argument in args,
  with the instance being ``None``. The class type should have been passed
  as the instance argument.

* If supplying an adapter function for a signature changing decorator
  using input in the form of a function argument specification, name lookup
  exceptions would occur where the adaptor function had annotations which
  referenced non builtin Python types. Although the issues have been
  addressed where using input data in the format usually returned by
  ``inspect.getfullargspec()`` to pass the function argument specification,
  you can still have problems when supplying a function signature as
  string. In the latter case only Python builtin types can be referenced
  in annotations.

* When a decorator was applied on top of a data/non-data descriptor in a
  class definition, the call to the special method ``__set_name__()`` to
  notify the descriptor of the variable name was not being propogated. Note
  that this issue has been addressed in the ``FunctionWrapper`` used by
  ``@wrapt.decorator`` but has not been applied to the generic
  ``ObjectProxy`` class. If using ``ObjectProxy`` directly to construct a
  custom wrapper which is applied to a descriptor, you will need to
  propogate the ``__set_name__()`` call yourself if required.

* The ``issubclass()`` builtin method would give incorrect results when used
  with a class which had a decorator applied to it. Note that this has only
  been able to be fixed for Python 3.7+. Also, due to what is arguably a
  bug (https://bugs.python.org/issue44847) in the Python standard library,
  you will still have problems when the class heirarchy uses a base class
  which has the ``abc.ABCMeta`` metaclass. In this later case an exception
  will be raised of ``TypeError: issubclass() arg 1 must be a class``.

Version 1.12.1
--------------

**Bugs Fixed**

* Applying a function wrapper to a static method of a class using the
  ``wrap_function_wrapper()`` function, or wrapper for the same, wasn't
  being done correctly when the static method was the immediate child of
  the target object. It was working when the name path had multiple name
  components. A failure would subsequently occur when the static method
  was called via an instance of the class, rather than the class.

Version 1.12.0
--------------

**Features Changed**

* Provided that you only want to support Python 3.7, when deriving from
  a base class which has a decorator applied to it, you no longer need
  to access the true type of the base class using ``__wrapped__`` in
  the inherited class list of the derived class.

**Bugs Fixed**

* When using the ``synchronized`` decorator on instance methods of a
  class, if the class declared special methods to override the result for
  when the class instance was tested as a boolean so that it returned
  ``False`` all the time, the synchronized method would fail when called.

* When using an adapter function to change the signature of the decorated
  function, ``inspect.signature()`` was returning the wrong signature
  when an instance method was inspected by accessing the method via the
  class type.

Version 1.11.2
--------------

**Bugs Fixed**

* Fix possible crash when garbage collection kicks in when invoking a
  destructor of wrapped object.

Version 1.11.1
--------------

**Bugs Fixed**

* Fixed memory leak in C extension variant of ``PartialCallableObjectProxy``
  class introduced in 1.11.0, when it was being used to perform binding,
  when a call of an instance method was made through the class type, and
  the self object passed explicitly as first argument.

* The C extension variant of the ``PartialCallableObjectProxy`` class
  introduced in 1.11.0, which is a version of ``functools.partial``
  which correctly handles binding when applied to methods of classes,
  couldn't be used when no positional arguments were supplied.

* When the C extension variant of ``PartialCallableObjectProxy`` was
  used and multiple positional arguments were supplied, the first
  argument would be replicated and used to all arguments, instead of
  correct values, when the partial was called.

* When the C extension variant of ``PartialCallableObjectProxy`` was
  used and keyword arguments were supplied, it would fail as was
  incorrectly using the positional arguments where the keyword arguments
  should have been used.

Version 1.11.0
--------------

**Bugs Fixed**

* When using arithmetic operations through a proxy object, checks about
  the types of arguments were not being performed correctly, which could
  result in an exception being raised to indicate that a proxy object had
  not been initialised when in fact the argument wasn't even an instance
  of a proxy object.
  
  Because an incorrect cast in C level code was being performed and
  an attribute in memory checked on the basis of it being a type different
  to what it actually was, technically it may have resulted in a process
  crash if the size of the object was smaller than the type being casted
  to.

* The ``__complex__()`` special method wasn't implemented and using
  ``complex()`` on a proxy object would give wrong results or fail.

* When using the C extension, if an exception was raised when using inplace
  or, ie., ``|=``, the error condition wasn't being correctly propagated
  back which would result in an exception showing up as wrong location
  in subsequent code.

* Type of ``long`` was used instead of ``Py_hash_t`` for Python 3.3+. This
  caused compiler warnings on Windows, which depending on what locale was
  set to, would cause pip to fail when installing the package.

* If calling ``Class.instancemethod`` and passing ``self`` explicitly, the
  ability to access ``__name__`` and ``__module__`` on the final bound
  method were not preserved. This was due to a ``partial`` being used for
  this special case, and it doesn't preserve introspection.

* Fixed typo in the getter property of ``ObjectProxy`` for accessing
  ``__annotations__``. Appeared that it was still working as would fall back
  to using generic ``__getattr__()`` to access attribute on wrapped object.

**Features Changed**

* Dropped support for Python 2.6 and 3.3.

* If ``copy.copy()`` or ``copy.deepcopy()`` is used on an instance of the
  ``ObjectProxy`` class, a ``NotImplementedError`` exception is raised, with
  a message indicating that the object proxy must implement the
  ``__copy__()`` or ``__deepcopy__()`` method. This is in place of the
  default ``TypeError`` exception with message indicating a pickle error.

* If ``pickle.dump()`` or ``pickle.dumps()`` is used on an instance of the
  ``ObjectProxy`` class, a ``NotImplementedError`` exception is raised, with
  a message indicating that the object proxy must implement the
  ``__reduce_ex__()`` method. This is in place of the default ``TypeError``
  exception with message indicating a pickle error.

Version 1.10.11
---------------

**Bugs Fixed**

* When wrapping a ``@classmethod`` in a class used as a base class, when
  the method was called via the derived class type, the base class type was
  being passed for the ``cls`` argument instead of the derived class type
  through which the call was made.

**New Features**

* The C extension can be disabled at runtime by setting the environment
  variable ``WRAPT_DISABLE_EXTENSIONS``. This may be necessary where there
  is currently a difference in behaviour between pure Python implementation
  and C extension and the C extension isn't having the desired result.

Version 1.10.10
---------------

**Features Changed**

* Added back missing description and categorisations when releasing to PyPi.

Version 1.10.9
--------------

**Bugs Fixed**

* Code for ``inspect.getargspec()`` when using Python 2.6 was missing
  import of ``sys`` module.

Version 1.10.8
--------------

**Bugs Fixed**

* Ensure that ``inspect.getargspec()`` is only used with Python 2.6 where
  required, as function has been removed in Python 3.6.

Version 1.10.7
--------------

**Bugs Fixed**

* The mod operator '%' was being incorrectly proxied in Python variant of
  object proxy to the xor operator '^'.

Version 1.10.6
--------------

**Bugs Fixed**

* Registration of post import hook would fail with an exception if
  registered after another import hook for the same target module had been
  registered and the target module also imported.

**New Features**

* Support for testing with Travis CI added to repository.

Version 1.10.5
--------------

**Bugs Fixed**

* Post import hook discovery was not working correctly where multiple
  target modules were registered in the same entry point list. Only the
  callback for the last would be called regardless of the target module.

* If a ``WeakFunctionProxy`` wrapper was used around a method of a class
  which was decorated using a wrapt decorator, the decorator wasn't being
  invoked when the method was called via the weakref proxy.

**Features Changed**

* The ``register_post_import_hook()`` function, modelled after the
  function of the same name in PEP-369 has been extended to allow a string
  name to be supplied for the import hook. This needs to be of the form
  ``module::function`` and will result in an import hook proxy being used
  which will only load and call the function of the specified moduled when
  the import hook is required. This avoids needing to load the code needed
  to operate on the target module unless required.

Version 1.10.4
--------------

**Bugs Fixed**

* Fixup botched package version number from 1.10.3 release.

Version 1.10.3
--------------

**Bugs Fixed**

* Post import hook discovery from third party modules declared via
  ``setuptools`` entry points was failing due to typo in temporary variable
  name. Also added the ``discover_post_import_hooks()`` to the public API
  as was missing.

**Features Changed**

* To ensure parity between pure Python and C extension variants of the
  ``ObjectProxy`` class, allow the ``__wrapped__`` attribute to be set
  in a derived class when the ``ObjectProxy.__init__()`` method hasn't
  been called.

Version 1.10.2
--------------

**Bugs Fixed**

* When creating a derived ``ObjectProxy``, if the base class ``__init__()``
  method wasn't called and the ``__wrapped__`` attribute was accessed,
  in the pure Python implementation a recursive call of ``__getattr__()``
  would occur and the maximum stack depth would be reached and an exception
  raised.

* When creating a derived ``ObjectProxy``, if the base class ``__init__()``
  method wasn't called, in the C extension implementation, if that instance
  was then used in a binary arithmetic operation the process would crash.

Version 1.10.1
--------------

**Bugs Fixed**

* When using ``FunctionWrapper`` around a method of an existing instance of
  a class, rather than on the type, then a memory leak could occur in two
  different scenarios.

  The first issue was that wrapping a method on an instance of a class was
  causing an unwanted reference to the class meaning that if the class type
  was transient, such as it is being created inside of a function call, the
  type object would leak.

  The second issue was that wrapping a method on an instance of a class and
  then calling the method was causing an unwanted reference to the instance
  meaning that if the instance was transient, it would leak.

  This was only occurring when the C extension component for the
  ``wrapt`` module was being used.

Version 1.10.0
--------------

**New Features**

* When specifying an adapter for a decorator, it is now possible to pass
  in, in addition to passing in a callable, a tuple of the form which
  is returned by ``inspect.getargspec()``, or a string of the form which
  is returned by ``inspect.formatargspec()``. In these two cases the
  decorator will automatically compile a stub function to use as the
  adapter. This eliminates the need for a caller to generate the stub
  function if generating the signature on the fly.

  ::

      def argspec_factory(wrapped):
          argspec = inspect.getargspec(wrapped)

          args = argspec.args[1:]
          defaults = argspec.defaults and argspec.defaults[-len(argspec.args):]

          return inspect.ArgSpec(args, argspec.varargs,
                  argspec.keywords, defaults)

      def session(wrapped):
          @wrapt.decorator(adapter=argspec_factory(wrapped))
          def _session(wrapped, instance, args, kwargs):
              with transaction() as session:
                  return wrapped(session, *args, **kwargs)

          return _session(wrapped)

  This mechanism and the original mechanism to pass a function, meant
  that the adapter function had to be created in advance. If the adapter
  needed to be generated on demand for the specific function to be
  wrapped, then it would have been necessary to use a closure around
  the definition of the decorator as above, such that the generator could
  be passed in.

  As a convenience, instead of using such a closure, it is also now
  possible to write:

  ::

      def argspec_factory(wrapped):
          argspec = inspect.getargspec(wrapped)

          args = argspec.args[1:]
          defaults = argspec.defaults and argspec.defaults[-len(argspec.args):]

          return inspect.ArgSpec(args, argspec.varargs,
                  argspec.keywords, defaults)

      @wrapt.decorator(adapter=wrapt.adapter_factory(argspec_factory))
      def _session(wrapped, instance, args, kwargs):
          with transaction() as session:
              return wrapped(session, *args, **kwargs)

  The result of ``wrapt.adapter_factory()`` will be recognised as indicating
  that the creation of the adapter is to be deferred until the decorator is
  being applied to a function. The factory function for generating the
  adapter function or specification on demand will be passed the function
  being wrapped by the decorator.

  If wishing to create a library of routines for generating adapter
  functions or specifications dynamically, then you can do so by creating
  classes which derive from ``wrapt.AdapterFactory`` as that is the type
  which is recognised as indicating lazy evaluation of the adapter
  function. For example, ``wrapt.adapter_factory()`` is itself implemented
  as:

  ::

      class DelegatedAdapterFactory(wrapt.AdapterFactory):
          def __init__(self, factory):
              super(DelegatedAdapterFactory, self).__init__()
              self.factory = factory
          def __call__(self, wrapped):
              return self.factory(wrapped)

      adapter_factory = DelegatedAdapterFactory

**Bugs Fixed**

* The ``inspect.signature()`` function was only added in Python 3.3.
  Use fallback when doesn't exist and on Python 3.2 or earlier Python 3
  versions.
  
  Note that testing is only performed for Python 3.3+, so it isn't
  actually known if the ``wrapt`` package works on Python 3.2.

Version 1.9.0
-------------

**Features Changed**

* When using ``wrapt.wrap_object()``, it is now possible to pass an
  arbitrary object in addition to a module object, or a string name
  identifying a module. Similar for underlying ``wrapt.resolve_path()``
  function.

**Bugs Fixed**

* It is necessary to proxy the special ``__weakref__`` attribute in the
  pure Python object proxy else using ``inspect.getmembers()`` on a
  decorator class will fail.

* The ``FunctionWrapper`` class was not passing through the instance
  correctly to the wrapper function when it was applied to a method of an
  existing instance of a class.

* The ``FunctionWrapper`` was not always working when applied around a
  method of a class type by accessing the method to be wrapped using
  ``getattr()``. Instead it is necessary to access the original unbound
  method from the class ``__dict__``. Updated the ``FunctionWrapper`` to
  work better in such situations, but also modify ``resolve_path()`` to
  always grab the class method from the class ``__dict__`` when wrapping
  methods using ``wrapt.wrap_object()`` so wrapping is more predictable.
  When doing monkey patching ``wrapt.wrap_object()`` should always be
  used to ensure correct operation.

* The ``AttributeWrapper`` class used internally to the function
  ``wrap_object_attribute()`` had wrongly named the ``__delete__`` method
  for the descriptor as ``__del__``.

Version 1.8.0
-------------

**Features Changed**

* Previously using @wrapt.decorator on a class type didn't really yield
  anything which was practically useful. This is now changed and when
  applied to a class an instance of the class will be automatically
  created to be used as the decorator wrapper function. The requirement
  for this is that the __call__() method be specified in the style as
  would be done for the decorator wrapper function.

  ::

      @wrapt.decorator
      class mydecoratorclass(object):
          def __init__(self, arg=None):
              self.arg = arg
          def __call__(self, wrapped, instance, args, kwargs):
              return wrapped(*args, **kwargs)

      @mydecoratorclass
      def function():
          pass

  If the resulting decorator class is to be used with no arguments, the
  __init__() method of the class must have all default arguments. These
  arguments can be optionally supplied though, by using keyword arguments
  to the resulting decorator when applied to the function to be decorated.

  ::

      @mydecoratorclass(arg=1)
      def function():
          pass

Version 1.7.0
-------------

**New Features**

* Provide wrapt.getcallargs() for determining how arguments mapped to a
  wrapped function. For Python 2.7 this is actually inspect.getcallargs()
  with a local copy being used in the case of Python 2.6.

* Added wrapt.wrap_object_attribute() as a way of wrapping or otherwise
  modifying the result of trying to access the attribute of an object
  instance. It works by adding a data descriptor with the same name as
  the attribute, to the class type, allowing reading of the attribute
  to be intercepted. It does not affect updates to or deletion of the
  attribute.

**Bugs Fixed**

* Need to explicitly proxy special methods __bytes__(), __reversed__()
  and __round__() as they are only looked up on the class type and not
  the instance, so can't rely on __getattr__() fallback.

* Raise more appropriate TypeError, with corresponding message, rather
  than IndexError, when a decorated instance or class method is called via
  the class but the required 1st argument of the instance or class is not
  supplied.

Version 1.6.0
-------------

**Bugs Fixed**

* The ObjectProxy class would return that the __call__() method existed
  even though the wrapped object didn't have one. Similarly, callable()
  would always return True even if the wrapped object was not callable.

  This resulted due to the existence of the __call__() method on the
  wrapper, required to support the possibility that the wrapped object
  may be called via the proxy object even if it may not turn out that
  the wrapped object was callable.

  Because checking for the existence of a __call__() method or using
  callable() can sometimes be used to indirectly infer the type of an
  object, this could cause issues. To ensure that this now doesn't
  occur, the ability to call a wrapped object via the proxy object has
  been removed from ObjectProxy. Instead, a new class CallableObjectProxy
  is now provided, with it being necessary to make a conscious choice as
  to which should be used based on whether the object to be wrapped is
  in fact callable.

  Note that neither before this change, or with the introduction of the
  class CallableObjectProxy, does the object proxy perform binding. If
  binding behaviour is required it still needs to be implemented
  explicitly to match the specific requirements of the use case.
  Alternatively, the FunctionWrapper class should be used which does
  implement binding, but also enforces a wrapper mechanism for
  manipulating what happens at the time of the call.

Version 1.5.1
-------------

**Bugs Fixed**

* Instance method locking for the synchronized decorator was not correctly
  locking on the instance but the class, if a synchronized class method
  had been called prior to the synchronized instance method.

Version 1.5.0
-------------

**New Features**

* Enhanced @wrapt.transient_function_wrapper so it can be applied to
  instance methods and class methods with the self/cls argument being
  supplied correctly. This allows instance and class methods to be used for
  this type of decorator, with the instance or class type being able to
  be used to hold any state required for the decorator.

**Bugs Fixed**

* If the wrong details for a function to be patched was given to the
  decorator @wrapt.transient_function_wrapper, the exception indicating
  this was being incorrectly swallowed up and mutating to a different
  more obscure error about local variable being access before being set.

Version 1.4.2
-------------

**Bugs Fixed**

* A process could crash if the C extension module was used and when using
  the ObjectProxy class a reference count cycle was created that required
  the Python garbage collector to kick in to break the cycle. This was
  occurring as the C extension had not implemented GC support in the
  ObjectProxy class correctly.

Version 1.4.1
-------------

**Bugs Fixed**

* Overriding __wrapped__ attribute directly on any wrapper more than once
  could cause corruption of memory due to incorrect reference count
  decrement.

Version 1.4.0
-------------

**New Features**

* Enhanced @wrapt.decorator and @wrapt.function_wrapper so they can be
  applied to instance methods and class methods with the self/cls argument
  being supplied correctly. This allows instance and class methods to be
  used as decorators, with the instance or class type being able to be used
  to hold any state required for the decorator.

**Bugs Fixed**

* Fixed process crash in extension when the wrapped object passed as first
  argument to FunctionWrapper did not have a tp_descr_get callback for the
  type at C code level. Now raised an AttributeError exception in line with
  what Python implementation does.

Version 1.3.1
-------------

**Bugs Fixed**

* The discover_post_import_hooks() function had not been added to the
  top level wrapt module.

Version 1.3.0
-------------

**New Features**

* Added a @transient_function_wrapper decorator for applying a wrapper
  function around a target function only for the life of a single function
  call. The decorator is useful for performing mocking or pass through
  data validation/modification when doing unit testing of packages.

Version 1.2.1
-------------

**Bugs Fixed**

* In C implementation, not dealing with unbound method type creation
  properly which would cause later problems when calling instance method
  via the class type in certain circumstances. Introduced problem in 1.2.0.

* Eliminated compiler warnings due to missing casts in C implementation.

Version 1.2.0
-------------

**New Features**

* Added an 'enabled' option to @decorator and FunctionWrapper which can
  be provided a boolean, or a function returning a boolean to allow the
  work of the decorator to be disabled dynamically. When a boolean, is
  used for @decorator, the wrapper will not even be applied if 'enabled'
  is False. If a function, then will be called prior to wrapper being
  called and if returns False, then original wrapped function called
  directly rather than the wrapper being called.

* Added in an implementation of a post import hook mechanism in line with
  that described in PEP 369.

* Added in helper functions specifically designed to assist in performing
  monkey patching of existing code.

**Features Changed**

* Collapsed functionality of _BoundMethodWrapper into _BoundFunctionWrapper
  and renamed the latter to BoundFunctionWrapper. If deriving from the
  FunctionWrapper class and needing to override the type of the bound
  wrapper, the class attribute ``__bound_function_wrapper__`` should be set
  in the derived FunctionWrapper class to the replacement type.

**Bugs Fixed**

* When creating a custom proxy by deriving from ObjectProxy and the custom
  proxy needed to override __getattr__(), it was not possible to called the
  base class ObjectProxy.__getattr__() when the C implementation of
  ObjectProxy was being used. The derived class __getattr__() could also
  get ignored.

* Using inspect.getargspec() now works correctly on bound methods when an
  adapter function can be provided to @decorator.

Version 1.1.3
-------------

**New Features**

* Added a _self_parent attribute to FunctionWrapper and bound variants.
  For the FunctionWrapper the value will always be None. In the case of the
  bound variants of the function wrapper, the attribute will refer back
  to the unbound FunctionWrapper instance. This can be used to get a back
  reference to the parent to access or cache data against the persistent
  function wrapper, the bound wrappers often being transient and only
  existing for the single call.

**Improvements**

* Use interned strings to optimise name comparisons in the setattro()
  method of the C implementation of the object proxy.

**Bugs Fixed**

* The pypy interpreter is missing operator.__index__() so proxying of that
  method in the object proxy would fail. This is a bug in pypy which is
  being addressed. Use operator.index() instead which pypy does provide
  and which also exists for CPython.

* The pure Python implementation allowed the __wrapped__ attribute to be
  deleted which could cause problems. Now raise a TypeError exception.

* The C implementation of the object proxy would crash if an attempt was
  made to delete the __wrapped__ attribute from the object proxy. Now raise a
  TypeError exception.

Version 1.1.2
-------------

**Improvements**

* Reduced performance overhead from previous versions. Most notable in the
  C implementation. Benchmark figures have been updated in documentation.

Version 1.1.1
-------------

**Bugs Fixed**

* Python object memory leak was occurring due to incorrect increment of
  object reference count in C implementation of object proxy when an
  instance method was called via the class and the instance passed in
  explicitly.

* In place operators in pure Python object proxy for __idiv__ and
  __itruediv__ were not replacing the wrapped object with the result
  of the operation on the wrapped object.

* In place operators in C implementation of Python object proxy were
  not replacing the wrapped object with the result of the operation on the
  wrapped object.

Version 1.1.0
-------------

**New Features**

* Added a synchronized decorator for performing thread mutex locking on
  functions, object instances or classes. This is the same decorator as
  covered as an example in the wrapt documentation.

* Added a WeakFunctionProxy class which can wrap references to instance
  methods as well as normal functions.

* Exposed from the C extension the classes _FunctionWrapperBase,
  _BoundFunctionWrapper and _BoundMethodWrapper so that it is possible to
  create new variants of FunctionWrapper in pure Python code.

**Bugs Fixed**

* When deriving from ObjectProxy, and the C extension variant
  was being used, if a derived class overrode __new__() and tried to access
  attributes of the ObjectProxy created using the base class __new__()
  before __init__() was called, then an exception would be raised
  indicating that the 'wrapper has not been initialised'.

* When deriving from ObjectProxy, and the C extension variant
  was being used, if a derived class __init__() attempted to update
  attributes, even the special '_self_' attributed before calling the base
  class __init__() method, then an exception would be raised indicating
  that the 'wrapper has not been initialised'.

Version 1.0.0
-------------

Initial release.
