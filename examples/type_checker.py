"""
Decorators that validate arguments of a wrapped function using
inspect.signature(), expressed with wrapt.

Two variants:

TypeChecker - validates argument types against the wrapped function's
              annotations.
ValueChecker - validates argument values against caller-supplied constraint
               callables.

The signature is derived from the already-bound `wrapped` on the
first call and cached on the state instance, so self/cls never appears
and no instance handling is required.
"""

import inspect

import wrapt

# ============================================================
# TypeChecker - validate argument types from annotations
# ============================================================


class TypeChecker:
    def __init__(self):
        self.signature = None

    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        if self.signature is None:
            self.signature = inspect.signature(wrapped)
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            annotation = self.signature.parameters[name].annotation
            if annotation is inspect.Parameter.empty:
                continue
            if not isinstance(value, annotation):
                raise TypeError(
                    f"Argument {name!r} must be {annotation.__name__}, "
                    f"got {type(value).__name__}"
                )
        return wrapped(*args, **kwargs)

    @staticmethod
    def check(func):
        return TypeChecker()(func)


type_checker = TypeChecker.check


# ============================================================
# ValueChecker - validate argument values with constraint callables
# ============================================================


class ValueChecker:
    def __init__(self, constraints):
        self.constraints = constraints
        self.signature = None

    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        if self.signature is None:
            self.signature = inspect.signature(wrapped)
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, constraint in self.constraints.items():
            if name not in bound.arguments:
                continue
            value = bound.arguments[name]
            if not constraint(value):
                raise ValueError(
                    f"Argument {name!r} with value {value!r} failed constraint "
                    f"{getattr(constraint, '__name__', constraint)!s}"
                )
        return wrapped(*args, **kwargs)

    @staticmethod
    def validate(func=None, /, **constraints):
        checker = ValueChecker(constraints=constraints)
        if func is None:
            return checker
        return checker(func)


value_checker = ValueChecker.validate


# ============================================================
# Constraint helpers used by the tests
# ============================================================


def is_positive(value):
    return value > 0


def is_short_string(value):
    return isinstance(value, str) and len(value) < 10


# ============================================================
# Decorated targets
# ============================================================


@type_checker
def add(x: int, y: int) -> int:
    return x + y


@value_checker(x=is_positive, y=is_positive)
def multiply(x, y):
    return x * y


@value_checker(label=is_short_string)
def tag(label, *, value=0):
    return f"{label}={value}"


# Stacked decorators. type_checker must be the outer (top) decorator so that
# it runs before value_checker; otherwise a wrong-typed argument would reach
# a constraint callable and raise a confusing TypeError from that callable
# (e.g. `"a" > 0`) instead of a clean "must be int" message.
@type_checker
@value_checker(x=is_positive, y=is_positive)
def scale(x: int, y: int) -> int:
    return x * y


class MyClass:
    @type_checker
    def imethod(self, x: int, y: int) -> int:
        return x + y

    @type_checker
    @classmethod
    def cmethod(cls, x: int, y: int) -> int:
        return x + y

    @type_checker
    @staticmethod
    def smethod(x: int, y: int) -> int:
        return x + y

    @value_checker(x=is_positive, y=is_positive)
    def vmethod(self, x, y):
        return x * y

    @type_checker
    @value_checker(x=is_positive, y=is_positive)
    def smethod_stacked(self, x: int, y: int) -> int:
        return x * y


# ============================================================
# Tests
# ============================================================


def expect_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        return e
    raise AssertionError(f"expected {exc_type.__name__} but no exception raised")


def test_type_checker():
    print("\n--- TypeChecker ---")

    # Plain function: valid and invalid
    assert add(1, 2) == 3
    print("  function valid call: OK")
    e = expect_raises(TypeError, add, 1, "2")
    print(f"  function type mismatch: {e}")

    # Instance method
    obj = MyClass()
    assert obj.imethod(1, 2) == 3
    print("  instance method valid call: OK")
    e = expect_raises(TypeError, obj.imethod, 1, "2")
    print(f"  instance method type mismatch: {e}")

    # Class method (via class and via instance)
    assert MyClass.cmethod(1, 2) == 3
    assert obj.cmethod(3, 4) == 7
    print("  classmethod valid call: OK")
    e = expect_raises(TypeError, MyClass.cmethod, 1, "2")
    print(f"  classmethod type mismatch: {e}")

    # Static method (via class and via instance)
    assert MyClass.smethod(1, 2) == 3
    assert obj.smethod(3, 4) == 7
    print("  staticmethod valid call: OK")
    e = expect_raises(TypeError, MyClass.smethod, 1, "2")
    print(f"  staticmethod type mismatch: {e}")

    print("  ALL PASSED")


def test_value_checker():
    print("\n--- ValueChecker ---")

    # Plain function: valid and invalid
    assert multiply(2, 3) == 6
    print("  function valid call: OK")
    e = expect_raises(ValueError, multiply, -1, 3)
    print(f"  function value violation: {e}")
    e = expect_raises(ValueError, multiply, 2, 0)
    print(f"  function value violation (zero): {e}")

    # Keyword argument constraint and default-value behaviour
    assert tag("hi", value=5) == "hi=5"
    assert tag("hi") == "hi=0"
    e = expect_raises(ValueError, tag, "way-too-long-label")
    print(f"  keyword-named constraint violation: {e}")

    # Instance method
    obj = MyClass()
    assert obj.vmethod(2, 3) == 6
    print("  instance method valid call: OK")
    e = expect_raises(ValueError, obj.vmethod, 2, -3)
    print(f"  instance method value violation: {e}")

    print("  ALL PASSED")


def test_stacked():
    # Stacking requires type_checker as the outer decorator so type validation
    # runs before value validation. Stacking the other way would feed a
    # wrong-typed value into the constraint callable and raise a TypeError
    # from the constraint rather than from our TypeChecker.
    print("\n--- Stacked (type_checker over value_checker) ---")

    # Valid call: both checks pass.
    assert scale(2, 3) == 6
    print("  function valid call: OK")

    # Correct type, bad value: value_checker raises ValueError.
    e = expect_raises(ValueError, scale, -1, 3)
    print(f"  value violation with valid types: {e}")

    # Wrong type: type_checker raises TypeError before value_checker runs.
    e = expect_raises(TypeError, scale, "a", 3)
    print(f"  type violation short-circuits value check: {e}")

    # Wrong type and bad value: type_checker still wins.
    e = expect_raises(TypeError, scale, "a", -1)
    print(f"  type violation preferred over value violation: {e}")

    # Method form
    obj = MyClass()
    assert obj.smethod_stacked(2, 3) == 6
    e = expect_raises(ValueError, obj.smethod_stacked, 2, -3)
    print(f"  method value violation: {e}")
    e = expect_raises(TypeError, obj.smethod_stacked, "a", 3)
    print(f"  method type violation short-circuits: {e}")

    print("  ALL PASSED")


if __name__ == "__main__":
    test_type_checker()
    test_value_checker()
    test_stacked()
    print("\nAll tests passed!")
