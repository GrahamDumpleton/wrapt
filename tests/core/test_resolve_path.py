import unittest

import wrapt
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

    def test_dynamic_attribute(self):
        # An attribute served dynamically rather than from a __dict__ is
        # still returned via the getattr() fallback.

        class Meta(type):
            def __getattr__(cls, name):
                if name == "dynamic":
                    return 42
                raise AttributeError(name)

        class MyClass(metaclass=Meta):
            pass

        parent, attribute, original = resolve_path(MyClass, "dynamic")
        self.assertIs(parent, MyClass)
        self.assertEqual(attribute, "dynamic")
        self.assertEqual(original, 42)


class TestResolvePathErrors(unittest.TestCase):

    def test_exceptions_exported(self):
        from wrapt.exceptions import PathResolutionError, TargetModuleNotFoundError

        self.assertIs(wrapt.PathResolutionError, PathResolutionError)
        self.assertIs(wrapt.TargetModuleNotFoundError, TargetModuleNotFoundError)
        self.assertIn("PathResolutionError", wrapt.__all__)
        self.assertIn("TargetModuleNotFoundError", wrapt.__all__)

    def test_nonexistent_attribute_error(self):
        import os

        with self.assertRaises(wrapt.PathResolutionError) as cm:
            resolve_path(os, "nonexistent_attribute_xyz")

        # The low-level error is preserved as __cause__ and the message
        # names the failing attribute and the target.

        self.assertIsInstance(cm.exception.__cause__, AttributeError)
        self.assertNotIsInstance(cm.exception.__cause__, wrapt.PathResolutionError)
        self.assertIn("'nonexistent_attribute_xyz'", str(cm.exception))
        self.assertIn("os", str(cm.exception))

    def test_nonexistent_attribute_compatibility(self):
        # Existing code catching AttributeError must keep working.

        import os

        try:
            resolve_path(os, "nonexistent_attribute_xyz")
        except AttributeError:
            pass
        else:
            self.fail("PathResolutionError was not raised")

    def test_nonexistent_dotted_path_error(self):
        # A failure at an intermediate segment names both the failing
        # segment and the full dotted path.

        import os

        with self.assertRaises(wrapt.PathResolutionError) as cm:
            resolve_path(os, "nosuch.attribute")

        self.assertIn("'nosuch'", str(cm.exception))
        self.assertIn("'nosuch.attribute'", str(cm.exception))

    def test_nonexistent_final_segment_error(self):
        # A failure at the final segment of a dotted path names that
        # segment and the full dotted path.

        import os

        with self.assertRaises(wrapt.PathResolutionError) as cm:
            resolve_path(os, "path.nonexistent_attribute_xyz")

        self.assertIn("'nonexistent_attribute_xyz'", str(cm.exception))
        self.assertIn("'path.nonexistent_attribute_xyz'", str(cm.exception))

    def test_nonexistent_module_error(self):
        with self.assertRaises(wrapt.TargetModuleNotFoundError) as cm:
            resolve_path("nonexistent_module_xyz", "function")

        # The low-level error is preserved as __cause__ and the message
        # names the module and the attribute path being resolved.

        self.assertIsInstance(cm.exception.__cause__, ModuleNotFoundError)
        self.assertIn("'nonexistent_module_xyz'", str(cm.exception))
        self.assertIn("'function'", str(cm.exception))

    def test_nonexistent_module_compatibility(self):
        # Existing code catching ImportError must keep working.

        try:
            resolve_path("nonexistent_module_xyz", "function")
        except ImportError:
            pass
        else:
            self.fail("TargetModuleNotFoundError was not raised")

    def test_wrap_object_error(self):
        # The wrap functions built on resolve_path surface the same
        # upgraded errors.

        import os

        with self.assertRaises(wrapt.PathResolutionError):
            wrapt.wrap_function_wrapper(
                os, "nonexistent_attribute_xyz", lambda *args: None
            )

        with self.assertRaises(wrapt.TargetModuleNotFoundError):
            wrapt.wrap_function_wrapper(
                "nonexistent_module_xyz", "function", lambda *args: None
            )
