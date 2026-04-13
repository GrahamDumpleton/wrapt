import unittest
import sys

import wrapt
from wrapt.importer import _post_import_hooks


class TestDeferredWrapFunctionWrapper(unittest.TestCase):

    def setUp(self):
        super(TestDeferredWrapFunctionWrapper, self).setUp()

        sys.modules.pop("colorsys", None)
        _post_import_hooks.pop("colorsys", None)

    def test_deferred_wrap_before_import(self):
        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append(True)
            return wrapped(*args, **kwargs)

        result = wrapt.wrap_function_wrapper("colorsys?", "rgb_to_hsv", wrapper)

        self.assertIsNone(result)
        self.assertEqual(len(called), 0)

        import colorsys

        # The wrapper should now be applied.

        colorsys.rgb_to_hsv(0.2, 0.4, 0.6)

        self.assertEqual(len(called), 1)

    def test_deferred_wrap_after_import(self):
        import colorsys

        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append(True)
            return wrapped(*args, **kwargs)

        result = wrapt.wrap_function_wrapper("colorsys?", "rgb_to_hsv", wrapper)

        # Module already imported, should wrap immediately.

        self.assertIsNotNone(result)

        colorsys.rgb_to_hsv(0.2, 0.4, 0.6)

        self.assertEqual(len(called), 1)

    def test_deferred_wrap_returns_none(self):
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        result = wrapt.wrap_function_wrapper("colorsys?", "rgb_to_hsv", wrapper)

        self.assertIsNone(result)

    def test_immediate_wrap_returns_wrapper(self):
        import colorsys

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        result = wrapt.wrap_function_wrapper("colorsys?", "rgb_to_hsv", wrapper)

        self.assertIsNotNone(result)

    def test_without_question_mark_imports_immediately(self):
        self.assertNotIn("colorsys", sys.modules)

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper("colorsys", "rgb_to_hsv", wrapper)

        # Module should have been imported immediately.

        self.assertIn("colorsys", sys.modules)


class TestDeferredPatchFunctionWrapper(unittest.TestCase):

    def setUp(self):
        super(TestDeferredPatchFunctionWrapper, self).setUp()

        sys.modules.pop("colorsys", None)
        _post_import_hooks.pop("colorsys", None)

    def test_deferred_patch_before_import(self):
        called = []

        @wrapt.patch_function_wrapper("colorsys?", "rgb_to_hsv")
        def wrapper(wrapped, instance, args, kwargs):
            called.append(True)
            return wrapped(*args, **kwargs)

        self.assertEqual(len(called), 0)

        import colorsys

        # The wrapper should now be applied.

        colorsys.rgb_to_hsv(0.2, 0.4, 0.6)

        self.assertEqual(len(called), 1)

    def test_deferred_patch_after_import(self):
        import colorsys

        called = []

        @wrapt.patch_function_wrapper("colorsys?", "rgb_to_hsv")
        def wrapper(wrapped, instance, args, kwargs):
            called.append(True)
            return wrapped(*args, **kwargs)

        colorsys.rgb_to_hsv(0.2, 0.4, 0.6)

        self.assertEqual(len(called), 1)

    def test_deferred_patch_returns_wrapper_function(self):
        # When deferred, the decorator should return the original wrapper
        # function so it remains usable.

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapper = wrapt.patch_function_wrapper("colorsys?", "rgb_to_hsv")(_wrapper)

        self.assertIs(wrapper, _wrapper)

    def test_immediate_patch_returns_wrapper_function(self):
        # When applied immediately, the decorator should also return the
        # original wrapper function.

        import colorsys

        def _wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapper = wrapt.patch_function_wrapper("colorsys?", "rgb_to_hsv")(_wrapper)

        self.assertIs(wrapper, _wrapper)

    def test_deferred_patch_with_enabled(self):
        called = []

        enable = False

        def enabled():
            return enable

        @wrapt.patch_function_wrapper("colorsys?", "rgb_to_hsv", enabled=enabled)
        def wrapper(wrapped, instance, args, kwargs):
            called.append(True)
            return wrapped(*args, **kwargs)

        import colorsys

        colorsys.rgb_to_hsv(0.2, 0.4, 0.6)

        self.assertEqual(len(called), 0)

        enable = True

        colorsys.rgb_to_hsv(0.2, 0.4, 0.6)

        self.assertEqual(len(called), 1)

    def test_without_question_mark_imports_immediately(self):
        self.assertNotIn("colorsys", sys.modules)

        @wrapt.patch_function_wrapper("colorsys", "rgb_to_hsv")
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        # Module should have been imported immediately.

        self.assertIn("colorsys", sys.modules)


if __name__ == "__main__":
    unittest.main()
