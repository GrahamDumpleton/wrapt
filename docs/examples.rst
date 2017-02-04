Assorted Examples
=================

This document provides various examples of decorators often described
elsewhere, to exhibit what can be done with decorators using the **wrapt**
module, for the purpose of comparison.

Thread Synchronization
----------------------

.. note::
    The final variant of the ``synchronized`` decorator described here
    is available within the **wrapt** package as ``wrapt.synchronized``.

Synchronization decorators are a simplified way of adding thread locking to
functions, methods, instances of classes or a class type. They work by
associating a thread mutex with a specific context and when a function is
called the lock is acquired prior to the call and then released once the
function returns.

The simplest example of a decorator for synchronization is one where the
lock is explicitly provided when the decorator is applied to a function. By
being supplied explicitly, it is up to the user of the decorator to
determine what context the lock applies to. For example, a lock may be
applied to a single function, a group of functions, or a class.

As the lock needs to be supplied when the decorator is applied to the
function we need to use a function closure as a means of supplying the
argument to the decorator.

::

    def synchronized(lock):
        @wrapt.decorator
        def _wrapper(wrapped, instance, args, kwargs):
            with lock:
                return wrapped(*args, **kwargs)
        return _wrapper

    import threading

    lock = threading.RLock()

    @synchronized(lock)
    def function():
        pass

    class Class(object):

        @synchronized(lock)
        def function(self):
            pass

Note that the recursive lock ``threading.RLock`` is used to ensure that
recursive calls, or calls to another synchronized function associated with
the same lock, doesn't cause a deadlock.

An alternative to requiring the lock be supplied when the decorator is
applied to a function, is to associate a lock automatically with the
wrapped function. That is, rather than require the lock be passed in
explicitly, create one on demand and attach it to the wrapped function.

::

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        # Retrieve the lock from the wrapped function.

        lock = vars(wrapped).get('_synchronized_lock', None)

        if lock is None:
            # There was no lock yet associated with the function so we
            # create one and associate it with the wrapped function.
            # We use ``dict.setdefault()`` as a means of ensuring that
            # only one thread gets to set the lock if multiple threads
            # do this at the same time. This may mean redundant lock
            # instances will get thrown away if there is a race to set
            # it, but all threads would still get back the same one lock.

            lock = vars(wrapped).setdefault('_synchronized_lock',
                    threading.RLock())

        with lock:
            return wrapped(*args, **kwargs)

    @synchronized
    def function():
        pass

This avoids the need for an instance of a lock to be passed in explicitly
when the decorator is being applied to a function, but it now means that
all decorated methods of a class will have a distinct lock.

A more severe issue in both these approaches is that locks on each method
work across all instances of the class where as what we really want is a
lock per instance of a class for all methods of the class decorated with
the ``@synchronized`` decorator.

To address this, we can use the fact that the decorator wrapper function
is passed the ``instance`` and so can determine when the function is being
invoked on an instance of a class and that it is not a normal function
call. In this case we can associate the lock with the instance instead.

::

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        # Use the instance as the context if function was bound.

        if instance is not None:
            context = vars(instance)
        else:
            context = vars(wrapped)

        # Retrieve the lock for the specific context.

        lock = context.get('_synchronized_lock', None)

        if lock is None:
            # There was no lock yet associated with the function so we
            # create one and associate it with the wrapped function.
            # We use ``dict.setdefault()`` as a means of ensuring that
            # only one thread gets to set the lock if multiple threads
            # do this at the same time. This may mean redundant lock
            # instances will get thrown away if there is a race to set
            # it, but all threads would still get back the same one lock.

            lock = context.setdefault('_synchronized_lock',
                    threading.RLock())

        with lock:
            return wrapped(*args, **kwargs)

    @synchronized
    def function():
        pass

