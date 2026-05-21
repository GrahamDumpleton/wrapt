import asyncio
import unittest

import wrapt


def _run(coro):
    return asyncio.run(coro)


@wrapt.synchronized
async def async_function():
    return "function"


class C1:

    @wrapt.synchronized
    async def method(self):
        return "method"

    @wrapt.synchronized
    @classmethod
    async def classmethod_(cls):
        return "classmethod"

    @wrapt.synchronized
    @staticmethod
    async def staticmethod_():
        return "staticmethod"


class TestAsyncDecorator(unittest.TestCase):

    def test_async_function(self):
        self.assertEqual(_run(async_function()), "function")

    def test_async_method(self):
        c = C1()
        self.assertEqual(_run(c.method()), "method")

    def test_async_classmethod(self):
        self.assertEqual(_run(C1.classmethod_()), "classmethod")

    def test_async_staticmethod(self):
        self.assertEqual(_run(C1.staticmethod_()), "staticmethod")

    def test_async_wrapper_is_coroutine_function(self):
        import inspect

        self.assertTrue(inspect.iscoroutinefunction(async_function))

    def test_per_instance_lock_created_lazily(self):
        c = C1()
        self.assertNotIn("_synchronized_async_lock", vars(c))
        _run(c.method())
        # Per-context lock stored on the instance itself (not the class), so
        # it is cleaned up when the instance is garbage collected.
        self.assertIn("_synchronized_async_lock", vars(c))

    def test_mutual_exclusion(self):
        # Two concurrent tasks on the same instance must serialise through the
        # per-instance asyncio.Lock.
        state = {"in_flight": 0, "max_concurrent": 0}

        class Holder:
            @wrapt.synchronized
            async def work(self):
                state["in_flight"] += 1
                state["max_concurrent"] = max(
                    state["max_concurrent"], state["in_flight"]
                )
                await asyncio.sleep(0.01)
                state["in_flight"] -= 1

        async def main():
            h = Holder()
            await asyncio.gather(*(h.work() for _ in range(5)))

        _run(main())
        self.assertEqual(state["max_concurrent"], 1)


class TestAsyncContextManager(unittest.TestCase):

    def test_async_with_on_decorator(self):
        @wrapt.synchronized
        def target():
            pass

        async def main():
            async with target:
                return "ok"

        self.assertEqual(_run(main()), "ok")

    def test_async_with_creates_independent_lock(self):
        @wrapt.synchronized
        def target():
            pass

        async def main():
            async with target:
                pass

        _run(main())
        self.assertTrue(hasattr(target.__wrapped__, "_synchronized_async_lock"))

    def test_sync_and_async_context_managers_coexist(self):
        @wrapt.synchronized
        def target():
            pass

        with target:
            pass

        async def main():
            async with target:
                pass

        _run(main())

        wrapped = target.__wrapped__
        self.assertTrue(hasattr(wrapped, "_synchronized_lock"))
        self.assertTrue(hasattr(wrapped, "_synchronized_async_lock"))
        # They are distinct objects of different types.
        self.assertIsNot(
            wrapped._synchronized_lock, wrapped._synchronized_async_lock
        )

    def test_async_context_mutual_exclusion(self):
        @wrapt.synchronized
        def target():
            pass

        state = {"in_flight": 0, "max_concurrent": 0}

        async def worker():
            async with target:
                state["in_flight"] += 1
                state["max_concurrent"] = max(
                    state["max_concurrent"], state["in_flight"]
                )
                await asyncio.sleep(0.01)
                state["in_flight"] -= 1

        async def main():
            await asyncio.gather(*(worker() for _ in range(4)))

        _run(main())
        self.assertEqual(state["max_concurrent"], 1)


