Ordering issues when monkey patching in Python
==============================================

In my recent post about [safely applying monkey patches in Python](
11-safely-applying-monkey-patches-in-python.md), I mentioned how one of the
issues that arises is when a monkey patch is applied. Specifically, if the
module you need to monkey patch has already been imported and was being
used by other code, that it could have created a local reference to a
target function you wish to wrap, in its own namespace. So although your
monkey patch would work fine where the original function was used direct
from the module, you would not cover where it was used via a local
reference.

Coincidentally, Ned Batchelder recently [posted](
http://nedbatchelder.com//blog/201503/finding_temp_file_creators.html)
about using monkey patching to debug an issue where temporary directories
were not being cleaned up properly. Ned described this exact issue in
relation to wanting to monkey patch the 'mkdtemp()' function from the
'tempfile' module. In that case he was able to find an alternate place
within the private implementation for the module to patch so as to avoid
the problem. Using some internal function like this may not always be
possible however.

What I want to start discussing with this post is mechanisms one can use
from wrapt to deal with this issue of ordering. A major part of the
solution is what are called post import hooks. This is a mechanism which
was described in [PEP 369](
https://www.python.org/dev/peps/pep-0369/) and although it never made it
into the Python core, it is still possible to graft this ability into
Python using existing APIs. From this we can then add additional
capabilities for discovering monkey patching code and automatically apply
it when modules are imported, before other modules get the module and so
before they can create a reference to a function in their own namespace.

Post import hook mechanism
--------------------------

In PEP 369, a primary use case presented was illustrated by the example:

```
import imp

@imp.when_imported('decimal')
def register(decimal):
    Inexact.register(decimal.Decimal)
```

The basic idea is that when this code was seen it would cause a callback to
be registered within the Python import system such that when the 'decimal'
module was imported, that the 'register()' function which the decorator had
been applied to, would be called. The argument to the 'register()' function
would be the reference to the module the registration had been against. The
function could then perform some action against the module before it was
returned to whatever code originally requested the import.

Instead of using the decorator '@imp.when_imported' decorator, one could
also explicitly use the 'imp.register_post_import_hook()' function to
register a post import hook.

```
import imp

def register(decimal):
    Inexact.register(decimal.Decimal)

imp.register_post_import_hook(register, 'decimal')
```

Although PEP 369 was never incorporated into Python, the wrapt module
provides implementations for both the decorator and the function, but
within the 'wrapt' module rather than 'imp'.

Now what neither the decorator or the function really solved alone was the
ordering issue. That is, you still had the problem that these could be
triggered after the target module had already been imported. In this case
the post import hook function would still be called, albeit for our case
too late to get in before the reference to the function we want to monkey
patch had been created in a different namespace.

The simplest solution to this problem is to modify the main Python script
for your application and setup all the post import hook registrations you
need as the absolute very first thing that is done. That is, before any
other modules are imported from your application or even modules from the
standard library used to parse any command line arguments.

Even if you are able to do this, because though the registration functions
require an actual callable, it does mean you are preloading the code to
perform all the monkey patches. This could be a problem if they in turn had
to import further modules as the state of your application may not yet have
been setup such that those imports would succeed.

They say though that one level of indirection can solve all problems and
this is an example of where that principle can be applied. That is, rather
than import the monkey patching code, you can setup a registration which
would only lazily load the monkey patching code itself if the module to be
patched was imported, and then execute it.

```
import sys

from wrapt import register_post_import_hook

def load_and_execute(name):
    def _load_and_execute(target_module):
        __import__(name)
        patch_module = sys.modules[name]
        getattr(patch_module, 'apply_patch')(target_module)
    return _load_and_execute

register_post_import_hook(load_and_execute('patch_tempfile'), 'tempfile')
```

In the module file 'patch_tempfile.py' we would now have:

```
from wrapt import wrap_function_wrapper

def _mkdtemp_wrapper(wrapped, instance, args, kwargs):
    print 'calling', wrapped.__name__
    return wrapped(*args, **kwargs)

def apply_patch(module):
    print 'patching', module.__name__
    wrap_function_wrapper(module, 'mkdtemp', _mkdtemp_wrapper)
```

Running the first script with the interactive interpreter so as to leave us
in the interpreter, we can then show what happens when we import the
'tempfile' module and execute the 'mkdtemp()' function.

```
$ python -i lazyloader.py
>>> import tempfile
patching tempfile
>>> tempfile.mkdtemp()
calling mkdtemp
'/var/folders/0p/4vcv19pj5d72m_bx0h40sw340000gp/T/tmpfB8r20'
```

In other words, unlike how most monkey patching is done, we aren't forcibly
importing a module in order to apply the monkey patches on the basis it
might be used. Instead the monkey patching code stays dormant and unused
until the target module is later imported. If the target module is never
imported, the monkey patch code for that module is itself not even
imported.

Discovery of post import hooks
------------------------------

Post import hooks as described provide a slightly better way of setting up
monkey patches so they are applied. This is because they are only activated
if the target module containing the function to be patched is even
imported. This avoids unnecessarily importing modules you may not even use,
and which otherwise would increase memory usage of your application.

Ordering is still important and as a result it is important to ensure that
any post import hook registrations are setup before any other modules are
imported. You also need to modify your application code every time you want
to change what monkey patches are applied. This latter point could be
inconvenient if only wanting to add monkey patches infrequently for the
purposes of debugging issues.

A solution to the latter issue is to separate out monkey patches into
separately installed modules and use a registration mechanism to announce
their availability. Python applications could then have common boiler plate
code executed at the very start which discovers based on supplied
configuration what monkey patches should be applied. The registration
mechanism would then allow the monkey patch modules to be discovered at
runtime.

One particular registration mechanism which can be used here is
'setuptools' entry points. Using this we can package up monkey patches so
they could be separately installed ready for use. The structure of such a
package would be:

```
setup.py
src/__init__.py
src/tempfile_debugging.py
```

The 'setup.py' file for this package will be:

```
from setuptools import setup

NAME = 'wrapt_patches.tempfile_debugging'

def patch_module(module, function=None):
    function = function or 'patch_%s' % module.replace('.', '_')
    return '%s = %s:%s' % (module, NAME, function)

ENTRY_POINTS = [
    patch_module('tempfile'),
]

setup_kwargs = dict(
    name = NAME,
    version = '0.1',
    packages = ['wrapt_patches'],
    package_dir = {'wrapt_patches': 'src'},
    entry_points = { NAME: ENTRY_POINTS },
)

setup(**setup_kwargs)
```

As a convention so that our monkey patch modules are easily identifiable we
use a namespace package. The parent package in this case will be
'wrapt_patches' since we are working with wrapt specifically.

The name for this specific package will be
'wrapt_patches.tempfile_debugging' as the theoretical intent is that we are
going to create some monkey patches to help us debug use of the 'tempfile'
module, along the lines of what Ned described in his blog post.

The key part of the 'setup.py' file is the definition of the
'entry_points'. This will be set to a dictionary mapping the package name
to a list of definitions listing what Python modules this package contains
monkey patches for.

The 'src/__init__.py' file will then contain:

```
import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)
```

as is required when creating a namespace package.

Finally, the monkey patches will actually be contained in
'src/tempfile_debugging.py' and for now is much like what we had before.

```
from wrapt import wrap_function_wrapper

def _mkdtemp_wrapper(wrapped, instance, args, kwargs):
    print 'calling', wrapped.__name__
    return wrapped(*args, **kwargs)

def patch_tempfile(module):
    print 'patching', module.__name__
    wrap_function_wrapper(module, 'mkdtemp', _mkdtemp_wrapper)
```

With the package defined we would install it into the Python installation
or virtual environment being used.

In place now of the explicit registrations which we previously added at the
very start of the Python application main script file, we would instead
add:

```
import os

from wrapt import discover_post_import_hooks

patches = os.environ.get('WRAPT_PATCHES')

if patches:
    for name in patches.split(','):
        name = name.strip()
        if name:
            print 'discover', name
            discover_post_import_hooks(name)
```

If we were to run the application with no specific configuration to enable
the monkey patches then nothing would happen. If however they were enabled,
then they would be automatically discovered and applied as necessary.

```
$ WRAPT_PATCHES=wrapt_patches.tempfile_debugging python -i entrypoints.py
discover wrapt_patches.tempfile_debugging
>>> import tempfile
patching tempfile
```

What would be ideal is if PEP 369 ever did make it into the core of Python
that a similar bootstrapping mechanism be incorporated into Python itself
so that it was possible to force registration of monkey patches very early
during interpreter initialisation. Having this in place we would have a
guaranteed way of addressing the ordering issue when doing monkey patching.

As that doesn't exist right now, what we did in this case was modify our
Python application to add the bootstrap code ourselves. This is fine where
you control the Python application you want to be able to potentially apply
monkey patches to, but what if you wanted to monkey patch a third party
application and you didn't want to have to modify its code. What are the
options in that case?

As it turns out there are some tricks that can be used in that case. I will
discuss such options for monkey patching a Python application you can't
actually modify in my next blog post on this topic of monkey patching.
