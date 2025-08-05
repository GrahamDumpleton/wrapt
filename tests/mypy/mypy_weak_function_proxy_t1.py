"""
This example demonstrates the correct usage of the WeakFunctionProxy.

It covers the following cases:
- Correct usage of partial with a function. (OKAY)
- Using partial with no arguments. (FAIL)
- Using partial with incorrect arguments. (FAIL)
"""

import weakref
from typing import Any, Callable

from wrapt import WeakFunctionProxy


def callback(
    ref: (
        weakref.ProxyType[Callable[..., Any]]
        | weakref.CallableProxyType[Callable[..., Any]]
    ),
) -> None:
    print("Object was finalized:", ref)


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


proxy = WeakFunctionProxy(function, callback=callback)

proxy(42)

proxy_no_args = WeakFunctionProxy()

proxy_incorrect_args = WeakFunctionProxy(None)
