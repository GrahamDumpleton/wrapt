Release Notes
=============

Version 2.1.0
-------------

**Features Changed**

* Drop support for Python 3.8. Python version 3.9 or later is now required.

Version 2.0.1
-------------

**Bugs Fixed**

* The ``wrapt.lazy_import()`` function wasn't included in the
  ``__all__`` attribute of the ``wrapt`` module, meaning that it wasn't
  accessible when using ``from wrapt import *`` and type checkers such as
  ``mypy`` or ``pylance`` may not see it as part of the public API.

* When using ``wrapt.lazy_import()`` to lazily import a function of a module,
  the resulting proxy object wasn't marked as callable until something triggered
  the import of the module via the proxy. This meant a ``callable()`` check
  on the proxy would return ``False`` until the module was actually imported.
  Further, calling the proxy before the module was imported would raise
  ``TypeError: 'LazyObjectProxy' object is not callable`` rather than
  importing the module and calling the function as expected. In order to
  address this issue, an additional keyword argument ``interface`` has been
  added to ``wrapt.lazy_import()`` which can be used to specify the expected
  interface type of the wrapped object. This will default to ``Callable``
  when an attribute name is supplied, and to ``ModuleType`` when no attribute
  name is supplied. If using ``wrapt.lazy_import()`` and supplying an
  ``attribute`` argument, and you expect the wrapped object to be something
  other than a callable, you should now also supply ``interface=...`` with the
  appropriate type from ``collections.abc`` to ensure the proxy behaves correctly
  prior to the module being imported. This should only be necessary where the
  wrapped object has special dunder methods on its type which need to exist on
  the proxy prior to the module being imported.

Version 2.0.0
-------------

There have been subtle changes in various corner cases of the behaviour of the
``ObjectProxy`` class, which although not expected to cause problems, still has
the potential for causing issues if code was for some reason dependent on prior
behaviour. All existing code related to Python 2.X has also been removed.
Finally it has also been a while since the last significant release. For all
these reasons a major version bump is being made.

**New Features**

* Added ``__all__`` attribute to ``wrapt`` module to expose the public API.

* The ``wrapt.PartialCallableObjectProxy`` class can now be accessed via the
  alias ``wrapt.partial``, which is a convenience for users who are used to using
  ``functools.partial`` and want to use the ``wrapt`` version of it.

* Type hints have been added to the ``wrapt`` module. The type hints are
  available when using Python 3.10 or later, and can be used with static type
  checkers such as ``pylance`` or ``mypy``. Note that due to limitations in
  Python's type hinting system, type checking is not always able to be applied
  or details such as default values may not be available. See the documentation
  for more details on limitations and workarounds.

* Added ``wrapt.BaseObjectProxy`` class which is the base class for all object
  proxy classes. This class is either the pure Python or C extension variant of
  the object proxy depending on whether the C extension is available. This used
  to be the ``ObjectProxy`` class, but has been renamed to ``BaseObjectProxy``
  to better reflect its role as the foundational class for all object proxies.
  This variant does though no longer provide a proxy implementation for the
  ``__iter__()`` special method as it was originally a mistake to include it
  in the ``ObjectProxy`` class as its presence could cause issues when the
  wrapped object is not iterable. A ``wrapt.ObjectProxy`` class is still
  provided but this is now a pure Python subclass of ``BaseObjectProxy`` which
  adds a proxy implementation for the ``__iter__()`` special method. This is
  done for backwards compatibility reasons as ``ObjectProxy`` with the
  ``__iter__()`` special method has been part of the public API for a long time.

