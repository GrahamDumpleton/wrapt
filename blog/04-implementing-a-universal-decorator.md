Implementing a universal decorator
==================================

This is the fourth post in my series of blog posts about Python decorators
and how I believe they are generally poorly implemented. It follows on from
the previous post titled [Implementing a factory for creating
decorators](03-implementing-a-factory-for-creating-decorators.md), with the
very first post in the series being [How you implemented your Python
decorator is
wrong](01-how-you-implemented-your-python-decorator-is-wrong.md).

In the second post of this series I described a better way of building a
decorator which avoided a number of issues I outlined with the typical way
in which decorators are coded. This entailed a measure of boiler plate code
which needed to be replicated each time. In the previous post to this one I
described how we could use a decorator as a decorator factory, and a bit of
delegation to hide the boiler plate code and reduce what a user needed to
actually declare for a new decorator.

In the prior post I also started to walk through some customisations which
could be made to the decorator pattern which would allow the decorator
wrapper function provided by a user to ascertain in what context it was
used in. That is, for the wrapper function to be able to determine whether
it was applied to a function, an instance method, a class method or a class
type. The ability to determine the context in this way is what I called a
universal decorator, as it avoided the need to have separate decorator
implementations for use in each circumstance as is done now with a more
traditional way of implementing a decorator.

The walk through got as far as showing how one could distinguish between
when the decorator was used on a normal function vs an instance method.
Unfortunately the change required to be able to detect when an instance
method was called via the class would cause problems for a class method or
static method, so we still have a bit more work to do.

In this post I will describe how we can accommodate the cases of a class
method and a static method as well as explore other use cases which may
give us problems in trying to come up with this pattern for a universal
decorator.

Normal functions vs instance methods
------------------------------------

The pattern for our universal decorator as described so far was as follows:

```
class bound_function_wrapper(object_proxy):  

    def __init__(self, wrapped, instance, wrapper):
        super(bound_function_wrapper, self).__init__(wrapped)
        self.instance = instance
        self.wrapper = wrapper 

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            instance, args = args[0], args[1:]
            wrapped = functools.partial(self.wrapped, instance)
            return self.wrapper(wrapped, instance, args, kwargs)
        return self.wrapper(self.wrapped, self.instance, args, kwargs) 

class function_wrapper(object_proxy): 

    def __init__(self, wrapped, wrapper):
        super(function_wrapper, self).__init__(wrapped)
        self.wrapper = wrapper 

    def __get__(self, instance, owner):
        wrapped = self.wrapped.__get__(instance, owner)
        return bound_function_wrapper(wrapped, instance, self.wrapper) 

    def __call__(self, *args, **kwargs):
        return self.wrapper(self.wrapped, None, args, kwargs)
```

This was used in conjunction with our decorator factory:

```
def decorator(wrapper):
    @functools.wraps(wrapper)
    def _decorator(wrapped):
        return function_wrapper(wrapped, wrapper)
    return _decorator
```

To test whether everything is working how we want we used our decorator
factory to create a decorator which would dump out the values of any
instance the wrapped function is bound to, and the arguments passed to the
call when executed.

```
@decorator
def my_function_wrapper(wrapped, instance, args, kwargs):
    print('INSTANCE', instance)
    print('ARGS', args)
    return wrapped(*args, **kwargs) 
```

This gave us the desired results for when the decorator was applied to a
normal function and instance method, including when an instance method was
called via the class and the instance passed in explicitly.

```
@my_function_wrapper
def function(a, b):
    pass

>>> function(1, 2)
INSTANCE None
ARGS (1, 2) 

class Class(object):
    @my_function_wrapper
    def function_im(self, a, b):
        pass 

c = Class() 

>>> c.function_im(1, 2)
INSTANCE <__main__.Class object at 0x1085ca9d0>
ARGS (1, 2) 

>>> Class.function_im(c, 1, 2)
INSTANCE <__main__.Class object at 0x1085ca9d0>
ARGS (1, 2) 
```

The change to support the latter however, broke things for the case of the
decorator being applied to a class method. Similarly for a static method.

```
class Class(object):

    @my_function_wrapper
    @classmethod
    def function_cm(self, a, b):
        pass 

    @my_function_wrapper
    @staticmethod
    def function_sm(a, b):
        pass

>>> Class.function_cm(1, 2)
INSTANCE 1
ARGS (2,) 

>>> Class.function_sm(1, 2)
INSTANCE 1
ARGS (2,) 
```

