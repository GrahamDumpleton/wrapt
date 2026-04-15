"""
Example of making a decorator built on top of `FunctionWrapper`
serialisable with `dill`.

This is a companion to `dill_proxy.py`. Where that example showed how
to make a subclass of `BaseObjectProxy` serialisable, this example
shows the same idea applied to `FunctionWrapper`, which is the proxy
class `wrapt` uses to implement decorators. Making a decorated
function serialisable therefore comes down to defining `__reduce__`
on a subclass of `FunctionWrapper` and using that subclass in the
decorator factory.

`FunctionWrapper` stores the user supplied wrapper function on the
proxy itself as the `_self_wrapper` attribute, alongside the wrapped
callable at `__wrapped__`. The rebuild recipe returned from
`__reduce__` is therefore simply the same pair of arguments
`FunctionWrapper` was constructed with in the first place.

As with `dill_proxy.py`, the `dill.dump()` call must be made with
`byref=True`. The proxy base class used by `FunctionWrapper` is
ultimately backed by a C extension type and cannot be reconstructed
from a serialised class body. Referencing classes and functions by
their import path instead of serialising them by value avoids that.

Running this example demonstrates two round-trips. The first saves
and restores a free decorated function. The second saves and restores
an instance of a class one of whose methods has been decorated,
showing that a bound decorator method also survives a dill round-trip.
"""

from pathlib import Path

import dill

import wrapt

FUNC_FILE = Path(__file__).parent / "decorated_func.dill"
INSTANCE_FILE = Path(__file__).parent / "decorated_instance.dill"


class SerialisableFunctionWrapper(wrapt.FunctionWrapper):
    """A `FunctionWrapper` subclass that can be serialised.

    The rebuild recipe returns the same two arguments `FunctionWrapper`
    was originally constructed with: the wrapped callable and the user
    supplied wrapper function. `dill` will recursively serialise both
    arguments so that the decorated function can be restored.
    """

    def __reduce__(self):
        return (type(self), (self.__wrapped__, self._self_wrapper))


def serialisable_decorator(wrapper):
    """A minimal decorator factory using `SerialisableFunctionWrapper`.

    This mirrors the shape of `wrapt.decorator` but substitutes the
    serialisable proxy class, so that any function or method decorated
    with it can be serialised with `dill`.
    """
    def _decorator(wrapped):
        return SerialisableFunctionWrapper(wrapped, wrapper)
    return _decorator


@serialisable_decorator
def trace(wrapped, instance, args, kwargs):
    print(f"[trace] calling {wrapped.__name__}({args}, {kwargs})")
    result = wrapped(*args, **kwargs)
    print(f"[trace] {wrapped.__name__} returned {result!r}")
    return result


@trace
def add(a, b):
    return a + b


class Calculator:
    def __init__(self, base):
        self.base = base

    @trace
    def add_to_base(self, x):
        return self.base + x


def save(data, path):
    # `byref=True` is required because `FunctionWrapper` is a subclass
    # of `wrapt.BaseObjectProxy`, which is ultimately backed by a C
    # extension type and cannot be reconstructed from a serialised
    # class body. Passing `byref=True` makes dill reference classes
    # and functions by their import path, the same way the standard
    # library `pickle` module does, rather than attempting to
    # serialise them by value.
    with open(path, "wb") as f:
        dill.dump(data, f, byref=True)
    print(f"Saved dilled data to {path}")


def load(path):
    with open(path, "rb") as f:
        data = dill.load(f)
    print(f"Loaded dilled data from {path}")
    return data


def roundtrip_function():
    print("--- Free function round-trip ---")
    print(f"  type(add) = {type(add).__name__}")
    print(f"  add(2, 3) = {add(2, 3)}")

    save(add, FUNC_FILE)
    restored = load(FUNC_FILE)

    print(f"  type(restored) = {type(restored).__name__}")
    print(f"  restored(10, 20) = {restored(10, 20)}")

    assert type(restored) is type(add)
    assert restored(10, 20) == 30


def roundtrip_instance():
    print("\n--- Calculator instance round-trip ---")
    calc = Calculator(base=100)
    print(f"  calc.add_to_base(5) = {calc.add_to_base(5)}")

    save(calc, INSTANCE_FILE)
    restored_calc = load(INSTANCE_FILE)

    print(f"  restored_calc.base = {restored_calc.base}")
    print(f"  restored_calc.add_to_base(5) = {restored_calc.add_to_base(5)}")

    assert restored_calc.base == 100
    assert restored_calc.add_to_base(5) == 105


def main():
    roundtrip_function()
    roundtrip_instance()
    print("\nOK: restored decorated function and decorated method match originals.")


if __name__ == "__main__":
    main()
