import os

from distutils.core import setup
from distutils.core import Extension

with_extensions = os.environ.get('WRAPT_EXTENSIONS', 'true')
with_extensions = (with_extensions.lower() != 'false')

setup_kwargs = dict(
      name = 'wrapt',
      version = '0.9.0',
      description = 'Module for decorators, wrappers and monkey patching.',
      author = 'Graham Dumpleton',
      author_email = 'Graham.Dumpleton@gmail.com',
      license = 'BSD',
      url = 'https://github.com/GrahamDumpleton/wrapt',
      packages = ['wrapt'],
      package_dir={'wrapt': 'src'},
     )

setup_extension_kwargs = dict(
    ext_modules = [Extension("wrapt._wrappers", ["src/_wrappers.c"])],
)

if with_extensions:
    setup_kwargs.update(setup_extension_kwargs)

setup(**setup_kwargs)