Class methods and static methods
--------------------------------

The point we are at therefore, is that in the case where the instance is
passed as ``None``, we need to be able to distinguish between the three
cases of:

* an instance method being called via the class
* a class method being called
* a static method being called

One way this can be done is by looking at the ``__self__`` attribute of the
bound function. This attribute will provide information about the type of
object which the function was bound to at that specific point in time. Lets
first check this out for where a method is called via the class.

```
>>> print(Class.function_im.__self__)
None 

>>> print(Class.function_cm.__self__)
<class '__main__.Class'> 

>>> print(Class.function_sm.__self__)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "test.py", line 19, in __getattr__
    return getattr(self.wrapped, name)
AttributeError: 'function' object has no attribute '__self__'
```

So for the case of calling an instance method via the class, ``__self__``
will be ``None``, for a class method it will be the class type and in the
case of a static method, there will not even be a ``__self__`` attribute.
This would therefore appear to give us a way of detecting the different
cases.

Before we code up a solution based on this though, lets check with Python 3
just to be sure we are okay there and that nothing has changed.

```
>>> print(Class.function_im.__self__)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "dectest.py", line 19, in __getattr__
    return getattr(self.wrapped, name)
AttributeError: 'function' object has no attribute '__self__' 

>>> print(Class.function_cm.__self__)
<class '__main__.Class'> 

>>> print(Class.function_sm.__self__)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "test.py", line 19, in __getattr__
    return getattr(self.wrapped, name)
AttributeError: 'function' object has no attribute '__self__'
```

That isn't good, Python 3 behaves differently to Python 2, meaning we
aren't going to be able to use this approach. Why is this case?

The reason for this is that in Python 3 they decided to eliminate the idea
of an unbound method and this check was relying on the fact that when
accessing an instance method via the class, it would actually return an
instance of an unbound method for which the ``__self__`` attribute was
``None``. So although we can distinguish the case for a class method still,
we can now no longer distinguish the case of calling an instance method via
the class, from the case of calling a static method.

The lack of this ability therefore leaves us with a bit of a problem for
Python 3 and the one alternative isn't necessarily a completely fool proof
way of doing it.

This alternative is in the constructor of the function wrapper, to look at
the type of the wrapped object and determine if it is an instance of a
class method or static method. This information can then be passed through
to the bound function wrapper and checked.

```
class bound_function_wrapper(object_proxy): 

    def __init__(self, wrapped, instance, wrapper, binding):
        super(bound_function_wrapper, self).__init__(wrapped)
        self.instance = instance
        self.wrapper = wrapper
        self.binding = binding 

    def __call__(self, *args, **kwargs):
        if self.binding == 'function' and self.instance is None:
            instance, args = args[0], args[1:]
            wrapped = functools.partial(self.wrapped, instance)
            return self.wrapper(wrapped, instance, args, kwargs) 
        return self.wrapper(self.wrapped, self.instance, args, kwargs) 

class function_wrapper(object_proxy): 

    def __init__(self, wrapped, wrapper):
        super(function_wrapper, self).__init__(wrapped)
        self.wrapper = wrapper 
        if isinstance(wrapped, classmethod):
            self.binding = 'classmethod'
        elif isinstance(wrapped, staticmethod):
            self.binding = 'staticmethod'
        else:
            self.binding = 'function' 

    def __get__(self, instance, owner):
        wrapped = self.wrapped.__get__(instance, owner)
        return bound_function_wrapper(wrapped, instance, self.wrapper,
                self.binding) 

    def __call__(self, *args, **kwargs):
        return self.wrapper(self.wrapped, None, args, kwargs)
```

Now this test is a bit fragile, but as I showed before though, the
traditional way that a decorator is written will fail if wrapped around a
class method or static method as it doesn't honour the descriptor protocol.
As such it is a pretty safe bet right now that I will only ever find an
actual class method or static method object because no one would be using
decorators around them.

If someone is actually implementing the descriptor protocol in their
decorator, hopefully they would also be using an object proxy as is done
here. Because the object proxy implements ``__class__`` as a property, it
would return the class of the wrapped object, this should mean that an
``isinstance()`` check will still be successful as ``isinstance()`` gives
priority to what ``__class__`` yields rather than the actual type of the
object.

Anyway, trying out our tests again with this change we get:

