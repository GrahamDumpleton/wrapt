How you implemented your Python decorator is wrong
==================================================

The rest of the Python community is currently doing lots of navel gazing
over the issue of Python 3 adoption and the whole unicode/bytes divide. I
am so over that and gave up caring when my will to work on WSGI stuff was
leached away by how long it took to get the WSGI specification updated for
Python 3.

Instead my current favourite gripe these days is about how people implement
Python decorators. Unfortunately, it appears to be a favourite topic for
blogging by Python developers. It is like how when WSGI was all the rage
and everyone wanted to write their own WSGI server or framework. Now it is
like a rite of passage that one must blog about how to implement Python
decorators as a way of showing that you understand Python. As such, I get
lots of opportunity to grumble and wince. If only they did truly understand
what they were describing and what problems exist with the approach they
use.

So what is my gripe then. My gripe is that although one can write a very
simple decorator using a function closure, the scope it can be used in is
usually limited. The most basic pattern for implementing a Python decorator
also breaks various stuff related to introspection.

Now most people will say who cares, it does the job I want to do and I
don't have time to care whether it is correct in all situations.

As people will know from when I did care more about WSGI, I am a pedantic
arse though and when one does something, I like to see it done correctly.

Besides my overly obsessive personal trait, it actually does also affect me
in my day job as well. This is because I write tools which are dependent
upon being able to introspect into code and I need the results I get back
to be correct. If they aren't, then the data I generate becomes useless as
information can get grouped against the wrong thing.

As well as using introspection, I also do lots of evil stuff with monkey
patching. As it happens, monkey patching and the function wrappers one
applies aren't much different to decorators, it is just how they get
applied which is different. Because though monkey patching entails going in
and modifying other peoples code when they were not expecting it, or
designing for it, means that when you do go in and wrap a function that how
you do it is very important. If you do not do it correctly then you can
crash the users application or inadvertently change how it runs.

The first thing that is vitally important is preserving introspection for
the wrapped function. Another not so obvious thing though is that you need
to ensure that you do not mess with how the execution model for the Python
object model works.

Now I can in my own function wrappers that are used when performing monkey
patching ensure that these two requirements are met so as to ensure that
the function wrapper is transparent, but it can all fall in a heap when one
needs to monkey patch functions which already have other decorators
applied.

So when you implement a Python decorator and do it poorly it can affect me
and what I want to do. If I have to subsequently work around when you do it
wrong, I get somewhat annoyed and grumpy as more often than not that
entails a lot of pain.

To cover everything there is to know about what is wrong with your typical
Python decorators and wrapping of functions, plus how to fix it, will take
a lot of explaining, so one blog post isn't going to be enough. See this
blog post therefore as just part one of an extended discussion.

For this first instalment I will simply go through the various ways in
which your typical Python decorator can cause problems.

Basics of a Python decorator
----------------------------

Everyone should know what the Python decorator syntax is.

```
@function_wrapper
def function():
    pass
```

The ``@`` annotation to denote the application of a decorator was only
added in Python 2.4. It is actually though only fancy syntactic sugar. It
is actually equivalent to writing:

```
def function():
    pass

function = function_wrapper(function)
```

and what you would have done prior to Python 2.4.

The decorator syntax is therefore just a short hand way of being able to
apply a wrapper around an existing function, or otherwise modify the
existing function in place, while the definition of the function is being
setup.

What is referred to as monkey patching achieves pretty much the same
outcome, the difference being that when monkey patching the wrapper isn't
being applied at the time the definition of the function is being setup,
but is applied retrospectively from a different context after the fact.

Anatomy of a function wrapper
-----------------------------

Although I mentioned using function closures to implement a decorator, to
understand how the more generic case of a function wrapper works it is more
illustrative to show how to implement it using a class.

```
class function_wrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

@function_wrapper
def function():
    pass
```

The class instance in this example is initialised with and records the
original function object. When the now wrapped function is called, it is
actually the ``__call__()`` method of the wrapper object which is invoked.
This in turn would then call the original wrapped function.

