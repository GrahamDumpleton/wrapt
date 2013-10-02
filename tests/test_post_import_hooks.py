from __future__ import print_function

import unittest

import wrapt

class TestPostImportHooks(unittest.TestCase):

    def test_simple(self):
        invoked = []

        @wrapt.when_imported('this')
        def hook_this(module):
            self.assertEqual(module.__name__, 'this')
            invoked.append(1)

        self.assertEqual(len(invoked), 0)

        import this

        self.assertEqual(len(invoked), 1)

if __name__ == '__main__':
    unittest.main()
