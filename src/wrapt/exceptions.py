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


class WrapperChainTooDeepError(RuntimeError):
    """
    Exception raised when a scan of a chain of wrappers reached the traversal
    limit with a further link still pending, so the result of the scan would
    be indeterminate. Inherits from RuntimeError, following the precedent of
    RecursionError for exhaustion of a depth limit, as it reports an
    execution limit rather than a contract violation.
    """

    pass


class WrapperNotFoundError(ValueError):
    """
    Exception raised when the wrapper to be removed was not found in the
    chain of wrappers of the attribute, meaning nothing of the caller's is
    installed there: it was never wrapped, was already removed, or the
    attribute was replaced wholesale by a third party.
    """

    pass


class WrapperNotOutermostError(ValueError):
    """
    Exception raised when the wrapper to be removed was found but cannot be
    removed, because what sits directly above it in the chain is not a wrapt
    wrapper whose link to it can be updated in place, or because the
    attribute is served dynamically and has no owning location to restore.
    """

    pass
