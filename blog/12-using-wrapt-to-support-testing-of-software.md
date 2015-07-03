Using wrapt to support testing of software
==========================================

When talking about unit testing in Python, one of the more popular packages
used to assist in that task is the Mock package. I will no doubt be
labelled as a heretic but when I have tried to use it for things it just
doesn't seem to sit right with my way of thinking.

It may also just be that what I am trying to apply it to isn't a good fit.
In what I want to test it usually isn't so much that I want to mock out
lower layers, but more that I simply want to validate data being passed
through to the next layer or otherwise modify results. In other words I
usually still need the system as a whole to function end to end and
possibly over an extended time.

So for the more complex testing I need to do I actually keep falling back
on the monkey patching capabilities of wrapt. It may well just be that
since I wrote wrapt that I am more familiar with its paradigm, or that I
prefer the more explicit way that wrapt requires you to do things. Either
way, for me at least wrapt helps me to get the job done quicker.

To explain a bit more about the monkey patching capabilities of wrapt, I am
in this blog post going to show how some of the things you can do in Mock
you can do with wrapt. Just keep in mind that I am an absolute novice when
it comes to Mock and so I could also just be too dumb to understand how to
use it properly for what I want to do easily.

Return values and side effects
------------------------------

If one is using Mock and you want to temporarily override the value
returned by a method of a class when called, one way is to use:

```
from mock import Mock, patch

class ProductionClass(object):
    def method(self, a, b, c, key):
        print a, b, c, key

@patch(__name__+'.ProductionClass.method', return_value=3)
def test_method(mock_method):
    real = ProductionClass()
    result = real.method(3, 4, 5, key='value')
    mock_method.assert_called_with(3, 4, 5, key='value')
    assert result == 3
```

With what I have presented so far of the wrapt package, an equivalent way
of doing this would be:

```
from wrapt import patch_function_wrapper

class ProductionClass(object):
    def method(self, a, b, c, key):
        print a, b, c, key

@patch_function_wrapper(__name__, 'ProductionClass.method')
def wrapper(wrapped, instance, args, kwargs):
    assert args == (3, 4, 5) and kwargs.get('key') == 'value'
    return 3

def test_method():
    real = ProductionClass()
    result = real.method(3, 4, 5, key='value')
    assert result == 3
```

An issue with this though is that the 'wrapt.patch_function_wrapper()'
function I previously described applies a permanent patch. This is okay
where it does need to survive for the life of the process, but in the
case of testing we usually want to only have a patch apply to the single
unit test function being run at that time. So the patch should be
removed at the end of that test and before the next function is called.

For that scenario, the wrapt package provides an alternate decorator
'@wrapt.transient_function_wrapper'. This can be used to create a wrapper
function that will only be applied for the scope of a specific call that
the decorated function is applied to. We can therefore write the above as:

```
from wrapt import transient_function_wrapper

class ProductionClass(object):
    def method(self, a, b, c, key):
        print a, b, c, key

@transient_function_wrapper(__name__, 'ProductionClass.method')
def apply_ProductionClass_method_wrapper(wrapped, instance, args, kwargs):
    assert args == (3, 4, 5) and kwargs.get('key') == 'value'
    return 3

@apply_ProductionClass_method_wrapper
def test_method():
    real = ProductionClass()
    result = real.method(3, 4, 5, key='value')
    assert result == 3
```

Although this example shows how to return a substitute for the method being
called, the more typical case is that I still want to call the original
wrapped function. Thus, perhaps validating the arguments being passed in or
the return value being passed back from the lower layers.

For this blog post when I tried to work out how to do that with Mock the
general approach I came up with was the following.

```
from mock import Mock, patch

class ProductionClass(object):
    def method(self, a, b, c, key):
        print a, b, c, key

def wrapper(wrapped):
    def _wrapper(self, *args, **kwargs):
        assert args == (3, 4, 5) and kwargs.get('key') == 'value'
        return wrapped(self, *args, **kwargs)
    return _wrapper

@patch(__name__+'.ProductionClass.method', autospec=True,
        side_effect=wrapper(ProductionClass.method))

def test_method(mock_method):
    real = ProductionClass()
    result = real.method(3, 4, 5, key='value')
```

There were two tricks here. The first is the 'autospec=True' argument to
'@Mock.patch' to have it perform method binding, and the second being the
need to capture the original method from the 'ProductionClass' before any
mock had been applied to it, so I could then in turn call it when the side
effect function for the mock was called.

No doubt someone will tell me that I am doing this all wrong and there is a
simpler way, but that is the best I could come up with after 10 minutes of
reading the Mock documentation.