Simply passing through the call to the wrapper alone isn't particularly
useful, so normally you would actually want to do some work either before
or after the wrapped function is called. Or you may want to modify the
input arguments or the result as they pass through the wrapper. This is
just a matter of modifying the ``__call__()`` method appropriately to do
what you want.

Using a class to implement the wrapper for a decorator isn't actually that
popular. Instead a function closure is more often used. In this case a
nested function is used as the wrapper and it is that which is returned by
the decorator function. When the now wrapped function is called, the nested
function is actually being called. This in turn would again then call the
original wrapped function.

```
def function_wrapper(wrapped):
    def _wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper 

@function_wrapper
def function():
    pass
```

In this example the nested function doesn't actually get passed the
original wrapped function explicitly. But it will still have access to it
via the arguments given to the outer function call. This does away with the
need to create a class to hold what was the wrapped function and thus why
it is convenient and generally more popular.

Introspecting a function
------------------------

Now when we talk about functions, we expect them to specify properties
which describe them as well as document what they do. These include the
``__name__`` and ``__doc__`` attributes. When we use a wrapper though, this
no longer works as we expect as in the case of using a function closure,
the details of the nested function are returned.

```
def function_wrapper(wrapped):
    def _wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper 

@function_wrapper
def function():
    pass 

>>> print(function.__name__)
_wrapper
```

If we use a class to implement the wrapper, as class instances do not
normally have a ``__name__`` attribute, attempting to access the name of
the function will actually result in an AttributeError exception.

```
class function_wrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs) 

@function_wrapper
def function():
    pass 

>>> print(function.__name__)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'function_wrapper' object has no attribute '__name__'
```

The solution here when using a function closure is to copy the attributes
of interest from the wrapped function to the nested wrapper function. This
will then result in the function name and documentation strings being
correct.

```
def function_wrapper(wrapped):
    def _wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)
    _wrapper.__name__ = wrapped.__name__
    _wrapper.__doc__ = wrapped.__doc__
    return _wrapper 

@function_wrapper
def function():
    pass 

>>> print(function.__name__)
function
```

Needing to manually copy the attributes is laborious, and would need to be
updated if any further special attributes were added which needed to be
copied. For example, we should also copy the ``__module__`` attribute, and
in Python 3 the ``__qualname__`` and ``__annotations__`` attributes were
added. To aid in getting this right, the Python standard library provides
the ``functools.wraps()`` decorator which does this task for you.

```
import functools 

def function_wrapper(wrapped):
    @functools.wraps(wrapped)
    def _wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)
    return _wrapper 

@function_wrapper
def function():
    pass 

>>> print(function.__name__)
function
```

If using a class to implement the wrapper, instead of the
``functools.wraps()`` decorator, we would use the
``functools.update_wrapper()`` function.

```
import functools 

class function_wrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        functools.update_wrapper(self, wrapped)
    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)
```

So we might have a solution to ensuring the function name and any
documentation string is correct in the form of ``functools.wraps()``, but
actually we don't and this will not always work as I will show below.

Now what if we want to query the argument specification for a function.
This also fails and instead of returning the argument specification for the
wrapped function, it returns that of the wrapper. In the case of using a
function closure, this is the nested function. The decorator is therefore
not signature preserving.

```
import inspect 

def function_wrapper(wrapped): ...

@function_wrapper
def function(arg1, arg2): pass 

>>> print(inspect.getargspec(function))
ArgSpec(args=[], varargs='args', keywords='kwargs', defaults=None)
```

A worse situation again occurs with the class based wrapper. This time we
get an exception complaining that the wrapped function isn't actually a
function. As a result it isn't possible to derive an argument specification
at all, even though the wrapped function is actually still callable.

