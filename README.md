# wrapt

[![PyPI](https://img.shields.io/pypi/v/wrapt.svg?logo=python&cacheSeconds=3600)](https://pypi.python.org/pypi/wrapt)
[![Documentation](https://img.shields.io/badge/docs-wrapt.readthedocs.io-blue.svg)](https://wrapt.readthedocs.io/)
[![License](https://img.shields.io/badge/license-BSD-green.svg)](LICENSE)

A Python module for decorators, wrappers and monkey patching.

## Overview

The **wrapt** module provides a transparent object proxy for Python, which can be used as the basis for the construction of function wrappers and decorator functions.

The **wrapt** module focuses very much on correctness. It goes way beyond existing mechanisms such as `functools.wraps()` to ensure that decorators preserve introspectability, signatures, type checking abilities etc. The decorators that can be constructed using this module will work in far more scenarios than typical decorators and provide more predictable and consistent behaviour.

To ensure that the overhead is as minimal as possible, a C extension module is used for performance critical components. An automatic fallback to a pure Python implementation is also provided where a target system does not have a compiler to allow the C extension to be compiled.

## Features

- **Universal decorators** that work with functions, methods, classmethods, staticmethods, and classes
- **Transparent object proxies** for advanced wrapping scenarios
- **Monkey patching utilities** for safe runtime modifications
- **C extension** for optimal performance with Python fallback
- **Comprehensive introspection preservation** (signatures, annotations, etc.)
- **Thread-safe decorator implementations**

## Installation

```bash
pip install wrapt
```

## Quick Start

### Basic Decorator

```python
import wrapt

@wrapt.decorator
def pass_through(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@pass_through
def function():
    pass
```

### Decorator with Arguments

```python
import wrapt

def with_arguments(myarg1, myarg2):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        print(f"Arguments: {myarg1}, {myarg2}")
        return wrapped(*args, **kwargs)
    return wrapper

@with_arguments(1, 2)
def function():
    pass
```

### Universal Decorator

```python
import inspect
import wrapt

@wrapt.decorator
def universal(wrapped, instance, args, kwargs):
    if instance is None:
        if inspect.isclass(wrapped):
            # Decorator was applied to a class
            print("Decorating a class")
        else:
            # Decorator was applied to a function or staticmethod
            print("Decorating a function")
    else:
        if inspect.isclass(instance):
            # Decorator was applied to a classmethod
            print("Decorating a classmethod")
        else:
            # Decorator was applied to an instancemethod
            print("Decorating an instance method")
    
    return wrapped(*args, **kwargs)
```

## Documentation

For comprehensive documentation, examples, and advanced usage patterns, visit:

**[wrapt.readthedocs.io](https://wrapt.readthedocs.io/)**

## Workshops

Two sets of guided, hands-on workshops run in JupyterLab and check your work as you go. Neither needs anything installed.

### Python decorators

[![Launch in your browser](https://img.shields.io/badge/launch-jupyterlite-F37626?logo=jupyter&logoColor=white)](https://grahamdumpleton.github.io/decorator-workshops/lab/index.html)
[![Launch on Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/GrahamDumpleton/decorator-workshops/main?urlpath=lab)
[![Open in GitHub Codespaces](https://img.shields.io/badge/launch-codespaces-579ACA?logo=github&logoColor=white)](https://codespaces.new/GrahamDumpleton/decorator-workshops?quickstart=1)

[decorator-workshops](https://github.com/GrahamDumpleton/decorator-workshops) teaches Python decorators using only the standard library, from what a decorator is through to writing your own for functions, methods, classes and coroutines. It is the place to start if decorators are new to you, and covers the ground the wrapt workshops build on. The badges above start the workshops in your browser with no account or server at all, on [mybinder.org](https://mybinder.org), or in [GitHub Codespaces](https://github.com/features/codespaces). The repository README explains each option and how to run the workshops locally.

### wrapt

[![Launch on Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/GrahamDumpleton/wrapt-workshops/main?urlpath=lab)
[![Open in GitHub Codespaces](https://img.shields.io/badge/launch-codespaces-579ACA?logo=github&logoColor=white)](https://codespaces.new/GrahamDumpleton/wrapt-workshops?quickstart=1)

[wrapt-workshops](https://github.com/GrahamDumpleton/wrapt-workshops) holds three collections of workshops on wrapt itself: writing decorators with wrapt, monkey patching with wrapt, and object proxies with wrapt, each shown beside the standard library way of doing the same thing. The badges above start them on [mybinder.org](https://mybinder.org) or in [GitHub Codespaces](https://github.com/features/codespaces). The repository README explains each option and how to run the workshops locally.

## Related Projects

If the monkey patching side of wrapt is what brought you here, also look at [wrapture](https://github.com/GrahamDumpleton/wrapture). It is a sibling project built on the monkey patching machinery of wrapt, and provides a higher level API on top of it. A clean lifecycle and behaviour vocabulary over `wrap_object()` lets you point at a method by name and stub it, fail it, transform its arguments or result, or wrap it with a decorator, then remove it again. On top of that sit unit testing, where the real code runs and how calls flowed through it is recorded and asserted on, and ad-hoc tracing, where a running application emits a structured call tree with no code changes, with export to OpenTelemetry. The [wrapture documentation](https://wrapture.readthedocs.io/) has the details, and [wrapture-workshops](https://github.com/GrahamDumpleton/wrapture-workshops) has guided workshops of its own.

## Supported Python Versions

- Python 3.9+
- CPython
- PyPy

## Contributing

We welcome contributions! This is a pretty casual process - if you're interested in suggesting changes, improvements, or have found a bug, please reach out via the [GitHub issue tracker](https://github.com/GrahamDumpleton/wrapt/issues/). Whether it's a small fix, new feature idea, or just a question about how something works, feel free to start a discussion.

Please note that wrapt is now considered a mature project. We're not expecting any significant new developments or major feature additions. The primary focus is on ensuring that the package continues to work correctly with newer Python versions and maintaining compatibility as the Python ecosystem evolves. Higher level functionality is being developed in [wrapture](https://github.com/GrahamDumpleton/wrapture) rather than here.

### Testing

For information about running tests, including Python version-specific test conventions and available test commands, see [TESTING.md](TESTING.md).

## License

This project is licensed under the BSD License - see the [LICENSE](LICENSE) file for details.

## Links

- **Documentation**: https://wrapt.readthedocs.io/
- **PyPI**: https://pypi.python.org/pypi/wrapt
- **Issues**: https://github.com/GrahamDumpleton/wrapt/issues/
- **Changelog**: https://wrapt.readthedocs.io/en/latest/changes.html

## Related Blog Posts

This repository also contains a series of blog posts explaining the design and implementation of wrapt:

- [How you implemented your Python decorator is wrong](blog/01-how-you-implemented-your-python-decorator-is-wrong.md)
- [The interaction between decorators and descriptors](blog/02-the-interaction-between-decorators-and-descriptors.md)
- [Implementing a factory for creating decorators](blog/03-implementing-a-factory-for-creating-decorators.md)
- [Implementing a universal decorator](blog/04-implementing-a-universal-decorator.md)
- [Decorators which accept arguments](blog/05-decorators-which-accept-arguments.md)
- [Maintaining decorator state using a class](blog/06-maintaining-decorator-state-using-a-class.md)
- [The missing synchronized decorator](blog/07-the-missing-synchronized-decorator.md)
- [The synchronized decorator as context manager](blog/08-the-synchronized-decorator-as-context-manager.md)
- [Performance overhead of using decorators](blog/09-performance-overhead-of-using-decorators.md)
- [Performance overhead when applying decorators to methods](blog/10-performance-overhead-when-applying-decorators-to-methods.md)
- [Safely applying monkey patches in Python](blog/11-safely-applying-monkey-patches-in-python.md)
- [Using wrapt to support testing of software](blog/12-using-wrapt-to-support-testing-of-software.md)
- [Ordering issues when monkey patching in Python](blog/13-ordering-issues-when-monkey-patching-in-python.md)
- [Automatic patching of Python applications](blog/14-automatic-patching-of-python-applications.md)
