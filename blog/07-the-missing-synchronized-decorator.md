The missing @synchronized decorator
===================================

This is the seventh post in my series of blog posts about Python decorators
and how I believe they are generally poorly implemented. It follows on from
the previous post titled [Maintaining decorator state using a
class](06-maintaining-decorator-state-using-a-class.md), with the very
first post in the series being [How you implemented your Python decorator
is wrong](01-how-you-implemented-your-python-decorator-is-wrong.md).

In the previous post I effectively rounded out the discussion on the
implementation of the decorator pattern, or at least the key parts that I
care to cover at this point. I may expand on a few other things that can be
done at a later time.

At this point I want to start looking at ways this decorator pattern can be
used to implement better decorators. For this post I want to look at the
``@synchronized`` decorator.

The concept of the ``@synchronized`` decorator originates from Java and the
idea of being able to write such a decorator in Python was a bit of a
poster child when decorators were first added to Python. Despite this,
there is no standard ``@synchronized`` decorator in the Python standard
library. If this was such a good example of why decorators are so useful,
why is this the case?

Stealing ideas from the Java language
-------------------------------------

The equivalent synchronization primitive from Java comes in two forms.
These are synchronized methods and synchronized statements.

In Java, to make a method synchronized, you simply add the synchronized
keyword to its declaration:

```
public class SynchronizedCounter {
    private int c = 0; 
    public synchronized void increment() {
        c++;
    } 
    public synchronized void decrement() {
        c--;
    } 
    public synchronized int value() {
        return c;
    }
}
```

Making a method synchronized means it is not possible for two invocations
of synchronized methods on the same object to interleave. When one thread
is executing a synchronized method for an object, all other threads that
invoke synchronized methods for the same object block (suspend execution)
until the first thread is done with the object.

In other words, each instance of the class has an intrinsic lock object and
upon entering a method the lock is being acquired, with it subsequently
being released when the method returns. The lock is what is called a
re-entrant lock, meaning that a thread can while it holds the lock, acquire
it again without blocking. This is so that from one synchronized method it
is possible to call another synchronized method on the same object.

The second way to create synchronized code in Java is with synchronized
statements. Unlike synchronized methods, synchronized statements must
specify the object that provides the intrinsic lock:

```
public void addName(String name) {
    synchronized(this) {
        lastName = name;
        nameCount++;
    }
    nameList.add(name);
}
```

Of note is that in Java one can use any object as the source of the lock,
it is not necessary to create an instance of a specific lock type to
synchronize on. If more fined grained locking is required within a class
one can simply create or use an existing arbitrary object to synchronize
on.

```
public class MsLunch {
    private long c1 = 0;
    private long c2 = 0;
    private Object lock1 = new Object();
    private Object lock2 = new Object(); 
    public void inc1() {
        synchronized(lock1) {
            c1++;
        }
    } 
    public void inc2() {
        synchronized(lock2) {
            c2++;
        }
    }
}
```

These synchronization primitives looks relatively simple to use, so how
close did people come to actually achieving the level of simplicity by
using decorators to do the same in Python.

Synchronizing off a thread mutex
--------------------------------

In Python it isn't possible to synchronize off an arbitrary object. Instead
it is necessary to create a specific lock object which internally holds a
thread mutex. Such a lock object provides an ``acquire()`` and
``release()`` method for manipulating the lock.

Since context managers were introduced to Python however, locks also
support being used in conjunction with the ``with`` statement. Using this
specific feature, the typical recipe given for implementing a
``@synchronized`` decorator for Python is:

```
def synchronized(lock=None):
    def _decorator(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(*args, **kwargs):
            with lock:
                return wrapped(*args, **kwargs)
        return _wrapper
    return _decorator 

lock = threading.RLock() 

@synchronized(lock)
def function():
    pass
```

Using this approach becomes annoying after a while because for every
distinct function that needs to be synchronized, you have to first create a
companion thread lock to go with it.

The alternative to needing to pass in the lock object each time, is to
create one automatically for each use of the decorator.

```
def synchronized(wrapped):
    lock = threading.RLock() 
    @functools.wraps(wrapped)
    def _wrapper(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)
    return _wrapper 

@synchronized
def function():
    pass
```

We can even use the pattern described previously for allowing optional
decorator arguments to permit either approach.

```
def synchronized(wrapped=None, lock=None):
    if wrapped is None:
        return functools.partial(synchronized, lock=lock) 
    if lock is None:
        lock = threading.RLock() 
    @functools.wraps(wrapped)
    def _wrapper(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)
    return _wrapper 

@synchronized
def function1():
    pass 

lock = threading.Lock() 

@synchronized(lock=lock)
def function2():
    pass
```

Whatever the approach, the decorator being based on a function closure
suffers all the problems we have already outlined. The first step we can
therefore take is to update it to use our new decorator factory instead.

