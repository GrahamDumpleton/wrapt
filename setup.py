from distutils.core import setup
from distutils.core import Extension

setup(name = 'wrapt',
      version = '0.9.0',
      description = 'Module for decorators, wrappers and monkey patching.',
      author = 'Graham Dumpleton',
      author_email = 'Graham.Dumpleton@gmail.com',
      license = 'BSD',
      url = 'https://github.com/GrahamDumpleton/wrapt',
      packages = ['wrapt'],
      package_dir={'wrapt': 'src'},
      ext_modules = [Extension("wrapt._wrappers", ["src/_wrappers.c"])],
     )
