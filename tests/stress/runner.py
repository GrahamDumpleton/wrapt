"""Driver for the free threading stress scenarios in this directory.

Each ``stress_*.py`` script is run as a separate subprocess, since the
failure mode being hunted is a hard crash of the interpreter which would
take an in-process test runner out with it. Exit code 0 from a scenario
means it survived, 77 means it was skipped, and any other exit code,
including death by signal, is a failure.

These are probabilistic tests, not deterministic ones. A crash proves a
bug, while a clean run only gives confidence proportional to how long
the scenarios ran. Control duration and concurrency with the
WRAPT_STRESS_SECONDS and WRAPT_STRESS_THREADS environment variables.
"""

import pathlib
import signal
import subprocess
import sys


def main():
    here = pathlib.Path(__file__).resolve().parent
    scenarios = sorted(here.glob("stress_*.py"))

    if not scenarios:
        print("no stress scenarios found", flush=True)
        return 1

    failures = []
    skipped = []

    for path in scenarios:
        print(f"=== {path.name} ===", flush=True)

        process = subprocess.run([sys.executable, str(path)])
        code = process.returncode

        if code == 0:
            print(f"PASS: {path.name}", flush=True)
        elif code == 77:
            print(f"SKIP: {path.name}", flush=True)
            skipped.append(path.name)
        elif code < 0:
            try:
                reason = signal.Signals(-code).name
            except ValueError:
                reason = f"signal {-code}"
            print(f"CRASH: {path.name} (terminated by {reason})", flush=True)
            failures.append(path.name)
        else:
            print(f"FAIL: {path.name} (exit code {code})", flush=True)
            failures.append(path.name)

        print(flush=True)

    passed = len(scenarios) - len(failures) - len(skipped)

    print(
        f"{passed} passed, {len(failures)} failed, {len(skipped)} skipped",
        flush=True,
    )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
