"""Stress concurrent in-place operations on a shared proxy.

Multiple threads concurrently apply ``+=`` to a single shared C
``ObjectProxy`` wrapping an object whose ``__iadd__`` returns a new
object each time, so every operation swaps the identity of the wrapped
object and releases the previous, uniquely held one.

Serialising the swap alone was not enough to make this survive: the
in-place operators also read the wrapped object before operating on it,
and while that read was a borrowed reference a concurrent swap could
release the object another thread was part way through using, crashing
the interpreter within seconds. With the operator paths holding strong
references for the duration of the operation the process must survive,
with competing updates simply being lost.

Exits 0 on survival, is killed by a signal on failure, and exits 77
(skip) if the C extension is not available.
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