Now we actually have two scenarios that match for where ``instance`` is not
``None``. One will be where an instance method is being called on a class,
which is what we are targeting in this case. We will also have ``instance``
being a value other than ``None`` for the case where a class method is
called. For this case ``instance`` will be a reference to the class type.

Having the lock being associated with the class type for class methods is
entirely reasonable, but a problem presents. That is that
``vars(instance)`` where ``instance`` is a class type, actually returns a
``dictproxy`` and not a ``dict``. As a ``dictproxy`` is effectively read
only, it is not possible to associate the lock with it.

A similar problem also occurs where ``instance`` is ``None`` but ``wrapped``
is a class type. That is, if the decorator was applied to a class. The result
is that the above technique will not work in these two cases.

The only way that it is possible to add attributes to a class type is to use
``setattr``, either explicitly or via direct attribute assignment. Although
this allows us to add attributes to a class, there is no equivalent to
``dict.setdefault()``, so we loose the ability to add the attribute which will
hold the lock atomically.

To get around this problem, we need to use an intermediary meta lock which
gates the attempt to associate a lock with a specific context. This meta
lock itself still needs to be created somehow, so what we do now is use
the ``dict.setdefault()`` trick against the decorator itself and use it as
the place to store the meta lock.

::

    @wrapt.decorator
    def synchronized(wrapped, instance, args, kwargs):
        # Use the instance as the context if function was bound.

        if instance is not None:
            context = instance
        else:
            context = wrapped

        # Retrieve the lock for the specific context.

        lock = vars(context).get('_synchronized_lock', None)

        if lock is None:
            # There is no existing lock defined for the context we
            # are dealing with so we need to create one. This needs
            # to be done in a way to guarantee there is only one
            # created, even if multiple threads try and create it at
            # the same time. We can't always use the setdefault()
            # method on the __dict__ for the context. This is the
            # case where the context is a class, as __dict__ is
            # actually a dictproxy. What we therefore do is use a
            # meta lock on this wrapper itself, to control the
            # creation and assignment of the lock attribute against
            # the context.

            meta_lock = vars(synchronized).setdefault(
                    '_synchronized_meta_lock', threading.Lock())

            with meta_lock:
                # We need to check again for whether the lock we want
                # exists in case two threads were trying to create it
                # at the same time and were competing to create the
                # meta lock.

                lock = vars(context).get('_synchronized_lock', None)

                if lock is None:
                    lock = threading.RLock()
                    setattr(context, '_synchronized_lock', lock)

        with lock:
            return wrapped(*args, **kwargs)

This means lock creation is all automatic, with an appropriate lock created
for the different contexts the decorator is used in.

::

    @synchronized # lock bound to function1
    def function1():
        pass

    @synchronized # lock bound to function2
    def function2():
        pass

    @synchronized # lock bound to Class
    class Class(object):

        @synchronized # lock bound to instance of Class
        def function_im(self):
            pass

        @synchronized # lock bound to Class
        @classmethod
        def function_cm(cls):
            pass

        @synchronized # lock bound to function_sm
        @staticmethod
        def function_sm():
            pass

Specifically, when the decorator is used on a normal function or static
method, a unique lock will be associated with each function. For the case
of instance methods, the lock will be against the instance. Finally, for
class methods and a decorator against an actual class, the lock will be
against the class type.

One requirement with this approach though is that only the execution of a
whole function can be synchronized. In Java where a similar mechanism
exists, it is also possible to have synchronized statements. In Python one
can emulate synchronized statements by using the 'with' statement in
conjunction with a lock. The trick with that is that if using it within a
method of a class, we want to be able to use the same lock as that which is
being applied to synchronized methods of the class. In effect we want to be
able to do the following.

::

    class Class(object):

        @synchronized
        def function_im_1(self):
            pass

        def function_im_2(self):
            with synchronized(self):
                pass

In other words we want the decorator function to serve a dual role of being
able to decorate a function to make it synchronized, but also return a
context manager for the lock for a specific context so that it can be used
with the 'with' statement.

