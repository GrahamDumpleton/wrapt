from __future__ import print_function

import unittest

import abc
import _py_abc

import wrapt

class TestClassInheritance(unittest.TestCase):

    def test_basic_inheritance(self):
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(args, kwargs)

        class B1:
            def method(self):
                pass

        @wrapper
        class C1(B1):
            def method(self):
                pass

        class D1(C1):
            def method(self):
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

        self.assertTrue(issubclass(B1, (B1, C1, D1)))
        self.assertTrue(issubclass(C1, (B1, C1, D1)))
        self.assertTrue(issubclass(D1, (B1, C1, D1)))

    def test_abc_inheritance(self):
        # XXX The checks commented out below all fail because the
        # helpers for issubclass() via __subclasscheck__() in ABCMeta
        # base class when C implementation is used does not support duck
        # typing and will fail if the argument it is given is an object
        # proxy like wrapt decorator uses. There is no known workaround
        # for this problem.
        #
        #       def __subclasscheck__(cls, subclass):
        #           """Override for issubclass(subclass, cls)."""
        #   >       return _abc_subclasscheck(cls, subclass)
        #   E       TypeError: issubclass() arg 1 must be a class

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(args, kwargs)

        class A1(metaclass=abc.ABCMeta):
            @abc.abstractmethod
            def method(self):
                pass

        class B1(A1):
            def method(self):
                pass

        @wrapper
        class C1(B1):
            def method(self):
                pass

        class D1(C1):
            def method(self):
                pass

        self.assertTrue(issubclass(A1, A1))
        self.assertTrue(issubclass(B1, A1))
        # self.assertTrue(issubclass(C1, A1))
        self.assertTrue(issubclass(D1, A1))

        self.assertFalse(issubclass(A1, B1))
        self.assertTrue(issubclass(B1, B1))
        # self.assertTrue(issubclass(C1, B1))
        self.assertTrue(issubclass(D1, B1))

        self.assertFalse(issubclass(A1, C1))
        self.assertFalse(issubclass(B1, C1))
        self.assertTrue(issubclass(C1, C1))
        self.assertTrue(issubclass(D1, C1))

        self.assertFalse(issubclass(A1, D1))
        self.assertFalse(issubclass(B1, D1))
        # self.assertFalse(issubclass(C1, D1))
        self.assertTrue(issubclass(D1, D1))

        self.assertTrue(issubclass(A1, (A1, B1, C1, D1)))
        self.assertTrue(issubclass(B1, (A1, B1, C1, D1)))
        # self.assertTrue(issubclass(C1, (A1, B1, C1, D1)))
        self.assertTrue(issubclass(D1, (A1, B1, C1, D1)))

    def test_py_abc_inheritance(self):
        # In contrast to above when C implementation for ABCMeta helpers
        # are used, these all pass as have use the Python implementation
        # instead.

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(args, kwargs)

        class A1(metaclass=_py_abc.ABCMeta):
            @abc.abstractmethod
            def method(self):
                pass

        class B1(A1):
            def method(self):
                pass

        @wrapper
        class C1(B1):
            def method(self):
                pass

        class D1(C1):
            def method(self):
                pass

        self.assertTrue(issubclass(A1, A1))
        self.assertTrue(issubclass(B1, A1))
        self.assertTrue(issubclass(C1, A1))
        self.assertTrue(issubclass(D1, A1))

        self.assertFalse(issubclass(A1, B1))
        self.assertTrue(issubclass(B1, B1))
        self.assertTrue(issubclass(C1, B1))
        self.assertTrue(issubclass(D1, B1))

        self.assertFalse(issubclass(A1, C1))
        self.assertFalse(issubclass(B1, C1))
        self.assertTrue(issubclass(C1, C1))
        self.assertTrue(issubclass(D1, C1))

        self.assertFalse(issubclass(A1, D1))
        self.assertFalse(issubclass(B1, D1))
        self.assertFalse(issubclass(C1, D1))
        self.assertTrue(issubclass(D1, D1))

        self.assertTrue(issubclass(A1, (A1, B1, C1, D1)))
        self.assertTrue(issubclass(B1, (A1, B1, C1, D1)))
        self.assertTrue(issubclass(C1, (A1, B1, C1, D1)))
        self.assertTrue(issubclass(D1, (A1, B1, C1, D1)))

if __name__ == '__main__':
    unittest.main()
