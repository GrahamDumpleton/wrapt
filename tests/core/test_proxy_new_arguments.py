"""Tests that the proxy classes accept extra arguments to __new__().

A derived class may add arguments to __init__(), in which case Python passes
the same arguments to __new__(). A derived class may also override __new__()
and pass on everything it was given to the base class, which it must do when
deriving from AutoObjectProxy as that needs the wrapped object in __new__().
Both must behave the same with the C extension and the pure Python
implementation. The pure Python BaseObjectProxy previously had no __new__()
of its own, so once a derived class overrode __new__() the call fell through
to object.__new__() which rejects extra arguments.
"""

import unittest

import wrapt


class _NewArgumentsTests:
    # The proxy class being derived from, and the first positional argument
    # its constructor takes, which for LazyObjectProxy is a callback.

    proxy_base = None

    def first_argument(self):
        return [1, 2, 3]

    def test_init_extra_positional_argument(self):
        class Proxy(self.proxy_base):
            def __init__(self, wrapped, label):
                super().__init__(wrapped)
                self._self_label = label

        proxy = Proxy(self.first_argument(), "label")

        self.assertEqual(proxy.__wrapped__, [1, 2, 3])
        self.assertEqual(proxy._self_label, "label")

    def test_init_extra_keyword_argument(self):
        class Proxy(self.proxy_base):
            def __init__(self, wrapped, *, label):
                super().__init__(wrapped)
                self._self_label = label

        proxy = Proxy(self.first_argument(), label="label")

        self.assertEqual(proxy.__wrapped__, [1, 2, 3])
        self.assertEqual(proxy._self_label, "label")

    def test_new_passes_arguments_through(self):
        class Proxy(self.proxy_base):
            def __new__(cls, wrapped, label):
                return super().__new__(cls, wrapped, label)

            def __init__(self, wrapped, label):
                super().__init__(wrapped)
                self._self_label = label

        proxy = Proxy(self.first_argument(), "label")

        self.assertIsInstance(proxy, Proxy)
        self.assertEqual(proxy.__wrapped__, [1, 2, 3])
        self.assertEqual(proxy._self_label, "label")

    def test_new_passes_keyword_arguments_through(self):
        class Proxy(self.proxy_base):
            def __new__(cls, wrapped, *, label):
                return super().__new__(cls, wrapped, label=label)

            def __init__(self, wrapped, *, label):
                super().__init__(wrapped)
                self._self_label = label

        proxy = Proxy(self.first_argument(), label="label")

        self.assertIsInstance(proxy, Proxy)
        self.assertEqual(proxy.__wrapped__, [1, 2, 3])
        self.assertEqual(proxy._self_label, "label")

    def test_new_without_arguments(self):
        # The form the Python documentation recommends for a class whose
        # base is a plain Python class must keep working too, except for
        # AutoObjectProxy which needs the wrapped object in __new__() to
        # build the class for the instance. LazyObjectProxy has a default
        # for its callback so is not affected.

        class Proxy(self.proxy_base):
            def __new__(cls, wrapped):
                return super().__new__(cls)

        if self.proxy_base is wrapt.AutoObjectProxy:
            with self.assertRaises(TypeError):
                Proxy(self.first_argument())
        else:
            proxy = Proxy(self.first_argument())

            self.assertIsInstance(proxy, Proxy)
            self.assertEqual(proxy.__wrapped__, [1, 2, 3])


class TestBaseObjectProxyNewArguments(_NewArgumentsTests, unittest.TestCase):
    proxy_base = wrapt.BaseObjectProxy


class TestObjectProxyNewArguments(_NewArgumentsTests, unittest.TestCase):
    proxy_base = wrapt.ObjectProxy


class TestCallableObjectProxyNewArguments(_NewArgumentsTests, unittest.TestCase):
    proxy_base = wrapt.CallableObjectProxy


class TestAutoObjectProxyNewArguments(_NewArgumentsTests, unittest.TestCase):
    proxy_base = wrapt.AutoObjectProxy

    def test_dunder_methods_still_injected(self):
        # The extra arguments must not stop the class for the instance
        # being built from the wrapped object.

        class Proxy(wrapt.AutoObjectProxy):
            def __init__(self, wrapped, label):
                super().__init__(wrapped)
                self._self_label = label

        proxy = Proxy([1, 2, 3], "label")

        self.assertTrue(hasattr(proxy, "__iter__"))
        self.assertEqual(list(proxy), [1, 2, 3])


class TestLazyObjectProxyNewArguments(_NewArgumentsTests, unittest.TestCase):
    proxy_base = wrapt.LazyObjectProxy

    def first_argument(self):
        return lambda: [1, 2, 3]

    def test_interface_with_extra_arguments(self):
        # The interface keyword must still reach __new__() alongside an
        # argument added by the derived class.

        class Proxy(wrapt.LazyObjectProxy):
            def __init__(self, callback, label, *, interface=...):
                super().__init__(callback, interface=interface)
                self._self_label = label

        proxy = Proxy(lambda: [1, 2, 3], "label", interface=list)

        self.assertTrue(hasattr(proxy, "__iter__"))
        self.assertEqual(list(proxy), [1, 2, 3])
        self.assertEqual(proxy._self_label, "label")
