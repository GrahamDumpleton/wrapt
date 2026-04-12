"""
Examples of attaching state to wrapt-decorated functions.

Version 1: Manual state attachment using __self_setattr__
Version 2: Automatic state attachment using wrapt.bind_state_to_wrapper
Version 3: With optional decorator arguments via static method
Version 4: Singleton tracker with per-function stats
"""

import wrapt
from wrapt import bind_state_to_wrapper


# ============================================================
# Version 1: Manual state attachment using __self_setattr__
# ============================================================


class CallTracker1:
    def __init__(self):
        self.call_count = 0

    @wrapt.function_wrapper
    def track(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1


def track_calls_v1(func):
    tracker = CallTracker1()
    wrapper = tracker.track(func)
    wrapper.__self_setattr__("tracker", tracker)
    return wrapper


# ============================================================
# Version 2: Automatic state attachment via descriptor decorator
# ============================================================


class CallTracker2:
    def __init__(self):
        self.call_count = 0

    @bind_state_to_wrapper(name="tracker")
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1


# ============================================================
# Version 3: With optional decorator arguments via static method
# ============================================================


class CallTracker3:
    def __init__(self, *, call_count=0):
        self.call_count = call_count

    @bind_state_to_wrapper(name="tracker")
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1

    @staticmethod
    def track(func=None, /, *, call_count=0):
        tracker = CallTracker3(call_count=call_count)
        if func is None:
            return tracker
        return tracker(func)


# ============================================================
# Version 4: Singleton tracker with per-function stats
# ============================================================


class CallTracker4:
    _instance = None

    def __init__(self):
        self.stats = {}

    @bind_state_to_wrapper(name="tracker")
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        name = f"{wrapped.__module__}:{wrapped.__qualname__}"
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.stats[name] = self.stats.get(name, 0) + 1

    def count(self, name):
        return self.stats.get(name, 0)

    @staticmethod
    def track(func=None, /):
        with wrapt.synchronized(CallTracker4):
            if CallTracker4._instance is None:
                CallTracker4._instance = CallTracker4()
        tracker = CallTracker4._instance
        if func is None:
            return tracker
        return tracker(func)


# ============================================================
# Test all versions
# ============================================================


@track_calls_v1
def add_v1(x, y):
    return x + y


@CallTracker2()
def add_v2(x, y):
    return x + y


class MyClass1:
    @track_calls_v1
    def method(self, x, y):
        return x + y

    @track_calls_v1
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @track_calls_v1
    @staticmethod
    def static_method(x, y):
        return x + y


# Version 3: without arguments (func passed directly)
@CallTracker3.track
def add_v3a(x, y):
    return x + y


# Version 3: with arguments (returns CallTracker3 instance, then binds)
@CallTracker3.track(call_count=10)
def add_v3b(x, y):
    return x + y


class MyClass2:
    @CallTracker2()
    def method(self, x, y):
        return x + y

    @CallTracker2()
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @CallTracker2()
    @staticmethod
    def static_method(x, y):
        return x + y


class MyClass3a:
    @CallTracker3.track
    def method(self, x, y):
        return x + y

    @CallTracker3.track
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @CallTracker3.track
    @staticmethod
    def static_method(x, y):
        return x + y


@CallTracker4.track
def add_v4(x, y):
    return x + y


class MyClass4:
    @CallTracker4.track
    def method(self, x, y):
        return x + y

    @CallTracker4.track
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @CallTracker4.track
    @staticmethod
    def static_method(x, y):
        return x + y


class MyClass3b:
    @CallTracker3.track(call_count=10)
    def method(self, x, y):
        return x + y

    @CallTracker3.track(call_count=10)
    @classmethod
    def class_method(cls, x, y):
        return x + y

    @CallTracker3.track(call_count=10)
    @staticmethod
    def static_method(x, y):
        return x + y


def test_version(label, func, cls, expected_base=0):
    print(f"\n--- {label} ---")

    expected = expected_base + 2

    # Normal function
    assert func(1, 2) == 3
    assert func(3, 4) == 7
    assert func.tracker.call_count == expected
    print(f"  function: call_count={func.tracker.call_count} (expected {expected})")

    # Instance method
    obj = cls()
    assert obj.method(1, 2) == 3
    assert obj.method(3, 4) == 7
    assert obj.method.tracker.call_count == expected
    print(f"  instance method: call_count={obj.method.tracker.call_count} (expected {expected})")

    # Class method
    assert cls.class_method(1, 2) == 3
    assert cls.class_method(3, 4) == 7
    assert cls.class_method.tracker.call_count == expected
    print(f"  class method: call_count={cls.class_method.tracker.call_count} (expected {expected})")

    # Static method
    assert cls.static_method(1, 2) == 3
    assert cls.static_method(3, 4) == 7
    assert cls.static_method.tracker.call_count == expected
    print(f"  static method: call_count={cls.static_method.tracker.call_count} (expected {expected})")

    # Access via instance
    obj2 = cls()
    assert obj2.class_method.tracker.call_count == expected
    assert obj2.static_method.tracker.call_count == expected
    print(f"  access via instance: OK")

    print(f"  ALL PASSED")


def test_version4():
    print("\n--- Version 4 (singleton, per-function stats) ---")

    tracker = CallTracker4._instance
    assert tracker is not None, "singleton should exist after decoration"

    # All wrappers share the same tracker instance
    assert add_v4.tracker is tracker
    assert MyClass4.method.tracker is tracker
    assert MyClass4.class_method.tracker is tracker
    assert MyClass4.static_method.tracker is tracker
    print("  all wrappers share singleton tracker: OK")

    # Reset stats for clean test
    tracker.stats.clear()

    # Normal function
    assert add_v4(1, 2) == 3
    add_v4(3, 4)
    func_name = f"{add_v4.__module__}:{add_v4.__qualname__}"
    assert tracker.count(func_name) == 2
    print(f"  function: {func_name} count={tracker.count(func_name)} (expected 2)")

    # Instance method
    obj = MyClass4()
    obj.method(1, 2)
    obj.method(3, 4)
    method_name = f"{MyClass4.method.__module__}:{MyClass4.method.__qualname__}"
    assert tracker.count(method_name) == 2
    print(f"  instance method: {method_name} count={tracker.count(method_name)} (expected 2)")

    # Class method
    MyClass4.class_method(1, 2)
    MyClass4.class_method(3, 4)
    cm_name = f"{MyClass4.class_method.__module__}:{MyClass4.class_method.__qualname__}"
    assert tracker.count(cm_name) == 2
    print(f"  class method: {cm_name} count={tracker.count(cm_name)} (expected 2)")

    # Static method
    MyClass4.static_method(1, 2)
    MyClass4.static_method(3, 4)
    sm_name = f"{MyClass4.static_method.__module__}:{MyClass4.static_method.__qualname__}"
    assert tracker.count(sm_name) == 2
    print(f"  static method: {sm_name} count={tracker.count(sm_name)} (expected 2)")

    # Complete stats
    assert len(tracker.stats) == 4
    assert all(v == 2 for v in tracker.stats.values())
    print(f"  complete stats: {tracker.stats}")

    # Unknown function returns 0
    assert tracker.count("nonexistent:func") == 0
    print("  unknown function count: 0 (expected 0)")

    print("  ALL PASSED")


if __name__ == "__main__":
    test_version("Version 1 (manual)", add_v1, MyClass1)
    test_version("Version 2 (bind_state_to_wrapper)", add_v2, MyClass2)
    test_version("Version 3a (static track, no args)", add_v3a, MyClass3a)
    test_version("Version 3b (static track, call_count=10)", add_v3b, MyClass3b, expected_base=10)
    test_version4()
    print("\nAll tests passed!")