Because of this dual requirement, we actually need to partly side step
``wrapt.decorator`` and drop down to using the underlying ``FunctionWrapper``
class that it uses to implement decorators. Specifically, we need to create
a derived version of ``FunctionWrapper`` which converts it into a context
manager, but at the same time can still be used as a decorator as before.

::

    def synchronized(wrapped):
        def _synchronized_lock(context):
            # Attempt to retrieve the lock for the specific context.

            lock = vars(context).get('_synchronized_lock', None)

            if lock is None:
                # There is no existing lock defined for the context we
                # are dealing with so we need to create one. This needs
                # to be done in a way to guarantee there is only one
                # created, even if multiple threads try and create it at
                # the same time. We can't always use the setdefault()
                # method on the __dict__ for the context. This is the
                # case where the context is a class, as __dict__ is
                # actually a dictproxy. What we therefore do is use a
                # meta lock on this wrapper itself, to control the
                # creation and assignment of the lock attribute against
                # the context.

                meta_lock = vars(synchronized).setdefault(
                        '_synchronized_meta_lock', Lock())

                with meta_lock:
                    # We need to check again for whether the lock we want
                    # exists in case two threads were trying to create it
                    # at the same time and were competing to create the
                    # meta lock.

                    lock = vars(context).get('_synchronized_lock', None)

                    if lock is None:
                        lock = RLock()
                        setattr(context, '_synchronized_lock', lock)

            return lock

        def _synchronized_wrapper(wrapped, instance, args, kwargs):
            # Execute the wrapped function while the lock for the
            # desired context is held. If instance is None then the
            # wrapped function is used as the context.

            with _synchronized_lock(instance or wrapped):
                return wrapped(*args, **kwargs)

        class _FinalDecorator(FunctionWrapper):

            def __enter__(self):
                self._self_lock = _synchronized_lock(self.__wrapped__)
                self._self_lock.acquire()
                return self._self_lock

            def __exit__(self, *args):
                self._self_lock.release()

        return _FinalDecorator(wrapped=wrapped, wrapper=_synchronized_wrapper)

When used in this way, the more typical use case would be to synchronize
against the class instance, but if needing to synchronize with the work of
a class method from an instance method, it could also be done against the
class itself.

::

    class Class(object):

        @synchronized
        @classmethod
        def function_cm(cls):
            pass

        def function_im(self):
            with synchronized(Class):
                pass

If wishing to have more than one normal function synchronize on the same
object, then it is possible to have the synchronization be against a data
structure which they all manipulate.

::

    class Data(object):
        pass

    data = Data()

    def function_1():
        with synchronized(data):
            pass

    def function_2():
        with synchronized(data):
            pass

In doing this you would be restricted to using a data structure to which
new attributes can be added, such that the hidden lock can be added. This
means for example, you could not do this with a dictionary. It also means
you can't just decorate the whole function.

What would perhaps be better is to return back to having the ``synchronized``
decorator allow an actual lock object to be supplied when the decorator is
being applied to a function. Being able to do this though would be
optional and if not done the lock would be associated with the appropriate
context of the wrapped function.

::

    lock = threading.RLock()

    @synchronized(lock)
    def function_1():
        pass

    @synchronized(lock)
    def function_2():
        pass

This requires what the decorator accepts to be overloaded and so may be
frowned on by some, but the implementation would be as follows.

