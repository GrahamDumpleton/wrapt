from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from compat import PY2, PY3, exec_

class TestInheritance(unittest.TestCase):

    def test_single_inheritance(self):
        @wrapt.decorator
        def passthru(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthru
        class BaseClass(object):
            def __init__(self):
                self.value = 1

        class DerivedClass(BaseClass):
            def __init__(self):
                super(DerivedClass, self).__init__()
                self.value = 2

        base = BaseClass()

        self.assertEqual(type(base), BaseClass.__wrapped__)
        self.assertTrue(isinstance(base, BaseClass.__wrapped__))
        self.assertEqual(base.value, 1)

        self.assertEqual(type(base).__mro__, (BaseClass.__wrapped__, object))
        self.assertEqual(BaseClass.__mro_entries__(()), (BaseClass.__wrapped__,))

        derived = DerivedClass()

        self.assertEqual(type(derived), DerivedClass)
        self.assertTrue(isinstance(derived, BaseClass.__wrapped__))
        self.assertTrue(isinstance(derived, DerivedClass))
        self.assertEqual(derived.value, 2)

        self.assertEqual(type(derived).__mro__, (DerivedClass, BaseClass.__wrapped__, object))

    def test_multiple_inheritance(self):
        @wrapt.decorator
        def passthru(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthru
        class BaseClass1(object):
            pass

        @passthru
        class BaseClass2(object):
            pass

        class DerivedClass(BaseClass1, BaseClass2):
            pass

        derived = DerivedClass()

        self.assertEqual(type(derived), DerivedClass)
        self.assertTrue(isinstance(derived, BaseClass1.__wrapped__))
        self.assertTrue(isinstance(derived, BaseClass2.__wrapped__))
        self.assertTrue(isinstance(derived, DerivedClass))

        self.assertEqual(type(derived).__mro__, (DerivedClass,
                BaseClass1.__wrapped__, BaseClass2.__wrapped__, object))

    def test_multiple_inheritance_common(self):
        @wrapt.decorator
        def passthru(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthru
        class CommonClass(object):
            pass

        @passthru
        class BaseClass1(CommonClass):
            pass

        @passthru
        class BaseClass2(CommonClass):
            pass

        class DerivedClass(BaseClass1, BaseClass2):
            pass

        derived = DerivedClass()

        self.assertEqual(type(derived), DerivedClass)
        self.assertTrue(isinstance(derived, CommonClass.__wrapped__))
        self.assertTrue(isinstance(derived, BaseClass1.__wrapped__))
        self.assertTrue(isinstance(derived, BaseClass2.__wrapped__))
        self.assertTrue(isinstance(derived, DerivedClass))

        self.assertEqual(type(derived).__mro__, (DerivedClass,
            BaseClass1.__wrapped__, BaseClass2.__wrapped__,
            CommonClass.__wrapped__, object))