* Added ``wrapt.AutoObjectProxy`` class which is a pure Python subclass of
  ``BaseObjectProxy`` which overrides the ``__new__()`` method to dynamically
  generate a custom subclass which includes methods for callable, descriptor and
  iterator protocols, as well as other select special methods. This is done using
  a dynamically generated subclass as the special methods for these protocols
  must be defined on the class itself and not on the instance. Because
  ``AutoObjectProxy`` dynamically generates a custom subclass for each instance,
  it has a notable memory overhead for every instance created, and thus should
  only be used where you know you will not be needing many instances of it.
  If you know what additional special methods you need, it is preferable to use
  ``BaseObjectProxy`` directly and add them to a subclass as needed. If you only
  need ``__iter__()`` support for backwards compatibility then use ``ObjectProxy``
  instead.

* Added ``wrapt.LazyObjectProxy`` class which is a variant of ``AutoObjectProxy``
  which takes a callable which returns the object to be wrapped. The callable is
  only invoked the first time an attribute of the wrapped object is accessed.
  This can be useful for deferring creation of expensive objects until they are
  actually needed. Note that the callable is only invoked once and protection
  is in place to ensure that if multiple threads try to access the wrapped object
  at the same time, only one thread will invoke the callable and the other
  threads will wait for the result. Because ``LazyObjectProxy`` is a subclass of
  ``AutoObjectProxy``, it has the same memory overhead considerations as
  ``AutoObjectProxy`` and should only be used where you know you will not be
  needing many instances of it.

* Added ``wrapt.lazy_import()`` function which takes a module name and returns a
  ``LazyObjectProxy`` which will import the module when it is first needed.
  This can be useful for deferring import of modules until they are actually
  needed. If the module name is a dotted name, then the full dotted name is
  imported and the last component returned. An optional ``attribute`` argument
  can be supplied which is the name of an attribute of the module to return
  instead of the module itself.

**Features Changed**

* Code related to Python 2.X and workarounds for older Python 3.X versions has
  been removed.

* Dependency at runtime on ``setuptools`` for calculating package entry points
  has been removed. Instead the ``importlib.metadata`` module is now used for
  this purpose. The ``wrapt`` package no longer requires ``setuptools`` to be
  installed at runtime. It is still required for building and installing the
  package from source, but not for installation using Python wheels, and not
  for using it.

* For reasons to do with backward/forward compatibility the ``wrapt`` module
  included references to ``getcallargs()`` and ``formatargspec()`` functions which
  were part of the ``inspect`` module at one time or another. These were provided
  as convenience for users of the ``wrapt`` module, but were not actually part of
  the public API. They have now been removed from the ``wrapt`` module and are
  no longer available. If you need these functions, you should use the
  ``inspect`` module directly.

* The ``enabled``, ``adapter`` and ``proxy`` arguments to the ``@decorator``
  decorator had to be keyword parameters, and the initial ``wrapped`` argument
  had to be positional only. Because though Python 2.X was still being supported
  it was not possible to use appropriate syntax to mark them as such. These
  arguments are now marked as positional and keyword only parameters in the
  function signature as appropriate.

* The object proxy classes now raise a ``WrapperNotInitializedError`` exception
  rather than Python builtin ``ValueError`` exception when an attempt is made
  to access an attribute of the wrapped object before the wrapper has been
  initialized. The ``WrapperNotInitializedError`` exception inherits from both
  ``ValueError`` and ``AttributeError`` so that it can be caught by code which
  wants to handle both cases. This is being done to allow IDEs such as PyCharm
  to give a live view of Python objects and their attributes. Previously a
  ``ValueError`` exception was being raised, which was problematic because
  PyCharm would see it as an actual error and fail. By using a custom exception
  that also inherits from ``AttributeError`` it is hoped the IDE will see it as
  a normal attribute access error rather than an actual error and so just not
  attempt to show the attribute within the IDE.

**Bugs Fixed**

* Reference count was not being incremented on type object for C implementation
  of the partial callable object proxy when module was initialized. If ``wrapt``
  was being used in Python sub interpreters which were deleted it could lead
  to the process crashing. Note that this change was also back ported and
  included in version 1.17.3 and 1.14.2 releases.