```
>>> c.function_im(1,2)
INSTANCE <__main__.Class object at 0x101f973d0>
ARGS (1, 2) 

>>> Class.function_im(c, 1, 2)
INSTANCE <__main__.Class object at 0x101f973d0>
ARGS (1, 2)

>>> c.function_cm(1,2)
INSTANCE <__main__.Class object at 0x101f973d0>
ARGS (1, 2)

>>> Class.function_cm(1, 2)
INSTANCE None
ARGS (1, 2) 

>>> c.function_sm(1,2)
INSTANCE <__main__.Class object at 0x101f973d0>
ARGS (1, 2) 

>>> Class.function_sm(1, 2)
INSTANCE None
ARGS (1, 2)
```

Success, we have fixed the issue with the argument list when both a class
method and a static method are called.

The problem now is that although the instance argument is fine for the case
of an instance method call, whether that be via the instance or the class,
the instance as passed for a class method and static method aren't
particularly useful as we can't use it to distinguish them from other
cases.

Ideally what we want in this circumstance is that for a class method call
we want the instance argument to always be the class type, and for the case
of a static method call, for it to always be ``None``.

For the case of a static method, we could just check for 'staticmethod'
from when we checked the type of object which was wrapped.

For the case of a class method, if we look back at our test to see if we
could use the ``__self__`` attribute, what we found was that for the class
method, ``__self__`` was the class instance and for a static method the
attribute didn't exist.

What we can therefore do, is if the type of the wrapped object wasn't a
function, then we can lookup up the value of ``__self__``, defaulting to
``None`` if it doesn't exist. This one check will cater for both cases.

What we now therefore have is:

```
class bound_function_wrapper(object_proxy):

    def __init__(self, wrapped, instance, wrapper, binding):
        super(bound_function_wrapper, self).__init__(wrapped)
        self.instance = instance
        self.wrapper = wrapper
        self.binding = binding 

    def __call__(self, *args, **kwargs):
        if self.binding == 'function':
            if self.instance is None:
                instance, args = args[0], args[1:]
                wrapped = functools.partial(self.wrapped, instance)
                return self.wrapper(wrapped, instance, args, kwargs)
            else:
                return self.wrapper(self.wrapped, self.instance, args, kwargs)
        else:
            instance = getattr(self.wrapped, '__self__', None)
            return self.wrapper(self.wrapped, instance, args, kwargs)
```

and if we run our tests one more time, we finally get the result we have
been looking for:

```
>>> c.function_im(1,2)
INSTANCE <__main__.Class object at 0x10c2c43d0>
ARGS (1, 2) 

>>> Class.function_im(c, 1, 2)
INSTANCE <__main__.Class object at 0x10c2c43d0>
ARGS (1, 2) 

>>> c.function_cm(1,2)
INSTANCE <class '__main__.Class'>
ARGS (1, 2) 

>>> Class.function_cm(1, 2)
INSTANCE <class '__main__.Class'>
ARGS (1, 2) 

>>> c.function_sm(1,2)
INSTANCE None
ARGS (1, 2) 

>>> Class.function_sm(1, 2)
INSTANCE None
ARGS (1, 2)
```

Are we able to celebrate yet? Unfortunately not.

Multiple levels of binding
--------------------------

There is yet another obscure case we have yet to consider, one that I
didn't even think of initially and only understood the problem when I
started to see code breaking in crazy ways.

This is when we take a reference to a method and reassign it back again as
an attribute of a class, or even an instance of a class, and then call it
via the alias so created. I only encountered this one due to some bizarre
stuff a meta class was doing.

```
>>> Class.function_rm = Class.function_im

>>> c.function_rm(1, 2)
INSTANCE 1
ARGS (2,)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "test.py", line 132, in __call__
    return self.wrapper(wrapped, instance, args, kwargs)
  File "test.py", line 58, in my_function_wrapper
    return wrapped(*args, **kwargs)
TypeError: unbound method function_im() must be called with Class instance as first argument (got int instance instead) 

>>> Class.function_rm = Class.function_cm

>>> c.function_rm(1, 2)
INSTANCE <class '__main__.Class'>
ARGS (1, 2) 

>>> Class.function_rm = Class.function_sm
>>> c.function_rm(1, 2)
INSTANCE None
ARGS (1, 2)
```

Things work fine for a class method or static method, but fails badly for
an instance method.

The problem here comes about because in accessing the instance method the
first time, it will return a bound function wrapper. That then gets
assigned back as an attribute of the class.

