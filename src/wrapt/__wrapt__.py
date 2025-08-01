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
