Safely applying monkey patches in Python
========================================

Monkey patching in Python is often see as being one of those things you
should never do. Some do regard it as a useful necessity you can't avoid in
order to patch bugs in third party code. Others will argue though that with
so much software being Open Source these days that you should simply submit
a fix to the upstream package maintainer.

Monkey patching has its uses well beyond just patching bugs though. The two
most commonly used forms of monkey patching in Python which you might not
even equate with monkey patching are decorators and the use of mocking
libraries to assist in performing unit testing. Another not some common
case of monkey patching is to add instrumentation to existing Python code
in order to add performance monitoring capabilities.

On the issue of decorators I wrote a quite detailed series of blog posts at
the start of last year about where decorators can cause problems. The
primary problem there was decorators which aren't implemented in a way
which preserve proper introspection capabilities, and which don't preserve
the correct semantics of the Python descriptor protocol when applied to
methods of classes.

When one starts to talk about monkey patching arbitrary code, rather than
simply applying decorators to your own code, both of these issues become
even more important as you could quite easily interfere with the behaviour
of the existing code you are monkey patching in unexpected ways.

This is especially the case when monkey patching methods of a class. This
is because when using decorators they would be applied while the class
definition is being constructed. When doing monkey patching you are coming
in after the class definition already exists and as a result you have to
deal with a number of non obvious problems.

Now when I went and wrote the blog posts last year on decorators it was
effectively the result of what I learnt from implementing the wrapt
package. Although that package is known as providing a way for creating
well behaved decorators, that wasn't the primary aim in creating the
package. The real reason for creating the package was actually to implement
robust mechanisms for monkey patching code. It just so happened that the
same underlying principles and mechanism required to safely do monkey
patching apply to implementing the function wrappers required for
decorators.

What I am going to do with this blog post is start to explain the monkey
patching capabilities of the wrapt package.

Creating a decorator
--------------------

Before we jump into monkey patching of arbitrary code we first need to
recap how the wrapt package could be used to create a decorator. The
primary pattern for this was:

```
import wrapt
import inspect 

@wrapt.decorator
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

A special feature of the decorators that could be created by the wrapt
package was that within the decorator you could determine the context the
decorator was used in. That is, whether the decorator was applied to a
class, a function or static method, a class method or an instance method.

For the case where the decorator was applied to an instance method you are
provided a separate argument to the instance of the class. For a class
method the separate argument is a reference to the class itself. In both
cases these are separated from the 'args' and 'kwargs' argument so you do
not need to fiddle around with extracting it yourself.

A decorator created using wrapt is therefore what I call a universal
decorator. In other words, it is possible to create a single decorator
implementation that can be used across functions, methods and classes and
you can tell at the time of the call the scenario and adjust the behaviour
of the decorator accordingly. You no longer have to create multiple
implementations of a decorator and ensure that you are using the correct
one in each scenario.

Using this decorator is then no different to any other way that decorators
would be used.

```
class Example(object):

    @universal
    def name(self):
        return 'name'
```

For those who have used Python long enough though, you would remember that
the syntax for applying a decorator in this way hasn't always existed.
Before the '@' syntax was allowed you could still create and use
decorators, but you had to be more explicit in applying them. That is, you
had to write:

```
class Example(object):

    def name(self):
        return 'name'
    name = universal(name) 
```

This can still be done and when written this way it makes it clearer how
decorators are in a way a form of monkey patching. This is because often
all they are doing is introducing a wrapper around some existing function
which allows the call to the original function to be intercepted. The
wrapper function then allows you to perform actions either before or after
the call to the original function, or allow you to modify the arguments
passed to the wrapped function, or otherwise modify the result in some way,
or even substitute the result completely.

What is an important distinction though with decorators is that the wrapper
function is being applied at the time the class containing the method is
being defined. In contrast more arbitrary monkey patching involves coming
in some time later after the class definition has been created and applying
the function wrapper at that point.

In effect you are doing:

```
class Example(object):
    def name(self):
        return 'name'

