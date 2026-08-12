"""Utilities for monkey patching and wrapping object attributes."""

import inspect
import sys
import warnings

from .__wrapt__ import FunctionWrapper
from .exceptions import PathResolutionError, TargetModuleNotFoundError
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
        try:
            __import__(target)
        except ModuleNotFoundError as exc:
            raise TargetModuleNotFoundError(
                f"unable to import module {target!r} while resolving "
                f"the target for {name!r}"
            ) from exc
        target = sys.modules[target]

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
    return a new object that will replace the original object.
    """

    if kwargs is None:
        kwargs = {}

    (parent, attribute, original) = resolve_path(target, name)
    wrapper = factory(original, *args, **kwargs)
    apply_patch(parent, attribute, wrapper)

    return wrapper


# Function for applying a proxy object to an attribute of a class
# instance. The wrapper works by defining an attribute of the same name
# on the class which is a descriptor and which intercepts access to the
# instance attribute. Note that this cannot be used on attributes which
# are themselves defined by a property object.


class AttributeWrapper:
    """A descriptor that intercepts access to an instance attribute to apply
    a wrapper factory."""

    def __init__(self, attribute, factory, args, kwargs):
        self.attribute = attribute
        self.factory = factory
        self.args = args
        self.kwargs = kwargs

    def __get__(self, instance, owner):
        value = instance.__dict__[self.attribute]
        return self.factory(value, *self.args, **self.kwargs)

    def __set__(self, instance, value):
        instance.__dict__[self.attribute] = value

    def __delete__(self, instance):
        del instance.__dict__[self.attribute]


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
    replace the original object.
    """

    if kwargs is None:
        kwargs = {}

    path, attribute = name.rsplit(".", 1)
    parent = resolve_path(module, path)[2]
    wrapper = AttributeWrapper(attribute, factory, args, kwargs)
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
                "patch_function_wrapper() got multiple values for "
                "argument 'enabled'"
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
                (parent, attribute, original) = resolve_path(target, name)
                replacement = FunctionWrapper(original, target_wrapper)

                # The attribute may not be defined directly on the parent,
                # instead being found on a base class of the parent via the
                # MRO, or via some dynamic lookup mechanism. In those cases
                # applying the patch creates a new attribute on the parent
                # which shadows where the original was found. Restoration
                # must then remove that shadowing attribute again rather
                # than set the original on the parent, else a permanent
                # copy of the original is left behind on the parent.

                try:
                    direct = attribute in vars(parent)
                except TypeError:
                    direct = True

                setattr(parent, attribute, replacement)
                try:
                    return wrapped(*args, **kwargs)
                finally:
                    if direct:
                        setattr(parent, attribute, original)
                    else:
                        try:
                            delattr(parent, attribute)
                        except AttributeError:
                            pass

            return FunctionWrapper(target_wrapped, _execute)

        return FunctionWrapper(wrapper, _wrapper)

    return _decorator
