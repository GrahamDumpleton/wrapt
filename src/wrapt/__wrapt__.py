"""This module is used to switch between C and Python implementations of the
wrappers.
"""

import os

from .wrappers import (
    BoundFunctionWrapper,
    CallableObjectProxy,
    FunctionWrapper,
    ObjectProxy,
    PartialCallableObjectProxy,
    _FunctionWrapperBase,
)

# Import Python fallbacks.


# Try to use C extensions if not disabled.

_use_extensions = not os.environ.get("WRAPT_DISABLE_EXTENSIONS")

if _use_extensions:
    try:
        from ._wrappers import (  # type: ignore[no-redef,import-not-found]
            BoundFunctionWrapper,
            CallableObjectProxy,
            FunctionWrapper,
            ObjectProxy,
            PartialCallableObjectProxy,
            _FunctionWrapperBase,
        )
    except ImportError:
        # C extensions not available, using Python implementations
        pass

# Provide an alias for partial().


def partial(*args, **kwargs):
    """Create a callable object proxy with partial application of the given
    arguments and keywords. This behaves the same as `functools.partial`, but
    implemented using the `ObjectProxy` class to provide better support for
    introspection.
    """
    return PartialCallableObjectProxy(*args, **kwargs)
