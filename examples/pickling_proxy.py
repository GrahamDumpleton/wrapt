"""
Example of making a custom object proxy pickleable.

By default an instance of `wrapt.ObjectProxy` (or `wrapt.BaseObjectProxy`)
cannot be pickled. The object proxy base classes define `__reduce__` so
that it raises `NotImplementedError`, because there is no generic way to
pickle a proxy that would correctly capture both the wrapped object and
any state the proxy subclass adds on top of it. It is therefore up to
the user to define their own `__reduce__` method on a proxy subclass,
indicating how its data should be saved and restored.

The method must return a tuple describing how to rebuild the proxy from
its wrapped object plus any additional state stored on the proxy itself.
State private to the proxy is conventionally held in attributes named
with a `_self_` prefix, which wrapt stores on the proxy instance rather
than forwarding to the wrapped object.

Running this example saves a pickle file next to the script, loads it back,
and verifies the restored proxy matches the original.
"""

import pickle
from pathlib import Path

import wrapt

PICKLE_FILE = Path(__file__).parent / "stats_proxy.pkl"


class StatsProxy(wrapt.BaseObjectProxy):
    """A transparent proxy around a dict of computed statistics.

    Adds a `label` attribute alongside the wrapped dict to demonstrate
    how proxy-local state is preserved through a pickle round-trip.
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
        # proxy: the wrapped object and any proxy-local state. Pickle
        # will recursively pickle these arguments, so the wrapped
        # object must itself be pickleable.
        return (type(self), (self.__wrapped__, self._self_label))


def compute_stats(numbers):
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "average": sum(numbers) / len(numbers),
        "values": list(numbers),
    }


def save(data, path=PICKLE_FILE):
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved pickled data to {path}")


def load(path=PICKLE_FILE):
    with open(path, "rb") as f:
        data = pickle.load(f)
    print(f"Loaded pickled data from {path}")
    return data


def main():
    numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]

    original = StatsProxy(compute_stats(numbers), label="pi-digits")
    print(f"Original proxy (label={original.label!r}):")
    print(dict(original))

    save(original)

    restored = load()
    print(f"Restored proxy (label={restored.label!r}):")
    print(dict(restored))

    assert dict(original) == dict(restored)
    assert original.label == restored.label
    print("OK: restored proxy matches original.")


if __name__ == "__main__":
    main()
