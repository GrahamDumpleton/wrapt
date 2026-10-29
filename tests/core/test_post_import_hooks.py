import importlib
import pathlib
import sys
import tempfile
import threading
import types
import unittest

import wrapt
from wrapt.importer import _post_import_hooks


class TestPostImportHooks(unittest.TestCase):

    def setUp(self):
        super(TestPostImportHooks, self).setUp()

        # So we can import 'this' and test post-import hooks multiple times
        # below in the context of a single Python process, remove 'this' from
        # sys.modules and post import hooks.

        sys.modules.pop("this", None)
        _post_import_hooks.pop("this", None)

    def test_before_import(self):
        invoked = []

        @wrapt.when_imported("this")
        def hook_this(module):
            self.assertEqual(module.__name__, "this")
            invoked.append(1)

        self.assertEqual(len(invoked), 0)

        import this

        self.assertEqual(len(invoked), 1)

    def test_after_import(self):
        invoked = []

        import this

        self.assertEqual(len(invoked), 0)

        @wrapt.when_imported("this")
        def hook_this(module):
            self.assertEqual(module.__name__, "this")
            invoked.append(1)

        self.assertEqual(len(invoked), 1)

    def test_hook_registered_during_import_waits_for_module_body(self):
        name = "_wrapt_partial_import"
        registration = name + "_registration"
        invoked = []

        def first_hook(module):
            invoked.append(module.value)
            wrapt.register_post_import_hook(
                lambda loaded: invoked.append(loaded.value), name
            )

        with tempfile.TemporaryDirectory() as directory:
            pathlib.Path(directory, name + ".py").write_text(
                "import " + registration + "\nvalue = 42\n", encoding="utf-8"
            )
            pathlib.Path(directory, registration + ".py").write_text(
                "import wrapt\n"
                "@wrapt.when_imported('" + name + "')\n"
                "def hook(module):\n"
                "    module.hook_value = module.value\n",
                encoding="utf-8",
            )
            sys.path.insert(0, directory)
            try:
                wrapt.register_post_import_hook(first_hook, name)
                module = importlib.import_module(name)
                self.assertEqual(module.hook_value, 42)
                self.assertEqual(invoked, [42, 42])
                self.assertNotIn(name, _post_import_hooks)
            finally:
                sys.path.remove(directory)
                sys.path_importer_cache.pop(directory, None)
                sys.modules.pop(name, None)
                sys.modules.pop(registration, None)
                _post_import_hooks.pop(name, None)

    def test_before_and_after_import(self):
        invoked_one = []
        invoked_two = []

        @wrapt.when_imported("this")
        def hook_this_one(module):
            self.assertEqual(module.__name__, "this")
            invoked_one.append(1)

        self.assertEqual(len(invoked_one), 0)
        self.assertEqual(len(invoked_two), 0)

        import this

        self.assertEqual(len(invoked_one), 1)
        self.assertEqual(len(invoked_two), 0)

        @wrapt.when_imported("this")
        def hook_this_two(module):
            self.assertEqual(module.__name__, "this")
            invoked_two.append(1)

        self.assertEqual(len(invoked_one), 1)
        self.assertEqual(len(invoked_two), 1)

    def test_hook_registered_from_another_thread_waits_for_module_body(self):
        name = "_wrapt_threaded_import"
        control_name = name + "_control"
        control = types.ModuleType(control_name)
        control.entered = threading.Event()
        control.release = threading.Event()
        invoked = []
        errors = []

        def import_module():
            try:
                importlib.import_module(name)
            except BaseException as exc:
                errors.append(exc)

        with tempfile.TemporaryDirectory() as directory:
            pathlib.Path(directory, name + ".py").write_text(
                "import " + control_name + " as control\n"
                "control.entered.set()\n"
                "assert control.release.wait(5)\n"
                "value = 42\n",
                encoding="utf-8",
            )
            sys.path.insert(0, directory)
            sys.modules[control_name] = control
            thread = threading.Thread(target=import_module)
            try:
                wrapt.register_post_import_hook(
                    lambda module: invoked.append(module.value), name
                )
                thread.start()
                self.assertTrue(control.entered.wait(5))
                wrapt.register_post_import_hook(
                    lambda module: invoked.append(module.value), name
                )
                self.assertEqual(invoked, [])
            finally:
                control.release.set()
                thread.join(timeout=5)
                sys.path.remove(directory)
                sys.path_importer_cache.pop(directory, None)
                sys.modules.pop(name, None)
                sys.modules.pop(control_name, None)
                _post_import_hooks.pop(name, None)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(invoked, [42, 42])

    def test_remove_from_sys_modules(self):
        invoked = []

        @wrapt.when_imported("this")
        def hook_this(module):
            self.assertEqual(module.__name__, "this")
            invoked.append(1)

        import this

        self.assertEqual(len(invoked), 1)

        del sys.modules["this"]
        wrapt.register_post_import_hook(hook_this, "this")
        import this

        self.assertEqual(len(invoked), 2)

    def test_import_deadlock_1(self):
        # This tries to verify that we haven't created a deadlock situation when
        # code executed from a post module import, for a module that has already
        # been imported, creates a thread which in turn attempts to register
        # another import hook.

        import this

        @wrapt.when_imported("this")
        def hook_this(module):
            def worker():
                @wrapt.when_imported("xxx")
                def hook_xxx(module):
                    pass

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=10)

            self.assertFalse(thread.is_alive())

        del sys.modules["this"]

    def test_import_deadlock_2(self):
        # This tries to verify that we haven't created a deadlock situation when
        # code executed from a post module import, for a module that has not yet
        # been imported, creates a thread which in turn attempts to register
        # another import hook.

        @wrapt.when_imported("this")
        def hook_this(module):
            def worker():
                @wrapt.when_imported("xxx")
                def hook_xxx(module):
                    pass

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=10)

            self.assertFalse(thread.is_alive())

        import this

        del sys.modules["this"]

    def test_import_deadlock_3(self):
        # This tries to verify that we haven't created a deadlock situation when
        # code executed from a post module import hook imports another module.

        hooks_called = []

        @wrapt.when_imported("this")
        def hook_this(module):
            hooks_called.append("this")

            self.assertFalse("wsgiref" in sys.modules)

            @wrapt.when_imported("wsgiref")
            def hook_wsgiref(module):
                hooks_called.append("wsgiref")

            def worker():
                import wsgiref

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=10)

            self.assertFalse(thread.is_alive())

        import this

        del sys.modules["this"]

        self.assertEqual(hooks_called, ["this", "wsgiref"])

    def test_loader(self):
        @wrapt.when_imported("this")
        def hook_this(module):
            pass

        import this
        from importlib.machinery import SourceFileLoader

        self.assertIsInstance(this.__loader__, SourceFileLoader)
        self.assertIsInstance(this.__spec__.loader, SourceFileLoader)


class TestPostImportHooksStringForm(unittest.TestCase):

    # A hook registered in the 'module:function' string form defers the
    # import of the callback module until the watched module is imported.
    # The callback module may itself be a module registered directly in
    # sys.modules under a dotted name whose parent package does not exist
    # on the import path.

    def setUp(self):
        super(TestPostImportHooksStringForm, self).setUp()

        sys.modules.pop("this", None)
        _post_import_hooks.pop("this", None)

        self.invoked = []

        callbacks = types.ModuleType("wraptsynthetic.callbacks")
        callbacks.setup = lambda module: self.invoked.append(module.__name__)
        sys.modules["wraptsynthetic.callbacks"] = callbacks

    def tearDown(self):
        sys.modules.pop("wraptsynthetic.callbacks", None)

    def test_string_hook_callback_in_synthetic_module(self):
        wrapt.register_post_import_hook(
            "wraptsynthetic.callbacks:setup", "this"
        )

        self.assertEqual(self.invoked, [])

        import this

        self.assertEqual(self.invoked, ["this"])


if __name__ == "__main__":
    unittest.main()