* Wasn't chaining ``__mro_entries__()`` calls when the wrapped object was not a
  type (class) and itself had a ``__mro_entries__()`` method. This meant that if
  using the object proxy as a base class for a generic class, the generic
  parameters were being ignored.

* When an object proxy wrapped an immutable type, such as an integer, and the
  object proxy had been assigned to a second variable, the result of an
  in-place operation on the second variable was also affecting the first
  variable, when instead the lifetime of the two variables should have been
  independent to reflect what occurs for normal immutable types.

Version 1.17.3
--------------

**Bugs Fixed**

* Reference count was not being incremented on type object for C implementation
  of the partial callable object proxy when module was initialized. If wrapt was
  being used in Python sub interpreters which were deleted it could lead to the
  process crashing.

Version 1.17.2
--------------

**New Features**

* Added universal binary wheels for macOS. That is, contains both x86_64 and
  arm64 architectures in the same wheel.

Version 1.17.1
--------------

**Bugs Fixed**

* Due to GitHub actions changes, binary wheels were missing for macOS Intel.

* Not implemented error for ``__reduce__()`` on ``ObjectProxy`` was incorrectly
  displaying the error as being on ``__reduce_ex__()``.

Version 1.17.0
--------------

Note that version 1.17.0 drops support for Python 3.6 and 3.7. Python version
3.8 or later is required.

**New Features**

* Add ``__format__()`` method to ``ObjectProxy`` class to allow formatting of
  wrapped object.

* Added C extension internal flag to indicate that ``wrapt`` should be safe for
  Python 3.13 free threading mode. Releases will include free threading variants
  of Python wheels. Note that as free threading is new, one should be cautious
  about using it in production until it has been more widely tested.

**Bugs Fixed**

* When a normal function or builtin function which had ``wrapt.decorator`` or a
  function wrapper applied, was assigned as a class attribute, and the function
  attribute called via the class or an instance of the class, an additional
  argument was being passed, inserted as the first argument, which was the class
  or instance. This was not the correct behaviour and the class or instance
  should not have been passed as the first argument.

* When an instance of a callable class object was wrapped which didn't not have
  a ``__get__()`` method for binding, and it was called in context where binding
  would be attempted, it would fail with error that ``__get__()`` did not exist
  when instead it should have been called directly, ignoring that binding was
  not possible.

* The ``__round__`` hook for the object proxy didn't accept ``ndigits`` argument.

Version 1.16.0
--------------

Note that version 1.16.0 drops support for Python 2.7 and 3.5. Python version
3.6 or later is required.

**New Features**

* The ``patch_function_wrapper()`` decorator now accepts an ``enabled``
  argument, which can be a literal boolean value, object that evaluates as
  boolean, or a callable object which returns a boolean. In the case of a
  callable, determination of whether the wrapper is invoked will be left until
  the point of the call. In the other cases, the wrapper will not be applied if
  the value evaluates false at the point of applying the wrapper.

**Features Changed**

* The import hook loader and finder objects are now implemented as transparent
  object proxies so they properly proxy pass access to attributes/functions of
  the wrapped loader or finder.

* Code files in the implementation have been reorganized such that the pure
  Python version of the ``ObjectProxy`` class is directly available even if the
  C extension variant is being used. This is to allow the pure Python variant to
  be used in exceptional cases where the C extension variant is not fully
  compatible with the pure Python implementation and the behaviour of the pure
  Python variant is what is required. This should only be relied upon if have
  absolutely no choice. The pure Python variant is not as performant as the C
  extension.

  To access the pure Python variant use ``from wrapt.wrappers import ObjectProxy``
  instead of just ``from wrapt import ObjectProxy``. Note that prior to this
  version if you had used ``from wrapt.wrappers import ObjectProxy`` you would
  have got the C extension variant of the class rather than the pure Python
  version if the C extension variant was available.

**Bugs Fixed**

* It was not possible to update the ``__class__`` attribute through the
  transparent object proxy when relying on the C implementation.