Example.name = universal(Example.name)
```

Although a decorator function created using the wrapt package can be used
in this way and will still work as expected, in general I would discourage
this pattern for monkey patching an existing method of a class.

This is because it isn't actually equivalent to doing the same thing within
the body of the class when it is defined. In particular the access of
'Example.name' actually invokes the descriptor protocol and so is returning
an instance method. We can see this by running the code:

```
class Example(object):
    def name(self):
        return 'name'
    print type(name)

print type(Example.name)
```

which produces:

```
<type 'function'>
<type 'instancemethod'>
```

In general this may not matter, but I have seen some really strange corner
cases where the distinction has mattered. To deal with this therefore, the
wrapt package provides an alternate way of applying wrapper functions when
doing monkey patching after the fact. In the case of adding wrappers to
methods of class, this will use a mechanism which avoids any problems
caused by this subtle distinction.

Adding function wrappers
------------------------

For general monkey patching using the wrapt package, rather than using the
decorator factory to create a decorator and then apply that to a function,
you instead define just the wrapper function and then use a separate
function to apply it to the target function.

The prototype for the wrapper function is the same as before, but we simply
do not apply the '@wrapt.decorator' to it.

```
def wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
```

To add the wrapper function to a target function we now use the
'wrapt.wrap_function_wrapper()' function.

```
class Example(object):
    def name(self):
        return 'name'

import wrapt

wrapt.wrap_function_wrapper(Example, 'name', wrapper)
```

In this case we had the class in the same code file, but we could also have
done:

```
import example

import wrapt

wrapt.wrap_function_wrapper(example, 'Example.name', wrapper)
```

That is, we provide the first argument as the module the target is defined
in, with the second argument being the object path to the method we wished
to apply the wrapper to.

We could also skip importing the module altogether and just used the name
of the module.

```
import wrapt

wrapt.wrap_function_wrapper('example', 'Example.name', wrapper)
```

Just to prove that just about anything can be simplified by the user of a
decorator, we finally could write the whole thing as:

```
import wrapt

@wrapt.patch_function_wrapper('example', 'Example.name')
def wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
```

What will happen in this final example is that as soon as the module this
is contained in is imported, the specified target function defined in the
'example' module will automatically be monkey patched with the wrapper
function.

Delayed patching is bad
-----------------------

Now a very big warning is required at this point. Applying monkey patches
after the fact like this will not always work.

The problem is that you are trying to apply a patch after the module has
been imported. In this case the 'wrapt.wrap_function_wrapper()' call will
ensure the module is imported if it wasn't already, but if the module had
already been imported previously by some other part of your code or by a
third party package you may have issues.

In particular, it the target function you were trying to monkey patch was a
normal global function of the module, some other code could have grabbed a
direct reference to it by doing:

```
from example import function
```

If you come along later and have:

```
import wrapt

@wrapt.patch_function_wrapper('example', 'function')
def wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
```

then yes the copy of the function contained in the target module will have
the wrapper applied, but the reference to it created by the other code will
not have the wrapper.

To ensure that your wrapper is always used in this scenario you would need
to patch it not just in the original module, but in any modules where a
reference had been stored. This would only be practical in very limited
circumstances because in reality you are not going to have any idea where
the function might be getting used if it is a common function.

This exact problem is one of the shortcomings in the way that monkey
patching is applied by packages such as gevent or eventlet. Both these
packages do delayed patching of functions and so are sensitive to the order
in which modules are imported. To get around this problem at least for
modules in the Python standard library, the 'time.sleep()' function which
they need to monkey patch, has to be patched not only in the 'time' module,
but also in the 'threading' module.

There are some techniques one can use to try and avoid such problems but I
will defer explaining those to some time down the track.

Instead for my next blog post I want to move onto some examples for where
monkey patching could be used by looking at how wrapt can be used as
alternative to packages such as the mock package when doing testing.
