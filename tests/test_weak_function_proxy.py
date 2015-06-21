from __future__ import print_function

import unittest
import gc

import wrapt

class TestWeakFunctionProxy(unittest.TestCase):

    def test_isinstance(self):
        def function(a, b):
            return a, b

        proxy = wrapt.WeakFunctionProxy(function)

        self.assertTrue(isinstance(proxy, type(function)))

    def test_no_callback(self):
        def function(a, b):
            return a, b

        proxy = wrapt.WeakFunctionProxy(function)

        self.assertEqual(proxy(1, 2), (1, 2))

        function = None
        gc.collect()

    def test_call_expired(self):
        def function(a, b):
            return a, b

        proxy = wrapt.WeakFunctionProxy(function)

        self.assertEqual(proxy(1, 2), (1, 2))

        function = None
        gc.collect()

        def run(*args):
            proxy()

        self.assertRaises(ReferenceError, run, ())

    def test_function(self):
        def function(a, b):
            return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        proxy = wrapt.WeakFunctionProxy(function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        function = None
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_instancemethod_delete_instance(self):
        class Class(object):
            def function(self, a, b):
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        c = Class()

        proxy = wrapt.WeakFunctionProxy(c.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        c = None
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_instancemethod_delete_function(self):
        class Class(object):
            def function(self, a, b):
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        c = Class()

        proxy = wrapt.WeakFunctionProxy(c.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        del c
        del Class.function
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_instancemethod_delete_function_and_instance(self):
        class Class(object):
            def function(self, a, b):
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        c = Class()

        proxy = wrapt.WeakFunctionProxy(c.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        c = None
        del Class.function
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_classmethod(self):
        class Class(object):
            @classmethod
            def function(cls, a, b):
                self.assertEqual(cls, Class)
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        proxy = wrapt.WeakFunctionProxy(Class.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        Class = None
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_staticmethod(self):
        class Class(object):
            @staticmethod
            def function(a, b):
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        proxy = wrapt.WeakFunctionProxy(Class.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        Class = None
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_decorator_method(self):
        @wrapt.decorator
        def bark(wrapped, instance, args, kwargs):
            return 'bark'

        class Animal(object):
            @bark
            def squeal(self):
                return 'squeal'

        animal = Animal()

        self.assertEqual(animal.squeal(), 'bark')

        method = wrapt.WeakFunctionProxy(animal.squeal)

        self.assertEqual(method(), 'bark')

if __name__ == '__main__':
    unittest.main()
