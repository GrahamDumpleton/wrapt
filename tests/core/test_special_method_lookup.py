import asyncio
import operator
import os
import unittest

import wrapt


def shadow(*args, **kwargs):
    raise AssertionError("instance attribute must not implement the protocol")


class SpecialMethodLookupTests(unittest.TestCase):
    def test_iterator_and_length_hint_ignore_instance_attributes(self):
        class Iterator:
            def __init__(self):
                self.values = iter([1, 2])

            def __iter__(self):
                return self

            def __next__(self):
                return next(self.values)

            def __length_hint__(self):
                return operator.length_hint(self.values)

        target = Iterator()
        target.__next__ = shadow
        target.__length_hint__ = shadow
        proxy = wrapt.AutoObjectProxy(target)
        self.assertEqual(operator.length_hint(target), 2)
        self.assertEqual(operator.length_hint(proxy), 2)
        self.assertEqual(next(target), 1)
        self.assertEqual(next(proxy), 2)
        with self.assertRaises(StopIteration):
            next(proxy)

    def test_path_ignores_instance_getattribute(self):
        class Path:
            def __getattribute__(self, name):
                if name == "__fspath__":
                    return shadow
                return super().__getattribute__(name)

            def __fspath__(self):
                return "original-path"

        target = Path()
        self.assertEqual(os.fspath(target), "original-path")
        self.assertEqual(os.fspath(wrapt.AutoObjectProxy(target)), os.fspath(target))
        lazy = wrapt.LazyObjectProxy(lambda: target, interface=Path)
        self.assertEqual(os.fspath(lazy), os.fspath(target))

    def test_async_iteration_ignores_instance_attributes(self):
        class Iterator:
            def __init__(self):
                self.values = iter([1, 2])
                self.__aiter__ = shadow
                self.__anext__ = shadow

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self.values)
                except StopIteration:
                    raise StopAsyncIteration from None

        async def collect(value):
            return [item async for item in value]

        self.assertEqual(asyncio.run(collect(Iterator())), [1, 2])
        self.assertEqual(
            asyncio.run(collect(wrapt.AutoObjectProxy(Iterator()))), [1, 2]
        )

    def test_await_ignores_instance_attributes(self):
        class Awaitable:
            def __await__(self):
                yield
                return 42

        async def wait(value):
            return await value

        target = Awaitable()
        target.__await__ = shadow
        self.assertEqual(asyncio.run(wait(target)), 42)
        self.assertEqual(asyncio.run(wait(wrapt.AutoObjectProxy(target))), 42)

    def test_descriptor_hooks_ignore_instance_attributes(self):
        class Descriptor:
            def __init__(self):
                self.events = []
                self.value = 1
                self.__get__ = shadow
                self.__set__ = shadow
                self.__delete__ = shadow
                self.__set_name__ = shadow

            def __set_name__(self, owner, name):
                self.events.append((owner.__name__, name))

            def __get__(self, instance, owner):
                return self.value

            def __set__(self, instance, value):
                self.value = value

            def __delete__(self, instance):
                self.value = None

        for proxied in (False, True):
            with self.subTest(proxied=proxied):
                target = Descriptor()
                descriptor = wrapt.AutoObjectProxy(target) if proxied else target

                class Owner:
                    field = descriptor

                self.assertEqual(target.events, [("Owner", "field")])
                self.assertEqual(Owner.field, 1)
                owner = Owner()
                self.assertEqual(owner.field, 1)
                owner.field = 2
                self.assertEqual(owner.field, 2)
                del owner.field
                self.assertIsNone(owner.field)

    def test_static_and_class_methods_ignore_metaclass_getattribute(self):
        checking = [False]

        class Meta(type):
            def __getattribute__(cls, name):
                if checking[0] and name in ("__dict__", "__mro__", "__next__"):
                    raise AssertionError("metaclass lookup must not run")
                return super().__getattribute__(name)

        class StaticIterator(metaclass=Meta):
            def __iter__(self):
                return self

            @staticmethod
            def __next__():
                return "static"

        class ClassIterator(metaclass=Meta):
            value = "class"

            def __iter__(self):
                return self

            @classmethod
            def __next__(cls):
                return cls.value

        for cls in (StaticIterator, ClassIterator):
            with self.subTest(cls=cls.__name__):
                checking[0] = False
                target = cls()
                proxy = wrapt.AutoObjectProxy(target)
                checking[0] = True
                self.assertEqual(next(proxy), next(target))

    def test_custom_descriptor_binds_to_target(self):
        class Method:
            def __get__(self, instance, owner):
                return lambda: (instance.value, owner.__name__)

        class Iterator:
            value = 42
            __next__ = Method()

        target = Iterator()
        self.assertEqual(next(wrapt.AutoObjectProxy(target)), next(target))

    def test_callable_special_method_without_descriptor(self):
        class Next:
            def __call__(self):
                return 42

        class Iterator:
            __next__ = Next()

        target = Iterator()
        self.assertEqual(next(wrapt.AutoObjectProxy(target)), next(target))

    def test_binding_attribute_error_propagates(self):
        class Method:
            def __get__(self, instance, owner):
                raise AttributeError("binding failed")

        class Iterator:
            __next__ = Method()

        for target in (Iterator(), wrapt.AutoObjectProxy(Iterator())):
            with self.assertRaisesRegex(AttributeError, "binding failed"):
                next(target)

    def test_descriptor_classmethod_get_stays_noncallable(self):
        class Descriptor:
            @classmethod
            def __get__(cls, instance, owner):
                return 42

        for proxied in (False, True):
            with self.subTest(proxied=proxied):
                target = Descriptor()

                class Owner:
                    field = wrapt.AutoObjectProxy(target) if proxied else target

                with self.assertRaises(TypeError):
                    Owner.field

    def test_descriptor_staticmethod_get_receives_descriptor(self):
        class Descriptor:
            value = 42

            @staticmethod
            def __get__(descriptor, instance, owner):
                return descriptor.value

        for proxied in (False, True):
            with self.subTest(proxied=proxied):
                target = Descriptor()

                class Owner:
                    field = wrapt.AutoObjectProxy(target) if proxied else target

                # Raw staticmethod objects became callable in Python 3.10.
                if callable(Descriptor.__dict__["__get__"]):
                    self.assertEqual(Owner.field, 42)
                else:
                    with self.assertRaises(TypeError):
                        Owner.field

    def test_special_method_staticmethod_get_receives_descriptor(self):
        class Method:
            @staticmethod
            def __get__(descriptor, instance, owner):
                return lambda: instance.value

        class Iterator:
            value = 42
            __next__ = Method()

        target = Iterator()
        proxy = wrapt.AutoObjectProxy(target)
        if callable(Method.__dict__["__get__"]):
            self.assertEqual(next(proxy), next(target))
        else:
            for value in (target, proxy):
                with self.assertRaises(TypeError):
                    next(value)

    def test_replacement_target_keeps_special_lookup(self):
        class Path:
            def __init__(self, value):
                self.value = value
                self.__fspath__ = shadow

            def __fspath__(self):
                return self.value

        proxy = wrapt.AutoObjectProxy(Path("first"))
        self.assertEqual(os.fspath(proxy), "first")
        proxy.__wrapped__ = Path("second")
        self.assertEqual(os.fspath(proxy), "second")

    def test_none_method_stays_noncallable(self):
        class Iterator:
            __next__ = None

        for target in (Iterator(), wrapt.AutoObjectProxy(Iterator())):
            with self.assertRaises(TypeError):
                next(target)
