from __future__ import print_function

import unittest
import sys
import threading

import wrapt
from wrapt.importer import _post_import_hooks

class TestPostImportHooks(unittest.TestCase):

    def setUp(self):
        super(TestPostImportHooks, self).setUp()

        # So we can import 'this' and test post-import hooks multiple times
        # below in the context of a single Python process, remove 'this' from
        # sys.modules and post import hooks.
        sys.modules.pop('this', None)
        _post_import_hooks.pop('this', None)

    def test_before_import(self):
        invoked = []

        @wrapt.when_imported('this')
        def hook_this(module):
            self.assertEqual(module.__name__, 'this')
            invoked.append(1)

        self.assertEqual(len(invoked), 0)

        import this

        self.assertEqual(len(invoked), 1)

    def test_after_import(self):
        invoked = []

        import this

        self.assertEqual(len(invoked), 0)

        @wrapt.when_imported('this')
        def hook_this(module):
            self.assertEqual(module.__name__, 'this')
            invoked.append(1)

        self.assertEqual(len(invoked), 1)

    def test_before_and_after_import(self):
        invoked_one = []
        invoked_two = []

        @wrapt.when_imported('this')
        def hook_this_one(module):
            self.assertEqual(module.__name__, 'this')
            invoked_one.append(1)

        self.assertEqual(len(invoked_one), 0)
        self.assertEqual(len(invoked_two), 0)

        import this

        self.assertEqual(len(invoked_one), 1)
        self.assertEqual(len(invoked_two), 0)

        @wrapt.when_imported('this')
        def hook_this_two(module):
            self.assertEqual(module.__name__, 'this')
            invoked_two.append(1)

        self.assertEqual(len(invoked_one), 1)
        self.assertEqual(len(invoked_two), 1)

    def test_remove_from_sys_modules(self):
        invoked = []

        @wrapt.when_imported('this')
        def hook_this(module):
            self.assertEqual(module.__name__, 'this')
            invoked.append(1)

        import this
        self.assertEqual(len(invoked), 1)

        del sys.modules['this']
        wrapt.register_post_import_hook(hook_this, 'this')
        import this
        self.assertEqual(len(invoked), 2)

    def test_import_deadlock(self):
        @wrapt.when_imported('this')
        def hook_this(module):
            ev.set()
            # The hook used to be called under _post_import_hooks_lock. Then
            # the import tried to acquire the import lock. If the other thread
            # already held it and was waiting for _post_import_hooks_lock, we
            # deadlocked.
            for _ in range(5):
                import module1
                del sys.modules['module1']

        def worker():
            ev.wait()
            # The import tries to acquire the import lock. ImportHookFinder
            # then tries to acquire _post_import_hooks_lock under it.
            for _ in range(5):
                import module2
                del sys.modules['module2']

        # A deadlock between notify_module_loaded and ImportHookFinder.
        ev = threading.Event()
        thread = threading.Thread(target=worker)
        thread.start()
        import this
        thread.join()

        # A deadlock between register_post_import_hook and ImportHookFinder.
        ev = threading.Event()
        thread = threading.Thread(target=worker)
        thread.start()
        wrapt.register_post_import_hook(hook_this, 'this')
        thread.join()

    def test_loader(self):
        @wrapt.when_imported('this')
        def hook_this(module):
            pass

        import this

        if sys.version_info[:2] >= (3, 3):
            from importlib.machinery import SourceFileLoader
            self.assertIsInstance(this.__loader__, SourceFileLoader)
            self.assertIsInstance(this.__spec__.loader, SourceFileLoader)

        else:
            self.assertEqual(hasattr(this, "__loader__"), False)

if __name__ == '__main__':
    unittest.main()
