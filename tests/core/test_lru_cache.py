import gc
import inspect
import unittest
import weakref

import wrapt


@wrapt.lru_cache
def cached_function(x):
    return x * 2


@wrapt.lru_cache(maxsize=32)
def cached_function_with_args(x):
    return x * 2


class CachedClass:
    @wrapt.lru_cache
    def method(self, x):
        return x * 2

    @wrapt.lru_cache(maxsize=32)
    @classmethod
    def class_method(cls, x):
        return x * 3

    @wrapt.lru_cache
    @staticmethod
    def static_method(x):
        return x * 4


class TestPlainFunction(unittest.TestCase):
    def setUp(self):
        cached_function.cache_clear()

    def test_returns_correct_result(self):
        self.assertEqual(cached_function(5), 10)

    def test_caching(self):
        cached_function(5)
        cached_function(5)
        info = cached_function.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)

    def test_cache_clear(self):
        cached_function(5)
        cached_function.cache_clear()
        info = cached_function.cache_info()
        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 0)
        self.assertEqual(info.currsize, 0)

    def test_different_args_cached_separately(self):
        cached_function(1)
        cached_function(2)
        cached_function(1)
        info = cached_function.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 2)
        self.assertEqual(info.currsize, 2)

    def test_cache_info_before_call(self):
        @wrapt.lru_cache
        def uncalled(x):
            return x

        self.assertIsNone(uncalled.cache_info())


class TestPlainFunctionWithArgs(unittest.TestCase):
    def setUp(self):
        cached_function_with_args.cache_clear()

    def test_returns_correct_result(self):
        self.assertEqual(cached_function_with_args(5), 10)

    def test_maxsize_passed_through(self):
        cached_function_with_args(5)
        info = cached_function_with_args.cache_info()
        self.assertEqual(info.maxsize, 32)

    def test_cache_parameters(self):
        cached_function_with_args(5)
        params = cached_function_with_args.cache_parameters()
        self.assertEqual(params["maxsize"], 32)
        self.assertFalse(params["typed"])


class CachedClassWithState:
    def __init__(self, factor):
        self.factor = factor

    @wrapt.lru_cache
    def method(self, x):
        return x * self.factor


class TestInstanceMethod(unittest.TestCase):
    def test_returns_correct_result(self):
        obj = CachedClass()
        self.assertEqual(obj.method(5), 10)

    def test_caching(self):
        obj = CachedClass()
        obj.method(5)
        obj.method(5)
        info = obj.method.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)

    def test_per_instance_separate_caches(self):
        obj1 = CachedClass()
        obj2 = CachedClass()
        obj1.method(5)
        obj2.method(5)
        info1 = obj1.method.cache_info()
        info2 = obj2.method.cache_info()
        self.assertEqual(info1.misses, 1)
        self.assertEqual(info2.misses, 1)

    def test_per_instance_correct_self(self):
        obj1 = CachedClassWithState(2)
        obj2 = CachedClassWithState(3)
        self.assertEqual(obj1.method(5), 10)
        self.assertEqual(obj2.method(5), 15)

    def test_instance_not_retained_by_cache(self):
        obj = CachedClass()
        ref = weakref.ref(obj)
        obj.method(5)
        del obj
        gc.collect()
        self.assertIsNone(ref())

    def test_cache_clear_per_instance(self):
        obj = CachedClass()
        obj.method(5)
        obj.method.cache_clear()
        obj.method(5)
        info = obj.method.cache_info()
        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 1)

    def test_cache_info_before_call(self):
        obj = CachedClass()
        self.assertIsNone(obj.method.cache_info())

    def test_non_hashable_instance(self):
        class Unhashable:
            __hash__ = None

            @wrapt.lru_cache
            def method(self, x):
                return x * 2

        obj = Unhashable()
        self.assertEqual(obj.method(5), 10)
        self.assertEqual(obj.method(5), 10)


class TestInstanceMethodCacheParameters(unittest.TestCase):
    def test_cache_parameters(self):
        obj = CachedClassSmall()
        obj.method(5)
        params = obj.method.cache_parameters()
        self.assertEqual(params["maxsize"], 2)
        self.assertFalse(params["typed"])

    def test_cache_parameters_before_call(self):
        obj = CachedClass()
        self.assertIsNone(obj.method.cache_parameters())


class CachedClassSmall:
    @wrapt.lru_cache(maxsize=2)
    def method(self, x):
        return x * 2


