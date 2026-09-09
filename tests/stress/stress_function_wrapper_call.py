"""Stress calling a shared function wrapper while it is re-initialised.

One writer thread repeatedly re-invokes ``__init__`` on a single shared
C ``FunctionWrapper``, each time passing a freshly created target
function and wrapper function which are uniquely held, while the
remaining threads continually call the wrapper. The call path reads the
wrapped object and the instance, wrapper, enabled and binding fields,
all of which the re-initialisation concurrently replaces and releases.
Each field is read by acquiring a strong reference held for the
duration of the call, so the process must survive; without that, a
released field value could be used mid call and crash the interpreter.

Exits 0 on survival, is killed by a signal on failure, and exits 77
(skip) if the C extension is not available.
"""

import os
import sys
import threading
import time

THREADS = max(2, int(os.environ.get("WRAPT_STRESS_THREADS", "8")))
SECONDS = float(os.environ.get("WRAPT_STRESS_SECONDS", "5"))


def make_target():
    def target():
        return 42

    return target


def make_wrapper():
    def wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    return wrapper


def main():
    try:
        from wrapt._wrappers import FunctionWrapper
    except ImportError:
        print("skipped: C extension not available", flush=True)
        return 77

    gil = getattr(sys, "_is_gil_enabled", lambda: True)()

    print(
        f"python={sys.version.split()[0]} gil={gil} "
        f"threads={THREADS} seconds={SECONDS}",
        flush=True,
    )

    shared = FunctionWrapper(make_target(), make_wrapper())

    stop = threading.Event()
    barrier = threading.Barrier(THREADS + 1)
    counts = [0] * THREADS

    def writer(index):
        barrier.wait()
        while not stop.is_set():
            shared.__init__(make_target(), make_wrapper())
            counts[index] += 1

    def caller(index):
        barrier.wait()
        while not stop.is_set():
            assert shared() == 42
            counts[index] += 1

    threads = [threading.Thread(target=writer, args=(0,))]
    threads.extend(
        threading.Thread(target=caller, args=(index,))
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
        f"survived: {counts[0]} initialisations, {sum(counts[1:])} calls",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
