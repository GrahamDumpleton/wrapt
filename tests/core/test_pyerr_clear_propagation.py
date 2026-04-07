"""Tests that non-AttributeError exceptions raised during attribute lookups
inside the wrapt C extension are propagated to the caller rather than being
silently swallowed by an unguarded ``PyErr_Clear()``.

Each test corresponds to a specific call site in ``src/wrapt/_wrappers.c``
where ``PyErr_Clear()`` is invoked without first checking that the pending
exception is actually an ``AttributeError``. The site is identified in the
test docstring by its enclosing C function name and the attribute lookup
that should be allowed to propagate non-``AttributeError`` exceptions.

The pure-Python implementation in ``src/wrapt/wrappers.py`` uses Python-level
``try/except AttributeError`` (or ``getattr(..., default)`` / ``hasattr(...)``,
both of which only suppress ``AttributeError`` on Python 3.2+), so the same
tests pass against the pure-Python implementation. A handful of sites have
no equivalent attribute lookup in the pure-Python code path at all (notably
the eager ``__module__`` / ``__doc__`` caching done by the C ``raw_init``);
those tests are skipped on the pure-Python implementation since there is
nothing there to exercise.
"""

import unittest

import wrapt
import wrapt.__wrapt__

USING_C_EXTENSION = wrapt.__wrapt__._using_c_extension

c_extension_only = unittest.skipUnless(
    USING_C_EXTENSION,
    "exercises a code path that only exists in the C extension",
)


CANARY_MESSAGE = "pyerr_clear_canary"


class _Canary(RuntimeError):
    """Distinct exception type so tests cannot accidentally match an
    unrelated ``RuntimeError`` raised by surrounding machinery."""


def _raise_canary():
    raise _Canary(CANARY_MESSAGE)


# ---------------------------------------------------------------------------
# Helpers for building objects whose attribute lookups raise non-AttributeError
# ---------------------------------------------------------------------------


def _make_raising_attr_class(target):
    """Build a class whose ``__getattribute__`` raises ``_Canary`` for the
    named attribute and otherwise behaves normally."""

    class RaisingAttr:
        def __getattribute__(self, name):
            if name == target:
                _raise_canary()
            return object.__getattribute__(self, name)

    RaisingAttr.__name__ = "RaisingAttr_" + target.strip("_")
    return RaisingAttr


class RaisingStartswithStr(str):
    """A ``str`` subclass whose ``startswith`` raises ``_Canary``. The
    wrapt setattro code paths invoke ``name.startswith('_self_')`` to
    decide where to route the assignment; if that call raises something
    other than ``AttributeError`` it must propagate, not be cleared."""

    def startswith(self, *args, **kwargs):  # type: ignore[override]
        _raise_canary()


# ---------------------------------------------------------------------------
# raw_init / uninitialized error
# ---------------------------------------------------------------------------


class TestRawInitAttributeLookups(unittest.TestCase):

    @c_extension_only
    def test_raw_init_module_propagates(self):
        """C: ``WraptObjectProxy_raw_init`` looking up ``__module__`` on the
        wrapped object during eager attribute caching."""

        cls = _make_raising_attr_class("__module__")
        with self.assertRaises(_Canary):
            wrapt.ObjectProxy(cls())

    @c_extension_only
    def test_raw_init_doc_propagates(self):
        """C: ``WraptObjectProxy_raw_init`` looking up ``__doc__`` on the
        wrapped object during eager attribute caching."""

        cls = _make_raising_attr_class("__doc__")
        with self.assertRaises(_Canary):
            wrapt.ObjectProxy(cls())

    def test_raw_init_wrapped_factory_propagates(self):
        """C: ``WraptObjectProxy_raw_init`` looking up ``__wrapped_factory__``
        on the proxy when the wrapped argument is ``None``."""

        class Proxy(wrapt.ObjectProxy):
            @property
            def __wrapped_factory__(self):
                _raise_canary()

        with self.assertRaises(_Canary):
            Proxy(None)