When using wrapt to do the same thing, what is used is little different to
what was used when mocking the return value. This is because the wrapt
function wrappers will work with both normal functions or methods and so
nothing special has to be done when wrapping methods. Further, when the
wrapt wrapper function is called, it is always passed the original function
which was wrapped, so no magic is needed to stash that away.

```
from wrapt import transient_function_wrapper

class ProductionClass(object):
    def method(self, a, b, c, key):
        print a, b, c, key

@transient_function_wrapper(__name__, 'ProductionClass.method')
def apply_ProductionClass_method_wrapper(wrapped, instance, args, kwargs):
    assert args == (3, 4, 5) and kwargs.get('key') == 'value'
    return wrapped(*args, **kwargs)

@apply_ProductionClass_method_wrapper
def test_method():
    real = ProductionClass()
    result = real.method(3, 4, 5, key='value')
```

Using this ability to easily intercept a call to perform validation of data
being passed, but still call the original, I can relatively easily create a
whole bunch of decorators for performing validation on data as is it is
passed through different parts of the system. I can then stack up these
decorators on any test function that I need to add them to.

Wrapping of return values
-------------------------

The above recipes cover being able to return a fake return value, returning
the original, or some slight modification of the original where it is some
primitive data type or collection. In some cases though I actually want to
put a wrapper around the return value to modify how subsequent code
interacts with it.

The first example of this is where the wrapped function returns another
function which would then be called by something higher up the call chain.
Here I may want to put a wrapper around the returned function to allow me
to then intercept when it is called.

In the case of using Mock I would do something like:

```
from mock import Mock, patch

def function():
    pass

class ProductionClass(object):
    def method(self, a, b, c, key):
        return function

def wrapper2(wrapped):
    def _wrapper2(*args, **kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper2

def wrapper1(wrapped):
    def _wrapper1(self, *args, **kwargs):
        func = wrapped(self, *args, **kwargs)
        return Mock(side_effect=wrapper2(func))
    return _wrapper1

@patch(__name__+'.ProductionClass.method', autospec=True,
        side_effect=wrapper1(ProductionClass.method))
def test_method(mock_method):
    real = ProductionClass()
    func = real.method(3, 4, 5, key='value')
    result = func()
```

And with wrapt I would instead do:

```
from wrapt import transient_function_wrapper, function_wrapper

def function():
    pass

class ProductionClass(object):
    def method(self, a, b, c, key):
        return function

@function_wrapper
def result_function_wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@transient_function_wrapper(__name__, 'ProductionClass.method')
def apply_ProductionClass_method_wrapper(wrapped, instance, args, kwargs):
    return result_function_wrapper(wrapped(*args, **kwargs))

@apply_ProductionClass_method_wrapper
def test_method():
    real = ProductionClass()
    func = real.method(3, 4, 5, key='value')
    result = func()
```

In this example I have used a new decorator called
'@wrapt.function_wrapper'. I could also have used '@wrapt.decorator' in
this example. The '@wrapt.function_wrapper' decorator is actually just a
cut down version of '@wrapt.decorator', lacking some of the bells and
whistles that one doesn't generally need when doing explicit monkey
patching, but otherwise it can be used in the same way.

I can therefore apply a wrapper around a function returned as a result. I
could could even apply the same principal where a function is being passed
in as an argument to some other function.

A different scenario to a function being returned is where an instance of a
class is returned. In this case I may want to apply a wrapper around a
specific method of just that instance of the class.

With the Mock library it again comes down to using its 'Mock' class and
having to apply it in different ways to achieve the result you want. I am
going to step back from Mock now though and just focus on how one can do
things using wrapt.

So, depending on the requirements there are a couple of ways one could do
this with wrapt.

The first approach is to replace the method on the instance directly with a
wrapper which encapsulates the original method.

```
from wrapt import transient_function_wrapper, function_wrapper

class StorageClass(object):
    def run(self):
        pass

storage = StorageClass()

class ProductionClass(object):
    def method(self, a, b, c, key):
        return storage

@function_wrapper
def run_method_wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@transient_function_wrapper(__name__, 'ProductionClass.method')
def apply_ProductionClass_method_wrapper(wrapped, instance, args, kwargs):
    storage = wrapped(*args, **kwargs)
    storage.run = run_method_wrapper(storage.run)
    return storage

@apply_ProductionClass_method_wrapper
def test_method():
    real = ProductionClass()
    data = real.method(3, 4, 5, key='value')
    result = data.run()
```

This will create the desired result but in this example actually turns out
to be a bad way of doing it.

