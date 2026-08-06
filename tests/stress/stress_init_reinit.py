"""Stress concurrent re-invocation of __init__ on a shared proxy.

Multiple threads concurrently call ``__init__`` again on a single shared
C ``ObjectProxy`` which has already been initialised, each passing a
fresh, uniquely held object. Before wrapt 2.4.0 the initialisation path
updated the wrapped object using an unprotected pointer swap, the same
hazard as assignment to ``__wrapped__`` (issue #347), so two threads
could release the previous wrapped object twice. With the swap
serialised by a per-object critical section the process must survive.

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

    def reinit(index):
        barrier.wait()
        while not stop.is_set():
            shared.__init__(object())
            counts[index] += 1

    threads = [
        threading.Thread(target=reinit, args=(index,)) for index in range(THREADS)
    ]

    for thread in threads:
        thread.start()

    barrier.wait()
    time.sleep(SECONDS)
    stop.set()

    for thread in threads:
        thread.join()

    print(f"survived: {sum(counts)} initialisations", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