# ---------------------------------------------------------------------------
# set_wrapped __wrapped_setattr_fixups__
# ---------------------------------------------------------------------------


class TestSetWrappedFixups(unittest.TestCase):

    def test_set_wrapped_fixups_propagates(self):
        """C: ``WraptObjectProxy_set_wrapped`` looking up
        ``__wrapped_setattr_fixups__`` on the proxy after assigning to
        ``__wrapped__``."""

        class Proxy(wrapt.ObjectProxy):
            @property
            def __wrapped_setattr_fixups__(self):
                _raise_canary()

        proxy = Proxy(object())
        with self.assertRaises(_Canary):
            proxy.__wrapped__ = object()


# ---------------------------------------------------------------------------
# mro_entries
# ---------------------------------------------------------------------------


class TestMroEntries(unittest.TestCase):

    def test_mro_entries_propagates(self):
        """C: ``WraptObjectProxy_mro_entries`` looking up ``__mro_entries__``
        on the wrapped object."""

        class Wrapped:
            def __getattribute__(self, name):
                if name == "__mro_entries__":
                    _raise_canary()
                return object.__getattribute__(self, name)

        proxy = wrapt.ObjectProxy(Wrapped())

        def _build():
            class _C(proxy):  # type: ignore[misc]
                pass

        with self.assertRaises(_Canary):
            _build()


# ---------------------------------------------------------------------------
# setattro startswith
# ---------------------------------------------------------------------------


