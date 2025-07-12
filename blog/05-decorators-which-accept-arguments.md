Decorators which accept arguments
=================================

This is the fifth post in my series of blog posts about Python decorators
and how I believe they are generally poorly implemented. It follows on from
the previous post titled [Implementing a universal
decorator](04-implementing-a-universal-decorator.md), with the very first
post in the series being [How you implemented your Python decorator is
wrong](01-how-you-implemented-your-python-decorator-is-wrong.md).

So far in this series of posts I have explained the short comings of
implementing a decorator in the traditional way they are done in Python. I
have shown an alternative implementation based on an object proxy and a
descriptor which solves these issues, as well as provides the ability to
implement what I call a universal decorator. That is, a decorator which
understands the context it was used in and can determine whether it was
applied to a normal function, an instance method, a class method or a class
type.

In this post, I am going to take the decorator factory which was described
in the previous posts and describe how one can use that to implement
decorators which accept arguments. This will cover mandatory arguments, but
also how to have the one decorator optionally except arguments.

Pattern for creating decorators
-------------------------------

The key component of what was described in the prior posts was a function
wrapper object. I am not going to replicate the code for that here so see
the prior posts. In short though, it was a class type which accepted the
function to be wrapped and a user supplied wrapper function. The instance
of the resulting function wrapper object was used in place of the wrapped
function and when called, would delegate the calling of the wrapped
function to the user supplied wrapper function. This allows a user to
modify how the call was made, performing actions before or after the
wrapped function was called, or modify input arguments or the result.

This function wrapper was used in conjunction with the decorator factory
which was also described:

```python
def decorator(wrapper):
    @functools.wraps(wrapper)
    def _decorator(wrapped):
        return function_wrapper(wrapped, wrapper)
    return _decorator
```

allowing a user to define their own decorator as:

```python
@decorator
def my_function_wrapper(wrapped, instance, args, kwargs):
    print('INSTANCE', instance)
    print('ARGS', args)
    print('KWARGS', kwargs)
    return wrapped(*args, **kwargs)

@my_function_wrapper
def function(a, b):
    pass
```

In this example, the final decorator which is created does not accept any
arguments, but if we did want the decorator to be able to accept arguments,
with the arguments accessible at the time the user supplied wrapper
function was called, how would we do that?

Using a function closure to collect arguments
---------------------------------------------

The easiest way to implement a decorator which accepts arguments is using a
function closure.

```python
def with_arguments(arg):
    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper

@with_arguments(arg=1)
def function():
    pass
```

In effect the outer function is a decorator factory in its own right, where
a distinct decorator instance will be returned which is customised
according to what arguments were supplied to the outer decorator factory
function.

So, when this outer decorator factory function is applied to a function
with the specific arguments supplied, it returns the inner decorator
function and it is actually that which is applied to the function to be
wrapped. When the wrapper function is eventually called and it in turn
calls the wrapped function, it will have access to the original arguments
to the outer decorator factory function by virtue of being part of the
function closure.

Positional or keyword arguments can be used with the outer decorator
factory function, but I would suggest that keyword arguments are perhaps a
better convention to adopt as I will show later.

What now if a decorator with arguments had default values and as such they
could be left out from the call. With this way of implementing the
decorator, even though one would not need to pass the argument, one cannot
avoid needing to still write it out as a distinct call. That is, you still
need to supply empty parentheses.

```python
def with_arguments(arg='default'):
    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper

@with_arguments()
def function():
    pass
```

Although this is being specific and would dictate there be only one way to
do it, it can be felt that this looks ugly. As such some people like to
have a way that the parentheses are optional if the decorator arguments all
have default values and none are being supplied explicitly. In other words,
the desire is that when there are no arguments to be passed, that one can
write:

```python
@with_arguments
def function():
    pass
```

There is actually some merit in this idea when looked at the other way
around. That is, if a decorator originally accepted no arguments, but it
was determined later that it needed to be changed to optionally accept
arguments, then if the parentheses could be optional, it would allow
arguments to now be accepted, without needing to go back and change all
prior uses of the original decorator where no arguments were supplied.

Optionally allowing decorator arguments
---------------------------------------

To allow the decorator arguments to be optionally supplied, we can change
the above recipe to:

```python
def optional_arguments(wrapped=None, arg=1):
    if wrapped is None:
        return functools.partial(optional_arguments, arg=arg)

    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    return _wrapper(wrapped)

@optional_arguments(arg=2)
def function1():
    pass

@optional_arguments
def function2():
    pass
```

With the arguments having default values, the outer decorator factory would
take the wrapped function as first argument with None as a default. The
decorator arguments follow. Decorator arguments would need to be passed as
keyword arguments. On the first call, wrapped will be None, and a partial
is used to return the decorator factory again. On the second call, wrapped
is passed and this time it is wrapped with the decorator.

Because we have default arguments though, we don't actually need to pass
the arguments, in which case the decorator factory is applied direct to the
function being decorated. Because wrapped is not None when passed in, the
decorator is wrapped around the function immediately, skipping the return
of the factory a second time.

Now why I said a convention of having keyword arguments may perhaps be
preferable, is that Python 3 allows you to enforce it using the new keyword
only argument syntax.

