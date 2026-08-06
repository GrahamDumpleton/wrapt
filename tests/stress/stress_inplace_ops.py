"""Stress concurrent in-place operations on a shared proxy.

Multiple threads concurrently apply ``+=`` to a single shared C
``ObjectProxy`` wrapping an object whose ``__iadd__`` returns a new
object each time, so every operation swaps the identity of the wrapped
object and releases the previous, uniquely held one.

The swap itself is serialised by a per-object critical section as of
wrapt 2.4.0, but the in-place operators still read the wrapped object as
a borrowed reference before operating on it, so a concurrent swap can
release the object another thread is part way through using. This
scenario is therefore EXPECTED TO CRASH until the borrowed reference
uses in the operator paths are converted to strong references, and is
skipped by default so the default stress run reflects the guarantees
the current implementation actually makes. Set WRAPT_STRESS_UNSAFE=1 to
run it, either to demonstrate the outstanding hazard or, once the
conversion lands, to promote it into the default set by removing the
gate.

Exits 0 on survival, is killed by a signal on failure, and exits 77
(skip) if gated off or the C extension is not available.
"""

import os
import sys
import threading
import time

THREADS = int(os.environ.get("WRAPT_STRESS_THREADS", "8"))
SECONDS = float(os.environ.get("WRAPT_STRESS_SECONDS", "5"))


class Value:

    def __init__(self, number):
        self.number = number

    def __iadd__(self, other):
        return Value(self.number + other)


def main():
    if os.environ.get("WRAPT_STRESS_UNSAFE") != "1":
        print(
            "skipped: expected to crash until borrowed references in the "
            "in-place operator paths are converted to strong references; "
            "set WRAPT_STRESS_UNSAFE=1 to run",
            flush=True,
        )
        return 77

    try:
        from wrapt._wrappers import ObjectProxy
    except ImportError:
        print("skipped: C extension not available", flush=True)
        return 77

    gil = getattr(sys, "_is_gil_enabled", lambda: True)()

    print(
        f"python={sys.version.split()[0]} gil={gil} "
        f"threads={THREADS} seconds={SECONDS}",
        flush=True,
    )

    shared = ObjectProxy(Value(0))

    stop = threading.Event()
    barrier = threading.Barrier(THREADS + 1)
    counts = [0] * THREADS

    def adder(index):
        # The in-place operator returns the proxy itself, so the
        # augmented assignment rebinds the local name to the same shared
        # proxy on every iteration.
        target = shared
        barrier.wait()
        while not stop.is_set():
            target += 1
            counts[index] += 1

    threads = [
        threading.Thread(target=adder, args=(index,)) for index in range(THREADS)
    ]

    for thread in threads:
        thread.start()

    barrier.wait()
    time.sleep(SECONDS)
    stop.set()

    for thread in threads:
        thread.join()

    print(f"survived: {sum(counts)} in-place operations", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
