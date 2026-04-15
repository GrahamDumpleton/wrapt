"""
Example of making a custom object proxy serialisable with `dill`.

This is the companion to `pickling_proxy.py` but uses `dill` in place
of the standard library `pickle` module. `dill` relies on the same
pickle protocol for user defined types, so making a proxy subclass
serialisable with `dill` requires the same thing as for `pickle`:
defining `__reduce__` on the proxy subclass. The base proxy's
`__reduce__` raises `NotImplementedError`, and `dill` does not bypass
it.

What `dill` buys over `pickle` is the ability to serialise exotic
wrapped values that `pickle` cannot handle, such as lambdas, closures
and nested functions. To exercise that, this example embeds a closure
function inside the dict the proxy wraps. The proxy's `__reduce__`
handles the proxy shell, and `dill` handles the wrapped contents,
including the closure.

State private to the proxy is conventionally held in attributes named
with a `_self_` prefix, which wrapt stores on the proxy instance rather
than forwarding to the wrapped object.

Running this example saves a dill file next to the script, loads it
back, and verifies the restored proxy, including the closure, matches
the original.
"""

from pathlib import Path

import dill

import wrapt

DATA_FILE = Path(__file__).parent / "stats_proxy.dill"


class StatsProxy(wrapt.BaseObjectProxy):
    """A transparent proxy around a dict of computed statistics.

    Adds a `label` attribute alongside the wrapped dict to demonstrate
    how proxy-local state is preserved through a dill round-trip.
    """

    def __init__(self, wrapped, label):
        super().__init__(wrapped)
        # Attributes assigned via a `_self_` prefix are stored on the
        # proxy itself instead of being forwarded to the wrapped object.
        self._self_label = label

    @property
    def label(self):
        return self._self_label

    def __reduce__(self):
        # Return a callable and the arguments needed to rebuild the
        # proxy: the wrapped object and any proxy-local state. Dill
        # will recursively serialise these arguments using the pickle
        # protocol, extended with its own support for objects that
        # `pickle` cannot handle such as closures.
        return (type(self), (self.__wrapped__, self._self_label))


def compute_stats(numbers):
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "average": sum(numbers) / len(numbers),
        "values": list(numbers),
        # A closure function. The standard library `pickle` module
        # cannot serialise this, but `dill` can. It lives inside the
        # dict the proxy wraps, exercising the composition of the
        # proxy's `__reduce__` handling the proxy shell and `dill`
        # handling the wrapped contents.
        "scale": (lambda factor: lambda x: x * factor)(10),
    }


def save(data, path=DATA_FILE):
    # `byref=True` tells dill to reference classes and functions by
    # their import path, the same way the standard library `pickle`
    # does, instead of attempting to serialise them by value. This is
    # required for `StatsProxy` because its base class
    # `wrapt.BaseObjectProxy` is ultimately backed by a C extension
    # type which cannot be reconstructed from a serialised class body.
    # Without `byref=True` the dump step will fail.
    with open(path, "wb") as f:
        dill.dump(data, f, byref=True)
    print(f"Saved dilled data to {path}")


def load(path=DATA_FILE):
    with open(path, "rb") as f:
        data = dill.load(f)
    print(f"Loaded dilled data from {path}")
    return data


def main():
    numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]

    original = StatsProxy(compute_stats(numbers), label="pi-digits")
    print(f"Original proxy (label={original.label!r}):")
    print({k: v for k, v in original.items() if k != "scale"})
    print(f"  scale(7) = {original['scale'](7)}")

    save(original)

    restored = load()
    print(f"Restored proxy (label={restored.label!r}):")
    print({k: v for k, v in restored.items() if k != "scale"})
    print(f"  scale(7) = {restored['scale'](7)}")

    assert restored.label == original.label
    assert {k: v for k, v in restored.items() if k != "scale"} == \
           {k: v for k, v in original.items() if k != "scale"}
    assert restored["scale"](7) == original["scale"](7) == 70
    print("OK: restored proxy (including closure) matches original.")


if __name__ == "__main__":
    main()