class TestSetattroStartswith(unittest.TestCase):

    def test_object_proxy_setattro_startswith_propagates(self):
        """C: ``WraptObjectProxy_setattro`` calling ``name.startswith('_self_')``
        to decide where to route the assignment."""

        proxy = wrapt.ObjectProxy(object())
        weird_name = RaisingStartswithStr("anything")
        with self.assertRaises(_Canary):
            type(proxy).__setattr__(proxy, weird_name, 1)

    def test_bound_function_wrapper_setattro_startswith_propagates(self):
        """C: ``WraptBoundFunctionWrapper_setattro`` calling
        ``name.startswith('_self_')`` to decide where to route the
        assignment."""

        @wrapt.decorator
        def deco(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Owner:
            @deco
            def method(self):
                return 1

        bound = Owner().method  # BoundFunctionWrapper instance
        weird_name = RaisingStartswithStr("anything")
        with self.assertRaises(_Canary):
            type(bound).__setattr__(bound, weird_name, 1)


# ---------------------------------------------------------------------------
# FunctionWrapper init/call __self__ lookup
# ---------------------------------------------------------------------------


class _ToggleSelfCallable:
    """Callable whose ``__self__`` lookup is benign during construction
    (raises ``AttributeError`` so the wrapt binding-detection code falls
    through to ``binding = "callable"``) but starts raising ``_Canary``
    once ``armed`` is set. Used to test attribute lookup paths that fire
    *after* the wrapper has been constructed."""

    def __init__(self):
        object.__setattr__(self, "armed", False)

    @property
    def __self__(self):
        if object.__getattribute__(self, "armed"):
            _raise_canary()
        raise AttributeError("__self__")

    def __call__(self, *args, **kwargs):
        return args, kwargs


class _AlwaysRaisingSelfCallable:
    """Callable whose ``__self__`` always raises ``_Canary``. Used to drive
    the lookup that happens inside ``WraptFunctionWrapper_init``."""

    @property
    def __self__(self):
        _raise_canary()

    def __call__(self, *args, **kwargs):
        return args, kwargs


class TestFunctionWrapperSelfLookups(unittest.TestCase):

    def test_function_wrapper_init_self_propagates(self):
        """C: ``WraptFunctionWrapper_init`` looking up ``__self__`` on the
        wrapped callable while determining the binding type."""

        callable_ = _AlwaysRaisingSelfCallable()

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with self.assertRaises(_Canary):
            wrapt.FunctionWrapper(callable_, _wrapper)

    def test_function_wrapper_call_self_propagates(self):
        """C: ``WraptFunctionWrapperBase_call`` looking up ``__self__`` on the
        wrapped callable while routing the call for classmethod-like
        bindings."""

        callable_ = _ToggleSelfCallable()

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapper = wrapt.FunctionWrapper(callable_, _wrapper)
        object.__setattr__(callable_, "armed", True)

        with self.assertRaises(_Canary):
            wrapper()

    def test_bound_function_wrapper_call_self_propagates(self):
        """C: ``WraptBoundFunctionWrapper_call`` looking up ``__self__`` on the
        wrapped descriptor result.

        Drives the ``else`` branch of ``BoundFunctionWrapper.__call__`` that
        handles classmethod/staticmethod-style bindings by looking up
        ``__self__`` on the descriptor result. We construct a real bound
        wrapper for a classmethod, then swap the bound wrapper's
        ``__wrapped__`` for an object whose ``__self__`` raises ``_Canary``.
        """

        @wrapt.decorator
        def deco(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Owner:
            @deco
            @classmethod
            def cm(cls, *args, **kwargs):
                return cls, args, kwargs

        bound = Owner.cm  # BoundFunctionWrapper instance for the classmethod

        callable_ = _AlwaysRaisingSelfCallable()
        # Replace the bound wrapper's wrapped object so the call-time
        # __self__ lookup hits our raising property. We use object.__setattr__
        # via the proxy machinery: assigning __wrapped__ goes through
        # WraptObjectProxy_set_wrapped which is exactly the path we want.
        bound.__wrapped__ = callable_

        with self.assertRaises(_Canary):
            bound()


# ---------------------------------------------------------------------------
# descr_get __bound_function_wrapper__ lookup
# ---------------------------------------------------------------------------


class TestDescrGetBoundType(unittest.TestCase):

    def test_descr_get_bound_type_propagates(self):
        """C: ``WraptFunctionWrapperBase_descr_get`` looking up
        ``__bound_function_wrapper__`` on the wrapper.

        The lookup only fires for a user subclass of ``FunctionWrapper`` (the
        base type short-circuits to the default ``BoundFunctionWrapper``).
        We define a subclass whose ``__bound_function_wrapper__`` property
        raises and trigger the descriptor protocol via ``__get__``."""

        class RaisingFunctionWrapper(wrapt.FunctionWrapper):
            @property
            def __bound_function_wrapper__(self):
                _raise_canary()

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        def _target(self):
            return self

        wrapper = RaisingFunctionWrapper(_target, _wrapper)

        class Instance:
            pass

        with self.assertRaises(_Canary):
            wrapper.__get__(Instance(), Instance)


# ---------------------------------------------------------------------------
# __set_name__ lookup on wrapped
# ---------------------------------------------------------------------------


class TestSetNameLookup(unittest.TestCase):

    def test_set_name_propagates(self):
        """C: ``WraptFunctionWrapperBase_set_name`` looking up ``__set_name__``
        on the wrapped object."""

        class Wrapped:
            def __getattribute__(self, name):
                if name == "__set_name__":
                    _raise_canary()
                return object.__getattribute__(self, name)

            def __call__(self, *args, **kwargs):
                return args, kwargs

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapper = wrapt.FunctionWrapper(Wrapped(), _wrapper)

        class Owner:
            pass

        with self.assertRaises(_Canary):
            wrapper.__set_name__(Owner, "name")


# ---------------------------------------------------------------------------
# __subclasscheck__ wrapped lookup on the subclass argument
# ---------------------------------------------------------------------------


class TestSubclassCheckWrappedLookup(unittest.TestCase):

    def test_subclasscheck_wrapped_propagates(self):
        """C: ``WraptFunctionWrapperBase_subclasscheck`` looking up
        ``__wrapped__`` on the candidate subclass."""

        class WrappedClass:
            pass

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapper = wrapt.FunctionWrapper(WrappedClass, _wrapper)

        class RaisingWrappedMeta(type):
            @property
            def __wrapped__(cls):
                _raise_canary()

        class Probe(metaclass=RaisingWrappedMeta):
            pass

        with self.assertRaises(_Canary):
            wrapper.__subclasscheck__(Probe)


# ---------------------------------------------------------------------------
# Attribute lookup fall-through paths in getattro / __getattr__
# ---------------------------------------------------------------------------
#
# The following tests pin the behaviour of the two attribute-lookup paths
# that intentionally swallow ``AttributeError`` in order to fall through to
# a secondary lookup (``__getattr__`` delegation on ``ObjectProxy``, parent
# delegation on ``BoundFunctionWrapper``). For each path there are two
# tests:
#
#   * an ``AttributeError`` raised from the primary lookup must be caught
#     and the fall-back code path must run (delegation works);
#   * any other exception must propagate to the caller unchanged rather
#     than being treated as "attribute not found".


class TestAttributeLookupFallback(unittest.TestCase):

    def test_object_proxy_getattro_attribute_error_falls_through(self):
        """C: ``WraptObjectProxy_getattro`` clears ``AttributeError`` from
        ``PyObject_GenericGetAttr`` and delegates via ``__getattr__``."""

        class Wrapped:
            pass

        wrapped = Wrapped()
        wrapped.foo = "wrapped_foo"

        proxy = wrapt.ObjectProxy(wrapped)

        # ``foo`` is not on the proxy type or instance dict, so the generic
        # lookup raises ``AttributeError``; the guarded clear allows
        # ``__getattr__`` to delegate to the wrapped object.
        self.assertEqual(proxy.foo, "wrapped_foo")

    def test_object_proxy_getattro_other_exception_propagates(self):
        """C: ``WraptObjectProxy_getattro`` must NOT clear non-``AttributeError``
        raised by ``PyObject_GenericGetAttr``."""

        class RaisingDescriptor:
            def __get__(self, obj, objtype=None):  # noqa: ARG002
                _raise_canary()

        class Proxy(wrapt.ObjectProxy):
            boom = RaisingDescriptor()

        proxy = Proxy(object())

        # ``boom`` is found on the proxy type as a data descriptor; its
        # ``__get__`` raises ``_Canary``. The guarded clear must let it
        # escape rather than falling through to ``__getattr__``.
        with self.assertRaises(_Canary):
            proxy.boom

    def test_bound_function_wrapper_getattr_attribute_error_falls_through(self):
        """C: ``WraptBoundFunctionWrapper_getattr`` clears ``AttributeError``
        from the parent lookup and delegates to the base proxy ``__getattr__``."""

        @wrapt.decorator
        def deco(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Owner:
            @deco
            def method(self):
                return 1

            method.extra_attr = "parent_value"  # type: ignore[attr-defined]

        bound = Owner().method

        # ``extra_attr`` is not on the bound wrapper itself, so its
        # ``__getattr__`` looks it up on the parent ``FunctionWrapper`` where
        # we stashed it. This is the AttributeError-clears-then-fall-through
        # path on the parent side: the bound wrapper's parent lookup
        # succeeds, no fallback to wrapped is needed, and the value is
        # returned.
        self.assertEqual(bound.extra_attr, "parent_value")

    def test_bound_function_wrapper_getattr_other_exception_propagates(self):
        """C: ``WraptBoundFunctionWrapper_getattr`` must NOT clear
        non-``AttributeError`` raised by the parent lookup."""

        class RaisingFunctionWrapper(wrapt.FunctionWrapper):
            @property
            def boom(self):
                _raise_canary()

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        def _target(self):
            return self

        parent = RaisingFunctionWrapper(_target, _wrapper)

        class Instance:
            pass

        bound = parent.__get__(Instance(), Instance)

        # ``boom`` is not on the bound wrapper, so its ``__getattr__`` looks
        # it up on the parent. The parent lookup hits the ``boom`` property
        # which raises ``_Canary``. The guarded clear must let it escape
        # rather than falling through to the wrapped object's attribute
        # lookup.
        with self.assertRaises(_Canary):
            bound.boom


if __name__ == "__main__":
    unittest.main()