class TestExplicitAsyncLock(unittest.TestCase):

    def test_decorator_with_asyncio_lock(self):
        async def main():
            lock = asyncio.Lock()

            @wrapt.synchronized(lock)
            async def fn():
                self.assertTrue(lock.locked())
                return 42

            return await fn()

        self.assertEqual(_run(main()), 42)

    def test_context_manager_with_asyncio_lock(self):
        async def main():
            lock = asyncio.Lock()
            cm = wrapt.synchronized(lock)
            async with cm as acquired:
                self.assertIs(acquired, lock)
                self.assertTrue(lock.locked())
            self.assertFalse(lock.locked())

        _run(main())

    def test_asyncio_lock_mutual_exclusion(self):
        async def main():
            lock = asyncio.Lock()

            @wrapt.synchronized(lock)
            async def fn(state):
                state["in_flight"] += 1
                state["max_concurrent"] = max(
                    state["max_concurrent"], state["in_flight"]
                )
                await asyncio.sleep(0.01)
                state["in_flight"] -= 1

            state = {"in_flight": 0, "max_concurrent": 0}
            await asyncio.gather(*(fn(state) for _ in range(5)))
            return state

        state = _run(main())
        self.assertEqual(state["max_concurrent"], 1)

    def test_async_with_synchronized_self_in_instance_method(self):
        # The method itself is NOT decorated; it uses
        # `async with wrapt.synchronized(self):` inside an async body. The
        # async lock should be created on the instance.

        class Holder:
            async def work(self):
                async with wrapt.synchronized(self):
                    return "ok"

        h = Holder()
        self.assertNotIn("_synchronized_async_lock", vars(h))

        self.assertEqual(_run(h.work()), "ok")

        self.assertIn("_synchronized_async_lock", vars(h))
        self.assertIsInstance(h._synchronized_async_lock, asyncio.Lock)

        # Separate instances get separate locks.
        h2 = Holder()
        _run(h2.work())
        self.assertIsNot(
            h._synchronized_async_lock, h2._synchronized_async_lock
        )

        # Mutual exclusion across tasks sharing the same instance.
        state = {"in_flight": 0, "max_concurrent": 0}

        class Contend:
            async def work(self, s):
                async with wrapt.synchronized(self):
                    s["in_flight"] += 1
                    s["max_concurrent"] = max(
                        s["max_concurrent"], s["in_flight"]
                    )
                    await asyncio.sleep(0.01)
                    s["in_flight"] -= 1

        async def main():
            c = Contend()
            await asyncio.gather(*(c.work(state) for _ in range(5)))

        _run(main())
        self.assertEqual(state["max_concurrent"], 1)

    def test_async_with_synchronized_arbitrary_shared_object(self):
        # Using `async with wrapt.synchronized(obj):` from unrelated async
        # callers locks notionally on `obj`: the asyncio.Lock is stored
        # as an attribute on `obj` and all callers share it.

        class Resource:
            pass

        shared = Resource()
        self.assertNotIn("_synchronized_async_lock", vars(shared))

        async def caller_one():
            async with wrapt.synchronized(shared):
                return shared._synchronized_async_lock

        async def caller_two():
            async with wrapt.synchronized(shared):
                return shared._synchronized_async_lock

        other = Resource()
        state = {"in_flight": 0, "max_concurrent": 0}

        async def worker():
            async with wrapt.synchronized(shared):
                state["in_flight"] += 1
                state["max_concurrent"] = max(
                    state["max_concurrent"], state["in_flight"]
                )
                await asyncio.sleep(0.01)
                state["in_flight"] -= 1

        async def main():
            lock_a = await caller_one()
            lock_b = await caller_two()
            async with wrapt.synchronized(other):
                pass
            await asyncio.gather(*(worker() for _ in range(5)))
            return lock_a, lock_b

        lock_a, lock_b = _run(main())

        self.assertIsInstance(lock_a, asyncio.Lock)
        self.assertIs(lock_a, lock_b)
        self.assertIs(shared._synchronized_async_lock, lock_a)

        # A different object gets its own independent lock.
        self.assertIsNot(
            shared._synchronized_async_lock, other._synchronized_async_lock
        )

        # Mutual exclusion across tasks targeting the same shared object.
        self.assertEqual(state["max_concurrent"], 1)

    def test_async_with_synchronized_cls_in_classmethod(self):
        # The classmethod itself is NOT decorated; it uses
        # `async with wrapt.synchronized(cls):` inside an async body. The
        # async lock should be created on the class.

        class Holder:
            @classmethod
            async def work(cls):
                async with wrapt.synchronized(cls):
                    return "ok"

        self.assertNotIn("_synchronized_async_lock", vars(Holder))

        self.assertEqual(_run(Holder.work()), "ok")

        self.assertIn("_synchronized_async_lock", vars(Holder))
        self.assertIsInstance(Holder._synchronized_async_lock, asyncio.Lock)

        # Mutual exclusion across tasks sharing the same class-level lock.
        state = {"in_flight": 0, "max_concurrent": 0}

        class Contend:
            @classmethod
            async def work(cls, s):
                async with wrapt.synchronized(cls):
                    s["in_flight"] += 1
                    s["max_concurrent"] = max(
                        s["max_concurrent"], s["in_flight"]
                    )
                    await asyncio.sleep(0.01)
                    s["in_flight"] -= 1

        async def main():
            await asyncio.gather(*(Contend.work(state) for _ in range(5)))

        _run(main())
        self.assertEqual(state["max_concurrent"], 1)

    def test_sync_lock_path_unchanged(self):
        # Passing a threading lock still goes through the sync branch.
        import threading

        lock = threading.Lock()

        @wrapt.synchronized(lock)
        def fn():
            self.assertTrue(lock.locked())
            return 1

        self.assertEqual(fn(), 1)
        self.assertFalse(lock.locked())


if __name__ == "__main__":
    unittest.main()
