import unittest

import abc
import platform
import sys

import wrapt


class Base:
    pass


class Child(Base):
    pass


class GrandChild(Child):
    pass


class TestIssubclassProxyOnRight(unittest.TestCase):
    """Tests for issubclass(real_class, proxy_of_class).

    When the proxy wraps a type and appears on the right side of issubclass(),
    Python calls type(proxy).__subclasscheck__(proxy, subclass). The
    __subclasscheck__ on ObjectProxy delegates to the wrapped type.
    """

    def test_same_class(self):
        proxy = wrapt.ObjectProxy(Child)
        self.assertTrue(issubclass(Child, proxy))

    def test_subclass(self):
        proxy = wrapt.ObjectProxy(Base)
        self.assertTrue(issubclass(Child, proxy))

    def test_grandchild(self):
        proxy = wrapt.ObjectProxy(Base)
        self.assertTrue(issubclass(GrandChild, proxy))

    def test_not_subclass(self):
        proxy = wrapt.ObjectProxy(Child)
        self.assertFalse(issubclass(Base, proxy))

    def test_unrelated_class(self):
        class Unrelated:
            pass

        proxy = wrapt.ObjectProxy(Child)
        self.assertFalse(issubclass(Unrelated, proxy))

    def test_subclass_is_also_proxy(self):
        proxy_base = wrapt.ObjectProxy(Base)
        proxy_child = wrapt.ObjectProxy(Child)
        self.assertTrue(issubclass(proxy_child, proxy_base))

    def test_proxy_in_tuple(self):
        proxy = wrapt.ObjectProxy(Base)
        self.assertTrue(issubclass(Child, (proxy,)))

    def test_proxy_in_tuple_mixed(self):
        proxy = wrapt.ObjectProxy(Child)

        class Unrelated:
            pass

        self.assertTrue(issubclass(GrandChild, (Unrelated, proxy)))


class TestIssubclassProxyOnLeft(unittest.TestCase):
    """Tests for issubclass(proxy_of_class, real_class).

    When the proxy wraps a type and appears on the left side of issubclass(),
    the check is driven by the right-hand side's metaclass __subclasscheck__.
    CPython's default implementation walks proxy.__bases__ looking for the
    right-hand class. It finds ancestors but the identity check for the
    wrapped class itself fails because proxy is not the wrapped class.
    """

    def test_ancestor(self):
        proxy = wrapt.ObjectProxy(Child)
        self.assertTrue(issubclass(proxy, Base))

    def test_object(self):
        proxy = wrapt.ObjectProxy(Child)
        self.assertTrue(issubclass(proxy, object))

    def test_same_class(self):
        proxy = wrapt.ObjectProxy(Child)
        # KNOWN LIMITATION: issubclass(X, X) normally returns True via an
        # identity check (X is X). But proxy is not Child, and Child is not
        # in its own __bases__, so the walk doesn't find it either. The
        # proxy cannot control the right-hand side's __subclasscheck__
        # behavior, so this cannot be fixed.
        self.assertFalse(issubclass(proxy, Child))

    def test_not_subclass(self):
        proxy = wrapt.ObjectProxy(Base)
        self.assertFalse(issubclass(proxy, Child))


class TestIssubclassProxyOnLeftWithABC(unittest.TestCase):
    """Tests for issubclass(proxy_of_class, abc_class).

    When the right-hand side uses ABCMeta, its C-level __subclasscheck__
    strictly requires the left argument to be a real class. A proxy is not
    a class, so this raises TypeError. This is the same limitation documented
    in test_inheritance.py for decorated classes.
    """

    @unittest.skipIf(
        platform.python_implementation() == "PyPy",
        "PyPy uses the pure-Python abc implementation, which lacks the strict "
        "PyType_Check guard in CPython's _abc C extension and so does not "
        "raise TypeError here.",
    )
    def test_abc_raises_type_error(self):
        class AbstractBase(metaclass=abc.ABCMeta):
            @abc.abstractmethod
            def method(self):
                pass

        class Concrete(AbstractBase):
            def method(self):
                pass

        proxy = wrapt.ObjectProxy(Concrete)
        # KNOWN LIMITATION: ABCMeta's C-level __subclasscheck__ rejects
        # non-class arguments with TypeError. The proxy cannot influence
        # this.
        with self.assertRaises(TypeError):
            issubclass(proxy, AbstractBase)


class TestIsinstanceProxyOnRight(unittest.TestCase):
    """Tests for isinstance(instance, proxy_of_class).

    When the proxy wraps a type and appears on the right side of isinstance(),
    Python calls type(proxy).__instancecheck__(proxy, instance). The
    __instancecheck__ on ObjectProxy delegates to the wrapped type.
    """

    def test_direct_instance(self):
        proxy = wrapt.ObjectProxy(Child)
        self.assertTrue(isinstance(Child(), proxy))

    def test_subclass_instance(self):
        proxy = wrapt.ObjectProxy(Base)
        self.assertTrue(isinstance(Child(), proxy))

    def test_grandchild_instance(self):
        proxy = wrapt.ObjectProxy(Base)
        self.assertTrue(isinstance(GrandChild(), proxy))

    def test_not_instance(self):
        proxy = wrapt.ObjectProxy(Child)
        self.assertFalse(isinstance(Base(), proxy))

    def test_proxied_instance_against_proxy_type(self):
        proxy_type = wrapt.ObjectProxy(Child)
        proxy_instance = wrapt.ObjectProxy(Child())
        self.assertTrue(isinstance(proxy_instance, proxy_type))


