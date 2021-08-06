from __future__ import print_function

import unittest

import wrapt

class TestClassInheritance(unittest.TestCase):

    def test_copy(self):
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(args, kwargs)

        class B1:
            def method(cls):
                pass

        @wrapper
        class C1(B1):
            def method(cls):
                pass

        class D1(C1):
            def method(cls):
                pass

        self.assertTrue(issubclass(B1, B1))
        self.assertTrue(issubclass(C1, B1))
        self.assertTrue(issubclass(D1, B1))

        self.assertFalse(issubclass(B1, C1))
        self.assertTrue(issubclass(C1, C1))
        self.assertTrue(issubclass(D1, C1))

        self.assertFalse(issubclass(B1, D1))
        self.assertFalse(issubclass(C1, D1))
        self.assertTrue(issubclass(D1, D1))

        self.assertTrue(issubclass(D1, (B1, C1, D1)))

if __name__ == '__main__':
    unittest.main()
