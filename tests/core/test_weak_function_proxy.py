import gc
import unittest
import weakref

import wrapt


class TestWeakFunctionProxy(unittest.TestCase):

    def test_decorated_function(self):
        @wrapt.decorator
        def decorator(wrapped, instance, args, kwargs):
            return "decorated", wrapped(*args, **kwargs)

        @decorator
        def function(value):
            return value

        callbacks = []
        proxy = wrapt.WeakFunctionProxy(function, lambda ref: callbacks.append(id(ref)))
        self.assertEqual(proxy(42), ("decorated", 42))
        del function
        gc.collect()
        self.assertEqual(callbacks, [id(proxy)])
        with self.assertRaises(ReferenceError):
            proxy(42)

    def test_decorated_descriptors(self):
        @wrapt.decorator
        def decorator(wrapped, instance, args, kwargs):
            return instance, wrapped(*args, **kwargs)

        class Class:
            @decorator
            def method(self, value):
                return value

            @decorator
            @classmethod
            def class_method(cls, value):
                return cls, value

            @decorator
            @staticmethod
            def static_method(value):
                return value

        class Subclass(Class):
            pass

        obj = Class()
        targets = ((Class, Class), (obj, Class), (Subclass, Subclass), (Subclass(), Subclass))
        for target, owner in targets:
            with self.subTest(target=target, kind="classmethod"):
                proxy = wrapt.WeakFunctionProxy(target.class_method)
                self.assertEqual(proxy(42), (owner, (owner, 42)))
            with self.subTest(target=target, kind="staticmethod"):
                proxy = wrapt.WeakFunctionProxy(target.static_method)
                self.assertEqual(proxy(42), (None, 42))

        proxy = wrapt.WeakFunctionProxy(Class.method)
        self.assertEqual(proxy(obj, 42), (obj, 42))

    def test_decorated_classmethod_does_not_retain_owner(self):
        @wrapt.decorator
        def decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @decorator
            @classmethod
            def method(cls):
                return 42

        callbacks = []
        owner = weakref.ref(Class)
        proxy = wrapt.WeakFunctionProxy(Class.method, lambda ref: callbacks.append(id(ref)))
        self.assertEqual(proxy(), 42)
        del Class
        gc.collect()
        self.assertIsNone(owner())
        self.assertEqual(callbacks, [id(proxy)])
        with self.assertRaises(ReferenceError):
            proxy()

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
        class Class:
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

        with self.assertRaises(ReferenceError):
            proxy(1, 2)

    def test_instancemethod_delete_function(self):
        class Class:
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

        with self.assertRaises(ReferenceError):
            proxy(1, 2)

    def test_instancemethod_delete_function_and_instance(self):
        class Class:
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

        with self.assertRaises(ReferenceError):
            proxy(1, 2)

    def test_classmethod(self):
        class Class:
            @classmethod
            def function(cls, a, b):
                self.assertEqual(cls, Class)
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        proxy = wrapt.WeakFunctionProxy(Class.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        Class.function = None
        Class = None
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

        with self.assertRaises(ReferenceError):
            proxy(1, 2)

    def test_staticmethod(self):
        class Class:
            @staticmethod
            def function(a, b):
                return a, b

        result = []

        def callback(proxy):
            result.append(id(proxy))

        proxy = wrapt.WeakFunctionProxy(Class.function, callback)

        self.assertEqual(proxy(1, 2), (1, 2))

        Class.function = None
        Class = None
        gc.collect()

        self.assertEqual(len(result), 1)
        self.assertEqual(id(proxy), result[0])

    def test_decorator_method(self):
        @wrapt.decorator
        def bark(wrapped, instance, args, kwargs):
            return "bark"

        class Animal:
            @bark
            def squeal(self):
                return "squeal"

        animal = Animal()

        self.assertEqual(animal.squeal(), "bark")

        method = wrapt.WeakFunctionProxy(animal.squeal)

        self.assertEqual(method(), "bark")


class TestArgumentUnpackingWeakFunctionProxy(unittest.TestCase):

    def test_self_keyword_argument(self):
        def function(self, *args, **kwargs):
            return self, args, kwargs

        proxy = wrapt.WeakFunctionProxy(function)

        self.assertEqual(
            proxy(self="self", arg1="arg1"), ("self", (), dict(arg1="arg1"))
        )


if __name__ == "__main__":
    unittest.main()