```python
def optional_arguments(wrapped=None, *, arg=1):
    if wrapped is None:
        return functools.partial(optional_arguments, arg=arg)

    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    return _wrapper(wrapped)
```

This way you avoid the problem of someone accidentally passing in a
decorator argument as the positional argument for wrapped. For consistency,
keyword only arguments can also be enforced for required arguments even
though it isn't strictly necessary.

```python
def required_arguments(*, arg):
    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper
```

Maintaining state between wrapper calls
---------------------------------------

Quite often a decorator doesn't perform an isolated task for each
invocation of a function it may be applied to. Instead it may need to
maintain state between calls. A classic example of this is a cache
decorator.

In this scenario, because no state information can be maintained within the
wrapper function itself, any state object needs to be maintained in an
outer scope which the wrapper has access to.

There are a few ways in which this can be done.

The first is to require that the object which maintains the state, be
passed in as an explicit argument to the decorator.

```python
def cache(d):
    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        try:
            key = (args, frozenset(kwargs.items()))
            return d[key]
        except KeyError:
            result = d[key] = wrapped(*args, **kwargs)
            return result
    return _wrapper

_d = {}

@cache(_d)
def function():
    return time.time()
```

Unless there is a specific need to be able to pass in the state object, a
second better way is to create the state object on the stack within the
call of the outer function.

```python
def cache(wrapped):
    d = {}

    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        try:
            key = (args, frozenset(kwargs.items()))
            return d[key]
        except KeyError:
            result = d[key] = wrapped(*args, **kwargs)
            return result

    return _wrapper(wrapped)

@cache
def function():
    return time.time()
```

In this case the outer function rather than taking a decorator argument, is
taking the function to be wrapped. This is then being explicitly wrapped by
the decorator defined within the function and returned.

If this was a reasonable default, but you did in some cases still need to
optionally pass the state object in as an argument, then optional decorator
arguments could instead be used.

```python
def cache(wrapped=None, d=None):
    if wrapped is None:
        return functools.partial(cache, d=d)

    if d is None:
        d = {}

    @decorator
    def _wrapper(wrapped, instance, args, kwargs):
        try:
            key = (args, frozenset(kwargs.items()))
            return d[key]
        except KeyError:
            result = d[key] = wrapped(*args, **kwargs)
            return result

    return _wrapper(wrapped)

@cache
def function1():
    return time.time()

_d = {}

@cache(d=_d)
def function2():
    return time.time()

@cache(d=_d)
def function3():
    return time.time()
```

Decorators as a class
---------------------

Now way back in the very first post in this series of blog posts, a way in
which a decorator could be implemented as a class was described.

```python
class function_wrapper:

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)
```

Although this had short comings which were explained and which resulted in
the alternate decorator pattern being presented, this original approach is
also able to maintain state. Specifically, the constructor of the class can
save away the state object as an attribute of the instance of the class,
along with the reference to the wrapped function.

```python
class cache:

    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.d = {}

    def __call__(self, *args, **kwargs):
        try:
            key = (args, frozenset(kwargs.items()))
            return self.d[key]
        except KeyError:
            result = self.d[key] = self.wrapped(*args, **kwargs)
            return result

@cache
def function():
    return time.time()
```

Use of a class in this way had some benefits in that where the work of the
decorator was quite complex, it could all be encapsulated in the class
implementing the decorator itself.

With our new function wrapper and decorator factory, the user can only
supply the wrapper as a function, which would appear to limit being able to
implement a direct equivalent.

One could still use a class to encapsulate the required behaviour, with an
instance of the class created within the scope of a function closure for
use by the wrapper function, and the wrapper function then delegating to
that, but it isn't self contained as it was before.

The question is, is there any way that one could still achieve the same
thing with our new decorator pattern. Turns out there possibly is.

What one should be able to do, at least for where there are required
arguments, is do:

```python
class with_arguments:

    def __init__(self, arg):
        self.arg = arg

    @decorator
    def __call__(self, wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

@with_arguments(arg=1)
def function():
    pass
```

What will happen here is that application of the decorator with arguments
being supplied, will result in an instance of the class being created. In
the next phase where that is called with the wrapped function, the
`__call__()` method with `@decorator` applied will be used as a
decorator on the wrapped function. The end result should be that the
`__call__()` method of the class instance created ends up being our
wrapper function.

When the decorated function is now called, the `__call__()` method of the
class would be called to then in turn call the wrapped function. As the
`__call__()` method at that point is bound to an instance of the class,
it would have access to the state that it contained.

What actually happens when we do this though?

```pycon
Traceback (most recent call last):
  File "test.py", line 483, in <module>
    @with_arguments(1)
TypeError: _decorator() takes exactly 1 argument (2 given)
```

So nice idea, but it fails.

Is it game over? The answer is of course not, because if it isn't obvious
by now, I don't give up that easily.

Now the reason this failed is actually because of how our decorator factory
is implemented.

```python
def decorator(wrapper):
    @functools.wraps(wrapper)
    def _decorator(wrapped):
        return function_wrapper(wrapped, wrapper)
    return _decorator
```

I will not describe in this post what the problem is though and will leave
the solving of this particular problem to a short followup post as the next
in this blog post series on decorators.
