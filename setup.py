from __future__ import print_function

import os
import sys

from distutils.core import setup
from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.errors import (CCompilerError, DistutilsExecError,
                DistutilsPlatformError)

if sys.platform == 'win32':
    build_ext_errors = (CCompilerError, DistutilsExecError,
            DistutilsPlatformError, IOError, OSError)
else:
    build_ext_errors = (CCompilerError, DistutilsExecError,
            DistutilsPlatformError)

class BuildExtFailed(Exception):
    pass

class optional_build_ext(build_ext):
    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildExtFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except build_ext_errors:
            raise BuildExtFailed()

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
]

setup_kwargs = dict(
      name='wrapt',
      version='1.10.11',
      description='Module for decorators, wrappers and monkey patching.',
      long_description=open('README.rst').read(),
      author='Graham Dumpleton',
      author_email='Graham.Dumpleton@gmail.com',
      license='BSD',
      classifiers=classifiers,
      url='https://github.com/GrahamDumpleton/wrapt',
      packages=['wrapt'],
      package_dir={'': 'src'},
     )

def run_setup(with_extensions):
    setup_kwargs_tmp = dict(setup_kwargs)

    if with_extensions:
        setup_kwargs_tmp['ext_modules'] = [
                Extension("wrapt._wrappers", ["src/wrapt/_wrappers.c"])]
        setup_kwargs_tmp['cmdclass'] = dict(build_ext=optional_build_ext)

    setup(**setup_kwargs_tmp)

with_extensions = os.environ.get('WRAPT_INSTALL_EXTENSIONS')

# Use WRAPT_INSTALL_EXTENSIONS now, but also check WRAPT_EXTENSIONS
# for backward compatibility in case people had hard wired that.

if with_extensions is None:
    with_extensions = os.environ.get('WRAPT_EXTENSIONS')

if with_extensions:
    if with_extensions.lower() == 'true':
        with_extensions = True
    elif with_extensions.lower() == 'false':
        with_extensions = False
    else:
        with_extensions = None

if hasattr(sys, 'pypy_version_info'):
    with_extensions = False

WARNING = """
WARNING: The C extension component for wrapt could not be compiled.
"""

if with_extensions is not None:
    run_setup(with_extensions=with_extensions)

else:
    try:
        run_setup(with_extensions=True)

    except BuildExtFailed:

        print(75 * '*')

        print(WARNING)
        print("INFO: Trying to build without extensions.")

        print()
        print(75 * '*')

        run_setup(with_extensions=False)

        print(75 * '*')

        print(WARNING)
        print("INFO: Only pure Python version of package installed.")

        print()
        print(75 * '*')
