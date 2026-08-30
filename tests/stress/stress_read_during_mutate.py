"""Stress reading __wrapped__ while another thread reassigns it.

One writer thread continually assigns fresh, uniquely held objects to
``__wrapped__`` on a shared C ``ObjectProxy`` while the remaining
threads continually read ``__wrapped__`` back. Before wrapt 2.4.0 the
getter read the raw field pointer and incremented its reference count in
two separate steps, so on a free-threaded build the incref could race
the writer releasing the old value, incrementing the reference count of
an already freed object. With the read and incref performed atomically
inside the per-object critical section the process must survive and
every value the readers observe must remain valid while they hold it.

The readers exercise both direct ``__wrapped__`` attribute access and
reads which delegate through the proxy, such as ``str()``, ``hash()``
and comparison, all of which must hold their own reference to the
wrapped object for the duration of the delegated operation rather than
using the raw field pointer.

Exits 0 on survival, is killed by a signal on failure, and exits 77
(skip) if the C extension is not available.
"""

import os
import sys
import threading
import time

THREADS = max(2, int(os.environ.get("WRAPT_STRESS_THREADS", "8")))
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

    def writer(index):
        barrier.wait()
        while not stop.is_set():
            shared.__wrapped__ = object()
            counts[index] += 1

    def reader(index):
        barrier.wait()
        while not stop.is_set():
            value = shared.__wrapped__
            # Touch the value so a stale reference to a freed object
            # cannot go unnoticed.
            assert type(value) is object
            str(shared)
            hash(shared)
            _ = shared == value
            counts[index] += 1

    threads = [threading.Thread(target=writer, args=(0,))]
    threads.extend(
        threading.Thread(target=reader, args=(index,))
        for index in range(1, THREADS)
    )

    for thread in threads:
        thread.start()

    barrier.wait()
    time.sleep(SECONDS)
    stop.set()

    for thread in threads:
        thread.join()

    print(
        f"survived: {counts[0]} assignments, {sum(counts[1:])} reads",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
