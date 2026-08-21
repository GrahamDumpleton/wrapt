"""Utilities for monkey patching and wrapping object attributes."""

import contextlib
import importlib
import inspect
import sys
import warnings

from .__wrapt__ import BaseObjectProxy, FunctionWrapper
from .exceptions import (
    PathResolutionError,
    TargetModuleNotFoundError,
    WrapperChainTooDeepError,
    WrapperNotFoundError,
    WrapperNotOutermostError,
)
from .importer import register_post_import_hook

# Sentinel used where the absence of a value must be distinguishable from
# None being supplied, or where an attribute having had no prior definition
# must be represented as a value. Exposed as public API since code walking
# wrapper chains needs to be able to test for it by identity, but only
# meaningful where wrapt itself checks for it.


class _MissingType:
    """The type of the MISSING sentinel, which marks the absence of a value
    or attribute definition where None is itself meaningful."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "<wrapt.MISSING>"

    def __reduce__(self):
        # Pickle and copy resolve back to the singleton so identity
        # comparison against MISSING survives a round trip.
        return (_MissingType, ())


MISSING = _MissingType()

# Helper functions for applying wrappers to existing functions.


def resolve_path(target, name):
    """
    Resolves the dotted path supplied as `name` to an attribute on a target
    object. The `target` can be a module, class, or instance of a class. If the
    `target` argument is a string, it is assumed to be the name of a module,
    which will be imported if necessary and then used as the target object.
    Returns a tuple containing the parent object holding the attribute lookup
    resolved to, the attribute name (path prefix removed if present), and the
    original attribute value. If the module cannot be imported, raises
    `TargetModuleNotFoundError`, and if the attribute path cannot be resolved,
    raises `PathResolutionError`, in both cases with the original exception
    preserved as the `__cause__` attribute.
    """

    if isinstance(target, str):
        # Use importlib.import_module() rather than __import__() as the
        # latter, even though it imports a dotted module name successfully
        # from the sys.modules cache, computes its return value by importing
        # the top level package, which fails for a module registered in
        # sys.modules whose parent package is not importable.

        try:
            target = importlib.import_module(target)
        except ModuleNotFoundError as exc:
            raise TargetModuleNotFoundError(
                f"unable to import module {target!r} while resolving "
                f"the target for {name!r}"
            ) from exc

    parent = target

    path = name.split(".")
    attribute = path[0]

    # We can't just always use getattr() because in doing
    # that on a class it will cause binding to occur which
    # will complicate things later and cause some things not
    # to work. For the case of a class we therefore access
    # the __dict__ directly. To cope though with the wrong
    # class being given to us, or a method being moved into
    # a base class, we need to walk the class hierarchy to
    # work out exactly which __dict__ the method was defined
    # in, as accessing it from __dict__ will fail if it was
    # not actually on the class given. Fallback to using
    # getattr() if we can't find it. If it truly doesn't
    # exist, then that will fail.

    def lookup_attribute(parent, attribute):
        try:
            if inspect.isclass(parent):
                for cls in inspect.getmro(parent):
                    if attribute in vars(cls):
                        return vars(cls)[attribute]
                else:
                    return getattr(parent, attribute)
            else:
                return getattr(parent, attribute)
        except AttributeError as exc:
            raise PathResolutionError(
                f"unable to resolve attribute {attribute!r} in path "
                f"{name!r} on {target!r}"
            ) from exc

    original = lookup_attribute(parent, attribute)

    for attribute in path[1:]:
        parent = original
        original = lookup_attribute(parent, attribute)

    return (parent, attribute, original)


def resolve_owner(target, name):
    """
    Sibling of the `resolve_path()` function, resolving the dotted path
    supplied as `name` on a target object in the same way and returning a
    tuple of the same shape, with one difference: the first element is the
    object whose `__dict__` actually defines the attribute, rather than
    the object the path resolved to. The two answer different questions.
    `resolve_path()` answers where to write so that lookups through the
    named object are affected, which is the correct location for
    installing a wrapper, and shadowing an inherited definition is
    legitimate there. `resolve_owner()` answers where the attribute
    physically lives, which is the correct location for removing a
    wrapper, since restoring anywhere other than the defining location
    would leave a shadowing copy behind. For a class target the owner is
    the defining class found by walking the MRO, for an instance target
    it is the instance itself if the attribute is in its `__dict__` and
    otherwise the defining class, and for a module target it is the
    module. For dotted paths the owner logic applies to the final segment
    only. An attribute served dynamically, such as by a module level or
    metaclass `__getattr__`, exists in no `__dict__`, and rather than
    guess, `PathResolutionError` is raised, where `resolve_path()` would
    return the value happily. Failures resolving the path itself raise
    exactly as for `resolve_path()`.
    """

    parent, attribute, original = resolve_path(target, name)

    if inspect.isclass(parent):
        candidates = inspect.getmro(parent)
    elif inspect.ismodule(parent):
        candidates = (parent,)
    else:
        candidates = (parent,) + tuple(inspect.getmro(type(parent)))

    for candidate in candidates:
        try:
            if attribute in vars(candidate):
                return (candidate, attribute, original)
        except TypeError:
            continue

    raise PathResolutionError(
        f"attribute {attribute!r} of {parent!r} is not defined in any "
        f"__dict__; it is served dynamically, so there is no owning "
        f"location to patch"
    )


def apply_patch(parent, attribute, replacement):
    """
    Convenience function for applying a patch to an attribute. This maps to
    the standard setattr() function.
    """

    setattr(parent, attribute, replacement)


def wrap_object(target, name, factory, args=(), kwargs=None):
    """
    Wraps an object which is the attribute of a target object with a wrapper
    object created by the `factory` function. The `target` can be a module,
    class, or instance of a class. In the special case of `target` being a
    string, it is assumed to be the name of a module, with the module being
    imported if necessary and then used as the target object. The `name` is a
    string representing the dotted path to the attribute. The `factory` function
    should accept the original object and may accept additional positional and
    keyword arguments which will be set by unpacking input arguments using
    `*args` and `**kwargs` calling conventions. The factory function should
    return a new object that will replace the original object, and should
    ordinarily be a `BaseObjectProxy` subclass or return an instance of
    one, so that the replacement can carry the installation details which
    `unwrap_object()` later relies upon to restore things faithfully.
    """

    if kwargs is None:
        kwargs = {}

    parent, attribute, original = resolve_path(target, name)

    # Record whether applying the patch creates the attribute slot on the
    # parent, or overwrites one which already existed. When the value was
    # being served from somewhere else, such as a base class via the MRO,
    # the class of an instance, or a dynamic __getattr__, the patch
    # creates a shadowing slot, and faithful removal is deleting that
    # slot again rather than assigning the original into it. This fact
    # only exists at installation time, so it is stashed on the wrapper
    # itself, in the local state of the proxy where lookups cannot be
    # confused with anything of the wrapped object's, for
    # unwrap_object() to consult. A factory result which is not a wrapt
    # proxy cannot carry it and unwrap_object() falls back to what can
    # be determined at removal time.

    try:
        created = attribute not in vars(parent)
    except TypeError:
        created = False

    wrapper = factory(original, *args, **kwargs)

    try:
        wrapper.__self_setattr__("__wrapt_wrap_object_created_slot__", created)
    except AttributeError:
        pass

    apply_patch(parent, attribute, wrapper)

    return wrapper


# Function for applying a proxy object to an attribute of a class
# instance. The wrapper works by defining an attribute of the same name
# on the class which is a descriptor and which intercepts access to the
# instance attribute. The descriptor is itself an object proxy wrapping
# whatever previously occupied the class attribute, be that another
# AttributeWrapper, some other descriptor such as a property, a plain
# class default, or the MISSING sentinel when nothing was defined, so
# stacked applications compose rather than replace one another and the
# prior definition keeps working beneath the interception.


class AttributeWrapper(BaseObjectProxy):
    """A descriptor that intercepts access to an instance attribute to apply
    a wrapper factory. The descriptor is an object proxy whose wrapped object
    is whatever previously occupied the class attribute, or the MISSING
    sentinel when nothing did, so stacked applications compose and a prior
    descriptor keeps executing its own logic beneath the interception."""

    def __init__(self, wrapped, attribute, factory, args=(), kwargs=None):
        super(AttributeWrapper, self).__init__(wrapped)
        self._self_attribute = attribute
        self._self_factory = factory
        self._self_args = args
        self._self_kwargs = kwargs if kwargs is not None else {}

    def __get__(self, instance, owner=None):
        # Class level access returns the descriptor itself. Being a
        # transparent proxy, introspection of the prior definition then
        # works through delegation.

        if instance is None:
            return self

        # Reads follow the standard attribute lookup precedence: a data
        # descriptor prior takes precedence over the instance
        # dictionary, a non-data descriptor prior yields to it, and a
        # plain class default is the fallback when no instance value
        # exists. Only when the prior is the MISSING sentinel, meaning
        # no definition of any sort existed, is AttributeError raised.

        prior = self.__wrapped__
        prior_type = type(prior)

        if hasattr(prior_type, "__get__") and (
            hasattr(prior_type, "__set__") or hasattr(prior_type, "__delete__")
        ):
            value = prior.__get__(instance, owner)
        elif self._self_attribute in instance.__dict__:
            value = instance.__dict__[self._self_attribute]
        elif hasattr(prior_type, "__get__"):
            value = prior.__get__(instance, owner)
        elif prior is not MISSING:
            value = prior
        else:
            raise AttributeError(
                f"{type(instance).__name__!r} object has no attribute "
                f"{self._self_attribute!r}"
            )

        return self._self_factory(value, *self._self_args, **self._self_kwargs)

    def __set__(self, instance, value):
        # Writes delegate to a prior descriptor which implements
        # __set__, so its validation and storage are honoured, and
        # otherwise store into the instance dictionary.

        prior = self.__wrapped__

        if hasattr(type(prior), "__set__"):
            prior.__set__(instance, value)
        else:
            instance.__dict__[self._self_attribute] = value

    def __delete__(self, instance):
        prior = self.__wrapped__

        if hasattr(type(prior), "__delete__"):
            prior.__delete__(instance)
        else:
            # Match the exception deleting the attribute would raise if
            # the wrapper had not been applied, which is AttributeError
            # rather than the KeyError of the raw dictionary lookup.

            try:
                del instance.__dict__[self._self_attribute]
            except KeyError:
                raise AttributeError(
                    f"{type(instance).__name__!r} object has no attribute "
                    f"{self._self_attribute!r}"
                ) from None


def wrap_object_attribute(module, name, factory, args=(), kwargs=None):
    """
    Wraps an object which is the attribute of a class instance with a wrapper
    object created by the `factory` function. It does this by patching the
    class, not the instance, with a descriptor that intercepts access to the
    instance attribute. The `module` can be a module, class, or instance of a
    class. In the special case of `module` being a string, it is assumed to be
    the name of a module, with the module being imported if necessary and then
    used as the target object. The `name` is a string representing the dotted
    path to the attribute. The `factory` function should accept the original
    object and may accept additional positional and keyword arguments which will
    be set by unpacking input arguments using `*args` and `**kwargs` calling
    conventions. The factory function should return a new object that will
    replace the original object. Returns the `AttributeWrapper` descriptor
    installed on the class, which wraps whatever previously occupied the
    class attribute, or the `MISSING` sentinel when nothing did, so repeated
    applications compose rather than replace one another.
    """

    if kwargs is None:
        kwargs = {}

    path, attribute = name.rsplit(".", 1)
    parent = resolve_path(module, path)[2]
    prior = vars(parent).get(attribute, MISSING)
    wrapper = AttributeWrapper(prior, attribute, factory, args, kwargs)
    apply_patch(parent, attribute, wrapper)
    return wrapper


# Functions for creating a simple decorator using a FunctionWrapper,
# plus short cut functions for applying wrappers to functions. These are
# for use when doing monkey patching. For a more featured way of
# creating decorators see the decorator decorator instead.


def function_wrapper(wrapper):
    """
    Creates a decorator for wrapping a function with a `wrapper` function.
    The decorator which is returned may also be applied to any other callable
    objects such as lambda functions, methods, classmethods, and staticmethods,
    or objects which implement the `__call__()` method. The `wrapper` function
    should accept the `wrapped` function, `instance`, `args`, and `kwargs`,
    arguments and return the result of calling the wrapped function or some
    other appropriate value.
    """

    def _wrapper(wrapped, instance, args, kwargs):
        target_wrapped = args[0]
        if instance is None:
            target_wrapper = wrapper
        elif inspect.isclass(instance):
            target_wrapper = wrapper.__get__(None, instance)
        else:
            target_wrapper = wrapper.__get__(instance, type(instance))
        return FunctionWrapper(target_wrapped, target_wrapper)

    return FunctionWrapper(wrapper, _wrapper)


def wrap_function_wrapper(target, name, wrapper):
    """
    Wraps a function which is the attribute of a target object with a `wrapper`
    function. The `target` can be a module, class, or instance of a class. In
    the special case of `target` being a string, it is assumed to be the name
    of a module, with the module being imported if necessary. If the `target`
    is a string with a trailing ``?``, the wrapping will be deferred until the
    module is imported. If the module is already imported, the wrapping will be
    applied immediately. The `name` is a string representing the dotted path to
    the attribute. The `wrapper` function should accept the `wrapped` function,
    `instance`, `args`, and `kwargs` arguments, and would return the result of
    calling the wrapped attribute or some other appropriate value. Returns the
    wrapped target function if the wrapping was applied immediately, or ``None``
    if the wrapping was deferred.
    """

    if isinstance(target, str) and target.endswith("?"):
        target = target[:-1]

        if target in sys.modules:
            return wrap_object(sys.modules[target], name, FunctionWrapper, (wrapper,))

        def callback(module):
            wrap_object(module, name, FunctionWrapper, (wrapper,))

        register_post_import_hook(callback, target)
        return None

    return wrap_object(target, name, FunctionWrapper, (wrapper,))


def patch_function_wrapper(target, name, _enabled=MISSING, *, enabled=MISSING):
    """
    Creates a decorator which can be applied to a wrapper function, where the
    wrapper function will be used to wrap a function which is the attribute of
    a target object. The decorator returns the original wrapper function. The
    `target` can be a module, class, or instance of a class. In the special case
    of `target` being a string, it is assumed to be the name of a module, with
    the module being imported if necessary. If the `target` is a string with a
    trailing ``?``, the wrapping will be deferred until the module is imported.
    If the module is already imported, the wrapping will be applied immediately.
    The `name` is a string representing the dotted path to the attribute. The
    `enabled` argument is keyword only and can be a boolean or a callable that
    returns a boolean. When a callable is provided, it will be called each time
    the wrapper is invoked to determine if the wrapper function should be
    executed or whether the wrapped function should be called directly. If
    `enabled` is not provided, or an explicit value of `None` is supplied,
    the wrapper is enabled by default.
    """

    if _enabled is not MISSING:
        if enabled is not MISSING:
            raise TypeError(
                "patch_function_wrapper() got multiple values for " "argument 'enabled'"
            )
        warnings.warn(
            "Passing 'enabled' positionally to patch_function_wrapper() is "
            "deprecated and will be an error in a future version of wrapt; "
            "pass it as a keyword argument.",
            DeprecationWarning,
            stacklevel=2,
        )
        enabled = _enabled

    if enabled is MISSING:
        enabled = None

    def _wrapper(wrapper):
        if isinstance(target, str) and target.endswith("?"):
            _target = target[:-1]

            if _target in sys.modules:
                wrap_object(
                    sys.modules[_target], name, FunctionWrapper, (wrapper, enabled)
                )
                return wrapper

            def callback(module):
                wrap_object(module, name, FunctionWrapper, (wrapper, enabled))

            register_post_import_hook(callback, _target)
            return wrapper

        wrap_object(target, name, FunctionWrapper, (wrapper, enabled))
        return wrapper

    return _wrapper


def transient_function_wrapper(target, name):
    """Creates a decorator that patches a target function with a wrapper
    function, but only for the duration of the call that the decorator was
    applied to. The `target` can be a module, class, or instance of a class.
    In the special case of `target` being a string, it is assumed to be the name
    of a module, with the module being imported if necessary. The `name` is a
    string representing the dotted path to the attribute. The patch is applied
    to the object the path resolves to, so patching an attribute reached
    through inheritance, or through an instance, only affects lookups made
    through that object and not the class where the attribute is defined. In
    that case the temporary attribute which shadowed the inherited definition
    is removed again when the call exits, restoring the original lookup.

    The temporary wrapper is removed using `unwrap_object()`, so if code
    called within the scope of the patch wrapped over the top of the
    temporary wrapper with a wrapt wrapper and left it there, the temporary
    wrapper is spliced out beneath it, with the other wrapper left in
    place. If something removed or replaced the temporary wrapper during
    the call, `WrapperNotFoundError` is raised, and if what was applied on
    top of it is not a wrapt wrapper and so cannot be spliced past,
    `WrapperNotOutermostError` is raised. Both are loud deliberately, as
    they indicate the surrounding code, typically a test harness, is not
    managing its own patches properly, and the leaked patch state would
    otherwise surface as hard to diagnose failures later.
    """

    def _decorator(wrapper):
        def _wrapper(wrapped, instance, args, kwargs):
            target_wrapped = args[0]
            if instance is None:
                target_wrapper = wrapper
            elif inspect.isclass(instance):
                target_wrapper = wrapper.__get__(None, instance)
            else:
                target_wrapper = wrapper.__get__(instance, type(instance))

            def _execute(wrapped, instance, args, kwargs):
                # The wrap and unwrap functions handle all the details:
                # wrap_object() records whether applying the patch created
                # a shadowing attribute slot, and unwrap_object() consults
                # that record to restore or remove the attribute
                # faithfully, splices the temporary wrapper out from
                # beneath any wrapt wrapper left applied on top of it, and
                # raises if the temporary wrapper was removed, replaced,
                # or pinned beneath a non wrapt wrapper. An exception
                # raised on exit supersedes any in-flight exception from
                # the wrapped call, which remains visible as the chained
                # __context__.

                replacement = wrap_object(
                    target, name, FunctionWrapper, (target_wrapper,)
                )

                try:
                    return wrapped(*args, **kwargs)
                finally:
                    unwrap_object(target, name, replacement)

            return FunctionWrapper(target_wrapped, _execute)

        return FunctionWrapper(wrapper, _wrapper)

    return _decorator


@contextlib.contextmanager
def scoped_function_wrapper(target, name, wrapper):
    """Returns a context manager which patches a target function with a
    wrapper function for the duration of a with statement, the block scoped
    counterpart of the `transient_function_wrapper()` decorator. The
    arguments take the same form as for `wrap_function_wrapper()`: the
    `target` can be a module, class, or instance of a class, or the name of
    a module as a string, the `name` is a string representing the dotted
    path to the attribute, and the `wrapper` function should accept the
    `wrapped`, `instance`, `args`, and `kwargs` arguments. The deferred
    form of the `target` with a trailing ``?`` is not supported, since the
    patch must be applied at the point the with statement is entered. The
    context manager yields nothing, is single use, and removes the wrapper
    using `unwrap_object()` when the block exits, with the same behaviour
    as `transient_function_wrapper()` when something interfered with the
    patch during the block: a wrapt wrapper applied on top of the temporary
    wrapper and left there is tolerated, with the temporary wrapper spliced
    out beneath it, while the temporary wrapper having been removed or
    replaced raises `WrapperNotFoundError`, and a non wrapt wrapper left
    applied on top raises `WrapperNotOutermostError`.
    """

    if isinstance(target, str) and target.endswith("?"):
        raise ValueError(
            "deferred wrapping using a target with a trailing '?' cannot "
            "be used with scoped_function_wrapper()"
        )

    handle = wrap_function_wrapper(target, name, wrapper)

    try:
        yield
    finally:
        unwrap_object(target, name, handle)


# Functions for introspecting chains of wrappers, linked by each wrapper
# holding the object it wraps as the __wrapped__ attribute. The chain
# protocol is shared by wrapt proxies and wrappers, functions decorated
# using functools.wraps(), and anything else honouring the convention.


def wrapper_chain(obj, *, limit=64):
    """
    Returns an iterator yielding `obj`, then each successive object found
    by following the `__wrapped__` attribute, outermost wrapper first. The
    final item yielded is the innermost object of the chain, which is not
    itself a wrapper. Traversal ends cleanly at an object with no
    `__wrapped__` attribute, or upon returning to an object already seen.
    If the `limit` on the number of items yielded is reached with a further
    chain link still pending, `WrapperChainTooDeepError` is raised, as a
    truncated scan would otherwise be indistinguishable from a complete
    one. A chain of exactly `limit` items which ends naturally is not an
    error. Note that reading `__wrapped__` from a lazy object proxy will
    cause it to materialize, and an exception raised by a broken proxy or
    a lazy object factory will propagate to the caller.
    """

    # Cycle detection must use identity, not equality or a set of the
    # objects themselves, since proxies delegate __eq__ and __hash__ to
    # the wrapped object. Objects seen are therefore tracked by id(),
    # with strong references also held so no visited object can be
    # garbage collected and have its id reused while the scan runs, ids
    # being unique among simultaneously live objects.

    seen = []
    seen_ids = set()

    current = obj

    while True:
        if id(current) in seen_ids:
            return

        if len(seen) >= limit:
            raise WrapperChainTooDeepError(
                f"wrapper chain of {obj!r} exceeded {limit} levels"
            )

        seen.append(current)
        seen_ids.add(id(current))

        yield current

        try:
            current = current.__wrapped__
        except AttributeError:
            return


def unwrapped(obj, *, limit=64):
    """
    Returns the innermost object of the chain of wrappers followed from
    `obj` by the `wrapper_chain()` function, or `obj` itself when it is not
    wrapped. Shares the full contract of `wrapper_chain()`, including
    raising `WrapperChainTooDeepError` when the scan is indeterminate,
    rather than returning a mid chain wrapper as if it were the innermost
    object.
    """

    result = obj

    for result in wrapper_chain(obj, limit=limit):
        pass

    return result


def find_wrapper(obj, handle=None, *, predicate=None, limit=64):
    """
    Scans the chain of wrappers followed from `obj` by the
    `wrapper_chain()` function for a specific wrapper and returns it, or
    `None` when it is not present. The `handle` argument is the wrapper
    object to look for, as returned by the wrap functions when the wrapper
    was installed, and is matched by object identity only, never equality,
    which proxies delegate to the wrapped object. Alternatively a
    `predicate` function may be supplied, in which case the first chain
    entry for which it returns true is returned, and is itself usable as a
    handle thereafter. When both are supplied, both must match. At least
    one of the two must be supplied, since testing for the mere presence
    of any wrapper is fragile: were the target library to adopt wrapt for
    its own purposes, such a test would wrongly conclude a wrapper of
    yours was installed. Shares the full contract of `wrapper_chain()`,
    including raising `WrapperChainTooDeepError` when the scan is
    indeterminate, rather than returning `None` as a false negative.
    """

    if handle is None and predicate is None:
        raise TypeError(
            "find_wrapper() requires a wrapper handle or a predicate"
        )

    for entry in wrapper_chain(obj, limit=limit):
        if handle is not None and entry is not handle:
            continue
        if predicate is not None and not predicate(entry):
            continue
        return entry

    return None


def is_wrapped_by(obj, handle=None, *, predicate=None, limit=64):
    """
    Boolean convenience form of the `find_wrapper()` function, returning
    whether the wrapper is present in the chain of wrappers followed from
    `obj`. With a `handle`, this answers whether the wrapper it was
    returned for when installed is still in place, which is the check to
    run when a third party may have replaced the attribute wholesale.
    Shares the full contract of `find_wrapper()`, including raising
    `WrapperChainTooDeepError` when the scan is indeterminate, rather
    than returning `False` as a false negative.
    """

    return find_wrapper(obj, handle, predicate=predicate, limit=limit) is not None


def unwrap_object(target, name, handle, *, missing_ok=False):
    """
    Removes a wrapper which was installed on an attribute of a target
    object, the inverse of the `wrap_object()` function and the removal
    call for every wrap form, `wrap_function_wrapper()` and
    `wrap_object_attribute()` included. The `target` and `name` arguments
    take the same form as for `resolve_path()`. The `handle` argument is
    the wrapper object which was returned when the wrapper was installed,
    and is matched by object identity only. Note that it is not the
    wrapper function: passing the wrapper function surfaces immediately
    as `WrapperNotFoundError`, since a function is never a chain entry.

    When the wrapper is found and is outermost, the attribute is restored
    to the object the wrapper wrapped, at the location where the attribute
    is actually defined per `resolve_owner()`, so removal through a
    subclass restores the defining base class rather than leaving a
    shadowing copy. If restoring would merely shadow the identical object
    already reachable through the MRO, or the wrapper was installed where
    no prior definition existed (a `MISSING` terminal), the attribute is
    instead removed so no residue is left behind. When the wrapper is
    found buried beneath other wrapt wrappers, it is spliced out of the
    chain in place, without touching the attribute or disturbing the
    wrappers above it. When what sits directly above it is not a wrapt
    wrapper, such as a plain `functools.wraps()` closure whose
    `__wrapped__` is only metadata, `WrapperNotOutermostError` is raised
    naming what is above, since splicing there would silently not take
    effect.

    When the wrapper is not found, because the attribute was never
    wrapped, the wrapper was already removed, or a third party replaced
    the attribute wholesale, `WrapperNotFoundError` is raised by default.
    Passing `missing_ok=True` returns `None` instead, for shutdown paths
    which must tolerate third party interference. In either case nothing
    is mutated. The wrapper which was removed is returned. Note that
    `missing_ok` does not suppress `WrapperChainTooDeepError` from the
    underlying scan, since an indeterminate scan is not the same thing as
    the wrapper being gone.
    """

    try:
        owner, attribute, current = resolve_owner(target, name)
    except PathResolutionError as exc:
        # The attribute is either wholly absent or served dynamically
        # with no owning location. In neither case is anything of the
        # caller's statically installed, so both are the not-found
        # case, except when the wrapper is present in the dynamically
        # served value, where removal is simply not possible.

        try:
            current = resolve_path(target, name)[2]
        except PathResolutionError:
            current = None

        if current is not None and find_wrapper(current, handle) is not None:
            raise WrapperNotOutermostError(
                f"cannot remove {type(handle).__name__} from "
                f"{target!r}.{name}: the attribute is served dynamically "
                f"and has no owning location to restore"
            ) from exc

        if missing_ok:
            return None

        raise WrapperNotFoundError(
            f"handle {handle!r} not found on {target!r}.{name}"
        ) from exc

    found = find_wrapper(current, handle)

    if found is not None:
        try:
            restored = found.__wrapped__
        except AttributeError:
            # The terminal original object was matched, which the chain
            # also yields; not being a wrapper, it is not a legitimate
            # handle.
            found = None

    if found is None:
        if missing_ok:
            return None
        raise WrapperNotFoundError(
            f"handle {handle!r} not found on {target!r}.{name}"
        )

    if found is not current:
        chain = list(wrapper_chain(current))

        # The scan must use identity, since list.index() would use
        # __eq__, which proxies delegate to the wrapped object.

        position = next(
            index for index, entry in enumerate(chain) if entry is found
        )
        neighbour = chain[position - 1]

        if not issubclass(type(neighbour), BaseObjectProxy):
            above = [type(entry).__name__ for entry in chain[:position]]
            raise WrapperNotOutermostError(
                f"cannot remove {type(found).__name__} from "
                f"{target!r}.{name}: wrapped by {above}"
            )

        neighbour.__wrapped__ = restored
        return found

    if restored is MISSING:
        # The wrapper was installed where no prior definition existed.
        delattr(owner, attribute)
        return found

    # When wrap_object() installed the wrapper, it recorded on the
    # wrapper itself whether applying the patch created the attribute
    # slot. That fact is authoritative: since the wrapper is still
    # installed and outermost here, the slot cannot have been touched
    # since it was recorded. It must be read from the proxy's own local
    # state only, since ordinary attribute access would delegate a
    # missing entry to the wrapped object and could answer with an
    # inner wrapper's record instead.

    try:
        created = found.__self_dict__.get("__wrapt_wrap_object_created_slot__")
    except AttributeError:
        created = None

    if created is not None:
        if created:
            # Installing the wrapper created a shadowing slot, so
            # removing the attribute reinstates the original lookup,
            # be that through the MRO, the class of an instance, or a
            # dynamic __getattr__, rather than leaving a permanent
            # copy of the original behind.
            delattr(owner, attribute)
        else:
            apply_patch(owner, attribute, restored)
        return found

    # The wrapper does not carry the installation record, so fall back
    # to what can be determined at removal time: if removing the
    # attribute from a class would re-expose the identical restored
    # object through the MRO, the wrap must have created a shadow.

    if inspect.isclass(owner):
        inherited = next(
            (
                vars(cls)[attribute]
                for cls in inspect.getmro(owner)[1:]
                if attribute in vars(cls)
            ),
            None,
        )
        if inherited is restored:
            delattr(owner, attribute)
            return found

    apply_patch(owner, attribute, restored)
    return found
