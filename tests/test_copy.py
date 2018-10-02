from __future__ import print_function

import unittest

import copy

import wrapt

class CustomObjectProxy(wrapt.ObjectProxy):

    def __copy__(self):
        return CustomObjectProxy(copy.copy(self.__wrapped__))

    def __deepcopy__(self, memo):
        return CustomObjectProxy(copy.deepcopy(self.__wrapped__, memo))

class TestObjectCopy(unittest.TestCase):

    def test_copy(self):
        proxy1 = wrapt.ObjectProxy([1])

        with self.assertRaises(NotImplementedError) as context:
            proxy2 = copy.copy(proxy1)

        self.assertTrue(str(context.exception) ==
                'object proxy must define __copy__()')

    def test_deepcopy(self):
        proxy1 = wrapt.ObjectProxy([1])

        with self.assertRaises(NotImplementedError) as context:
            proxy2 = copy.deepcopy(proxy1)

        self.assertTrue(str(context.exception) ==
                'object proxy must define __deepcopy__()')

    def test_copy_proxy(self):
        proxy1 = CustomObjectProxy([1])
        proxy2 = copy.copy(proxy1)

        self.assertTrue(type(proxy1) == type(proxy2))
        self.assertEqual(proxy1, proxy2)
        self.assertEqual(proxy1.__wrapped__, proxy2.__wrapped__)

    def test_deepcopy_proxy(self):
        proxy1 = CustomObjectProxy([1])
        proxy2 = copy.deepcopy(proxy1)

        self.assertTrue(type(proxy1) == type(proxy2))
        self.assertEqual(proxy1, proxy2)
        self.assertEqual(proxy1.__wrapped__, proxy2.__wrapped__)

if __name__ == '__main__':
    unittest.main()
