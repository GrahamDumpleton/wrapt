import inspect
import unittest

import wrapt


def track_calls_wrapper_attrs(func):
    state = {"call_count": 0}

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        state["call_count"] += 1
        return wrapped(*args, **kwargs)

    decorated = wrapper(func)

    # Have to use __self_setattr__ since object.__setattr__ will fail
    # for Python <3.13 otherwise.

    decorated.__self_setattr__("call_count", lambda: state["call_count"])
    decorated.__self_setattr__("reset", lambda: state.update(call_count=0))

    return decorated


def track_calls_wrapped_attrs(func):
    state = {"call_count": 0}

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        state["call_count"] += 1
        return wrapped(*args, **kwargs)

    decorated = wrapper(func)

    func.call_count = lambda: state["call_count"]
    func.reset = lambda: state.update(call_count=0)

    return decorated


@track_calls_wrapper_attrs
def wrapper_attrs_function(x, y):
    return x + y


class WrapperAttrsClass:
    @track_calls_wrapper_attrs
    def method(self, x, y):
        return x + y

    @track_calls_wrapper_attrs
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @track_calls_wrapper_attrs
    @staticmethod
    def static_method(x, y):
        return x + y


@track_calls_wrapped_attrs
def wrapped_attrs_function(x, y):
    return x + y


class WrappedAttrsClass:
    @track_calls_wrapped_attrs
    def method(self, x, y):
        return x + y

    @track_calls_wrapped_attrs
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @track_calls_wrapped_attrs
    @staticmethod
    def static_method(x, y):
        return x + y




class TestNormalFunctionWrapperAttrs(unittest.TestCase):
    def setUp(self):
        wrapper_attrs_function.reset()

    def test_initial_count_zero(self):
        self.assertEqual(wrapper_attrs_function.call_count(), 0)

    def test_count_increments(self):
        wrapper_attrs_function(1, 2)
        self.assertEqual(wrapper_attrs_function.call_count(), 1)
        wrapper_attrs_function(3, 4)
        self.assertEqual(wrapper_attrs_function.call_count(), 2)

    def test_reset(self):
        wrapper_attrs_function(1, 2)
        wrapper_attrs_function(3, 4)
        self.assertEqual(wrapper_attrs_function.call_count(), 2)
        wrapper_attrs_function.reset()
        self.assertEqual(wrapper_attrs_function.call_count(), 0)

    def test_function_still_works(self):
        result = wrapper_attrs_function(1, 2)
        self.assertEqual(result, 3)




class TestInstanceMethodWrapperAttrs(unittest.TestCase):
    def setUp(self):
        WrapperAttrsClass.method.reset()

    def test_count_increments(self):
        obj = WrapperAttrsClass()
        obj.method(1, 2)
        self.assertEqual(obj.method.call_count(), 1)
        obj.method(3, 4)
        self.assertEqual(obj.method.call_count(), 2)

    def test_reset(self):
        obj = WrapperAttrsClass()
        obj.method(1, 2)
        obj.method(3, 4)
        self.assertEqual(obj.method.call_count(), 2)
        obj.method.reset()
        self.assertEqual(obj.method.call_count(), 0)

    def test_method_still_works(self):
        obj = WrapperAttrsClass()
        result = obj.method(1, 2)
        self.assertEqual(result, 3)

    def test_separate_instances_share_count(self):
        obj1 = WrapperAttrsClass()
        obj2 = WrapperAttrsClass()
        obj1.method(1, 2)
        obj2.method(3, 4)
        self.assertEqual(obj1.method.call_count(), 2)
        self.assertEqual(obj2.method.call_count(), 2)




class TestClassMethodWrapperAttrs(unittest.TestCase):
    def setUp(self):
        WrapperAttrsClass.class_method.reset()

    def test_count_increments(self):
        WrapperAttrsClass.class_method(1, 2)
        self.assertEqual(WrapperAttrsClass.class_method.call_count(), 1)
        WrapperAttrsClass.class_method(3, 4)
        self.assertEqual(WrapperAttrsClass.class_method.call_count(), 2)

    def test_reset(self):
        WrapperAttrsClass.class_method(1, 2)
        WrapperAttrsClass.class_method(3, 4)
        self.assertEqual(WrapperAttrsClass.class_method.call_count(), 2)
        WrapperAttrsClass.class_method.reset()
        self.assertEqual(WrapperAttrsClass.class_method.call_count(), 0)

    def test_classmethod_still_works(self):
        result = WrapperAttrsClass.class_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = WrapperAttrsClass()
        WrapperAttrsClass.class_method(1, 2)
        self.assertEqual(obj.class_method.call_count(), 1)