Version 1.15.0
--------------

**Bugs Fixed**

* When the C extension for wrapt was being used, and a property was used on an
  object proxy wrapping another object to intercept access to an attribute of
  the same name on the wrapped object, if the function implementing the property
  raised an exception, then the exception was ignored and not propagated back to
  the caller. What happened instead was that the original value of the attribute
  from the wrapped object was returned, thus silently suppressing that an
  exception had occurred in the wrapper. This behaviour was not happening when
  the pure Python version of wrapt was being used, with it raising the
  exception. The pure Python and C extension implementations thus did not behave
  the same.

  Note that in the specific case that the exception raised is AttributeError it
  still wouldn't be raised. This is the case for both Python and C extension
  implementations. If a wrapper for an attribute internally raises an
  AttributeError for some reason, the wrapper should if necessary catch the
  exception and deal with it, or propagate it as a different exception type if
  it is important that an exception still be passed back.

* Address issue where the post import hook mechanism of wrapt wasn't transparent
  and left the ``__loader__`` and ``__spec__.loader`` attributes of a module as
  the wrapt import hook loader and not the original loader. That the original
  loader wasn't preserved could interfere with code which needed access to the
  original loader.

* Address issues where a thread deadlock could occur within the wrapt module
  import handler, when code executed from a post import hook created a new
  thread and code executed in the context of the new thread itself tried to
  register a post import hook, or imported a new module.

* When using ``CallableObjectProxy`` as a wrapper for a type or function and
  calling the wrapped object, it was not possible to pass a keyword argument
  named ``self``. This only occurred when using the pure Python version of wrapt
  and did not occur when using the C extension based implementation.

* When using ``PartialCallableObjectProxy`` as a wrapper for a type or function,
  when constructing the partial object and when calling the partial object, it
  was not possible to pass a keyword argument named ``self``. This only occurred
  when using the pure Python version of wrapt and did not occur when using the C
  extension based implementation.

* When using ``FunctionWrapper`` as a wrapper for a type or function and calling
  the wrapped object, it was not possible to pass a keyword argument named
  ``self``. Because ``FunctionWrapper`` is also used by decorators, this also
  affected decorators on functions and class types. A similar issue also arose
  when these were applied to class and instance methods where binding occurred
  when the method was accessed. In that case it was in ``BoundFunctionWrapper``
  that the problem could arise. These all only occurred when using the pure
  Python version of wrapt and did not occur when using the C extension based
  implementation.

* When using ``WeakFunctionProxy`` as a wrapper for a function, when calling the
  function via the proxy object, it was not possible to pass a keyword argument
  named ``self``.

Version 1.14.2
--------------

**Bugs Fixed**

* Reference count was not being incremented on type object for C implementation
  of the partial callable object proxy when module was initialized. If wrapt was
  being used in Python sub interpreters which were deleted it could lead to the
  process crashing.

Version 1.14.1
--------------

**Bugs Fixed**

* When the post import hooks mechanism was being used, and a Python package with
  its own custom module importer was used, importing modules could fail if the
  custom module importer didn't use the latest Python import hook finder/loader
  APIs and instead used the deprecated API. This was actually occurring with the
  ``zipimporter`` in Python itself, which was not updated to use the newer
  Python APIs until Python 3.10.

Version 1.14.0
--------------

**Bugs Fixed**

* Python 3.11 dropped ``inspect.formatargspec()`` which was used in creating
  signature changing decorators. Now bundling a version of this function
  which uses ``Parameter`` and ``Signature`` from ``inspect`` module when
  available. The replacement function is exposed as ``wrapt.formatargspec()``
  if need it for your own code.

* When using a decorator on a class, ``isinstance()`` checks wouldn't previously
  work as expected and you had to manually use ``Type.__wrapped__`` to access
  the real type when doing instance checks. The ``__instancecheck__`` hook is
  now implemented such that you don't have to use ``Type.__wrapped__`` instead
  of ``Type`` as last argument to ``isinstance()``.

