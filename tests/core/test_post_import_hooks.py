import importlib
import os
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


class TestPostImportHooksPartialModule(unittest.TestCase):

    # A module is added to sys.modules before its body is executed. These
    # tests cover registering a hook for a module whose body is still being
    # executed, either in another thread or due to a circular import. The
    # module body coordinates with the test through a control module.

    def setUp(self):
        super(TestPostImportHooksPartialModule, self).setUp()

        self.directory = tempfile.TemporaryDirectory()
        sys.path.insert(0, self.directory.name)

        self.control = types.ModuleType("_wrapt_partial_control")
        self.control.entered = threading.Event()
        self.control.release = threading.Event()
        self.control.attempts = 0
        sys.modules[self.control.__name__] = self.control

        self.names = [self.control.__name__]

    def tearDown(self):
        self.control.release.set()

        sys.path.remove(self.directory.name)
        sys.path_importer_cache.pop(self.directory.name, None)

        for name in self.names:
            sys.modules.pop(name, None)
            _post_import_hooks.pop(name, None)

        self.directory.cleanup()
        importlib.invalidate_caches()

    def create_module(self, name, source):
        path = os.path.join(self.directory.name, name + ".py")
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(source)
        self.names.append(name)
        importlib.invalidate_caches()

    def start_import(self, name):
        errors = []

        def run():
            try:
                importlib.import_module(name)
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=run)
        thread.start()

        self.assertTrue(self.control.entered.wait(timeout=10))

        return thread, errors

    def finish_import(self, thread):
        self.control.release.set()
        thread.join(timeout=10)
        self.assertFalse(thread.is_alive())

    def test_registered_in_other_thread_during_import(self):
        # A hook registered from another thread while the module body is
        # executing is called once the body completes, rather than being
        # called immediately against the partially initialized module.

        name = "_wrapt_partial_threaded"

        self.create_module(
            name,
            "import _wrapt_partial_control as control\n"
            "control.entered.set()\n"
            "assert control.release.wait(timeout=10)\n"
            "value = 42\n",
        )

        invoked = []

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("first", module.value)), name
        )

        thread, errors = self.start_import(name)

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("second", module.value)), name
        )

        self.assertEqual(invoked, [])

        self.finish_import(thread)

        self.assertEqual(errors, [])
        self.assertEqual(invoked, [("first", 42), ("second", 42)])
        self.assertNotIn(name, _post_import_hooks)

        # Once the import has completed a further hook is called immediately.

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("third", module.value)), name
        )

        self.assertEqual(invoked[-1], ("third", 42))

    def test_registered_in_other_thread_during_failed_import(self):
        # A hook registered from another thread while the module body is
        # executing remains registered if the import fails, and is called
        # when the module is subsequently imported successfully.

        name = "_wrapt_partial_failed"

        self.create_module(
            name,
            "import _wrapt_partial_control as control\n"
            "control.attempts += 1\n"
            "if control.attempts == 1:\n"
            "    control.entered.set()\n"
            "    assert control.release.wait(timeout=10)\n"
            "    raise RuntimeError('import failed')\n"
            "value = 42\n",
        )

        invoked = []

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("first", module.value)), name
        )

        thread, errors = self.start_import(name)

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("second", module.value)), name
        )

        self.finish_import(thread)

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)
        self.assertEqual(invoked, [])
        self.assertNotIn(name, sys.modules)
        self.assertEqual(len(_post_import_hooks[name]), 2)

        importlib.import_module(name)

        self.assertEqual(invoked, [("first", 42), ("second", 42)])

    def test_registered_in_thread_started_by_module_body(self):
        # A thread started by the module body which registers a hook for the
        # module, and which the module body then waits on, must not block.

        name = "_wrapt_partial_spawned"

        self.create_module(
            name,
            "import threading\n"
            "import _wrapt_partial_control as control\n"
            "thread = threading.Thread(target=control.register)\n"
            "thread.start()\n"
            "thread.join(timeout=10)\n"
            "assert not thread.is_alive()\n"
            "value = 42\n",
        )

        invoked = []

        def register():
            wrapt.register_post_import_hook(
                lambda module: invoked.append(("second", module.value)), name
            )
            invoked.append("registered")

        self.control.register = register

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("first", module.value)), name
        )

        importlib.import_module(name)

        self.assertEqual(invoked, ["registered", ("first", 42), ("second", 42)])

    def test_registered_during_circular_import(self):
        # A hook registered as a result of a circular import, in the thread
        # executing the module body, is called immediately with the partially
        # initialized module, the same as an import statement would return
        # it. This is the case whether or not a hook was already registered.

        name = "_wrapt_partial_circular"
        other = name + "_other"

        self.create_module(name, "import " + other + "\nvalue = 42\n")

        self.create_module(
            other,
            "import wrapt\n"
            "import _wrapt_partial_control as control\n"
            "@wrapt.when_imported('" + name + "')\n"
            "def hook(module):\n"
            "    control.seen = hasattr(module, 'value')\n",
        )

        invoked = []

        wrapt.register_post_import_hook(
            lambda module: invoked.append(("first", module.value)), name
        )

        importlib.import_module(name)

        self.assertIs(self.control.seen, False)
        self.assertEqual(invoked, [("first", 42)])


if __name__ == "__main__":
    unittest.main()