class TestStaticMethodWrapperAttrs(unittest.TestCase):
    def setUp(self):
        WrapperAttrsClass.static_method.reset()

    def test_count_increments(self):
        WrapperAttrsClass.static_method(1, 2)
        self.assertEqual(WrapperAttrsClass.static_method.call_count(), 1)
        WrapperAttrsClass.static_method(3, 4)
        self.assertEqual(WrapperAttrsClass.static_method.call_count(), 2)

    def test_reset(self):
        WrapperAttrsClass.static_method(1, 2)
        WrapperAttrsClass.static_method(3, 4)
        self.assertEqual(WrapperAttrsClass.static_method.call_count(), 2)
        WrapperAttrsClass.static_method.reset()
        self.assertEqual(WrapperAttrsClass.static_method.call_count(), 0)

    def test_staticmethod_still_works(self):
        result = WrapperAttrsClass.static_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = WrapperAttrsClass()
        WrapperAttrsClass.static_method(1, 2)
        self.assertEqual(obj.static_method.call_count(), 1)


class TestNormalFunctionWrappedAttrs(unittest.TestCase):
    def setUp(self):
        wrapped_attrs_function.reset()

    def test_initial_count_zero(self):
        self.assertEqual(wrapped_attrs_function.call_count(), 0)

    def test_count_increments(self):
        wrapped_attrs_function(1, 2)
        self.assertEqual(wrapped_attrs_function.call_count(), 1)
        wrapped_attrs_function(3, 4)
        self.assertEqual(wrapped_attrs_function.call_count(), 2)

    def test_reset(self):
        wrapped_attrs_function(1, 2)
        wrapped_attrs_function(3, 4)
        self.assertEqual(wrapped_attrs_function.call_count(), 2)
        wrapped_attrs_function.reset()
        self.assertEqual(wrapped_attrs_function.call_count(), 0)

    def test_function_still_works(self):
        result = wrapped_attrs_function(1, 2)
        self.assertEqual(result, 3)


class TestInstanceMethodWrappedAttrs(unittest.TestCase):
    def setUp(self):
        WrappedAttrsClass.method.reset()

    def test_count_increments(self):
        obj = WrappedAttrsClass()
        obj.method(1, 2)
        self.assertEqual(obj.method.call_count(), 1)
        obj.method(3, 4)
        self.assertEqual(obj.method.call_count(), 2)

    def test_reset(self):
        obj = WrappedAttrsClass()
        obj.method(1, 2)
        obj.method(3, 4)
        self.assertEqual(obj.method.call_count(), 2)
        obj.method.reset()
        self.assertEqual(obj.method.call_count(), 0)

    def test_method_still_works(self):
        obj = WrappedAttrsClass()
        result = obj.method(1, 2)
        self.assertEqual(result, 3)

    def test_separate_instances_share_count(self):
        obj1 = WrappedAttrsClass()
        obj2 = WrappedAttrsClass()
        obj1.method(1, 2)
        obj2.method(3, 4)
        self.assertEqual(obj1.method.call_count(), 2)
        self.assertEqual(obj2.method.call_count(), 2)


class TestClassMethodWrappedAttrs(unittest.TestCase):
    def setUp(self):
        WrappedAttrsClass.class_method.reset()

    def test_count_increments(self):
        WrappedAttrsClass.class_method(1, 2)
        self.assertEqual(WrappedAttrsClass.class_method.call_count(), 1)
        WrappedAttrsClass.class_method(3, 4)
        self.assertEqual(WrappedAttrsClass.class_method.call_count(), 2)

    def test_reset(self):
        WrappedAttrsClass.class_method(1, 2)
        WrappedAttrsClass.class_method(3, 4)
        self.assertEqual(WrappedAttrsClass.class_method.call_count(), 2)
        WrappedAttrsClass.class_method.reset()
        self.assertEqual(WrappedAttrsClass.class_method.call_count(), 0)

    def test_classmethod_still_works(self):
        result = WrappedAttrsClass.class_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = WrappedAttrsClass()
        WrappedAttrsClass.class_method(1, 2)
        self.assertEqual(obj.class_method.call_count(), 1)