```
class function_wrapper(object): ... 

@function_wrapper
def function(arg1, arg2): pass 

>>> print(inspect.getargspec(function))
Traceback (most recent call last):
  File "...", line XXX, in <module>
    print(inspect.getargspec(function))
  File ".../inspect.py", line 813, in getargspec
    raise TypeError('{!r} is not a Python function'.format(func))
TypeError: <__main__.function_wrapper object at 0x107e0ac90> is not a Python function
```

Another example of introspection one can do is to use
``inspect.getsource()`` to get back the source code related to a function.
This also will fail, with it giving the source code for the nested wrapper
function in the case of a function closure and again failing outright with
an exception in the case of the class based wrapper.

Wrapping class methods
----------------------

Now, as well as normal functions, decorators can also be applied to methods
of classes. Python even includes a couple of special decorators called
``@classmethod`` and ``@staticmethod`` for converting normal instance
methods into these special method types. Methods of classes do provide a
number of potential problems though.

```
class Class(object): 

    @function_wrapper
    def method(self):
        pass 

    @classmethod
    def cmethod(cls):
        pass 

    @staticmethod
    def smethod():
        pass
```

The first is that even if using ``functools.wraps()`` or
``functools.update_wrapper()`` in your decorator, when the decorator is
applied around ``@classmethod`` or ``@staticmethod``, it can fail with an
exception. This is because the wrappers created by these, do not have some
of the attributes being copied.

```
class Class(object):
    @function_wrapper
    @classmethod
    def cmethod(cls):
        pass 

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 3, in Class
  File "<stdin>", line 2, in wrapper
  File ".../functools.py", line 33, in update_wrapper
    setattr(wrapper, attr, getattr(wrapped, attr))
AttributeError: 'classmethod' object has no attribute '__module__'
```

As it happens, this is a Python 2 bug and it is fixed in Python 3 by
ignoring missing attributes.

Even when we run it under Python 3, we still hit trouble though. This is
because both wrapper types assume that the wrapped function is directly
callable. This need not actually be the case. A wrapped function can
actually be what is called a descriptor, meaning that in order to get back
a callable, the descriptor has to be correctly bound to the instance first.

```
class Class(object):
    @function_wrapper
    @classmethod
    def cmethod(cls):
        pass 

>>> Class.cmethod() 
Traceback (most recent call last):
  File "classmethod.py", line 15, in <module>
    Class.cmethod()
  File "classmethod.py", line 6, in _wrapper
    return wrapped(*args, **kwargs)
TypeError: 'classmethod' object is not callable
```

Simple does not imply correctness
---------------------------------

So although the usual way that people implement decorators is simple, that
doesn't mean they are necessarily correct and will always work.

The issues highlighted so far are:

* Preservation of function ``__name__`` and ``__doc__``.
* Preservation of function argument specification.
* Preservation of ability to get function source code.
* Ability to apply decorators on top of other decorators that are implemented as descriptors.

The ``functools.wraps()`` function is given as a solution to the first but
doesn't always work, at least in Python 2. It doesn't help at all though
with preserving the introspection of a functions argument specification and
ability to get the source code for a function.

Even if one could solve the introspection problem, the simple decorator
implementation that is generally offered up as the way to do things, breaks
the execution model for the Python object model, not honouring the
descriptor protocol of anything which is wrapped by the decorator.

Third party packages do exist which try and solve these issues, such as the
decorator module available on PyPi. This module in particular though only
helps with the first two and still has potential issues with how it works
that may cause problems when trying to dynamically apply function wrappers
via monkey patching.

This doesn't mean these problems aren't solvable, and solvable in a way
that doesn't sacrifice performance. In my search at least, I could not
actually find any one who has described a comprehensive solution or offered
up a package which performs all the required magic so you don't have to
worry about it yourself.

This blog post is therefore the first step in me explaining how it can be
all made to work. I have stated the problems to be solved and in subsequent
posts I will explain how they can be solved and what extra capabilities
that gives you which enables the ability to write even more magic
decorators than what is possible now with traditional ways that decorators
have been implemented.

So stay tuned for the next instalment. Hopefully I can keep the momentum up
and keep them coming. Pester me if I don't.