::

    def synchronized(wrapped):
        # Determine if being passed an object which is a synchronization
        # primitive. We can't check by type for Lock, RLock, Semaphore etc,
        # as the means of creating them isn't the type. Therefore use the
        # existence of acquire() and release() methods. This is more
        # extensible anyway as it allows custom synchronization mechanisms.

        if hasattr(wrapped, 'acquire') and hasattr(wrapped, 'release'):
            # We remember what the original lock is and then return a new
            # decorator which accesses and locks it. When returning the new
            # decorator we wrap it with an object proxy so we can override
            # the context manager methods in case it is being used to wrap
            # synchronized statements with a 'with' statement.

            lock = wrapped

            @decorator
            def _synchronized(wrapped, instance, args, kwargs):
                # Execute the wrapped function while the original supplied
                # lock is held.

                with lock:
                    return wrapped(*args, **kwargs)

            class _PartialDecorator(ObjectProxy):

                def __enter__(self):
                    lock.acquire()
                    return lock

                def __exit__(self, *args):
                    lock.release()

            return _PartialDecorator(wrapped=_synchronized)

        # Following only apply when the lock is being created
        # automatically based on the context of what was supplied. In
        # this case we supply a final decorator, but need to use
        # FunctionWrapper directly as we want to derive from it to add
        # context manager methods in case it is being used to wrap
        # synchronized statements with a 'with' statement.

        def _synchronized_lock(context):
            # Attempt to retrieve the lock for the specific context.

            lock = vars(context).get('_synchronized_lock', None)

            if lock is None:
                # There is no existing lock defined for the context we
                # are dealing with so we need to create one. This needs
                # to be done in a way to guarantee there is only one
                # created, even if multiple threads try and create it at
                # the same time. We can't always use the setdefault()
                # method on the __dict__ for the context. This is the
                # case where the context is a class, as __dict__ is
                # actually a dictproxy. What we therefore do is use a
                # meta lock on this wrapper itself, to control the
                # creation and assignment of the lock attribute against
                # the context.

                meta_lock = vars(synchronized).setdefault(
                        '_synchronized_meta_lock', Lock())

                with meta_lock:
                    # We need to check again for whether the lock we want
                    # exists in case two threads were trying to create it
                    # at the same time and were competing to create the
                    # meta lock.

                    lock = vars(context).get('_synchronized_lock', None)

                    if lock is None:
                        lock = RLock()
                        setattr(context, '_synchronized_lock', lock)

            return lock

        def _synchronized_wrapper(wrapped, instance, args, kwargs):
            # Execute the wrapped function while the lock for the
            # desired context is held. If instance is None then the
            # wrapped function is used as the context.

            with _synchronized_lock(instance or wrapped):
                return wrapped(*args, **kwargs)

        class _FinalDecorator(FunctionWrapper):

            def __enter__(self):
                self._self_lock = _synchronized_lock(self.__wrapped__)
                self._self_lock.acquire()
                return self._self_lock

            def __exit__(self, *args):
                self._self_lock.release()

        return _FinalDecorator(wrapped=wrapped, wrapper=_synchronized_wrapper)

As well as normal functions, this can be used with methods of classes as
well. Because though the lock object has to be available at the time the
class definition is being created, it can only be used to refer to a lock
which is the same across the whole class, or one which is at global scope.

::

    class Class(object):
        lock1 = threading.RLock()
        lock2 = threading.RLock()

        @synchronized(lock1)
        @classmethod
        def function_cm_1(cls):
            pass

        @synchronized(lock1)
        def function_im_1(self):
            pass

        @synchronized(lock2)
        @classmethod
        def function_cm_2(cls):
            pass

The alternative is to use ``synchronized`` as a context manager and pass the
lock in at that time.

::

    class Class(object):

        def __init__(self):
            self.lock1 = threading.RLock()

        def function_im(self):
            with synchronized(self.lock1):
                pass

This is actually the same as using the 'with' statement directly on the lock,
but it you want to get carried away and have all the code look more or less
uniform, it is possible.

One benefit of being able to pass the lock in explicitly, is that you can
override the default lock type used, which is ``threading.RLock``. Any
synchronization primitive can be supplied so long as it provides a
``acquire()`` and ``release()`` method. This includes being able to pass
in your own custom class objects with such methods which do something
appropriate.

::

    semaphore = threading.Semaphore(2)

    @synchronized(semaphore)
    def function():
        pass