When a subsequent lookup is made via the new name, under normal
circumstances binding would occur once more to bind it to the actual
instance. In our implementation of the bound function wrapper, we do not
however provide a ``__get__()`` method and thus this rebinding does not
occur. The result is that on the subsequent call, it all falls apart.

The solution therefore is that we need to add a ``__get__()`` method to the
bound function wrapper which provides the ability to perform further
binding. We only want to do this where the instance was ``None``,
indicating that the initial binding wasn't actually against an instance,
and where we are dealing with an instance method and not a class method or
static method.

A further wrinkle is that we need to bind what was the original wrapped
function and not the bound one. The simplest way of handling that is to
pass a reference to the original function wrapper to the bound function
wrapper and reach back into that to get the original wrapped function.

```
class bound_function_wrapper(object_proxy): 

    def __init__(self, wrapped, instance, wrapper, binding, parent):
        super(bound_function_wrapper, self).__init__(wrapped)
        self.instance = instance
        self.wrapper = wrapper
        self.binding = binding
        self.parent = parent 

    def __call__(self, *args, **kwargs):
        if self.binding == 'function':
            if self.instance is None:
                instance, args = args[0], args[1:]
                wrapped = functools.partial(self.wrapped, instance)
                return self.wrapper(wrapped, instance, args, kwargs)
            else:
                return self.wrapper(self.wrapped, self.instance, args, kwargs)
        else:
            instance = getattr(self.wrapped, '__self__', None)
            return self.wrapper(self.wrapped, instance, args, kwargs) 

    def __get__(self, instance, owner):
        if self.instance is None and self.binding == 'function':
            descriptor = self.parent.wrapped.__get__(instance, owner)
            return bound_function_wrapper(descriptor, instance, self.wrapper,
                    self.binding, self.parent)
        return self 

class function_wrapper(object_proxy): 

    def __init__(self, wrapped, wrapper):
        super(function_wrapper, self).__init__(wrapped)
        self.wrapper = wrapper
        if isinstance(wrapped, classmethod):
            self.binding = 'classmethod'
        elif isinstance(wrapped, staticmethod):
            self.binding = 'staticmethod'
        else:
            self.binding = 'function' 

    def __get__(self, instance, owner):
        wrapped = self.wrapped.__get__(instance, owner)
        return bound_function_wrapper(wrapped, instance, self.wrapper,
                self.binding, self) 

    def __call__(self, *args, **kwargs):
        return self.wrapper(self.wrapped, None, args, kwargs)
```

Rerunning our most recent test once again we now get:

```
>>> Class.function_rm = Class.function_im

>>> c.function_rm(1, 2)
INSTANCE <__main__.Class object at 0x105609790>
ARGS (1, 2) 

>>> Class.function_rm = Class.function_cm
>>> c.function_rm(1, 2)
INSTANCE <class '__main__.Class'>
ARGS (1, 2) 

>>> Class.function_rm = Class.function_sm
>>> c.function_rm(1, 2)
INSTANCE None
ARGS (1, 2)
```

Order that decorators are applied
---------------------------------

We must be getting close now. Everything appears to be working.

If you had been paying close attention you would have noticed though that
in all cases so far our decorator has always been placed outside of the
existing decorators marking a method as either a class method or a static
method. What happens if we reverse the order?

```
class Class(object):

    @classmethod
    @my_function_wrapper
    def function_cm(self, a, b):
        pass 

    @staticmethod
    @my_function_wrapper
    def function_sm(a, b):
        pass 

c = Class() 

>>> c.function_cm(1,2)
INSTANCE None
ARGS (<class '__main__.Class'>, 1, 2) 

>>> Class.function_cm(1, 2)
INSTANCE None
ARGS (<class '__main__.Class'>, 1, 2) 

>>> c.function_sm(1,2)
INSTANCE None
ARGS (1, 2) 

>>> Class.function_sm(1, 2)
INSTANCE None
ARGS (1, 2)
```

So it works as we would expect for a static method but not for a class
method.

At this point you gotta be thinking why I am bothering.

As it turns out there is indeed absolutely nothing I can do about this one.
But that isn't actually my fault.

In this particular case, it actually can be seen as being a bug in Python
itself. Specifically, the classmethod decorator doesn't itself honour the
descriptor protocol when it calls whatever it is wrapping. This is the
exact same problem I faulted decorators implemented using a closure for
originally. If it wasn't for the classmethod decorator doing the wrong
thing, everything would be perfect.

