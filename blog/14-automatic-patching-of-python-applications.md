Automatic patching of Python applications
=========================================

In my [previous posts](
13-ordering-issues-when-monkey-patching-in-python.md) on monkey patching I
discussed the ordering problem. That is, that the ability to properly
monkey patch is dependent on whether we can get in before any other code
has already imported the module we want to patch. The specific issue in
this case is where other code has imported a reference to a function within
a module by name and stored that in it is own namespace. In other words,
where it has used:

```
from module import function
```

If we can't get in early enough, then it becomes necessary to monkey patch
all such uses of a target function as well, which in the general case is
impossible as we will not know where the function has been imported.

Part of the solution I described for this was to use a post import hook
mechanism to allow us to get access to a module for monkey patching before
the module is even returned back to any code where it is being imported.
This technique is still though dependent on the post import hook mechanism
itself being installed before any other code is effectively run. This means
having to manually modify the main Python script file for an application,
something which isn't always practical.

The point of this post is to look at how we can avoid the need to even
modify that main Python script file. For this there are a few techniques
that could be used. I am going to look at the most evil of those techniques
first and then talk about others in a subsequent post.

Executable code in .pth files
-----------------------------

As part of the Python import system and how it determines what directories
are searched for Python modules, there is a mechanism whereby for a package
it is possible to install a file with a .pth extension into the Python
'site-packages' directory. The actual Python package code itself then might
actually be installed in a different location not actually on the Python
module search path, most often actually in a versioned subdirectory of the
'site-packages' directory. The purpose of the .pth file is to act as a
pointer to where the actual code for the Python package lives.

In the simple case the .pth file will contain a relative or absolute path
name to the name of the actual directory containing the code for the Python
package. In the case of it being a relative path name, then it will be
taken relative to the directory in which the .pth file is located.

With such .pth files in place, when the Python interpreter is initialising
itself and setting up the Python module search path, after it has added in
all the default directories to be searched, it will look through the
site-packages directory and parse each .pth file, adding to the final list
of directories to be searched any directories specified within the .pth
files.

Now at one point in the history of Python this .pth mechanism was enhanced
to allow for a special case. This special case was that if a line in the
.pth file started with import, the line would be executed as Python code
instead of simply adding it as a directory to the list of directories to be
searched for modules.

I am told this originally was to allow special startup code to be executed
for a module to allow registration of a non standard codec for Unicode. It
has though since also been used in the implementation of easy_install and
if you have ever run easy-install and looked at the easy-install.pth file
in the site-packages directory you will find some code which looks like:

```
import sys; sys.__plen = len(sys.path)
./antigravity-0.1-py2.7.egg
import sys; new=sys.path[sys.__plen:]; del sys.path[sys.__plen:]; p=getattr(sys,'__egginsert',0); sys.path[p:p]=new; sys.__egginsert = p+len(new)
```

So as long as you can fit the code on one line, you can potentially do some
quite nasty stuff inside of a .pth file every time that the Python
interpreter is run.

Personally I find the concept of executable code inside of a .pth file
really dangerous and up until now have avoided relying on this feature of
.pth files.

My concerns over executable code in .pth files is the fact that it is
always run. This means that even if you had installed a pre built RPM/DEB
package or a Python wheel into a system wide Python installation, with the
idea that this was somehow much safer because you were avoiding running the
setup.py file for a package as the root user, the .pth file means that the
package can still subsequently run code without you realising and without
you even having imported the module into any application.

If one wanted to be paranoid about security, then Python should really have
a whitelisting mechanism for what .pth files you wanted to trust and allow
code to be executed from every time the Python interpreter is run,
especially as the root user.

I will leave that discussion up to others if anyone else cares to be
concerned and for now at least will show how this feature of .pth files can
be used (abused) to implement a mechanism for automated monkey patching of
any Python application being run.

Adding Python import hooks
--------------------------

In the previous post where I talked about the post import hook mechanism,
the code I gave as needing to be able to be manually added at the start of
any Python application script file was:

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

What this was doing was using an environment variable as the source of
names for any packages registered using setuptools entry points that
contained monkey patches we wanted to have applied.