* Eliminated deprecation warnings related to Python module import system, which
  would have turned into broken code in Python 3.12. This was used by the post
  import hook mechanism.

**New Features**

* Binary wheels provided on PyPi for ``aarch64`` Linux systems and macOS
  native silicon where supported by Python when using ``pypa/cibuildwheel``.

Version 1.13.3
--------------

**New Features**

* Adds wheels for Python 3.10 on PyPi and where possible also now
  generating binary wheels for ``musllinux``.

Version 1.13.2
--------------

**Features Changed**

* On the Windows platform when using Python 2.7, by default the C extension
  will not be installed and the pure Python implementation will be used.
  This is because too often on Windows when using Python 2.7, there is no
  working compiler available. Prior to version 1.13.0, when installing the
  package it would fallback to using the pure Python implementation
  automatically but that relied on a workaround to do it when there was
  no working compiler. With the changes in 1.13.0 to use the builtin
  mechanism of Python to not fail when a C extension cannot be compiled,
  this fallback doesn't work when the compiler doesn't exist, as the
  builtin mechanism in Python regards lack of a compiler as fatal and not
  a condition for which it is okay to ignore the fact that the extension
  could not be compiled.

  If you are using Python 2.7 on Windows, have a working compiler, and
  still want to attempt to install the C extension, you can do so by
  setting the ``WRAPT_INSTALL_EXTENSIONS`` environment variable to ``true``
  when installing the ``wrapt`` package.

  Note that the next significant release of ``wrapt`` will drop support for
  Python 2.7 and Python 3.5. The change described here is to ensure that
  ``wrapt`` can be used with Python 2.7 on Windows for just a little bit
  longer. If using Python 2.7 on non Windows platforms, it will still
  attempt to install the C extension.

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
  notify the descriptor of the variable name was not being propagated. Note
  that this issue has been addressed in the ``FunctionWrapper`` used by
  ``@wrapt.decorator`` but has not been applied to the generic
  ``ObjectProxy`` class. If using ``ObjectProxy`` directly to construct a
  custom wrapper which is applied to a descriptor, you will need to
  propagate the ``__set_name__()`` call yourself if required.

