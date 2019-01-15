from __future__ import print_function

import unittest

import wrapt

class TestPartialCallableObjectProxy(unittest.TestCase):

    def test_no_arguments(self):
        def func0():
            return ((), {})

        partial0 = wrapt.PartialCallableObjectProxy(func0)

        args, kwargs = (), {}

        self.assertEqual(partial0(), (args, kwargs))

if __name__ == '__main__':
    unittest.main()
