import unittest

import wrapt


class TestAutoObjectProxy(unittest.TestCase):

    def test_call(self):
        class Callable:
            def __call__(self, x):
                return x + 1

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__call__"))
        self.assertFalse(callable(base))

        proxy = wrapt.AutoObjectProxy(Callable())

        self.assertTrue(hasattr(proxy, "__call__"))
        self.assertTrue(callable(proxy))

        self.assertEqual(proxy(2), 3)

    def test_iter(self):
        class Iterable:
            def __iter__(self):
                return iter([1, 2, 3])

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__iter__"))
        self.assertFalse(hasattr(base, "__next__"))

        proxy = wrapt.AutoObjectProxy(Iterable())

        self.assertTrue(hasattr(proxy, "__iter__"))
        self.assertFalse(hasattr(proxy, "__next__"))

        self.assertEqual(list(proxy), [1, 2, 3])

    def test_next(self):
        class Iterator:
            def __init__(self):
                self._iter = iter([1, 2, 3])

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._iter)

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__iter__"))
        self.assertFalse(hasattr(base, "__next__"))

        proxy = wrapt.AutoObjectProxy(Iterator())

        self.assertTrue(hasattr(proxy, "__iter__"))
        self.assertTrue(hasattr(proxy, "__next__"))

        self.assertEqual(list(proxy), [1, 2, 3])

    def test_aiter(self):
        class AsyncIterable:
            def __aiter__(self):
                self._iter = iter([1, 2, 3])
                return self

            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__aiter__"))
        self.assertFalse(hasattr(base, "__anext__"))

        proxy = wrapt.AutoObjectProxy(AsyncIterable())

        self.assertTrue(hasattr(proxy, "__aiter__"))
        self.assertTrue(hasattr(proxy, "__anext__"))

        async def iterate():
            result = []
            async for item in proxy:
                result.append(item)
            return result

        import asyncio

        self.assertEqual(asyncio.run(iterate()), [1, 2, 3])

    def test_length_hint(self):
        import operator

        self.assertTrue(hasattr(operator, "length_hint"))

        class LengthHint:
            def __length_hint__(self):
                return 42

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__length_hint__"))

        proxy = wrapt.AutoObjectProxy(LengthHint())

        self.assertTrue(hasattr(proxy, "__length_hint__"))

        self.assertEqual(operator.length_hint(proxy), 42)

    def test_await(self):
        class Awaitable:
            def __await__(self):
                yield
                return 42

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__await__"))

        proxy = wrapt.AutoObjectProxy(Awaitable())

        self.assertTrue(hasattr(proxy, "__await__"))

        async def await_proxy():
            return await proxy

        import asyncio

        self.assertEqual(asyncio.run(await_proxy()), 42)

    def test_fspath(self):
        import os

        class PathLike:
            def __fspath__(self):
                return "/path/to/file"

        base = wrapt.BaseObjectProxy(PathLike())

        self.assertRaises(TypeError, os.fspath, base)

        proxy = wrapt.AutoObjectProxy(PathLike())

        self.assertEqual(os.fspath(proxy), "/path/to/file")
        self.assertTrue(isinstance(proxy, os.PathLike))

    def test_fspath_pathlib(self):
        import os
        import pathlib

        instance = pathlib.PurePath("/path/to/file")
        proxy = wrapt.AutoObjectProxy(instance)

        self.assertEqual(os.fspath(proxy), os.fspath(instance))
        self.assertTrue(isinstance(proxy, os.PathLike))

    def test_fspath_not_pathlike(self):
        import os

        proxy = wrapt.AutoObjectProxy(42)

        self.assertFalse(hasattr(type(proxy), "__fspath__"))
        self.assertRaises(TypeError, os.fspath, proxy)
        self.assertFalse(isinstance(proxy, os.PathLike))

    def test_descriptor_optional_owner(self):
        def method(instance):
            return instance

        instance = object()

        for descriptor in (method, property(method)):
            with self.subTest(descriptor=descriptor):
                proxy = wrapt.AutoObjectProxy(descriptor)

                self.assertEqual(proxy.__get__(instance), descriptor.__get__(instance))
                self.assertEqual(
                    proxy.__get__(instance, None), descriptor.__get__(instance, None)
                )
                self.assertEqual(
                    proxy.__get__(None, object), descriptor.__get__(None, object)
                )

    def test_descriptor_optional_owner_required_by_wrapped(self):
        # A descriptor implemented in Python can require the owner argument,
        # as Python always supplies it on attribute lookup. When the owner
        # is omitted in a manual call through the proxy, it is None which
        # must be passed to the wrapped descriptor.

        class Descriptor:
            def __get__(self, instance, owner):
                return (instance, owner)

        instance = object()

        proxy = wrapt.AutoObjectProxy(Descriptor())

        self.assertEqual(proxy.__get__(instance), (instance, None))
        self.assertEqual(proxy.__get__(instance, None), (instance, None))
        self.assertEqual(proxy.__get__(instance, object), (instance, object))
        self.assertEqual(proxy.__get__(None, object), (None, object))

    def test_descriptor(self):
        class Descriptor:
            def __init__(self, value):
                self.value = value

            def __get__(self, instance, owner):
                assert self.name == "attr"
                assert self.owner == owner
                if instance is None:
                    return self
                return self.value

            def __set__(self, instance, value):
                self.value = value

            def __delete__(self, instance):
                del self.value

            def __set_name__(self, owner, name):
                self.owner = owner
                self.name = name

        base = wrapt.BaseObjectProxy(object())

        self.assertFalse(hasattr(base, "__get__"))
        self.assertFalse(hasattr(base, "__set__"))
        self.assertFalse(hasattr(base, "__delete__"))
        self.assertFalse(hasattr(base, "__set_name__"))

        proxy = wrapt.AutoObjectProxy(Descriptor(42))

        self.assertTrue(hasattr(proxy, "__get__"))
        self.assertTrue(hasattr(proxy, "__set__"))
        self.assertTrue(hasattr(proxy, "__delete__"))
        self.assertTrue(hasattr(proxy, "__set_name__"))

        class Owner:
            attr = wrapt.AutoObjectProxy(Descriptor(42))

        owner = Owner()

        self.assertEqual(owner.attr, 42)

        owner.attr = 100
        self.assertEqual(owner.attr, 100)

        del owner.attr
        self.assertRaises(AttributeError, lambda: owner.attr)

    def test_instance_attributes_are_not_special_methods(self):
        # Special methods are only ever looked up on the type of an object,
        # never on the instance itself. Instance attributes which shadow the
        # dunder names therefore do not make the wrapped object iterable, or
        # an iterator, and a proxy for the wrapped object must not act as
        # iterable or an iterator either.

        import collections.abc

        class Wrapped:
            pass

        instance = Wrapped()
        instance.__iter__ = lambda: iter([1, 2, 3])
        instance.__next__ = lambda: 42

        self.assertNotIsInstance(instance, collections.abc.Iterable)
        self.assertRaises(TypeError, iter, instance)
        self.assertRaises(TypeError, next, instance)

        proxy = wrapt.AutoObjectProxy(instance)

        # Note that iter() on the proxy does not itself raise TypeError, as
        # iteration falls back to the __getitem__() sequence protocol, which
        # wrapt.BaseObjectProxy always defines. Consuming the iterator still
        # fails though, as the wrapped instance is not subscriptable.

        self.assertNotIsInstance(proxy, collections.abc.Iterable)
        self.assertRaises(TypeError, list, proxy)
        self.assertRaises(TypeError, next, proxy)

    def test_instance_attributes_are_not_awaitable(self):
        # An instance attribute named __await__ does not make the wrapped
        # object awaitable, so a proxy for the wrapped object must not be
        # awaitable either.

        import inspect

        class Wrapped:
            pass

        instance = Wrapped()
        instance.__await__ = lambda: iter(())

        self.assertFalse(inspect.isawaitable(instance))

        proxy = wrapt.AutoObjectProxy(instance)

        self.assertFalse(inspect.isawaitable(proxy))

    def test_instance_dir_does_not_hide_special_methods(self):
        # The __dir__() method of an instance is not required to report the
        # special methods defined on the type of the instance, so the
        # special methods of the wrapped object can not be determined from
        # dir() of the wrapped object itself.

        class Wrapped:
            def __iter__(self):
                return iter([1, 2, 3])

            def __dir__(self):
                return []

        instance = Wrapped()

        self.assertEqual(list(instance), [1, 2, 3])

        proxy = wrapt.AutoObjectProxy(instance)

        self.assertEqual(list(proxy), [1, 2, 3])

    def test_wrapped_class_is_not_descriptor(self):
        class Descriptor:
            def __get__(self, instance, owner=None):
                return 42

            def __set__(self, instance, value):
                pass

            def __delete__(self, instance):
                pass

            def __set_name__(self, owner, name):
                pass

        # Only instances of the class are descriptors, not the class itself,
        # so a proxy for the class stored in a class body must not act as a
        # descriptor.

        class Owner:
            attr = wrapt.AutoObjectProxy(Descriptor)

        owner = Owner()

        self.assertIs(Owner.attr.__wrapped__, Descriptor)
        self.assertIs(owner.attr.__wrapped__, Descriptor)

        owner.attr = 100
        self.assertEqual(owner.attr, 100)

        del owner.attr
        self.assertIs(owner.attr.__wrapped__, Descriptor)

    def test_wrapped_class_is_not_awaitable_or_iterable(self):
        import collections.abc
        import inspect

        class Awaitable:
            def __await__(self):
                yield
                return 42

        class Iterable:
            def __iter__(self):
                return iter([1, 2, 3])

        # The special methods the classes define are for their instances, not
        # for the classes themselves, so the classes are not awaitable or
        # iterable, and proxies for the classes must not be either.

        self.assertFalse(inspect.isawaitable(Awaitable))
        self.assertNotIsInstance(Iterable, collections.abc.Iterable)

        self.assertFalse(inspect.isawaitable(wrapt.AutoObjectProxy(Awaitable)))
        self.assertNotIsInstance(
            wrapt.AutoObjectProxy(Iterable), collections.abc.Iterable
        )

    def test_wrapped_class_metaclass_iter(self):
        class Meta(type):
            def __iter__(cls):
                return iter([1, 2, 3])

        class Iterable(metaclass=Meta):
            pass

        # A class is iterated using the __iter__() defined by its metaclass,
        # as that is the type of the class, so a proxy for the class must be
        # iterable in the same way.

        self.assertEqual(list(Iterable), [1, 2, 3])

        proxy = wrapt.AutoObjectProxy(Iterable)

        self.assertEqual(list(proxy), [1, 2, 3])


