import unittest

import abc

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
    in test_inheritance_py37.py for decorated classes.
    """

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


if __name__ == "__main__":
    unittest.main()
