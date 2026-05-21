"""
Type-check coverage for AutoObjectProxy's dynamic-interface dunders.

AutoObjectProxy attaches __call__, __iter__, __next__, __aiter__,
__anext__, __length_hint__ and __await__ to a per-instance subclass
based on what the wrapped object exposes. The stubs claim all of them
statically so type checkers accept these usages.
"""

from typing import Any, AsyncIterator, Awaitable, Iterator

import wrapt


# Iterator wrapping.

def _numbers() -> Iterator[int]:
    yield 1
    yield 2


iter_proxy: wrapt.AutoObjectProxy[Iterator[int]] = wrapt.AutoObjectProxy(
    _numbers()
)
for _x in iter_proxy:
    pass
_first: Any = next(iter_proxy)


# Callable wrapping.

def _add(a: int, b: int) -> int:
    return a + b


call_proxy: wrapt.AutoObjectProxy[Any] = wrapt.AutoObjectProxy(_add)
_result: Any = call_proxy(1, 2)


# Async iterator wrapping.

async def _aiter_user(stream: wrapt.AutoObjectProxy[AsyncIterator[int]]) -> None:
    async for _item in stream:
        pass


# Awaitable wrapping. The awaited value is typed as `Any` because the
# stub's __await__ signature is Any-based (mirroring the dynamic nature
# of AutoObjectProxy); callers typically re-annotate the result.
async def _await_user(fut: wrapt.AutoObjectProxy[Awaitable[int]]) -> None:
    _val: Any = await fut