```
def synchronized(wrapped=None, lock=None):
    if wrapped is None:
        return functools.partial(synchronized, lock=lock) 

    if lock is None:
        lock = threading.RLock() 

    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        with lock:
            return wrapped(*args, **kwargs)

    return _wrapper(wrapped)
```

Because this is using our decorator factory, it also means that the same
code is safe to use on instance, class or static methods as well.

Using this on methods of a class though starts to highlight why this
simplistic approach isn't particularly useful. This is because the locking
only applies to calls made to the specific method which is wrapped. Plus
that it will be across that one method on all instances of the class. This
isn't really want we want and doesn't mirror how synchronized methods in
Java work.

Reiterating what we are after again, for all instance methods of a specific
instance of a class, if they have been decorated as being synchronized, we
want them to synchronize off a single lock object associated with the class
instance.

Now there have been posts describing how to improve on this in the past,
including for example this quite involved attempt. Personally though I find
the way in which it is done is quite clumsy and even suspect it isn't
actually thread safe, with a race condition over the creation of some of
the locks.

Because it used function closures and didn't have our concept of a
universal decorator, it was also necessary to create a multitude of
different decorators and then try and plaster them together under a single
decorator entry point. Obviously, we should now be able to do a lot better
than this.

Storing the thread mutex on objects
-----------------------------------

Starting over, lets take a fresh look at how we can manage the thread locks
we need to have. Rather than requiring the lock be passed in, or creating
it within a function closure which is then available to the nested wrapper,
lets try and manage the locks within the wrapper itself.

In doing this the issue is where can we store the thread lock. The only
options for storing any data between invocations of the wrapper are going
to be on the wrapper itself, on the wrapped function object, in the case of
wrapping an instance method, on the class instance, or for a class method,
on the class.

Lets first consider the case of a normal function. In that case what we can
do is store the required thread lock on the wrapped function object itself.

```
@decorator
def synchronized(wrapped, instance, args, kwargs):
    lock = vars(wrapped).get('_synchronized_lock', None) 
    if lock is None:
        lock = vars(wrapped).setdefault('_synchronized_lock', threading.RLock()) 
    with lock:
        return wrapped(*args, **kwargs) 

@synchronized
def function():
    pass 

>>> function() 
>>> function._synchronized_lock
<_RLock owner=None count=0>
```

A key issue we have to deal with in doing this is how to create the thread
lock the first time it is required. To do that the first thing we need do
is to see if we already have created a thread lock.

```
lock = vars(wrapped).get('_synchronized_lock', None)
```

If this returns a valid thread lock object we are fine and can continue on
to attempt to acquire the lock. If however it didn't exist we need to
create it, but we have to be careful how we do this in order to avoid a
race condition when two threads have entered this section of code at the
same time and both believe it is responsible for creating the thread lock.

The trick we use to solve this is to use:

```
lock = vars(wrapped).setdefault('_synchronized_lock', threading.RLock())
```

In the case of two threads trying to set the lock at the same time, they
will both actually create an instance of a thread lock, but by virtue of
using ``dict.setdefault()``, only one of them will win and actually be able
to set it to the instance of the thread lock it created.

As ``dict.setdefault()`` then returns whichever is the first value to be
stored, both threads will then continue on and attempt to acquire the same
thread lock object. It doesn't matter here that one of the thread objects
gets thrown away as it will only occur at the time of initialisation and
only if there was actually a race to set it.

We have therefore managed to replicate what we had originally, the
difference though being that the thread lock is stored on the wrapped
function, rather than on the stack of an enclosing function. We still have
the issue that every instance method will have a distinct lock.

The simple solution is that we use the fact that this is what we are
calling a universal decorator and use the ability to detect in what context
the decorator was used.

Specifically, what we want to do is detect when we are being used on an
instance method or class method, and store the lock on the object passed as
the ``instance`` argument instead.

```
@decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        context = vars(wrapped)
    else:
        context = vars(instance) 

    lock = context.get('_synchronized_lock', None) 

    if lock is None:
        lock = context.setdefault('_synchronized_lock', threading.RLock()) 

    with lock:
        return wrapped(*args, **kwargs)

class Object(object):

    @synchronized
    def method_im(self):
        pass 

    @synchronized
    @classmethod
    def method_cm(cls):
        pass

o1 = Object()
o2 = Object() 

>>> o1.method_im()
>>> o1._synchronized_lock
<_RLock owner=None count=0>
>>> id(o1._synchronized_lock)
4386605392 

>>> o2.method_im()
>>> o2._synchronized_lock
<_RLock owner=None count=0>
>>> id(o2._synchronized_lock)
4386605456
```

This simple change has actually achieved the result we desired. If the
synchronized decorator is used on a normal function then the thread lock
will be stored on the function itself and it will stand alone and only be
synchronized with calls to the same function.

