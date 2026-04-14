import unittest

import wrapt


class Target:
    def __init__(self, name):
        self.name = name


class TestSelfDict(unittest.TestCase):

    def test_returns_dict(self):
        # __self_dict__ should return a dict object distinct from the
        # wrapped object's __dict__.

        target = Target("test")
        proxy = wrapt.ObjectProxy(target)

        self.assertIsInstance(proxy.__self_dict__, dict)
        self.assertIsNot(proxy.__self_dict__, target.__dict__)

    def test_contains_self_prefixed_attributes(self):
        # Attributes set with the _self_ prefix on a subclass should
        # appear in __self_dict__.

        class MyProxy(wrapt.ObjectProxy):
            def __init__(self, wrapped):
                super().__init__(wrapped)
                self._self_tag = "example"
                self._self_count = 42

        proxy = MyProxy(Target("test"))

        self.assertEqual(proxy.__self_dict__["_self_tag"], "example")
        self.assertEqual(proxy.__self_dict__["_self_count"], 42)

    def test_does_not_contain_wrapped_attributes(self):
        # Attributes of the wrapped object should not appear in
        # __self_dict__.

        target = Target("test")
        proxy = wrapt.ObjectProxy(target)

        self.assertNotIn("name", proxy.__self_dict__)

    def test_vars_still_returns_wrapped_dict(self):
        # Adding __self_dict__ should not change the behaviour of
        # vars() — it should still return the wrapped object's dict.

        target = Target("test")
        proxy = wrapt.ObjectProxy(target)

        self.assertEqual(vars(proxy), vars(target))

    def test_mutations_affect_proxy(self):
        # __self_dict__ should be the live instance dictionary — setting
        # a key in it should be observable as an attribute on the proxy.

        class MyProxy(wrapt.ObjectProxy):
            pass

        proxy = MyProxy(Target("test"))
        proxy.__self_dict__["_self_new"] = 99

        self.assertEqual(proxy._self_new, 99)

    def test_attribute_assignment_visible_in_self_dict(self):
        # Conversely, setting a _self_ attribute on the proxy should be
        # visible through __self_dict__.

        class MyProxy(wrapt.ObjectProxy):
            pass

        proxy = MyProxy(Target("test"))
        proxy._self_tag = "hello"

        self.assertEqual(proxy.__self_dict__["_self_tag"], "hello")

    def test_wrapping_object_without_dict(self):
        # Wrapping an object that has no __dict__ (e.g. an int) should
        # still allow __self_dict__ to work.

        class MyProxy(wrapt.ObjectProxy):
            def __init__(self, wrapped):
                super().__init__(wrapped)
                self._self_tag = "example"

        proxy = MyProxy(1234)

        self.assertIsInstance(proxy.__self_dict__, dict)
        self.assertEqual(proxy.__self_dict__["_self_tag"], "example")

    def test_works_on_plain_object_proxy(self):
        # __self_dict__ should be accessible on a plain ObjectProxy
        # (not a subclass) with no _self_ attributes.

        target = Target("test")
        proxy = wrapt.ObjectProxy(target)

        self.assertIsInstance(proxy.__self_dict__, dict)

    def test_works_on_deep_subclass(self):
        # A subclass of a subclass of ObjectProxy should also expose
        # __self_dict__.

        class LevelOne(wrapt.ObjectProxy):
            def __init__(self, wrapped):
                super().__init__(wrapped)
                self._self_one = 1

        class LevelTwo(LevelOne):
            def __init__(self, wrapped):
                super().__init__(wrapped)
                self._self_two = 2

        proxy = LevelTwo(Target("test"))

        self.assertEqual(proxy.__self_dict__["_self_one"], 1)
        self.assertEqual(proxy.__self_dict__["_self_two"], 2)

    def test_custom_dict_property_preserved(self):
        # If a subclass defines its own __dict__ property, the metaclass
        # must not overwrite it with the default delegating property.

        class IntrospectableProxy(wrapt.ObjectProxy):
            def __init__(self, wrapped):
                super().__init__(wrapped)
                self._self_tag = "example"

            @property
            def __dict__(self):
                result = self.__wrapped__.__dict__.copy()
                result.update(self.__self_dict__)
                return result

        target = Target("test")
        proxy = IntrospectableProxy(target)

        combined = vars(proxy)
        self.assertEqual(combined["name"], "test")
        self.assertEqual(combined["_self_tag"], "example")

    def test_self_dict_is_read_only(self):
        # __self_dict__ should not be settable as an attribute on the
        # proxy — it is exposed as a read-only descriptor.

        proxy = wrapt.ObjectProxy(Target("test"))

        with self.assertRaises(AttributeError):
            proxy.__self_dict__ = {}


if __name__ == "__main__":
    unittest.main()
