from __future__ import print_function

import unittest

import wrapt

class TestPostImportHooks(unittest.TestCase):

    def test_simple(self):
        invoked = []

        @wrapt.when_imported('socket')
        def hook_socket(module):
            self.assertEqual(module.__name__, 'socket')
            invoked.append(1)

        self.assertEqual(len(invoked), 0)

        import socket

        self.assertEqual(len(invoked), 1)

if __name__ == '__main__':
    unittest.main()