For the case of the instance method, the thread lock will be stored on the
instance of the class the instance methods are bound too and any instance
methods marked as being synchronized on that class will all synchronize on
that single thread lock, thus mimicking how Java behaves.

Now what about that class method. In this case the instance argument is
actually the class type. If the thread lock is stored on the type, then the
result would be that if there were multiple class methods and they were all
marked as synchronized, they would exclude each other. The thread lock in
this case is distinct from any used by instance methods, but that is also
actually what we want.

Does the code work though for a class method?

```
>>> Object.method_cm()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "test.py", line 38, in __call__
    return self.wrapper(self.wrapped, instance, args, kwargs)
  File "synctest.py", line 176, in synchronized
    lock = context.setdefault('_synchronized_lock',
AttributeError: 'dictproxy' object has no attribute 'setdefault'
```

Unfortunately not.

The reason this is the case is that the ``__dict__`` of a class type is not
a normal dictionary, but a dictproxy. A dictproxy doesn't share the same
methods as a normal dict and in particular, it does not provide the
``setdefault()`` method.

We therefore need a different way of synchronizing the creation of the
thread lock the first time for the case where instance is a class.

We also have another issue due to a dictproxy being used. That is that
dictproxy doesn't support item assignment.

```
>>> vars(Object)['_synchronized_lock'] = threading.RLock()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'dictproxy' object does not support item assignment
```

What it does still support though is attribute assignment.

```
>>> setattr(Object, '_synchronized_lock', threading.RLock())
>>> Object._synchronized_lock
<_RLock owner=None count=0>
```

and since both function objects and class instances do as well, we will
need to switch to that method of updating attributes.

Storing a meta lock on the decorator
------------------------------------

As to an alternative for using dict.setdefault() as an atomic way of
setting the lock the first time, what we can do instead is use a meta
thread lock stored on the ``@synchronized`` decorator itself. With this we
still have the issue though of ensuring that only one thread can get to set
it. We therefore use ``dict.setdefault()`` to control creation of the meta
lock at least.

```
@decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        owner = wrapped
    else:
        owner = instance 

    lock = vars(owner).get('_synchronized_lock', None) 

    if lock is None:
        meta_lock = vars(synchronized).setdefault(
                '_synchronized_meta_lock', threading.Lock()) 

        with meta_lock:
            lock = vars(owner).get('_synchronized_lock', None) 
            if lock is None:
                lock = threading.RLock()
                setattr(owner, '_synchronized_lock', lock) 

    with lock:
        return wrapped(*args, **kwargs)
```

Note that because of the gap between checking for the existence of the lock
for the wrapped function and creating the meta lock, after we have acquired
the meta lock we need to once again check to see if the lock exists. This
is to handle the case where two threads came into the code at the same time
and are racing to be the first to create the lock.

Now one thing which is very important in this change is that we only
swapped to using attribute access for updating the lock for the wrapped
function. We have not changed to using ``getattr()`` for looking up the
lock in the first place and are still looking it up in ``__dict__`` as
returned by ``vars()``.

This is necessary because when ``getattr()`` is used on an instance of a
class, if that attribute doesn't exist on the instance of the class, then
the lookup rules mean that if the attribute instead existed on the class
type, then that would be returned instead.

This would cause problems if a synchronized class method was the first to
be called, because it would then leave a lock on the class type. When the
instance method was subsequently called, if ``getattr()`` were used, it
would find the lock on the class type and return it and it would be wrongly
used. Thus we stay with looking for the lock via ``__dict__`` as that will
only contain what actually exists in the instance.

With these changes we are now all done and all lock creation is now
completely automatic, with an appropriate lock created for the different
contexts the decorator is used in.

```
@synchronized
def function():
    pass 

class Object(object):

    @synchronized
    def method_im(self):
        pass 

    @synchronized
    @classmethod
    def method_cm(cls):
        pass 

o = Object() 

>>> function()
>>> id(function._synchronized_lock)
4338158480 

>>> Object.method_cm()
>>> id(Object._synchronized_lock)
4338904656 

>>> o.method_im()
>>> id(o._synchronized_lock)
4338904592
```

The code also works for where ``@synchronized`` is used on a static method
or class type. In summary, the result for the different places
``@synchronized`` can be placed is:

```
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
```

Implementing synchronized statements
------------------------------------

So we are all done with implementing support for synchronized methods, but
what about those synchronized statements. The goal here is that we want to
be able to write:

```
class Object(object): 

    @synchronized
    def function_im_1(self):
        pass 

    def function_im_2(self):
        with synchronized(self):
            pass
```

That is, we need for ``synchronized`` to not only be usable as a decorator,
but for it also be able to be used as a context manager.

In this role, similar to with Java, it would be supplied the object on
which synchronization is to occur, which for instance methods would be the
``self`` object or instance of the class.

For an explanation of how we can do this though, you will need to wait for
the next instalment in this series of posts.
