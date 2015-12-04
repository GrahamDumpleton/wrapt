from __future__ import print_function

import unittest
import sys

import wrapt
from wrapt.importer import _post_import_hooks

class TestPostImportHooks(unittest.TestCase):

    def setUp(self):
        super(TestPostImportHooks, self).setUp()

        # So we can import 'this' and test post-import hooks multiple times
        # below in the context of a single Python process, remove 'this' from
        # sys.modules and post import hooks.
        if 'this' in sys.modules:
            del sys.modules['this']
        if 'this' in _post_import_hooks:
            del _post_import_hooks['this']

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

if __name__ == '__main__':
    unittest.main()
