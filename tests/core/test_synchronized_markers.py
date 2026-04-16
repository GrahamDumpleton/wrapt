import asyncio
import inspect
import unittest

import wrapt


def _run(coro):
    return asyncio.run(coro)


class TestMarkAsSync(unittest.TestCase):

    def test_async_def_reports_not_coroutine(self):
        async def f():
            return 1

        wrapped = wrapt.mark_as_sync(f)
        self.assertFalse(inspect.iscoroutinefunction(wrapped))

    def test_sync_def_reports_not_coroutine(self):
        def f():
            return 1

        wrapped = wrapt.mark_as_sync(f)
        self.assertFalse(inspect.iscoroutinefunction(wrapped))

    def test_signature_preserved(self):
        async def f(a, b, c=3):
            return a + b + c

        wrapped = wrapt.mark_as_sync(f)
        self.assertEqual(inspect.signature(wrapped), inspect.signature(f))

    def test_on_method_class_and_instance_access(self):
        class C:
            @wrapt.mark_as_sync
            async def m(self):
                return 1

        c = C()
        self.assertFalse(inspect.iscoroutinefunction(C.m))
        self.assertFalse(inspect.iscoroutinefunction(c.m))

    def test_survives_passthrough_decorator(self):
        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthrough
        @wrapt.mark_as_sync
        async def f(a, b):
            return a + b

        self.assertFalse(inspect.iscoroutinefunction(f))
        self.assertEqual(str(inspect.signature(f)), "(a, b)")


class TestMarkAsAsync(unittest.TestCase):

    def test_sync_def_reports_coroutine(self):
        def f():
            return 1

        wrapped = wrapt.mark_as_async(f)
        self.assertTrue(inspect.iscoroutinefunction(wrapped))

    def test_async_def_reports_coroutine(self):
        async def f():
            return 1

        wrapped = wrapt.mark_as_async(f)
        self.assertTrue(inspect.iscoroutinefunction(wrapped))

    def test_signature_preserved(self):
        def f(a, b, c=3):
            return a + b + c

        wrapped = wrapt.mark_as_async(f)
        self.assertEqual(inspect.signature(wrapped), inspect.signature(f))

    def test_on_method_class_and_instance_access(self):
        class D:
            @wrapt.mark_as_async
            def m(self):
                return 1

        d = D()
        self.assertTrue(inspect.iscoroutinefunction(D.m))
        self.assertTrue(inspect.iscoroutinefunction(d.m))

    def test_survives_passthrough_decorator(self):
        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthrough
        @wrapt.mark_as_async
        def f(a, b):
            return a * b

        self.assertTrue(inspect.iscoroutinefunction(f))


class TestAsyncToSync(unittest.TestCase):

    def test_runs_async_synchronously(self):
        @wrapt.async_to_sync
        async def add(a, b):
            return a + b

        self.assertFalse(inspect.iscoroutinefunction(add))
        self.assertEqual(add(2, 3), 5)

    def test_signature_preserved(self):
        async def add(a, b):
            return a + b

        wrapped = wrapt.async_to_sync(add)
        self.assertEqual(inspect.signature(wrapped), inspect.signature(add))

    def test_stacked_under_passthrough(self):
        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthrough
        @wrapt.async_to_sync
        async def sub(a, b):
            return a - b

        self.assertFalse(inspect.iscoroutinefunction(sub))
        self.assertEqual(sub(10, 3), 7)


class TestSyncToAsync(unittest.TestCase):

    def test_runs_sync_in_executor(self):
        @wrapt.sync_to_async
        def mul(a, b):
            return a * b

        self.assertTrue(inspect.iscoroutinefunction(mul))
        self.assertEqual(_run(mul(4, 5)), 20)

    def test_signature_preserved(self):
        def mul(a, b):
            return a * b

        wrapped = wrapt.sync_to_async(mul)
        self.assertEqual(inspect.signature(wrapped), inspect.signature(mul))

    def test_stacked_under_passthrough(self):
        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthrough
        @wrapt.sync_to_async
        def add(a, b):
            return a + b

        self.assertTrue(inspect.iscoroutinefunction(add))
        self.assertEqual(_run(add(1, 2)), 3)


class TestSynchronizedWithMarkers(unittest.TestCase):

    def test_synchronized_over_async_to_sync_async_def(self):
        @wrapt.synchronized
        @wrapt.async_to_sync
        async def f(x):
            return x + 1

        self.assertFalse(inspect.iscoroutinefunction(f))
        self.assertEqual(f(10), 11)

    def test_synchronized_over_sync_to_async_sync_def(self):
        @wrapt.synchronized
        @wrapt.sync_to_async
        def f(x):
            return x * 2

        self.assertTrue(inspect.iscoroutinefunction(f))
        self.assertEqual(_run(f(10)), 20)

    def test_synchronized_over_mark_as_async_sync_def(self):
        @wrapt.synchronized
        @wrapt.mark_as_async
        async def inner(x):
            return x + 1

        # Effectively async: synchronized picks async wrapper.
        self.assertTrue(inspect.iscoroutinefunction(inner))

    def test_unmarked_async_def_still_auto_detects(self):
        @wrapt.synchronized
        async def f():
            return "async"

        self.assertTrue(inspect.iscoroutinefunction(f))
        self.assertEqual(_run(f()), "async")

    def test_unmarked_sync_def_still_auto_detects(self):
        @wrapt.synchronized
        def f():
            return "sync"

        self.assertFalse(inspect.iscoroutinefunction(f))
        self.assertEqual(f(), "sync")


class TestDetectionInternals(unittest.TestCase):

    def _detect(self, obj):
        from wrapt.decorators import _synchronized_is_async_callable

        return _synchronized_is_async_callable(obj)

    def test_first_true_wins(self):
        async def inner():
            return 1

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        outer = passthrough(inner)
        self.assertTrue(self._detect(outer))

    def test_not_coroutine_marker_short_circuits(self):
        async def inner():
            return 1

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        outer = passthrough(wrapt.mark_as_sync(inner))
        self.assertFalse(self._detect(outer))

    def test_functools_wraps_sync_over_async_descends(self):
        import functools

        async def inner():
            return 1

        @functools.wraps(inner)
        def outer():
            return inner()

        # Outer is plain def, so iscoroutinefunction(outer) is False,
        # but the walk descends via __wrapped__ and finds inner.
        self.assertTrue(self._detect(outer))

    def test_classmethod_at_each_layer(self):
        class C:
            @classmethod
            async def m(cls):
                return 1

        self.assertTrue(self._detect(C.__dict__["m"]))

    def test_cycle_raises(self):
        class Cycle:
            pass

        a = Cycle()
        b = Cycle()
        a.__wrapped__ = b
        b.__wrapped__ = a

        with self.assertRaises(ValueError):
            self._detect(a)


if __name__ == "__main__":
    unittest.main()