Knowing about the ability to have executable code in .pth files, lets now
work out how we can use that to instead have this code executed
automatically every time the Python interpreter is run, thereby avoiding
the need to manually modify every Python application we want to have monkey
patches applied to.

In practice however, the code we will need is actually going to have to be
slightly more complicated than this and as a result not something that can
be readily added directly to a .pth file due to the limitation of code
needing to all be on one line. What we will therefore do is put all our
code in a separate module and execute it from there. We don't want to be too
nasty and import that module every time though, perhaps scaring users when
they see it imported even if not used, so we will gate even that by the
presence of the environment variable.

What we can therefore use in our ‘.pth’ is:

```
import os, sys; os.environ.get('AUTOWRAPT_BOOTSTRAP') and __import__('autowrapt.bootstrap') and sys.modules['autowrapt.bootstrap'].bootstrap()
```

That is, if the environment variable is set to a non empty value only then
do we import our module containing our bootstrap code and execute it.

As to the bootstrap code, this is where things get a bit messy. We can't
just use the code we had used before when manually modifying the Python
application script file. This is because of where in the Python interpreter
initialisation the parsing of .pth files is done.

The problems are twofold. The first issue with executing the discovery of
the import hooks directly when the .pth file is processed is that the order
in which they are processed is unknown and so at the point our code is run
the final Python module search path may not have been setup. The second
issue is that .pth file processing is done before any sitecustomize.py or
usercustomize.py processing has been done. The Python interpreter therefore
may not be in its final configured state. We therefore have to be a little
bit careful of what we do.

What we really want is to defer any actions until the Python interpreter
initialisation has been completed. The problem is how we achieve that.

Python interpreter ‘site’ module
--------------------------------

The actual final parts of Python interpreter initialisation is performed
from the main() function of the site module:

```
def main():
    global ENABLE_USER_SITE
    abs__file__()
    known_paths = removeduppaths()
    if ENABLE_USER_SITE is None:
        ENABLE_USER_SITE = check_enableusersite()
    known_paths = addusersitepackages(known_paths)
    known_paths = addsitepackages(known_paths)
    if sys.platform == 'os2emx':
        setBEGINLIBPATH()
    setquit()
    setcopyright()
    sethelper()
    aliasmbcs()
    setencoding()
    execsitecustomize()
    if ENABLE_USER_SITE:
        execusercustomize()
    # Remove sys.setdefaultencoding() so that users cannot change the
    # encoding after initialization. The test for presence is needed when
    # this module is run as a script, because this code is executed twice.
    if hasattr(sys, "setdefaultencoding"):
        del sys.setdefaultencoding
```

The .pth parsing and code execution we want to rely upon is done within the
addsitepackages() function.

What we really want therefore is to defer any execution of our code until
after the functions execsitecustomize() or execusercustomize() are run. The
way to achieve that is to monkey patch those two functions and trigger our
code when they have completed.

We have to monkey patch both because the usercustomize.py processing is
optional dependent on whether ENABLE_USER_SITE is true or not. Our
'bootstrap() function therefore needs to look like:

```
def _execsitecustomize_wrapper(wrapped):
    def _execsitecustomize(*args, **kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            if not site.ENABLE_USER_SITE:
                _register_bootstrap_functions()
    return _execsitecustomize

def _execusercustomize_wrapper(wrapped):
    def _execusercustomize(*args, **kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            _register_bootstrap_functions()
    return _execusercustomize

def bootstrap():
    site.execsitecustomize = _execsitecustomize_wrapper(site.execsitecustomize)
    site.execusercustomize = _execusercustomize_wrapper(site.execusercustomize)
```

Despite everything I have ever said about how manually constructed monkey
patches is bad and that the wrapt module should be used for doing monkey
patching, we can't actually use the wrapt module in this case. This is
because technically, as a user installed package, the wrapt package may not
be usable at this point. This could occur where wrapt was installed in such
a way that the ability to import it was itself dependent on the processing
of .pth files. As a result we drop down to using a simple wrapper using a
function closure.