For those who are interested in the details, you can check out [issue
19072](http://bugs.python.org/issue19072) in the Python bug tracker. If I
had tried hard I could well have got it fixed by the time Python 3.4 came
out, but I simply didn't have the time nor the real motivation to satisfy
all the requirements to get the fix accepted.

Decorating a class
------------------

Excluding that one case related to ordering of decorators for class
methods, our pattern for implementing a universal decorator is looking
good.

I did mention though in the last post that the goal was that we could also
distinguish when a decorator was applied to a class. So lets check that.

```
@my_function_wrapper
class Class(object):
    pass 

>>> c = Class()
INSTANCE None
ARGS ()
```

Based on that we aren't able to distinguish it from a normal function or a
class method.

If we think about it though, we are in this case wrapping an actual class,
so the wrapped object which is passed to the decorator wrapper function
will be the class itself. Lets print out the value of the wrapped argument
passed to the decorator wrapper function as well and see whether that can
be used to distinguish this case from others.

```
@decorator
def my_function_wrapper(wrapped, instance, args, kwargs):
    print('WRAPPED', wrapped)
    print('INSTANCE', instance)
    print('ARGS', args)
    return wrapped(*args, **kwargs) 

@my_function_wrapper
def function(a, b):
    pass 

>>> function(1, 2)
WRAPPED <function function at 0x10e13bb18>
INSTANCE None
ARGS (1, 2) 

class Class(object):

    @my_function_wrapper
    def function_im(self, a, b):
        pass

    @my_function_wrapper
    @classmethod
    def function_cm(self, a, b):
        pass

    @my_function_wrapper
    @staticmethod
    def function_sm(a, b):
        pass 

c = Class() 

>>> c.function_im(1,2)
WRAPPED <bound method Class.function_im of <__main__.Class object at 0x107e90950>>
INSTANCE <__main__.Class object at 0x107e90950>
ARGS (1, 2) 

>>> Class.function_im(c, 1, 2)
WRAPPED <functools.partial object at 0x107df3208>
INSTANCE <__main__.Class object at 0x107e90950>
ARGS (1, 2) 

>>> c.function_cm(1,2)
WRAPPED <bound method type.function_cm of <class '__main__.Class'>>
INSTANCE <class '__main__.Class'>
ARGS (1, 2) 

>>> Class.function_cm(1, 2)
WRAPPED <bound method type.function_cm of <class '__main__.Class'>>
INSTANCE <class '__main__.Class'>
ARGS (1, 2) 

>>> c.function_sm(1,2)
WRAPPED <function function_sm at 0x107e918c0>
INSTANCE None
ARGS (1, 2) 

>>> Class.function_sm(1, 2)
WRAPPED <function function_sm at 0x107e918c0>
INSTANCE None
ARGS (1, 2) 

@my_function_wrapper
class Class(object):
    pass 

c = Class() 

>>> c = Class()
WRAPPED <class '__main__.Class'>
INSTANCE None
ARGS ()
```

And the answer is yes, as it is the only case where wrapped will be a type
object.

The structure of a universal decorator
--------------------------------------

The goal of a decorator, one decorator, that can be implemented and applied
to normal functions, instance methods, class methods and classes is
therefore achievable. The odd one out is static methods, but in practice
these aren't really different to normal functions, just being contained in
a different scope, so I think I will let that one slide.

The information to identify the static method is actually available in the
way the decorator works, but since there is nothing in the arguments passed
to a static method that link it to the class it is contained in, there
doesn't seem a point. If that information was required, it probably should
have been a class method to begin with.

Anyway, after all this work, our universal decorator then would be written
as:

```
@decorator
def universal(wrapped, instance, args, kwargs):
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
```

Are there actual uses for such a universal decorator? I believe there are
some quite good examples and I will cover one in particular in a subsequent
blog post.

You also have frameworks such as Django which already use hacks to allow a
decorator designed for use with a function, to be applied to an instance
method. Turns out that the method they use is broken because it doesn't
honour the descriptor protocol though. If you are interested in that one,
see [issue 21247](https://code.djangoproject.com/ticket/21247) in the
Django bug tracker.

I will not cover this example of a use case for a universal decorator just
yet. Instead in my next blog post in this series I will look at issues
around having decorators that have optional arguments and how to capture
any such arguments so the decorator can make use of them.

