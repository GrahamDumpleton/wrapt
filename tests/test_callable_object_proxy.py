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

    def test_empty_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {}

        partial0 = wrapt.PartialCallableObjectProxy(func0, *args, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_1_positional_argument(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (1,), {}

        partial0 = wrapt.PartialCallableObjectProxy(func0, *args)

        self.assertEqual(partial0(), (args, kwargs))

    def test_1_keyword_argument(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {'k1': 1}

        partial0 = wrapt.PartialCallableObjectProxy(func0, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_multiple_positional_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (1, 2, 3), {}

        partial0 = wrapt.PartialCallableObjectProxy(func0, *args)

        self.assertEqual(partial0(), (args, kwargs))

    def test_multiple_keyword_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {'k1': 1, 'k2': 2, 'k3': 3}

        partial0 = wrapt.PartialCallableObjectProxy(func0, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

if __name__ == '__main__':
    unittest.main()
