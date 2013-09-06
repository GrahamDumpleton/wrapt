Examples
========

At this time the **wrapt** module does not provide any bundled decorators,
only the one decorator for creating other decorators. This document
provides various examples of decorators often described elsewhere, to
exhibit what can be done with decorators using the **wrapt** module, for
the purpose of comparison.

Synchronization
---------------

Synchronization decorators are a simplified way of adding thread locking to
functions, methods, instances of classes or a class type. They work by
associating a thread mutex with a specific context and when a function is
called the lock is acquired prior to the call and then released once the
function returns.

The simplist example of a decorator for synchronization is one where the
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

    _lock = threading.RLock()

    @synchronized(_lock)
    def function():
        pass

    class Class(object):

        @synchronized(_lock):
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

        lock = vars(wrapped).get('_synchronized_lock', None):

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

        lock = context.get('_synchronized_lock', None):

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

        lock = getattr(context, '_synchronized_lock', None)

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

                lock = getattr(context, '_synchronized_lock', None)

                if lock is None:
                    lock = threading.RLock()
                    setattr(context, '_synchronized_lock', lock)

        with lock:
            return wrapped(*args, **kwargs)

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

This means lock creation is all automatic, with an appropriate lock created
for the different contexts the decorator is used in.

Specifically, when the decorator is used on a normal function or static
method, a unique lock will be associated with each function. For the case
of instance methods, the lock will be against the instance. Finally, for
class methods and a decorator against an actual class, the lock will be
against the class type.