In the actual wrappers, you can see how which of the two wrappers actually
ends up calling _register_bootstrap_functions() is dependent on whether
ENABLE_USER_SITE is true or not, only calling it in execsitecustomize() if
support for usersitecustomize was enabled.

Finally we now have our '_register_bootstrap_functions()’ defined as:

```
_registered = False

def _register_bootstrap_functions():
    global _registered
    if _registered:
        return
    _registered = True

    from wrapt import discover_post_import_hooks
    for name in os.environ.get('AUTOWRAPT_BOOTSTRAP', '').split(','):
        discover_post_import_hooks(name)
```

Bundling it up as a package
---------------------------

We have worked out the various bits we require, but how do we get this
installed, in particular how do we get the custom .pth file installed. For
that we use a setup.py file of:

```
import sys
import os

from setuptools import setup
from distutils.sysconfig import get_python_lib

setup_kwargs = dict(
    name = 'autowrapt',
    packages = ['autowrapt'],
    package_dir = {'autowrapt': 'src'},
    data_files = [(get_python_lib(prefix=''), ['autowrapt-init.pth'])],
    entry_points = {'autowrapt.examples’: ['this = autowrapt.examples:autowrapt_this']},
    install_requires = ['wrapt>=1.10.4'],
)

setup(**setup_kwargs)
```

To get that .pth installed we have used the data_files argument to the
setup() call. The actual location for installing the file is determined
using the get_python_lib() function from the distutils.sysconfig module.
The prefix' argument of an empty string ensures that a relative path for
the site-packages directory where Python packages should be installed is
used rather than an absolute path.

Very important when installing this package though is that you cannot use
easy_install or python setup.py install. One can only install this package
using pip.

The reason for this is that if not using pip, then the package installation
tool can install the package as an egg. In this situation the custom .pth
file will actually be installed within the egg directory and not actually
within the site-packages directory.

The only .pth file added to the site-packages directory will be that used
to map that the autowrapt package exists in the sub directory. The
addsitepackages() function called from the site module doesn't in turn
process .pth files contained in a directory added by a .pth file, so our
custom .pth file would be skipped.

When using ‘pip’ it doesn’t use eggs by default and so we are okay.

Also do be aware that this package will not work with buildout as it will
always install packages as eggs and explicitly sets up the Python module
search path itself in any Python scripts installed into the Python
installation.

Trying out an example
---------------------

The actual complete source code for this package can be found at:

* https://github.com/GrahamDumpleton/autowrapt

The package has also been released on PyPi as autowrapt so you can actually
try it, and use it if you really want to.

To allow for a easy quick test to see that it works, the autowrapt package
bundles an example monkey patch. In the above setup.py this was set up by:

```
entry_points = {'autowrapt.examples’: ['this = autowrapt.examples:autowrapt_this']},
```

This entry point definition names a monkey patch with the name
autowrapt.examples. The definition says that when the this module is
installed, the monkey patch function autowrapt_this() in the module
autowrapt.examples will be called.

So to run the test do:

```
pip install autowrapt
```

This should also install the wrapt module if you don't have the required
minimum version.

Now run the command line interpreter as normal and at the prompt do:

```
import this
```

This should result in the Zen of Python being displayed.

Exit the Python interpreter and now instead run:

```
AUTOWRAPT_BOOTSTRAP=autowrapt.examples python
```

This runs the Python interpreter again, but also sets the environment
variable AUTOWRAPT_BOOTSTRAP with the value autowrapt.examples matching the
name of the entry point defined in the setup.py file for autowrapt'.

The actual code for the ‘autowrapt_this()’ function was:

```
from __future__ import print_function

def autowrapt_this(module):
    print('The wrapt package is absolutely amazing and you should use it.')
```

so if we now again run:

```
import this
```

we should now see an extended version of the Zen of Python.

We didn't actually monkey patch any code in the target module in this case,
but it shows that the monkey patch function was actually triggered when
expected.

Other bootstrapping mechanisms
------------------------------

Although this mechanism is reasonably clean and only requires the setting
of an environment variable, it cannot be used with buildout as mentioned.
For buildout we need to investigate other approaches we could use to
achieve the same affect. I will cover such other options in the next blog
post on this topic.