* The ``issubclass()`` builtin method would give incorrect results when used
  with a class which had a decorator applied to it. Note that this has only
  been able to be fixed for Python 3.7+. Also, due to what is arguably a
  bug (https://bugs.python.org/issue44847) in the Python standard library,
  you will still have problems when the class hierarchy uses a base class
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
  which will only load and call the function of the specified module when
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

* Previously using ``@wrapt.decorator`` on a class type didn't really yield
  anything which was practically useful. This is now changed and when
  applied to a class an instance of the class will be automatically
  created to be used as the decorator wrapper function. The requirement
  for this is that the ``__call__()`` method be specified in the style as
  would be done for the decorator wrapper function.

  ::

      @wrapt.decorator
      class mydecoratorclass:
          def __init__(self, arg=None):
              self.arg = arg
          def __call__(self, wrapped, instance, args, kwargs):
              return wrapped(*args, **kwargs)

      @mydecoratorclass
      def function():
          pass

  If the resulting decorator class is to be used with no arguments, the
  ``__init__()`` method of the class must have all default arguments. These
  arguments can be optionally supplied though, by using keyword arguments
  to the resulting decorator when applied to the function to be decorated.

  ::

      @mydecoratorclass(arg=1)
      def function():
          pass

Version 1.7.0
-------------

**New Features**

* Provide ``wrapt.getcallargs()`` for determining how arguments mapped to a
  wrapped function. For Python 2.7 this is actually ``inspect.getcallargs()``
  with a local copy being used in the case of Python 2.6.

* Added ``wrapt.wrap_object_attribute()`` as a way of wrapping or otherwise
  modifying the result of trying to access the attribute of an object
  instance. It works by adding a data descriptor with the same name as
  the attribute, to the class type, allowing reading of the attribute
  to be intercepted. It does not affect updates to or deletion of the
  attribute.

**Bugs Fixed**

* Need to explicitly proxy special methods ``__bytes__()``, ``__reversed__()``
  and ``__round__()`` as they are only looked up on the class type and not
  the instance, so can't rely on ``__getattr__()`` fallback.

* Raise more appropriate ``TypeError``, with corresponding message, rather
  than ``IndexError``, when a decorated instance or class method is called via
  the class but the required 1st argument of the instance or class is not
  supplied.

Version 1.6.0
-------------

**Bugs Fixed**

* The ``ObjectProxy`` class would return that the ``__call__()`` method existed
  even though the wrapped object didn't have one. Similarly, ``callable()``
  would always return True even if the wrapped object was not callable.

  This resulted due to the existence of the ``__call__()`` method on the
  wrapper, required to support the possibility that the wrapped object
  may be called via the proxy object even if it may not turn out that
  the wrapped object was callable.

  Because checking for the existence of a ``__call__()`` method or using
  ``callable()`` can sometimes be used to indirectly infer the type of an
  object, this could cause issues. To ensure that this now doesn't
  occur, the ability to call a wrapped object via the proxy object has
  been removed from ``ObjectProxy``. Instead, a new class ``CallableObjectProxy``
  is now provided, with it being necessary to make a conscious choice as
  to which should be used based on whether the object to be wrapped is
  in fact callable.

  Note that neither before this change, or with the introduction of the
  class ``CallableObjectProxy``, does the object proxy perform binding. If
  binding behaviour is required it still needs to be implemented
  explicitly to match the specific requirements of the use case.
  Alternatively, the ``FunctionWrapper`` class should be used which does
  implement binding, but also enforces a wrapper mechanism for
  manipulating what happens at the time of the call.

Version 1.5.1
-------------

**Bugs Fixed**

* Instance method locking for the ``synchronized`` decorator was not correctly
  locking on the instance but the class, if a synchronized class method
  had been called prior to the synchronized instance method.

Version 1.5.0
-------------

**New Features**

* Enhanced ``@wrapt.transient_function_wrapper`` so it can be applied to
  instance methods and class methods with the ``self``/``cls`` argument being
  supplied correctly. This allows instance and class methods to be used for
  this type of decorator, with the instance or class type being able to
  be used to hold any state required for the decorator.

**Bugs Fixed**

* If the wrong details for a function to be patched was given to the
  decorator ``@wrapt.transient_function_wrapper``, the exception indicating
  this was being incorrectly swallowed up and mutating to a different
  more obscure error about local variable being access before being set.

Version 1.4.2
-------------

**Bugs Fixed**

* A process could crash if the C extension module was used and when using
  the ``ObjectProxy`` class a reference count cycle was created that required
  the Python garbage collector to kick in to break the cycle. This was
  occurring as the C extension had not implemented GC support in the
  ``ObjectProxy`` class correctly.

Version 1.4.1
-------------

**Bugs Fixed**

* Overriding ``__wrapped__`` attribute directly on any wrapper more than once
  could cause corruption of memory due to incorrect reference count
  decrement.

Version 1.4.0
-------------

**New Features**

* Enhanced ``@wrapt.decorator`` and ``@wrapt.function_wrapper`` so they can be
  applied to instance methods and class methods with the ``self``/``cls`` argument
  being supplied correctly. This allows instance and class methods to be
  used as decorators, with the instance or class type being able to be used
  to hold any state required for the decorator.

**Bugs Fixed**

* Fixed process crash in extension when the wrapped object passed as first
  argument to FunctionWrapper did not have a ``tp_descr_get`` callback for the
  type at C code level. Now raised an ``AttributeError`` exception in line with
  what Python implementation does.

Version 1.3.1
-------------

**Bugs Fixed**

* The ``discover_post_import_hooks()`` function had not been added to the
  top level wrapt module.

Version 1.3.0
-------------

**New Features**

* Added a ``@transient_function_wrapper`` decorator for applying a wrapper
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

* Added an ``enabled`` option to ``@decorator`` and ``FunctionWrapper`` which can
  be provided a boolean, or a function returning a boolean to allow the
  work of the decorator to be disabled dynamically. When a boolean, is
  used for ``@decorator``, the wrapper will not even be applied if ``enabled``
  is ``False``. If a function, then will be called prior to wrapper being
  called and if returns ``False``, then original wrapped function called
  directly rather than the wrapper being called.

* Added in an implementation of a post import hook mechanism in line with
  that described in PEP 369.

* Added in helper functions specifically designed to assist in performing
  monkey patching of existing code.

**Features Changed**

* Collapsed functionality of ``_BoundMethodWrapper`` into ``_BoundFunctionWrapper``
  and renamed the latter to ``BoundFunctionWrapper``. If deriving from the
  ``FunctionWrapper`` class and needing to override the type of the bound
  wrapper, the class attribute ``__bound_function_wrapper__`` should be set
  in the derived ``FunctionWrapper`` class to the replacement type.

**Bugs Fixed**

* When creating a custom proxy by deriving from ``ObjectProxy`` and the custom
  proxy needed to override ``__getattr__()``, it was not possible to called the
  base class ``ObjectProxy.__getattr__()`` when the C implementation of
  ObjectProxy was being used. The derived class ``__getattr__()`` could also
  get ignored.

* Using ``inspect.getargspec()`` now works correctly on bound methods when an
  adapter function can be provided to ``@decorator``.

Version 1.1.3
-------------

**New Features**

* Added a ``_self_parent`` attribute to ``FunctionWrapper`` and bound variants.
  For the ``FunctionWrapper`` the value will always be ``None``. In the case of the
  bound variants of the function wrapper, the attribute will refer back
  to the unbound ``FunctionWrapper`` instance. This can be used to get a back
  reference to the parent to access or cache data against the persistent
  function wrapper, the bound wrappers often being transient and only
  existing for the single call.

**Improvements**

* Use interned strings to optimise name comparisons in the setattro()
  method of the C implementation of the object proxy.

**Bugs Fixed**

* The pypy interpreter is missing ``operator.__index__()`` so proxying of that
  method in the object proxy would fail. This is a bug in pypy which is
  being addressed. Use ``operator.index()`` instead which pypy does provide
  and which also exists for CPython.

* The pure Python implementation allowed the ``__wrapped__`` attribute to be
  deleted which could cause problems. Now raise a TypeError exception.

* The C implementation of the object proxy would crash if an attempt was
  made to delete the ``__wrapped__`` attribute from the object proxy. Now raise a
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

* In place operators in pure Python object proxy for ``__idiv__`` and
  ``__itruediv__`` were not replacing the wrapped object with the result
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

* Added a ``WeakFunctionProxy`` class which can wrap references to instance
  methods as well as normal functions.

* Exposed from the C extension the classes ``_FunctionWrapperBase``,
  ``_BoundFunctionWrapper`` and ``_BoundMethodWrapper`` so that it is possible to
  create new variants of ``FunctionWrapper`` in pure Python code.

**Bugs Fixed**

* When deriving from ``ObjectProxy``, and the C extension variant
  was being used, if a derived class overrode ``__new__()`` and tried to access
  attributes of the ObjectProxy created using the base class ``__new__()``
  before ``__init__()`` was called, then an exception would be raised
  indicating that the 'wrapper has not been initialised'.

* When deriving from ``ObjectProxy``, and the C extension variant
  was being used, if a derived class ``__init__()`` attempted to update
  attributes, even the special ``_self_`` attributed before calling the base
  class ``__init__()`` method, then an exception would be raised indicating
  that the 'wrapper has not been initialised'.

Version 1.0.0
-------------

Initial release.
