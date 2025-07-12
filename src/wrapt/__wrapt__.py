"""This module is used to switch between C and Python implementations of the
wrappers.
"""

import os

# Import Python fallbacks.

from .wrappers import (
    ObjectProxy,
    CallableObjectProxy,
    PartialCallableObjectProxy,
    FunctionWrapper,
    BoundFunctionWrapper,
    _FunctionWrapperBase,
)

# Try to use C extensions if not disabled.

_use_extensions = not os.environ.get("WRAPT_DISABLE_EXTENSIONS")

if _use_extensions:
    try:
        from ._wrappers import (
            ObjectProxy,
            CallableObjectProxy,
            PartialCallableObjectProxy,
            FunctionWrapper,
            BoundFunctionWrapper,
            _FunctionWrapperBase,
        )
    except ImportError:
        # C extensions not available, using Python implementations
        pass
