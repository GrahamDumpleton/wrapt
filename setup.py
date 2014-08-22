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
            DistutilsPlatformError, IOError)
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

setup_kwargs = dict(
      name = 'wrapt',
      version = '1.9.0',
      description = 'Module for decorators, wrappers and monkey patching.',
      author = 'Graham Dumpleton',
      author_email = 'Graham.Dumpleton@gmail.com',
      license = 'BSD',
      url = 'https://github.com/GrahamDumpleton/wrapt',
      packages = ['wrapt'],
      package_dir={'wrapt': 'src'},
     )

def run_setup(with_extensions):
    setup_kwargs_tmp = dict(setup_kwargs)

    if with_extensions:
        setup_kwargs_tmp['ext_modules'] = [
                Extension("wrapt._wrappers", ["src/_wrappers.c"])]
        setup_kwargs_tmp['cmdclass'] = dict(build_ext=optional_build_ext)

    setup(**setup_kwargs_tmp)

with_extensions = os.environ.get('WRAPT_EXTENSIONS', None)

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