class TestStaticMethodWrappedAttrs(unittest.TestCase):
    def setUp(self):
        WrappedAttrsClass.static_method.reset()

    def test_count_increments(self):
        WrappedAttrsClass.static_method(1, 2)
        self.assertEqual(WrappedAttrsClass.static_method.call_count(), 1)
        WrappedAttrsClass.static_method(3, 4)
        self.assertEqual(WrappedAttrsClass.static_method.call_count(), 2)

    def test_reset(self):
        WrappedAttrsClass.static_method(1, 2)
        WrappedAttrsClass.static_method(3, 4)
        self.assertEqual(WrappedAttrsClass.static_method.call_count(), 2)
        WrappedAttrsClass.static_method.reset()
        self.assertEqual(WrappedAttrsClass.static_method.call_count(), 0)

    def test_staticmethod_still_works(self):
        result = WrappedAttrsClass.static_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = WrappedAttrsClass()
        WrappedAttrsClass.static_method(1, 2)
        self.assertEqual(obj.static_method.call_count(), 1)


class CountedBoundWrapper(wrapt.BoundFunctionWrapper):
    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        finally:
            self._self_call_count += 1


class CountedWrapper(wrapt.FunctionWrapper):
    __bound_function_wrapper__ = CountedBoundWrapper

    def __init__(self, wrapped, wrapper, **kwargs):
        super().__init__(wrapped, wrapper, **kwargs)
        self._self_call_count = 0

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        finally:
            self._self_call_count += 1


@wrapt.decorator(proxy=CountedWrapper)
def counted_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


@counted_decorator
def counted_function(x, y):
    return x + y


class CountedClass:
    @counted_decorator
    def method(self, x, y):
        return x + y

    @counted_decorator
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @counted_decorator
    @staticmethod
    def static_method(x, y):
        return x + y


class TestNormalFunctionCountedWrapper(unittest.TestCase):
    def setUp(self):
        counted_function._self_call_count = 0

    def test_count_increments(self):
        counted_function(1, 2)
        self.assertEqual(counted_function._self_call_count, 1)
        counted_function(3, 4)
        self.assertEqual(counted_function._self_call_count, 2)

    def test_function_still_works(self):
        result = counted_function(1, 2)
        self.assertEqual(result, 3)


class TestInstanceMethodCountedWrapper(unittest.TestCase):
    def setUp(self):
        CountedClass.method._self_call_count = 0

    def test_count_increments(self):
        obj = CountedClass()
        obj.method(1, 2)
        self.assertEqual(obj.method._self_call_count, 1)
        obj.method(3, 4)
        self.assertEqual(obj.method._self_call_count, 2)

    def test_method_still_works(self):
        obj = CountedClass()
        result = obj.method(1, 2)
        self.assertEqual(result, 3)

    def test_separate_instances_share_count(self):
        obj1 = CountedClass()
        obj2 = CountedClass()
        obj1.method(1, 2)
        obj2.method(3, 4)
        self.assertEqual(obj1.method._self_call_count, 2)
        self.assertEqual(obj2.method._self_call_count, 2)


class TestClassMethodCountedWrapper(unittest.TestCase):
    def setUp(self):
        CountedClass.class_method._self_call_count = 0

    def test_count_increments(self):
        CountedClass.class_method(1, 2)
        self.assertEqual(CountedClass.class_method._self_call_count, 1)
        CountedClass.class_method(3, 4)
        self.assertEqual(CountedClass.class_method._self_call_count, 2)

    def test_classmethod_still_works(self):
        result = CountedClass.class_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = CountedClass()
        CountedClass.class_method(1, 2)
        self.assertEqual(obj.class_method._self_call_count, 1)


