"""
Type-check coverage for BaseObjectProxy as a context manager.

Mirrors the pattern from issue #314 (smart_open wraps a file object in a
BaseObjectProxy subclass and the consumer uses `with open(...) as f:`). Prior
to adding context-manager dunders to the stub, pylance/mypy/pyright all
rejected the `with` statement with `"ObjectProxy" has no attribute
"__enter__"`.
"""

from io import TextIOWrapper
from typing import Any

import wrapt


# Plain proxy of a context manager.

f_proxy: wrapt.BaseObjectProxy[TextIOWrapper[Any]] = wrapt.BaseObjectProxy(
    open("/dev/null")
)

with f_proxy as f:
    for line in f:
        _ = line.strip()


# Subclass pattern used by smart_open.

class FileProxy(wrapt.BaseObjectProxy[TextIOWrapper[Any]]):
    pass


fp = FileProxy(open("/dev/null"))
with fp as f2:
    _ = f2.read()
