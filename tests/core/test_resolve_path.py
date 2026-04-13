import unittest

from wrapt.patches import resolve_path


class TestResolvePath(unittest.TestCase):

    def test_module_as_string(self):
        parent, attribute, original = resolve_path("os.path", "join")
        import os.path

        self.assertIs(parent, os.path)
        self.assertEqual(attribute, "join")
        self.assertIs(original, os.path.join)

    def test_module_as_object(self):
        import os.path

        parent, attribute, original = resolve_path(os.path, "join")
        self.assertIs(parent, os.path)
        self.assertEqual(attribute, "join")
        self.assertIs(original, os.path.join)

    def test_simple_attribute(self):
        import os

        parent, attribute, original = resolve_path(os, "getcwd")
        self.assertIs(parent, os)
        self.assertEqual(attribute, "getcwd")
        self.assertIs(original, os.getcwd)

    def test_dotted_path(self):
        import os.path

        parent, attribute, original = resolve_path("os", "path.join")
        self.assertIs(parent, os.path)
        self.assertEqual(attribute, "join")
        self.assertIs(original, os.path.join)

    def test_class_attribute(self):
        class MyClass:
            value = 42

        parent, attribute, original = resolve_path(MyClass, "value")

        # resolve_path walks the class __dict__ directly, so we get the raw
        # value rather than a bound descriptor.

        self.assertIs(parent, MyClass)
        self.assertEqual(attribute, "value")
        self.assertEqual(original, 42)

    def test_class_method(self):
        class MyClass:
            def method(self):
                pass

        parent, attribute, original = resolve_path(MyClass, "method")
        self.assertIs(parent, MyClass)
        self.assertEqual(attribute, "method")

        # Should get the raw function from __dict__, not a bound method.

        self.assertIs(original, MyClass.__dict__["method"])

    def test_inherited_attribute(self):
        class Base:
            def method(self):
                pass

        class Child(Base):
            pass

        parent, attribute, original = resolve_path(Child, "method")

        # The method is defined on Base, so resolve_path should find it
        # by walking the MRO.

        self.assertIs(parent, Child)
        self.assertEqual(attribute, "method")
        self.assertIs(original, Base.__dict__["method"])

    def test_instance_attribute(self):
        class MyClass:
            def __init__(self):
                self.value = 99

        instance = MyClass()
        parent, attribute, original = resolve_path(instance, "value")
        self.assertIs(parent, instance)
        self.assertEqual(attribute, "value")
        self.assertEqual(original, 99)

    def test_nonexistent_attribute(self):
        import os

        with self.assertRaises(AttributeError):
            resolve_path(os, "nonexistent_attribute_xyz")

    def test_nonexistent_dotted_path(self):
        import os

        with self.assertRaises(AttributeError):
            resolve_path(os, "path.nonexistent_attribute_xyz")
