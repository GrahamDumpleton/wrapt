"""Tests for ``FunctionWrapper.__get__`` against the full range of descriptor
types found in CPython: the native C descriptor types (slot wrappers, method
descriptors, classmethod descriptors, getset descriptors, member descriptors)
as well as the Python-level descriptors (property, classmethod, staticmethod,
and user-defined descriptors). Each is exercised at class-level access (where
the C descriptor protocol passes ``NULL`` for the instance argument of the
``tp_descr_get`` slot) and at instance-level access where applicable.

These cases verify that ``FunctionWrapper.__get__`` forwards the instance
argument it receives through to the wrapped descriptor's ``__get__`` slot
without modification. Native CPython descriptor types other than the
descriptor for ordinary Python functions distinguish between ``NULL`` and
``Py_None`` for the instance argument and raise ``TypeError`` if ``Py_None``
is passed where ``NULL`` is expected, so any future change which substitutes
``Py_None`` for ``NULL`` before invoking the wrapped descriptor is detected
here. The same tests are executed against the C and pure Python wrapper
implementations.
"""

import io
import platform
import socket
import types
import unittest

import wrapt

# The native CPython descriptor types tested below (slot wrappers, method
# descriptors, classmethod descriptors, getset descriptors, member
# descriptors) are CPython implementation details. PyPy implements its
# descriptor protocol differently and does not always expose the same
# distinct types, and modules such as ``_pickle`` which are used here to
# obtain a C-extension backed slot wrapper are also absent. The tests
# guarding behaviour of these CPython specific descriptors are skipped
# on PyPy. The bug they guard against was specific to the wrapt C
# extension which is not built on PyPy in any case.

IS_PYPY = platform.python_implementation() == "PyPy"

skip_on_pypy = unittest.skipIf(
    IS_PYPY,
    "exercises CPython specific native descriptor types not present on PyPy",
)

if not IS_PYPY:
    import _pickle  # type: ignore[import-not-found]


def _wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


def _wrap(target):
    return wrapt.FunctionWrapper(target, _wrapper)


def _find_member_descriptor():
    # ``socket.socket`` uses ``__slots__`` and reliably exposes
    # ``MemberDescriptorType`` attributes on CPython.
    for value in vars(socket.socket).values():
        if isinstance(value, types.MemberDescriptorType):
            return value
    return None


@skip_on_pypy
class TestSlotWrapperDescriptor(unittest.TestCase):
    # ``wrapper_descriptor`` is the descriptor type for C-level type slots
    # such as ``_pickle.Unpickler.load`` (displayed as
    # ``<slot wrapper 'load' of '_pickle.Unpickler' objects>``). A C
    # extension type is used so the slot wrapper is backed by a C function
    # rather than a Python function.

    def test_class_level_get(self):
        wrapped = _wrap(_pickle.Unpickler.load)
        result = wrapped.__get__(None, _pickle.Unpickler)
        self.assertIsNotNone(result.__doc__)

    def test_subclass_class_level_get(self):
        class Sub(_pickle.Unpickler):
            pass

        wrapped = _wrap(_pickle.Unpickler.load)
        result = wrapped.__get__(None, Sub)
        self.assertIsNotNone(result.__doc__)

    def test_instance_level_get(self):
        wrapped = _wrap(_pickle.Unpickler.load)
        instance = _pickle.Unpickler(io.BytesIO())
        bound = wrapped.__get__(instance, _pickle.Unpickler)
        self.assertIsNotNone(bound)


@skip_on_pypy
class TestMethodDescriptor(unittest.TestCase):
    # ``method_descriptor`` is the descriptor type for built-in methods
    # defined in C such as ``str.upper``.

    def test_class_level_get(self):
        wrapped = _wrap(str.upper)
        result = wrapped.__get__(None, str)
        self.assertIsNotNone(result.__doc__)

    def test_subclass_class_level_get(self):
        class SubStr(str):
            pass

        wrapped = _wrap(str.upper)
        result = wrapped.__get__(None, SubStr)
        self.assertIsNotNone(result.__doc__)

    def test_instance_level_call(self):
        wrapped = _wrap(str.upper)
        bound = wrapped.__get__("hello", str)
        self.assertEqual(bound(), "HELLO")


@skip_on_pypy
class TestClassMethodDescriptor(unittest.TestCase):
    # ``classmethod_descriptor`` is the descriptor type for C-level
    # classmethods such as ``dict.fromkeys``. A classmethod descriptor
    # ignores the instance argument entirely, so class-level and
    # instance-level access behave identically.

    def test_class_level_get(self):
        wrapped = _wrap(dict.fromkeys)
        bound = wrapped.__get__(None, dict)
        self.assertEqual(bound(["a", "b"], 1), {"a": 1, "b": 1})


