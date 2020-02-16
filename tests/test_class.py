from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from compat import PY2, PY3, exec_

DECORATORS_CODE = """
import wrapt

@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
"""

decorators = imp.new_module('decorators')
exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

class class1(object):
    pass

class1o = class1

class1d = decorators.passthru_decorator(class1)

class TestIntrospection(unittest.TestCase):

    def test_getmembers(self):
        class1o_members = inspect.getmembers(class1o)
        class1d_members = inspect.getmembers(class1d)

class TestInheritance(unittest.TestCase):

    def test_single_inheritance(self):
        @wrapt.decorator
        def passthru(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthru
        class BaseClass(object):
            def __init__(self):
                self.value = 1

        class DerivedClass(BaseClass.__wrapped__):
            def __init__(self):
                super(DerivedClass, self).__init__()
                self.value = 2

        base = BaseClass()

        self.assertEqual(type(base), BaseClass.__wrapped__)
        self.assertTrue(isinstance(base, BaseClass.__wrapped__))
        self.assertEqual(base.value, 1)

        self.assertEqual(type(base).__mro__, (BaseClass.__wrapped__, object))

        derived = DerivedClass()

        self.assertEqual(type(derived), DerivedClass)
        self.assertTrue(isinstance(derived, BaseClass.__wrapped__))
        self.assertTrue(isinstance(derived, DerivedClass))
        self.assertEqual(derived.value, 2)

        self.assertEqual(type(derived).__mro__, (DerivedClass, BaseClass.__wrapped__, object))
