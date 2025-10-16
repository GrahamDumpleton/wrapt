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
