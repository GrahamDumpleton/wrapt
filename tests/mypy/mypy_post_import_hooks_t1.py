"""
This example demonstrates the usage of post import hooks.
"""

import sys
from types import ModuleType

from wrapt import (
    discover_post_import_hooks,
    notify_module_loaded,
    register_post_import_hook,
    when_imported,
)


def callback_1(module: ModuleType) -> None:
    """A simple callback function to be registered as a post import hook."""
    print(f"Module {module.__name__} has been imported.")


register_post_import_hook(callback_1, "this")

register_post_import_hook(f"{__name__}:callback_1", "this")


@when_imported("this")
def callback_2(module: ModuleType) -> None:
    """Another callback function to be registered as a post import hook."""
    print(f"Module {module.__name__} has been imported with when_imported.")


notify_module_loaded(sys.modules[__name__])

discover_post_import_hooks("wrapt:post_import_hooks")


def callback_correct_prototype_1() -> None:
    return


# Hook function with incorrect prototype. (FAIL)
register_post_import_hook(callback_correct_prototype_1, "this")


@when_imported("this")
def callback_correct_prototype_2(module: ModuleType) -> None:
    return


# Discover post import hooks with incorrect args. (FAIL)
discover_post_import_hooks(None)

# Notify module called with incorrect args. (FAIL)
notify_module_loaded(None)

# When import decorator with incorrect prototype. (FAIL)
when_imported(None)
