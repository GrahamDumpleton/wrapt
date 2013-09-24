Changes
=======

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
