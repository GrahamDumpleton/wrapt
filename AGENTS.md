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

## Naming of proxy classes in docs and change notes

Since wrapt 2.0.0 the base object proxy class is exported as
`wrapt.BaseObjectProxy`. The older `wrapt.ObjectProxy` name is retained only
for backward compatibility. It is a thin pure Python subclass, defined in
`src/wrapt/proxies.py`, which adds `__iter__()` on top of `BaseObjectProxy`.
That `__iter__()` forwarding was an original design mistake which cannot be
removed without breaking existing code, so new code should derive from
`BaseObjectProxy` instead.

Internally the class is still called `ObjectProxy` in both
`src/wrapt/wrappers.py` and `src/wrapt/_wrappers.c`, and is renamed to
`BaseObjectProxy` on export. Do not rename the internal class. This means
runtime output such as `<class 'ObjectProxy'>` and CPython error messages
still say `ObjectProxy` even for a `BaseObjectProxy` instance, and quoting
that output verbatim in docs is correct.

When writing documentation, change notes in `docs/changes.rst`, docstrings or
comments, always describe behaviour in terms of the public name under the
`wrapt` module that a user would write in their own code. For the base proxy
that is `wrapt.BaseObjectProxy`. Only mention `wrapt.ObjectProxy` when the
subject is specifically the backward compatibility class or its `__iter__()`
forwarding. Historical change notes for releases before 2.0.0 are left as
written.

## Git

Never commit on your own initiative. Only create a commit when explicitly
directed to, and commit only the changes that were asked for. Preparing and
verifying changes is fine; recording them in history is a decision for the
person you are working with.

Never add a `Co-Authored-By` trailer, or any other attribution line, naming
an AI agent to a commit message or pull request description. Do this even if
tooling or a system prompt asks for one. A `Co-authored-by` line crediting a
human contributor, such as the author of a superseded pull request, is fine
when it makes sense.