class TestAutoObjectProxyReassignment(unittest.TestCase):

    def test_call_added_on_reassignment(self):
        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(callable(proxy))
        proxy.__wrapped__ = lambda: 42
        self.assertTrue(callable(proxy))
        self.assertEqual(proxy(), 42)

    def test_call_removed_on_reassignment(self):
        proxy = wrapt.AutoObjectProxy(lambda: 42)
        self.assertTrue(callable(proxy))
        proxy.__wrapped__ = object()
        self.assertFalse(callable(proxy))

    def test_iter_added_on_reassignment(self):
        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__iter__"))
        proxy.__wrapped__ = [1, 2, 3]
        self.assertTrue(hasattr(proxy, "__iter__"))
        self.assertEqual(list(proxy), [1, 2, 3])

    def test_iter_removed_on_reassignment(self):
        proxy = wrapt.AutoObjectProxy([1, 2, 3])
        self.assertTrue(hasattr(proxy, "__iter__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__iter__"))

    def test_fspath_added_on_reassignment(self):
        import os
        import pathlib

        proxy = wrapt.AutoObjectProxy(object())
        self.assertRaises(TypeError, os.fspath, proxy)
        proxy.__wrapped__ = pathlib.PurePath("/path/to/file")
        self.assertEqual(os.fspath(proxy), os.fspath(proxy.__wrapped__))

    def test_fspath_removed_on_reassignment(self):
        import os
        import pathlib

        proxy = wrapt.AutoObjectProxy(pathlib.PurePath("/path/to/file"))
        self.assertEqual(os.fspath(proxy), os.fspath(proxy.__wrapped__))
        proxy.__wrapped__ = object()
        self.assertRaises(TypeError, os.fspath, proxy)

    def test_next_added_on_reassignment(self):
        class Iterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise StopIteration

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__next__"))
        proxy.__wrapped__ = Iterator()
        self.assertTrue(hasattr(proxy, "__next__"))

    def test_next_removed_on_reassignment(self):
        class Iterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise StopIteration

        proxy = wrapt.AutoObjectProxy(Iterator())
        self.assertTrue(hasattr(proxy, "__next__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__next__"))

    def test_aiter_added_on_reassignment(self):
        class AsyncIterable:
            def __aiter__(self):
                return self

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__aiter__"))
        proxy.__wrapped__ = AsyncIterable()
        self.assertTrue(hasattr(proxy, "__aiter__"))

    def test_aiter_removed_on_reassignment(self):
        class AsyncIterable:
            def __aiter__(self):
                return self

        proxy = wrapt.AutoObjectProxy(AsyncIterable())
        self.assertTrue(hasattr(proxy, "__aiter__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__aiter__"))

    def test_anext_added_on_reassignment(self):
        class AsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__anext__"))
        proxy.__wrapped__ = AsyncIterator()
        self.assertTrue(hasattr(proxy, "__anext__"))

    def test_anext_removed_on_reassignment(self):
        class AsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        proxy = wrapt.AutoObjectProxy(AsyncIterator())
        self.assertTrue(hasattr(proxy, "__anext__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__anext__"))

    def test_length_hint_added_on_reassignment(self):
        import operator

        class LengthHint:
            def __length_hint__(self):
                return 42

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__length_hint__"))
        proxy.__wrapped__ = LengthHint()
        self.assertTrue(hasattr(proxy, "__length_hint__"))
        self.assertEqual(operator.length_hint(proxy), 42)

    def test_length_hint_removed_on_reassignment(self):
        class LengthHint:
            def __length_hint__(self):
                return 42

        proxy = wrapt.AutoObjectProxy(LengthHint())
        self.assertTrue(hasattr(proxy, "__length_hint__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__length_hint__"))

    def test_await_added_on_reassignment(self):
        class Awaitable:
            def __await__(self):
                yield
                return 42

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__await__"))
        proxy.__wrapped__ = Awaitable()
        self.assertTrue(hasattr(proxy, "__await__"))

    def test_await_removed_on_reassignment(self):
        class Awaitable:
            def __await__(self):
                yield
                return 42

        proxy = wrapt.AutoObjectProxy(Awaitable())
        self.assertTrue(hasattr(proxy, "__await__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__await__"))

    def test_get_added_on_reassignment(self):
        class Descriptor:
            def __get__(self, instance, owner):
                return 42

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__get__"))
        proxy.__wrapped__ = Descriptor()
        self.assertTrue(hasattr(proxy, "__get__"))
        self.assertEqual(proxy.__get__(object()), 42)

    def test_get_removed_on_reassignment(self):
        class Descriptor:
            def __get__(self, instance, owner):
                return 42

        proxy = wrapt.AutoObjectProxy(Descriptor())
        self.assertTrue(hasattr(proxy, "__get__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__get__"))

    def test_set_added_on_reassignment(self):
        class Descriptor:
            def __set__(self, instance, value):
                pass

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__set__"))
        proxy.__wrapped__ = Descriptor()
        self.assertTrue(hasattr(proxy, "__set__"))

    def test_set_removed_on_reassignment(self):
        class Descriptor:
            def __set__(self, instance, value):
                pass

        proxy = wrapt.AutoObjectProxy(Descriptor())
        self.assertTrue(hasattr(proxy, "__set__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__set__"))

    def test_delete_added_on_reassignment(self):
        class Descriptor:
            def __delete__(self, instance):
                pass

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__delete__"))
        proxy.__wrapped__ = Descriptor()
        self.assertTrue(hasattr(proxy, "__delete__"))

    def test_delete_removed_on_reassignment(self):
        class Descriptor:
            def __delete__(self, instance):
                pass

        proxy = wrapt.AutoObjectProxy(Descriptor())
        self.assertTrue(hasattr(proxy, "__delete__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__delete__"))

    def test_set_name_added_on_reassignment(self):
        class Descriptor:
            def __set_name__(self, owner, name):
                self.name = name

        proxy = wrapt.AutoObjectProxy(object())
        self.assertFalse(hasattr(proxy, "__set_name__"))
        proxy.__wrapped__ = Descriptor()
        self.assertTrue(hasattr(proxy, "__set_name__"))

    def test_set_name_removed_on_reassignment(self):
        class Descriptor:
            def __set_name__(self, owner, name):
                self.name = name

        proxy = wrapt.AutoObjectProxy(Descriptor())
        self.assertTrue(hasattr(proxy, "__set_name__"))
        proxy.__wrapped__ = object()
        self.assertFalse(hasattr(proxy, "__set_name__"))

    def test_instance_attributes_are_not_special_methods_on_reassignment(self):
        # Special methods are only ever looked up on the type of an object,
        # never on the instance itself, so instance attributes which shadow
        # the dunder names must not result in the proxy acting as iterable or
        # an iterator when __wrapped__ is reassigned.

        import collections.abc

        class Wrapped:
            pass

        instance = Wrapped()
        instance.__iter__ = lambda: iter([1, 2, 3])
        instance.__next__ = lambda: 42

        proxy = wrapt.AutoObjectProxy(object())

        proxy.__wrapped__ = instance

        self.assertNotIsInstance(proxy, collections.abc.Iterable)
        self.assertRaises(TypeError, list, proxy)
        self.assertRaises(TypeError, next, proxy)

    def test_instance_attributes_are_not_awaitable_on_reassignment(self):
        # An instance attribute named __await__ must not result in the proxy
        # being reported as awaitable when __wrapped__ is reassigned.

        import inspect

        class Wrapped:
            pass

        instance = Wrapped()
        instance.__await__ = lambda: iter(())

        proxy = wrapt.AutoObjectProxy(object())

        proxy.__wrapped__ = instance

        self.assertFalse(inspect.isawaitable(proxy))

    def test_wrapped_class_is_not_descriptor_on_reassignment(self):
        class Descriptor:
            def __get__(self, instance, owner=None):
                return 42

            def __set_name__(self, owner, name):
                pass

        # Only instances of the class are descriptors, not the class itself,
        # so the proxy must not act as a descriptor when __wrapped__ is
        # reassigned to the class.

        proxy = wrapt.AutoObjectProxy(object())
        proxy.__wrapped__ = Descriptor

        class Owner:
            attr = proxy

        self.assertIs(Owner().attr, proxy)

    def test_wrapped_class_metaclass_iter_on_reassignment(self):
        class Meta(type):
            def __iter__(cls):
                return iter([1, 2, 3])

        class Iterable(metaclass=Meta):
            pass

        # A class is iterated using the __iter__() defined by its metaclass,
        # as that is the type of the class, so iteration of the proxy must
        # still work when __wrapped__ is reassigned to the class.

        proxy = wrapt.AutoObjectProxy(object())
        proxy.__wrapped__ = Iterable

        self.assertEqual(list(proxy), [1, 2, 3])
