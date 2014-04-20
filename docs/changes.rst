Release Notes
=============

Version 1.7.0
-------------

**Bugs Fixed**

* Need to explicitly proxy special methods __bytes__(), __reversed__()
  and __round__() as they are only looked up on the class type and not
  the instance, so can't rely on __getattr__() fallback.

Version 1.6.0
-------------

**Bugs Fixed**

* The ObjectProxy class would return that the __call__() method existed
  even though the wrapped object didn't have one. Similarly, callable()
  would always return True even if the wrapped object was not callable.

  This resulted due to the existance of the __call__() method on the
  wrapper, required to support the possibility that the wrapped object
  may be called via the proxy object even if it may not turn out that
  the wrapped object was callable.

  Because checking for the existance of a __call__() method or using
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
  occuring as the C extension had not implemented GC support in the
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

**Features Changes**

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

* Python object memory leak was occuring due to incorrect increment of
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
  class __init__() methid, then an exception would be raised indicating
  that the 'wrapper has not been initialised'.

Version 1.0.0
-------------

Initial release.