class TestInstanceMethodEviction(unittest.TestCase):
    def test_per_instance_maxsize(self):
        obj = CachedClassSmall()
        obj.method(1)
        obj.method(2)
        info = obj.method.cache_info()
        self.assertEqual(info.currsize, 2)
        self.assertEqual(info.maxsize, 2)

    def test_eviction_within_instance(self):
        obj = CachedClassSmall()
        obj.method(1)
        obj.method(2)
        obj.method(3)  # evicts 1
        obj.method(1)  # miss, was evicted
        info = obj.method.cache_info()
        self.assertEqual(info.misses, 4)
        self.assertEqual(info.currsize, 2)

    def test_eviction_independent_across_instances(self):
        obj1 = CachedClassSmall()
        obj2 = CachedClassSmall()
        obj1.method(1)
        obj1.method(2)
        obj1.method(3)  # evicts 1 from obj1
        obj2.method(1)
        obj2.method(2)
        info2 = obj2.method.cache_info()
        self.assertEqual(info2.misses, 2)
        self.assertEqual(info2.currsize, 2)
        obj1.method(1)
        info1 = obj1.method.cache_info()
        self.assertEqual(info1.misses, 4)


class TestClassMethod(unittest.TestCase):
    def setUp(self):
        CachedClass.class_method.cache_clear()

    def test_returns_correct_result(self):
        self.assertEqual(CachedClass.class_method(5), 15)

    def test_caching(self):
        CachedClass.class_method(5)
        CachedClass.class_method(5)
        info = CachedClass.class_method.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)

    def test_access_via_instance(self):
        CachedClass.class_method(5)
        obj = CachedClass()
        obj.class_method(5)
        info = obj.class_method.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)

    def test_maxsize_passed_through(self):
        CachedClass.class_method(5)
        info = CachedClass.class_method.cache_info()
        self.assertEqual(info.maxsize, 32)


class TestStaticMethod(unittest.TestCase):
    def setUp(self):
        CachedClass.static_method.cache_clear()

    def test_returns_correct_result(self):
        self.assertEqual(CachedClass.static_method(5), 20)

    def test_caching(self):
        CachedClass.static_method(5)
        CachedClass.static_method(5)
        info = CachedClass.static_method.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)

    def test_access_via_instance(self):
        CachedClass.static_method(5)
        obj = CachedClass()
        obj.static_method(5)
        info = obj.static_method.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)


class OverrideBase:
    def __init__(self):
        self.base_calls = 0
        self.derived_calls = 0

    @wrapt.lru_cache
    def compute(self, x):
        self.base_calls += 1
        return x * 2


class OverrideDerived(OverrideBase):
    @wrapt.lru_cache
    def compute(self, x):
        self.derived_calls += 1
        return super().compute(x) + 1


class TestOverriddenMethodWithSuper(unittest.TestCase):
    def test_super_call_returns_correct_result(self):
        obj = OverrideDerived()
        self.assertEqual(obj.compute(10), 21)

    def test_super_call_does_not_recurse(self):
        # Regression test: a subclass method decorated with lru_cache that
        # called the base method via super() used to recurse forever because
        # the base and derived methods shared a single per-instance cache
        # slot derived from the method name alone.
        obj = OverrideDerived()
        try:
            result = obj.compute(10)
        except RecursionError:
            self.fail("super() call recursed instead of reaching base method")
        self.assertEqual(result, 21)

    def test_both_bodies_execute_once(self):
        obj = OverrideDerived()
        obj.compute(10)
        self.assertEqual(obj.derived_calls, 1)
        self.assertEqual(obj.base_calls, 1)

    def test_base_and_derived_cached_independently(self):
        obj = OverrideDerived()
        obj.compute(10)
        obj.compute(10)
        # Second call is served from both caches, so neither body re-runs.
        self.assertEqual(obj.derived_calls, 1)
        self.assertEqual(obj.base_calls, 1)
        info = obj.compute.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 1)

    def test_base_class_instance_unaffected(self):
        obj = OverrideBase()
        self.assertEqual(obj.compute(10), 20)
        self.assertEqual(obj.base_calls, 1)
        self.assertEqual(obj.derived_calls, 0)

    def test_separate_instances_have_separate_caches(self):
        obj1 = OverrideDerived()
        obj2 = OverrideDerived()
        obj1.compute(10)
        obj2.compute(10)
        self.assertEqual(obj1.derived_calls, 1)
        self.assertEqual(obj2.derived_calls, 1)
        self.assertEqual(obj1.base_calls, 1)
        self.assertEqual(obj2.base_calls, 1)


class TestIntrospection(unittest.TestCase):
    def test_function_name(self):
        self.assertEqual(cached_function.__name__, "cached_function")

    def test_function_qualname(self):
        self.assertEqual(cached_function.__qualname__, "cached_function")

    def test_function_signature(self):
        sig = inspect.signature(cached_function)
        self.assertEqual(list(sig.parameters), ["x"])

    def test_method_name(self):
        self.assertEqual(CachedClass.method.__name__, "method")

    def test_method_qualname(self):
        self.assertEqual(CachedClass.method.__qualname__, "CachedClass.method")

    def test_bound_method_signature(self):
        obj = CachedClass()
        sig = inspect.signature(obj.method)
        self.assertEqual(list(sig.parameters), ["x"])


if __name__ == "__main__":
    unittest.main()