class TestStaticMethodCountedWrapper(unittest.TestCase):
    def setUp(self):
        CountedClass.static_method._self_call_count = 0

    def test_count_increments(self):
        CountedClass.static_method(1, 2)
        self.assertEqual(CountedClass.static_method._self_call_count, 1)
        CountedClass.static_method(3, 4)
        self.assertEqual(CountedClass.static_method._self_call_count, 2)

    def test_staticmethod_still_works(self):
        result = CountedClass.static_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = CountedClass()
        CountedClass.static_method(1, 2)
        self.assertEqual(obj.static_method._self_call_count, 1)


class CallTracker:
    def __init__(self):
        self.call_count = 0

    @wrapt.function_wrapper
    def track(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1


def track_calls_tracker(func):
    tracker = CallTracker()
    wrapper = tracker.track(func)
    wrapper.__self_setattr__("tracker", tracker)
    return wrapper


@track_calls_tracker
def tracker_function(x, y):
    return x + y


class TrackerClass:
    @track_calls_tracker
    def method(self, x, y):
        return x + y

    @track_calls_tracker
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @track_calls_tracker
    @staticmethod
    def static_method(x, y):
        return x + y




class TestNormalFunctionTracker(unittest.TestCase):
    def setUp(self):
        tracker_function.tracker.call_count = 0

    def test_initial_count_zero(self):
        self.assertEqual(tracker_function.tracker.call_count, 0)

    def test_count_increments(self):
        tracker_function(1, 2)
        self.assertEqual(tracker_function.tracker.call_count, 1)
        tracker_function(3, 4)
        self.assertEqual(tracker_function.tracker.call_count, 2)

    def test_reset(self):
        tracker_function(1, 2)
        tracker_function(3, 4)
        tracker_function.tracker.call_count = 0
        self.assertEqual(tracker_function.tracker.call_count, 0)

    def test_function_still_works(self):
        result = tracker_function(1, 2)
        self.assertEqual(result, 3)




class TestInstanceMethodTracker(unittest.TestCase):
    def setUp(self):
        TrackerClass.method.tracker.call_count = 0

    def test_count_increments(self):
        obj = TrackerClass()
        obj.method(1, 2)
        self.assertEqual(obj.method.tracker.call_count, 1)
        obj.method(3, 4)
        self.assertEqual(obj.method.tracker.call_count, 2)

    def test_reset(self):
        obj = TrackerClass()
        obj.method(1, 2)
        obj.method(3, 4)
        obj.method.tracker.call_count = 0
        self.assertEqual(obj.method.tracker.call_count, 0)

    def test_method_still_works(self):
        obj = TrackerClass()
        result = obj.method(1, 2)
        self.assertEqual(result, 3)

    def test_separate_instances_share_count(self):
        obj1 = TrackerClass()
        obj2 = TrackerClass()
        obj1.method(1, 2)
        obj2.method(3, 4)
        self.assertEqual(obj1.method.tracker.call_count, 2)
        self.assertEqual(obj2.method.tracker.call_count, 2)




class TestClassMethodTracker(unittest.TestCase):
    def setUp(self):
        TrackerClass.class_method.tracker.call_count = 0

    def test_count_increments(self):
        TrackerClass.class_method(1, 2)
        self.assertEqual(TrackerClass.class_method.tracker.call_count, 1)
        TrackerClass.class_method(3, 4)
        self.assertEqual(TrackerClass.class_method.tracker.call_count, 2)

    def test_reset(self):
        TrackerClass.class_method(1, 2)
        TrackerClass.class_method(3, 4)
        TrackerClass.class_method.tracker.call_count = 0
        self.assertEqual(TrackerClass.class_method.tracker.call_count, 0)

    def test_classmethod_still_works(self):
        result = TrackerClass.class_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = TrackerClass()
        TrackerClass.class_method(1, 2)
        self.assertEqual(obj.class_method.tracker.call_count, 1)




class TestStaticMethodTracker(unittest.TestCase):
    def setUp(self):
        TrackerClass.static_method.tracker.call_count = 0

    def test_count_increments(self):
        TrackerClass.static_method(1, 2)
        self.assertEqual(TrackerClass.static_method.tracker.call_count, 1)
        TrackerClass.static_method(3, 4)
        self.assertEqual(TrackerClass.static_method.tracker.call_count, 2)

    def test_reset(self):
        TrackerClass.static_method(1, 2)
        TrackerClass.static_method(3, 4)
        TrackerClass.static_method.tracker.call_count = 0
        self.assertEqual(TrackerClass.static_method.tracker.call_count, 0)

    def test_staticmethod_still_works(self):
        result = TrackerClass.static_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = TrackerClass()
        TrackerClass.static_method(1, 2)
        self.assertEqual(obj.static_method.tracker.call_count, 1)


class BoundCallTracker:
    def __init__(self):
        self.call_count = 0

    @wrapt.bind_state_to_wrapper(name="tracker")
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1


@BoundCallTracker()
def bound_tracker_function(x, y):
    return x + y


class BoundTrackerClass:
    @BoundCallTracker()
    def method(self, x, y):
        return x + y

    @BoundCallTracker()
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @BoundCallTracker()
    @staticmethod
    def static_method(x, y):
        return x + y


class TestNormalFunctionBoundTracker(unittest.TestCase):
    def setUp(self):
        bound_tracker_function.tracker.call_count = 0

    def test_initial_count_zero(self):
        self.assertEqual(bound_tracker_function.tracker.call_count, 0)

    def test_count_increments(self):
        bound_tracker_function(1, 2)
        self.assertEqual(bound_tracker_function.tracker.call_count, 1)
        bound_tracker_function(3, 4)
        self.assertEqual(bound_tracker_function.tracker.call_count, 2)

    def test_reset(self):
        bound_tracker_function(1, 2)
        bound_tracker_function(3, 4)
        bound_tracker_function.tracker.call_count = 0
        self.assertEqual(bound_tracker_function.tracker.call_count, 0)

    def test_function_still_works(self):
        result = bound_tracker_function(1, 2)
        self.assertEqual(result, 3)


class TestInstanceMethodBoundTracker(unittest.TestCase):
    def setUp(self):
        BoundTrackerClass.method.tracker.call_count = 0

    def test_count_increments(self):
        obj = BoundTrackerClass()
        obj.method(1, 2)
        self.assertEqual(obj.method.tracker.call_count, 1)
        obj.method(3, 4)
        self.assertEqual(obj.method.tracker.call_count, 2)

    def test_reset(self):
        obj = BoundTrackerClass()
        obj.method(1, 2)
        obj.method(3, 4)
        obj.method.tracker.call_count = 0
        self.assertEqual(obj.method.tracker.call_count, 0)

    def test_method_still_works(self):
        obj = BoundTrackerClass()
        result = obj.method(1, 2)
        self.assertEqual(result, 3)

    def test_separate_instances_share_count(self):
        obj1 = BoundTrackerClass()
        obj2 = BoundTrackerClass()
        obj1.method(1, 2)
        obj2.method(3, 4)
        self.assertEqual(obj1.method.tracker.call_count, 2)
        self.assertEqual(obj2.method.tracker.call_count, 2)


class TestClassMethodBoundTracker(unittest.TestCase):
    def setUp(self):
        BoundTrackerClass.class_method.tracker.call_count = 0

    def test_count_increments(self):
        BoundTrackerClass.class_method(1, 2)
        self.assertEqual(BoundTrackerClass.class_method.tracker.call_count, 1)
        BoundTrackerClass.class_method(3, 4)
        self.assertEqual(BoundTrackerClass.class_method.tracker.call_count, 2)

    def test_reset(self):
        BoundTrackerClass.class_method(1, 2)
        BoundTrackerClass.class_method(3, 4)
        BoundTrackerClass.class_method.tracker.call_count = 0
        self.assertEqual(BoundTrackerClass.class_method.tracker.call_count, 0)

    def test_classmethod_still_works(self):
        result = BoundTrackerClass.class_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = BoundTrackerClass()
        BoundTrackerClass.class_method(1, 2)
        self.assertEqual(obj.class_method.tracker.call_count, 1)


class TestStaticMethodBoundTracker(unittest.TestCase):
    def setUp(self):
        BoundTrackerClass.static_method.tracker.call_count = 0

    def test_count_increments(self):
        BoundTrackerClass.static_method(1, 2)
        self.assertEqual(BoundTrackerClass.static_method.tracker.call_count, 1)
        BoundTrackerClass.static_method(3, 4)
        self.assertEqual(BoundTrackerClass.static_method.tracker.call_count, 2)

    def test_reset(self):
        BoundTrackerClass.static_method(1, 2)
        BoundTrackerClass.static_method(3, 4)
        BoundTrackerClass.static_method.tracker.call_count = 0
        self.assertEqual(BoundTrackerClass.static_method.tracker.call_count, 0)

    def test_staticmethod_still_works(self):
        result = BoundTrackerClass.static_method(1, 2)
        self.assertEqual(result, 3)

    def test_access_via_instance(self):
        obj = BoundTrackerClass()
        BoundTrackerClass.static_method(1, 2)
        self.assertEqual(obj.static_method.tracker.call_count, 1)


class TestBoundTrackerIntrospection(unittest.TestCase):
    def test_descriptor_proxies_name(self):
        self.assertEqual(BoundCallTracker.__call__.__name__, "__call__")

    def test_descriptor_proxies_qualname(self):
        self.assertEqual(
            BoundCallTracker.__call__.__qualname__, "BoundCallTracker.__call__"
        )

    def test_descriptor_proxies_signature(self):
        sig = inspect.signature(BoundCallTracker.__call__)
        self.assertIn("wrapped", sig.parameters)

    def test_function_preserves_name(self):
        self.assertEqual(bound_tracker_function.__name__, "bound_tracker_function")

    def test_function_preserves_qualname(self):
        self.assertEqual(
            bound_tracker_function.__qualname__, "bound_tracker_function"
        )

    def test_function_preserves_signature(self):
        sig = inspect.signature(bound_tracker_function)
        self.assertEqual(list(sig.parameters), ["x", "y"])

    def test_method_preserves_name(self):
        self.assertEqual(BoundTrackerClass.method.__name__, "method")

    def test_method_preserves_qualname(self):
        self.assertEqual(
            BoundTrackerClass.method.__qualname__, "BoundTrackerClass.method"
        )

    def test_bound_method_preserves_name(self):
        obj = BoundTrackerClass()
        self.assertEqual(obj.method.__name__, "method")

    def test_bound_method_preserves_signature(self):
        obj = BoundTrackerClass()
        sig = inspect.signature(obj.method)
        self.assertEqual(list(sig.parameters), ["x", "y"])


class TestBoundSetattr(unittest.TestCase):
    def test_set_self_prefixed_via_bound_persists(self):
        obj = WrapperAttrsClass()
        obj.method._self_custom = "hello"
        self.assertEqual(obj.method._self_custom, "hello")

    def test_set_self_prefixed_via_bound_visible_on_class(self):
        obj = WrapperAttrsClass()
        obj.method._self_tag = 42
        self.assertEqual(WrapperAttrsClass.method._self_tag, 42)

    def test_set_self_prefixed_shared_across_instances(self):
        obj1 = WrapperAttrsClass()
        obj2 = WrapperAttrsClass()
        obj1.method._self_label = "shared"
        self.assertEqual(obj2.method._self_label, "shared")

    def test_internal_slots_not_delegated(self):
        obj = WrapperAttrsClass()
        parent_wrapper = WrapperAttrsClass.method._self_wrapper
        bound = obj.method
        self.assertIs(bound._self_wrapper, parent_wrapper)

    def test_set_self_prefixed_on_normal_function(self):
        wrapper_attrs_function._self_custom = "hello"
        self.assertEqual(wrapper_attrs_function._self_custom, "hello")

    def test_non_self_prefixed_on_normal_function(self):
        wrapper_attrs_function.custom = "value"
        self.assertEqual(wrapper_attrs_function.custom, "value")

    def test_non_self_prefixed_on_bound_raises(self):
        obj = WrapperAttrsClass()
        with self.assertRaises(AttributeError):
            obj.method.custom = "value"


if __name__ == "__main__":
    unittest.main()
