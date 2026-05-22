"""Tests for ``FunctionWrapper.__get__`` with native C descriptors (slot
wrappers, method descriptors, getset descriptors, member descriptors) and
Python descriptors (property, classmethod, staticmethod) at both class-level
and instance-level access.
"""

import io
import socket
import types
import unittest

import _pickle

import wrapt
import wrapt.__wrapt__

# ``wrapt.FunctionWrapper`` resolves to the C type when the extension is
# loaded, so the pure-Python class is only reachable via ``wrapt.wrappers``.
from wrapt.wrappers import FunctionWrapper as PurePythonFunctionWrapper

USING_C_EXTENSION = wrapt.__wrapt__._using_c_extension

c_extension_only = unittest.skipUnless(
    USING_C_EXTENSION,
    "exercises a code path that only exists in the C extension",
)


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


class TestSlotWrapperDescriptor(unittest.TestCase):
    # ``wrapper_descriptor`` — the descriptor type for C-level type slots,
    # e.g. ``_pickle.Unpickler.load`` (displayed as
    # ``<slot wrapper 'load' of '_pickle.Unpickler' objects>``).
    # A C extension type is used so the slot is not a plain Python function.

    @c_extension_only
    def test_class_level_get(self):
        wrapped = _wrap(_pickle.Unpickler.load)
        result = wrapped.__get__(None, _pickle.Unpickler)
        self.assertIsNotNone(result.__doc__)

    @c_extension_only
    def test_subclass_class_level_get(self):
        class Sub(_pickle.Unpickler):
            pass

        wrapped = _wrap(_pickle.Unpickler.load)
        result = wrapped.__get__(None, Sub)
        self.assertIsNotNone(result.__doc__)

    @c_extension_only
    def test_instance_level_get(self):
        wrapped = _wrap(_pickle.Unpickler.load)
        instance = _pickle.Unpickler(io.BytesIO())
        bound = wrapped.__get__(instance, _pickle.Unpickler)
        self.assertIsNotNone(bound)


class TestMethodDescriptor(unittest.TestCase):
    @c_extension_only
    def test_class_level_get(self):
        wrapped = _wrap(str.upper)
        result = wrapped.__get__(None, str)
        self.assertIsNotNone(result.__doc__)

    @c_extension_only
    def test_subclass_class_level_get(self):
        class SubStr(str):
            pass

        wrapped = _wrap(str.upper)
        result = wrapped.__get__(None, SubStr)
        self.assertIsNotNone(result.__doc__)

    @c_extension_only
    def test_instance_level_call(self):
        wrapped = _wrap(str.upper)
        bound = wrapped.__get__("hello", str)
        self.assertEqual(bound(), "HELLO")


class TestClassMethodDescriptor(unittest.TestCase):
    # ``classmethod_descriptor`` — classmethod descriptors ignore ``obj``
    # entirely, so class-level and instance-level access behave identically.

    @c_extension_only
    def test_class_level_get(self):
        wrapped = _wrap(dict.fromkeys)
        bound = wrapped.__get__(None, dict)
        self.assertEqual(bound(["a", "b"], 1), {"a": 1, "b": 1})


class TestGetSetDescriptor(unittest.TestCase):
    @staticmethod
    def _descriptor():
        # Resolve via __dict__ so the lookup doesn't run the descriptor itself.
        descr = type.__dict__["__name__"]
        assert isinstance(descr, types.GetSetDescriptorType)
        return descr

    @c_extension_only
    def test_class_level_get(self):
        wrapped = _wrap(self._descriptor())
        result = wrapped.__get__(None, type)
        self.assertIsInstance(result, types.GetSetDescriptorType)

    @c_extension_only
    def test_instance_level_get(self):
        wrapped = _wrap(self._descriptor())
        self.assertEqual(wrapped.__get__(str, type), "str")


class TestMemberDescriptor(unittest.TestCase):
    @c_extension_only
    def test_class_level_get(self):
        descr = _find_member_descriptor()
        if descr is None:
            self.skipTest("no member_descriptor available in this interpreter")
        wrapped = _wrap(descr)
        result = wrapped.__get__(None, socket.socket)
        self.assertIsInstance(result, types.MemberDescriptorType)


class TestProperty(unittest.TestCase):
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
    def test_class_level_get(self):
        class C:
            @classmethod
            def make(cls):
                return cls

        wrapped = _wrap(C.__dict__["make"])
        self.assertIs(wrapped.__get__(None, C)(), C)


class TestStaticMethod(unittest.TestCase):
    def test_class_level_get(self):
        class C:
            @staticmethod
            def make():
                return 42

        wrapped = _wrap(C.__dict__["make"])
        self.assertEqual(wrapped.__get__(None, C)(), 42)


class TestCustomDescriptor(unittest.TestCase):
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
    @c_extension_only
    def test_wrapped_slot_wrapper_via_subclass(self):
        class Sub(_pickle.Unpickler):
            pass

        wrapped = _wrap(_pickle.Unpickler.load)
        Sub.load = wrapped
        self.assertIsNotNone(Sub.load.__doc__)

    @c_extension_only
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


class TestPurePythonWraptPath(unittest.TestCase):
    def test_slot_wrapper(self):
        wrapped = PurePythonFunctionWrapper(_pickle.Unpickler.load, _wrapper)
        result = wrapped.__get__(None, _pickle.Unpickler)
        self.assertIsNotNone(result.__doc__)

    def test_method_descriptor(self):
        wrapped = PurePythonFunctionWrapper(str.upper, _wrapper)
        result = wrapped.__get__(None, str)
        self.assertIsNotNone(result.__doc__)


if __name__ == "__main__":
    unittest.main()
