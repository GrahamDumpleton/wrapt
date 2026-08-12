"""Exception types raised by wrapt."""


class WrapperNotInitializedError(ValueError):
    """
    Exception raised when a wrapper is in an inconsistent state: __init__ was
    called but __wrapped__ is not set. Inherits from ValueError only, so it is
    not silently swallowed by hasattr/getattr/except AttributeError patterns.
    """

    pass


class PathResolutionError(AttributeError):
    """
    Exception raised when the dotted attribute path supplied for a patch
    target could not be resolved. Inherits from AttributeError so existing
    code catching that continues to work, while the message carries the
    target, the full dotted path, and the failing segment, and the low-level
    error is preserved as __cause__.
    """

    pass


class TargetModuleNotFoundError(ModuleNotFoundError):
    """
    Exception raised when a patch target supplied as a string named a module
    that could not be imported. Inherits from ModuleNotFoundError so existing
    code catching that, or ImportError, continues to work, while the message
    names the module and the attribute path being resolved, and the low-level
    error is preserved as __cause__.
    """

    pass
