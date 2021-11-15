Performance overhead of using decorators
========================================

This is the ninth post in my series of blog posts about Python decorators
and how I believe they are generally poorly implemented. It follows on from
the previous post titled [The @synchronized decorator as context
manager](08-the-synchronized-decorator-as-context-manager.md), with the
very first post in the series being [How you implemented your Python
decorator is
wrong](01-how-you-implemented-your-python-decorator-is-wrong.md).

The posts so far in this series were bashed out in quick succession in a
bit over a week. Because that was quite draining on the brain and due to
other commitments I took a bit of a break. Hopefully I can get through
another burst of posts, initially about performance considerations when
implementing decorators and then start a dive into how to implement the
object proxy which underlies the function wrapper the decorator mechanism
described relies on.

Overhead in decorating a normal function
----------------------------------------

In this post I am only going to look at the overhead of decorating a normal
function with the decorator mechanism which has been described. The
relevant part of the decorator mechanism which comes into play in this case
is:

```python
class function_wrapper(object_proxy):

    def __init__(self, wrapped, wrapper):
        super(function_wrapper, self).__init__(wrapped)
        self.wrapper = wrapper
        ...

    def __get__(self, instance, owner):
        ...

    def __call__(self, *args, **kwargs):
        return self.wrapper(self.wrapped, None, args, kwargs)

def decorator(wrapper):
    def _wrapper(wrapped, instance, args, kwargs):
        def _execute(wrapped):
            if instance is None:
                return function_wrapper(wrapped, wrapper)
            elif inspect.isclass(instance):
                return function_wrapper(wrapped, wrapper.__get__(None, instance))
            else:
                return function_wrapper(wrapped, wrapper.__get__(instance, type(instance)))
        return _execute(*args, **kwargs)
    return function_wrapper(wrapper, _wrapper)
```

If you want to refresh your memory of the complete code that was previously
presented you can check back to the last post where it was described in
full.

With our decorator factory, when creating a decorator and then decorating a
normal function with it we would use:

```python
@decorator
def my_function_wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@my_function_wrapper
def function():
    pass
```

This is in contrast to the same decorator created in the more traditional
way using a function closure.

```python
def my_function_wrapper(wrapped):
    def _my_function_wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)
    return _my_function_wrapper

@my_function_wrapper
def function():
    pass
```

Now what actually occurs in these two different cases when we make the call:

```python
function()
```

Tracing the execution of the function
-------------------------------------

In order to trace the execution of our code we can use Python's profile
hooks mechanism.

```python
import sys
def tracer(frame, event, arg):
    print(frame.f_code.co_name, event)

sys.setprofile(tracer)

function()
```

The purpose of the profile hook is to allow you to register a callback
function which is called on the entry and exit of all functions. Using this
was can trace the sequence of function calls that are being made.

For the case of a decorator implemented as a function closure this yields:

```
_my_function_wrapper call
    function call
    function return
_my_function_wrapper return
```

So what we see here is that the nested function of our function closure is
called. This is because the decorator in the case of a using a function
closure is replacing `function` with a reference to that nested function.
When that nested function is called, it then in turn calls the original
wrapped function.

For our implementation using our decorator factory, when we do the same
thing we instead get:

```
__call__ call
    my_function_wrapper call
        function call
        function return
    my_function_wrapper return
__call__ return
```

The difference here is that our decorator replaces `function` with an
instance of our function wrapper class. Being a class, when it is called as
if it was a function, the `__call__()` method is invoked on the instance
of the class. The `__call__()` method is then invoking the user supplied
wrapper function, which in turn calls the original wrapped function.

The result therefore is that we have introduced an extra level of
indirection, or in other words an extra function call into the execution
path.

Keep in mind though that `__call__()` is actually a method though and not
just a normal function. Being a method that means there is actually a lot
more work going on behind the scenes than a normal function call. In
particular, the unbound method needs to be bound to the instance of our
function wrapper class before it can be called. This doesn't appear in the
trace of the calls, but it is occurring and that will incur additional
overhead.

Timing the execution of the function
------------------------------------

By performing the trace above we know that our solution incurs an
additional method call overhead. How much actual extra overhead is this
resulting in though?

To try and measure the increase in overhead in each solution we can use the
`timeit` module to time the execution of our function call. As a baseline,
we first want to time the call of a function without any decorator applied.

```python
# benchmarks.py
def function():
    pass
```

To time this we use the command:

```sh
$ python -m timeit -s 'import benchmarks' 'benchmarks.function()'
```

The `timeit` module when used in this way will perform a suitable large
number of iterations of calling the function, divide the resulting total
time for all calls with the count of the number and end up with a time
value for a single call.

For a 2012 model MacBook Pro this yields:

```
10000000 loops, best of 3: 0.132 usec per loop
```

Next up is to try with a decorator implemented as a function closure. For
this we get:

```
1000000 loops, best of 3: 0.326 usec per loop
```

And finally with our decorator factory:

```
1000000 loops, best of 3: 0.771 usec per loop
```

In this final case, rather than use the exact code as has been presented so
far in this series of blog posts, I have used the `wrapt` module
implementation of what has been described. This implementation works
slightly differently as it has a few extra capabilities over what has been
described and the design is also a little bit different. The overhead will
still be roughly equivalent and if anything will cast things as being
slightly worse than the more minimal implementation.

Speeding up execution of the wrapper
------------------------------------

At this point no doubt there will be people wanting to point out that this
so called better way of implementing a decorator is too slow to be
practical to use, even if it is more correct as far as properly honouring
things such as the descriptor protocol for method invocation.

Is there therefore anything that can be done to speed up the implementation?

That is of course a stupid question for me to be asking because you should
realise by now that I would find a way. :-)

The path that can be taken at this point is to implement everything that
has been described for the function wrapper and object proxy as a Python C
extension module. For simplicity we can keep the decorator factory itself
implemented as pure Python code as execution of that is not time critical
as it would only be invoked once when the decorator is applied to the
function and not on every call of the decorated function.

One thing I am definitely not going to do is blog about how to go about
implementing the function wrapper and object proxy as a Python C extension
module. Rest assured though that it works in the same way as the parallel
pure Python implementation. It does obviously though run a lot quicker due
to being implemented as C code using the Python C APIs rather than as pure
Python code.

What is the result then by implementing the function wrapper and object
proxy as a Python C extension module? It is:

```
1000000 loops, best of 3: 0.382 usec per loop
```

So although a lot more effort was required in actually implementing the
function wrapper and object proxy as a Python C extension module, the
effort was well worth it, with the results now being very close to the
implementation of the decorator that used a function closure.

Normal functions vs methods of classes
--------------------------------------

So far we have only considered the case of decorating a normal function. As
expected, due to the introduction of an extra level of indirection as well
as the function wrapper being implemented as a class, overhead was notably
more. Albeit, that it was still in the order of only half a microsecond.

All the same, we were able to speed things up to a point, by implementing
our function wrapper and object proxy as C code, where the overhead above
that of a decorator implemented as a function closure was negligible.

What now about where we decorate methods of a class. That is, instance
methods, class methods and static methods. For that you will need to wait
until the next blog post in this series on decorators.