The problem in this case is that the object being returned is one which has
a life time beyond the test. That is, we are modifying an object stored at
global scope and which might be used for a different test. By simply
replacing the method on the instance, we have made a permanent change.

This would be okay if it was a temporary instance of a class created on
demand just for that one call, but not where it is persistent like in this
case.

We can't therefore modify the instance itself, but need to wrap the
instance in some other way to intercept the method call.

To do this we make use of what is called an object proxy. This is a special
object type which we can create an instance of to wrap another object. When
accessing the proxy object, any attempts to access attributes will actually
return the attribute from the wrapped object. Similarly, calling a method
on the proxy will call the method on the wrapped object.

Having a distinct proxy object though allows us to change the behaviour on
the proxy object and so change how code interacts with the wrapped object.
We can therefore avoid needing to change the original object itself.

For this example what we can therefore do is:

```
from wrapt import transient_function_wrapper, ObjectProxy

class StorageClass(object):
    def run(self):
        pass

storage = StorageClass()

class ProductionClass(object):
    def method(self, a, b, c, key):
        return storage

class StorageClassProxy(ObjectProxy):
    def run(self):
        return self.__wrapped__.run()

@transient_function_wrapper(__name__, 'ProductionClass.method')
def apply_ProductionClass_method_wrapper(wrapped, instance, args, kwargs):
    storage = wrapped(*args, **kwargs)
    return StorageClassProxy(storage)

@apply_ProductionClass_method_wrapper
def test_method():
    real = ProductionClass()
    data = real.method(3, 4, 5, key='value')
    result = data.run()
```

That is, we define the 'run()' method on the proxy object to intercept the
call of the same method on the original object. We can then proceed to
return fake values, validate arguments or results, or modify them as
necessary.

With the proxy we can even intercept access to an attribute of the original
object by adding a property to the proxy object.

```
from wrapt import transient_function_wrapper, ObjectProxy

class StorageClass(object):
    def __init__(self):
        self.name = 'name'

storage = StorageClass()

class ProductionClass(object):
    def method(self, a, b, c, key):
        return storage

class StorageClassProxy(ObjectProxy):
    @property
    def name(self):
        return self.__wrapped__.name

@transient_function_wrapper(__name__, 'ProductionClass.method')
def apply_ProductionClass_method_wrapper(wrapped, instance, args, kwargs):
    storage = wrapped(*args, **kwargs)
    return StorageClassProxy(storage)

@apply_ProductionClass_method_wrapper
def test_method():
    real = ProductionClass()
    data = real.method(3, 4, 5, key='value')
    assert data.name == 'name'
```

Building a better Mock
----------------------

You might be saying at this point that Mock does a lot more than this. You
might even want to point out how Mock can save away details about the call
which can be checked later at the level of the test harness, rather than
having to resort to raising assertion errors down in the wrappers
themselves which can be an issue if code catches the exceptions before you
see them.

This is all true, but the goal at this point for wrapt has been to provide
monkey patching mechanisms which do respect introspection, the descriptor
protocol and other things besides. That I can use it for the type of
testing I do is a bonus.

You aren't limited to using just the basic building blocks themselves
though and personally I think wrapt could be a great base on which to build
a better Mock library for testing.

I therefore leave you with one final example to get you thinking about the
ways this might be done if you are partial to the way that Mock does
things.

```
from wrapt import transient_function_wrapper

class ProductionClass(object):
    def method(self, a, b, c, key):
        pass

def patch(module, name):
    def _decorator(wrapped):
        class Wrapper(object):
            @transient_function_wrapper(module, name)
            def __call__(self, wrapped, instance, args, kwargs):
                self.args = args
                self.kwargs = kwargs
                return wrapped(*args, **kwargs)
        wrapper = Wrapper()
        @wrapper
        def _wrapper():
            return wrapped(wrapper)
        return _wrapper
    return _decorator

@patch(__name__, 'ProductionClass.method')
def test_method(mock_method):
    real = ProductionClass()
    result = real.method(3, 4, 5, key='value')
    assert real.method.__name__ == 'method'
    assert mock_method.args == (3, 4, 5)
    assert mock_method.kwargs.get('key') == 'value'
```

So that is a quick run down of the main parts of the functionality provided
by wrapt for doing monkey patching. There are a few others things, but that
is in the main all you usually require. I use monkey patching for actually
adding instrumentation into existing code to support performance
monitoring, but I have shown here how the same techniques can be used in
writing tests for your code as an alternative to a package like Mock.

As I mentioned in my [previous
post](11-safely-applying-monkey-patches-in-python.md) though, one of the
big problems with monkey patching is the order in which modules get
imported relative to when the monkey patching is done. I will talk more
about that issue in the next post.