@skip_on_pypy
class TestGetSetDescriptor(unittest.TestCase):
    # ``getset_descriptor`` is the descriptor type generated for attributes
    # defined via ``PyGetSetDef`` in C, such as ``type.__name__``.

    @staticmethod
    def _descriptor():
        # Resolve via __dict__ so the lookup doesn't run the descriptor itself.
        descr = type.__dict__["__name__"]
        assert isinstance(descr, types.GetSetDescriptorType)
        return descr

    def test_class_level_get(self):
        # Class-level access must return the descriptor itself rather than
        # invoking the getter.
        wrapped = _wrap(self._descriptor())
        result = wrapped.__get__(None, type)
        self.assertIsInstance(result, types.GetSetDescriptorType)

    def test_instance_level_get(self):
        # Instance-level access must invoke the getter and return the value
        # of the attribute on the instance.
        wrapped = _wrap(self._descriptor())
        self.assertEqual(wrapped.__get__(str, type), "str")


@skip_on_pypy
class TestMemberDescriptor(unittest.TestCase):
    # ``member_descriptor`` is the descriptor type generated for slots
    # defined via ``PyMemberDef`` in C and for entries in ``__slots__``.

    def test_class_level_get(self):
        descr = _find_member_descriptor()
        if descr is None:
            self.skipTest("no member_descriptor available in this interpreter")
        wrapped = _wrap(descr)
        result = wrapped.__get__(None, socket.socket)
        self.assertIsInstance(result, types.MemberDescriptorType)


class TestProperty(unittest.TestCase):
    # ``property`` is the Python-level descriptor for read/write computed
    # attributes. Class-level access returns the property object itself
    # whereas instance-level access invokes the getter.

    def test_class_level_get(self):
        class C:
            @property
            def value(self):
                return 42

        wrapped = _wrap(C.__dict__["value"])
        result = wrapped.__get__(None, C)
        self.assertIsInstance(result, property)

    def test_instance_level_get(self):
        class C:
            @property
            def value(self):
                return 42

        wrapped = _wrap(C.__dict__["value"])
        self.assertEqual(wrapped.__get__(C(), C), 42)


class TestClassMethod(unittest.TestCase):
    # ``classmethod`` is the Python-level descriptor which binds the owning
    # class as the first argument. The wrapper must forward to the
    # classmethod's ``__get__`` so that calling the bound result invokes
    # the underlying function with the class.

    def test_class_level_get(self):
        class C:
            @classmethod
            def make(cls):
                return cls

        wrapped = _wrap(C.__dict__["make"])
        self.assertIs(wrapped.__get__(None, C)(), C)


class TestStaticMethod(unittest.TestCase):
    # ``staticmethod`` is the Python-level descriptor which returns the
    # underlying function unchanged. The wrapper must forward to the
    # staticmethod's ``__get__`` so that calling the bound result invokes
    # the function with no implicit first argument.

    def test_class_level_get(self):
        class C:
            @staticmethod
            def make():
                return 42

        wrapped = _wrap(C.__dict__["make"])
        self.assertEqual(wrapped.__get__(None, C)(), 42)


class TestCustomDescriptor(unittest.TestCase):
    # A user-defined Python descriptor receives the arguments
    # ``FunctionWrapper.__get__`` was called with. This case asserts on the
    # exact ``(instance, owner)`` tuple seen by the inner descriptor's
    # ``__get__`` so that any modification of the instance argument by the
    # wrapper between caller and wrapped descriptor is detected.

    def test_class_level_get_forwards_to_descriptor_get(self):
        calls = []

        class Descriptor:
            def __get__(self, instance, owner):
                calls.append((instance, owner))
                return self

        descr = Descriptor()
        wrapped = _wrap(descr)
        result = wrapped.__get__(None, str)
        self.assertEqual(calls, [(None, str)])
        self.assertIs(result.__wrapped__, descr)


class TestSubclassAttributeAccess(unittest.TestCase):
    # A wrapped descriptor installed on a subclass must remain accessible
    # via class attribute access on that subclass. This is the realistic
    # monkey patching pattern used by instrumentation libraries: take an
    # existing descriptor off a parent class, wrap it, and install the
    # wrapper as an attribute of a subclass.

    @skip_on_pypy
    def test_wrapped_slot_wrapper_via_subclass(self):
        class Sub(_pickle.Unpickler):
            pass

        wrapped = _wrap(_pickle.Unpickler.load)
        Sub.load = wrapped
        self.assertIsNotNone(Sub.load.__doc__)

    @skip_on_pypy
    def test_wrapped_dict_slot_via_subclass(self):
        class SubDict(dict):
            pass

        wrapped = _wrap(dict.__dict__["__contains__"])
        SubDict.__contains__ = wrapped
        self.assertIsNotNone(SubDict.__contains__)

    def test_wrapped_python_method_via_subclass(self):
        class Parent:
            def method(self):
                return "parent"

        class Child(Parent):
            pass

        Child.method = _wrap(Parent.__dict__["method"])
        self.assertEqual(Child().method(), "parent")


if __name__ == "__main__":
    unittest.main()
