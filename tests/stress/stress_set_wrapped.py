"""Stress concurrent assignment to __wrapped__ on a shared proxy.

Multiple threads concurrently assign fresh, uniquely held objects to
``__wrapped__`` on a single shared C ``ObjectProxy``. Before wrapt 2.4.0
the C extension updated the wrapped object using an unprotected pointer
swap, so on a free-threaded build two threads could read the same old
value and both release it, freeing it twice and crashing the interpreter
within seconds (issue #347). With the swap serialised by a per-object
critical section the process must survive, with one of the competing
updates simply being lost.

Exits 0 on survival, is killed by a signal on failure, and exits 77
(skip) if the C extension is not available.
"""

import os
import sys
import threading
import time

THREADS = int(os.environ.get("WRAPT_STRESS_THREADS", "8"))
SECONDS = float(os.environ.get("WRAPT_STRESS_SECONDS", "5"))


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

    shared = ObjectProxy(object())

    stop = threading.Event()
    barrier = threading.Barrier(THREADS + 1)
    counts = [0] * THREADS

    def setter(index):
        barrier.wait()
        while not stop.is_set():
            shared.__wrapped__ = object()
            counts[index] += 1

    threads = [
        threading.Thread(target=setter, args=(index,)) for index in range(THREADS)
    ]

    for thread in threads:
        thread.start()

    barrier.wait()
    time.sleep(SECONDS)
    stop.set()

    for thread in threads:
        thread.join()

    print(f"survived: {sum(counts)} assignments", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
