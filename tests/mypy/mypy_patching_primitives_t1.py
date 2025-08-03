"""
This example demonstrates the usage of primitive functions for object patching.

It covers the following cases:
- Normal use cases, target module directly. (OKAY)
- Normal use cases, target module by name. (OKAY)
- Wrong args/result for `resolve_path()`. (FAIL)
- Wrong attribute path for `apply_patch()`. (FAIL)
- Wrong args for `wrap_object()`. (FAIL)
"""

import sys
from typing import Any, Callable

from wrapt import apply_patch, resolve_path, wrap_object


def function(x: int, y: str = "default") -> str:
    """A simple function to be wrapped."""
    return f"{x}: {y}"


this_module = sys.modules[__name__]


def factory(original: Any, *args: Any, **kwargs: Any) -> Any:
    return original


class Factory:
    def __call__(self, original: Any, *args: Any, **kwargs: Any) -> Any:
        return original


factory_instance = Factory()


(parent_1a, attribute_1a, original_1a) = resolve_path(this_module, "function")

wrapper_1a = factory(original_1a, 1, 2, a=3, b=4)

apply_patch(parent_1a, attribute_1a, wrapper_1a)

wrapper_2a = wrap_object(this_module, "function", factory, (1, 2), {"a": 3, "b": 4})


wrapper_3a = wrap_object(this_module, "function", factory, (1, 2), {"a": 3, "b": 4})

(parent_1b, attribute_1b, original_1b) = resolve_path(__name__, "function")

wrapper_2b = factory_instance(original_1b, 1, 2, a=3, b=4)

apply_patch(parent_1b, attribute_1b, wrapper_2b)

wrapper_2b = wrap_object(
    this_module, "function", factory_instance, (1, 2), {"a": 3, "b": 4}
)

wrapper_3b = wrap_object(
    this_module, "function", factory_instance, (1, 2), {"a": 3, "b": 4}
)

(dummy_1a, dummy_2a) = resolve_path(this_module, None)

apply_patch(parent_1a, None, wrapper_1a)

wrap_object(this_module, None, None, None, None)
