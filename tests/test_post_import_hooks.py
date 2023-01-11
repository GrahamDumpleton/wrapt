from __future__ import print_function

import unittest
import sys
import threading

import wrapt
from wrapt.importer import _post_import_hooks

from compat import PY2, PY3

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

    def test_import_deadlock_1(self):
        # This tries to verify that we haven't created a deadlock situation when
        # code executed from a post module import, for a module that has already
        # been imported, creates a thread which in turn attempts to register
        # another import hook.

        import this

        @wrapt.when_imported('this')
        def hook_this(module):
            def worker():
                @wrapt.when_imported('xxx')
                def hook_xxx(module):
                    pass

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=10)

            self.assertFalse(thread.is_alive())

        del sys.modules['this']

    def test_import_deadlock_2(self):
        # This tries to verify that we haven't created a deadlock situation when
        # code executed from a post module import, for a module that has not yet
        # been imported, creates a thread which in turn attempts to register
        # another import hook.

        @wrapt.when_imported('this')
        def hook_this(module):
            def worker():
                @wrapt.when_imported('xxx')
                def hook_xxx(module):
                    pass

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=10)

            self.assertFalse(thread.is_alive())

        import this
        del sys.modules['this']

    def test_import_deadlock_3(self):
        # This tries to verify that we haven't created a deadlock situation when
        # code executed from a post module import hook imports another module.

        # Note that we cannot run this test on Python 2.X as it has a single
        # global module import lock which means that if a thread runs during
        # module import and it in turns does an import that it will then block
        # on the parent thread which holds the global module import lock. This
        # is a fundamental behaviour of Python and not wrapt. In Python 3.X
        # there is a module import lock per named module and so we do not have
        # this problem.

        if PY2:
          return

        hooks_called = []

        @wrapt.when_imported('this')
        def hook_this(module):
            hooks_called.append('this')

            self.assertFalse('wsgiref' in sys.modules)
    
            @wrapt.when_imported('wsgiref')
            def hook_wsgiref(module):
                hooks_called.append('wsgiref')

            def worker():
                import wsgiref

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=10)

            self.assertFalse(thread.is_alive())

        import this
        del sys.modules['this']

        self.assertEqual(hooks_called, ['this', 'wsgiref'])

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
