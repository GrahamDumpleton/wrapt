"""The `with_doc` decorator: override the docstring that introspection tools
see for a wrapped callable without mutating the wrapped function itself.
Accepts the docstring directly, or a factory that derives it from the
wrapped function at decoration time.

This is the companion of `with_signature`, which overrides the signature in
the same way. Assigning to `__doc__` on an ordinary wrapt wrapper writes
through to the wrapped function, because `__doc__` on every proxy delegates
to the wrapped object, so a wrapper carrying its own docstring is the only
way to change what is reported without touching the wrapped function.
"""

from .__wrapt__ import BoundFunctionWrapper, FunctionWrapper

# Marker for a wrapper which carries no docstring override, so that `__doc__`
# keeps delegating to the wrapped function. Distinct from None, which is a
# legitimate docstring override.

_NO_DOC_OVERRIDE = object()

# The `__doc__` property for a function wrapper which may carry a docstring
# override in its `_self_doc` slot. The wrapper class must assign this to
# `__doc__` in its own class body, rather than inherit it from a mixin, and
# set `_self_doc` in its `__init__()`, to `_NO_DOC_OVERRIDE` when there is
# none.
#
# Both the pure Python metaclass and the C extension attribute hooks
# recognise a `__doc__` descriptor defined by a derived class and consult it
# in place of the default delegation to the wrapped object. It has to be in
# the class dictionary of the wrapper class itself though, because `pydoc`
# reads `__doc__` using `object.__getattribute__()` to avoid inherited
# docstrings, and with the C extension that bypasses the attribute hooks and
# would otherwise find the copy of the wrapped function's docstring which is
# held in the instance dictionary.
#
# Without an override, assignment and deletion write through to the wrapped
# function as they do for any other wrapt wrapper. With one, assignment
# replaces the override and deletion removes it, restoring delegation to the
# wrapped function.


def _get_doc(self):
    doc = self._self_doc
    if doc is _NO_DOC_OVERRIDE:
        return self.__wrapped__.__doc__
    return doc


def _set_doc(self, value):
    if self._self_doc is _NO_DOC_OVERRIDE:
        self.__wrapped__.__doc__ = value
    else:
        self._self_doc = value


def _del_doc(self):
    if self._self_doc is _NO_DOC_OVERRIDE:
        del self.__wrapped__.__doc__
    else:
        self._self_doc = _NO_DOC_OVERRIDE


_DOC_PROPERTY = property(_get_doc, _set_doc, _del_doc)

# The `__doc__` property for the bound wrapper of a function wrapper which
# may carry a docstring override, reading it from the parent. A bound
# wrapper is read only, as `__doc__` of a bound method is.


def _get_bound_doc(self):
    doc = self._self_parent._self_doc
    if doc is _NO_DOC_OVERRIDE:
        return self.__wrapped__.__doc__
    return doc


_BOUND_DOC_PROPERTY = property(_get_bound_doc)


class _BoundDocFunctionWrapper(BoundFunctionWrapper):
    __doc__ = _BOUND_DOC_PROPERTY


class _DocFunctionWrapper(FunctionWrapper):
    __doc__ = _DOC_PROPERTY

    __bound_function_wrapper__ = _BoundDocFunctionWrapper

    def __init__(self, wrapped, wrapper, doc):
        super().__init__(wrapped, wrapper)
        self._self_doc = doc


def with_doc(wrapped=None, /, *, doc=None, factory=None):
    """Override the docstring of a wrapped callable.

    Exactly one of `doc` or `factory` must be supplied:

    - `doc`: the docstring to report.
    - `factory`: a callable `factory(wrapped)` invoked at decoration time
      that returns the docstring to report.

    The resulting wrapper reports the override as its `__doc__`, and so it
    is what `help()` and `pydoc` display. The wrapped function is not
    mutated, and assigning to `__doc__` on the wrapper replaces the override
    rather than writing through to the wrapped function. Calling behaviour
    is unchanged.
    """

    if doc is None and factory is None:
        raise TypeError("with_doc requires one of doc= or factory=")
    if doc is not None and factory is not None:
        raise TypeError("with_doc accepts only one of doc= or factory=")

    def _decorator(wrapped):
        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        if factory is not None:
            resolved = factory(wrapped)
        else:
            resolved = doc

        return _DocFunctionWrapper(wrapped, _wrapper, resolved)

    if wrapped is None:
        return _decorator
    return _decorator(wrapped)