class TestIssubclassBothProxied(unittest.TestCase):
    """Tests where both arguments to issubclass() are proxied types."""

    def test_child_of_base(self):
        proxy_child = wrapt.ObjectProxy(Child)
        proxy_base = wrapt.ObjectProxy(Base)
        self.assertTrue(issubclass(proxy_child, proxy_base))

    def test_same_class(self):
        proxy_a = wrapt.ObjectProxy(Child)
        proxy_b = wrapt.ObjectProxy(Child)
        self.assertTrue(issubclass(proxy_a, proxy_b))

    def test_not_subclass(self):
        proxy_child = wrapt.ObjectProxy(Child)
        proxy_base = wrapt.ObjectProxy(Base)
        self.assertFalse(issubclass(proxy_base, proxy_child))


class TestPathLikeProtocol(unittest.TestCase):
    """Tests pinning the documented behaviour of object proxies with the
    os.PathLike protocol. The base object proxy deliberately does not
    implement __fspath__, as its presence on the proxy type would cause
    every proxy to be classified as path like by code branching on
    isinstance(obj, os.PathLike). See the section on os.PathLike in
    docs/issues.rst. If these tests start failing on a new Python
    version, the interaction between the proxy and the protocol has
    changed and the documentation needs to be revisited.
    """

    def test_isinstance_pathlike_true_for_wrapped_path(self):
        # ABCMeta.__instancecheck__ consults the instance __class__,
        # which the proxy delegates to the wrapped object, so the
        # classification reflects the wrapped object.

        import os
        import pathlib

        proxy = wrapt.ObjectProxy(pathlib.PurePath("/path/to/file"))

        self.assertTrue(isinstance(proxy, os.PathLike))

    def test_isinstance_pathlike_false_for_wrapped_non_path(self):
        import os

        proxy = wrapt.ObjectProxy(42)

        self.assertFalse(isinstance(proxy, os.PathLike))

    def test_fspath_fails_for_wrapped_path(self):
        # os.fspath() looks up __fspath__ on the actual type of the
        # proxy, not via __class__, so it fails even though the
        # isinstance() check above says the proxy is path like.

        import os
        import pathlib

        proxy = wrapt.ObjectProxy(pathlib.PurePath("/path/to/file"))

        self.assertRaises(TypeError, os.fspath, proxy)

    def test_fspath_via_instance_access(self):
        # Instance level access still forwards via __getattr__.

        import os
        import pathlib

        instance = pathlib.PurePath("/path/to/file")
        proxy = wrapt.ObjectProxy(instance)

        self.assertEqual(proxy.__fspath__(), os.fspath(instance))


class TestBufferProtocol(unittest.TestCase):
    """Tests pinning the documented behaviour of object proxies with the
    buffer protocol. The base object proxy deliberately does not
    implement __buffer__ or __release_buffer__, as their presence on
    the proxy type would cause every proxy to be classified as
    bytes-like. See the section on the buffer protocol in
    docs/issues.rst. If these tests start failing on a new Python
    version, the interaction between the proxy and the protocol has
    changed and the documentation needs to be revisited.
    """

    def test_memoryview_fails_for_wrapped_bytes_like(self):
        # The buffer protocol is looked up on the actual type of the
        # proxy at the C level, so a proxy around a bytes-like object
        # cannot be used as a buffer.

        proxy = wrapt.ObjectProxy(bytearray(b"data"))

        self.assertRaises(TypeError, memoryview, proxy)

    @unittest.skipIf(sys.version_info < (3, 12), "requires Python 3.12+")
    def test_isinstance_buffer_true_for_wrapped_bytes_like(self):
        # ABCMeta.__instancecheck__ consults the instance __class__,
        # which the proxy delegates to the wrapped object, so the
        # classification reflects the wrapped object even though
        # memoryview() on the same proxy fails.

        import collections.abc

        proxy = wrapt.ObjectProxy(bytearray(b"data"))

        self.assertTrue(isinstance(proxy, collections.abc.Buffer))

    @unittest.skipIf(sys.version_info < (3, 12), "requires Python 3.12+")
    def test_isinstance_buffer_false_for_wrapped_non_buffer(self):
        import collections.abc

        proxy = wrapt.ObjectProxy(42)

        self.assertFalse(isinstance(proxy, collections.abc.Buffer))

    @unittest.skipIf(sys.version_info < (3, 12), "requires Python 3.12+")
    def test_buffer_proxy_subclass(self):
        # The recipe documented in docs/issues.rst for opting in to the
        # buffer protocol on a derived proxy class.

        class BufferProxy(wrapt.BaseObjectProxy):
            def __buffer__(self, flags):
                return self.__wrapped__.__buffer__(flags)

            def __release_buffer__(self, view):
                view.release()

        proxy = BufferProxy(bytearray(b"world"))

        view = memoryview(proxy)

        self.assertEqual(bytes(view), b"world")

        view[0] = ord("W")

        # Exporter side effects apply through the proxy, so the wrapped
        # bytearray cannot be resized while the view is outstanding.

        self.assertRaises(BufferError, proxy.append, ord("!"))

        view.release()

        proxy.append(ord("!"))

        self.assertEqual(proxy, bytearray(b"World!"))

    @unittest.skipIf(sys.version_info < (3, 12), "requires Python 3.12+")
    def test_buffer_proxy_subclass_immutable(self):
        # Immutable exporters such as bytes define __buffer__ but not
        # __release_buffer__, which is why the recipe releases the view
        # it is given rather than delegating.

        class BufferProxy(wrapt.BaseObjectProxy):
            def __buffer__(self, flags):
                return self.__wrapped__.__buffer__(flags)

            def __release_buffer__(self, view):
                view.release()

        proxy = BufferProxy(b"data")

        view = memoryview(proxy)

        self.assertEqual(bytes(view), b"data")

        view.release()


if __name__ == "__main__":
    unittest.main()
