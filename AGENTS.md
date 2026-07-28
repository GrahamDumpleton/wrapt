# Guidance for AI agents working on wrapt

## Testing

Read `TESTING.md` before doing any test-related work. It documents the test
directory layout, the version-specific test file naming convention, the mypy
pair tests, and the environment variables controlling use of C extensions.

Always prefer the `Justfile` recipes over invoking pytest or mypy in ad hoc
virtual environments. The recipes handle building the C extension, selecting
compatible tool versions, and cleaning stale artifacts.

- Quick iteration while developing: run pytest against a specific test file
  in a development virtual environment, remembering to exercise both the C
  extension and pure Python implementations (`WRAPT_DISABLE_EXTENSIONS=true`).
- Verifying a single Python version: `just test-version 3.13`. This runs the
  full test suite in all three C extension variants (pure Python install,
  C extension enabled, C extension disabled at runtime).
- Definition of done for changes to `src/wrapt/` or `src/wrapt/_wrappers.c`:
  `just test`, which runs the full matrix across all supported Python
  versions. This takes a while; if it is impractical to run, say so
  explicitly in your report rather than silently skipping it.
- Type checking: `just test-mypy` (all versions) or
  `just test-mypy-version 3.13`.
- Changes to the stubs in `src/wrapt-stubs/` must be checked with
  `just test-stubtest` against `tests/stubtest_allowlist.txt`.

The mypy pair tests under `tests/mypy/` compare mypy output against checked
in `.out` files and only pass with the mypy version pinned by `mypy_version`
in the `Justfile` (older pin for Python 3.9). Running them with any other
mypy version produces false failures, so do not diagnose mismatches there as
pre-existing breakage before checking the mypy version in use.
