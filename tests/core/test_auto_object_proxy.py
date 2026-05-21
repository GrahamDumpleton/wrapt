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
