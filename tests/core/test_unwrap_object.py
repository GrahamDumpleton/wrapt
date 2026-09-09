import functools
import sys
import types
import unittest

import wrapt


def wrapper_a(wrapped, instance, args, kwargs):
    return ("a", wrapped(*args, **kwargs))


def wrapper_b(wrapped, instance, args, kwargs):
    return ("b", wrapped(*args, **kwargs))


class TestUnwrapObject(unittest.TestCase):

    def setUp(self):
        self.module = types.ModuleType("unwrap_object_target")
        self.module.function = lambda: "original"
        sys.modules["unwrap_object_target"] = self.module

    def tearDown(self):
        del sys.modules["unwrap_object_target"]

    def test_remove_outermost(self):
        original = self.module.function

        handle = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        self.assertIs(wrapt.unwrap_object(self.module, "function", handle), handle)
        self.assertIs(self.module.function, original)
        self.assertEqual(self.module.function(), "original")

    def test_remove_buried_splices(self):
        # A wrapper buried beneath another wrapt wrapper is spliced out
        # of the chain in place. The holder attribute is untouched and
        # the wrapper above keeps working.

        handle_a = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)
        handle_b = wrapt.wrap_function_wrapper(self.module, "function", wrapper_b)

        self.assertEqual(self.module.function(), ("b", ("a", "original")))

        self.assertIs(
            wrapt.unwrap_object(self.module, "function", handle_a), handle_a
        )

        self.assertIs(self.module.function, handle_b)
        self.assertEqual(self.module.function(), ("b", "original"))

        # The remaining wrapper unwraps normally afterwards.

        self.assertIs(
            wrapt.unwrap_object(self.module, "function", handle_b), handle_b
        )
        self.assertEqual(self.module.function(), "original")

    def test_buried_under_closure_raises(self):
        # When what sits above the wrapper is not a wrapt wrapper, its
        # __wrapped__ is only metadata, so splicing would silently not
        # take effect and the removal is refused, naming what is above.

        handle = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        inner = self.module.function

        @functools.wraps(inner)
        def closure():
            return ("closure", inner())

        self.module.function = closure

        with self.assertRaises(wrapt.WrapperNotOutermostError) as cm:
            wrapt.unwrap_object(self.module, "function", handle)

        self.assertIn("function", str(cm.exception))

        # missing_ok tolerates only the not-found case, not this one.

        with self.assertRaises(wrapt.WrapperNotOutermostError):
            wrapt.unwrap_object(self.module, "function", handle, missing_ok=True)

    def test_not_found(self):
        original = self.module.function
        handle = wrapt.FunctionWrapper(original, wrapper_a)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", handle)

        self.assertIsNone(
            wrapt.unwrap_object(self.module, "function", handle, missing_ok=True)
        )

        # Nothing was mutated either way.

        self.assertIs(self.module.function, original)

    def test_unwrap_twice(self):
        handle = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        wrapt.unwrap_object(self.module, "function", handle)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", handle)

        self.assertIsNone(
            wrapt.unwrap_object(self.module, "function", handle, missing_ok=True)
        )

    def test_wrapper_function_as_handle(self):
        # Passing the wrapper function where the handle is expected is
        # the predictable mistake; a function is never a chain entry, so
        # it surfaces immediately as not found rather than silently
        # doing nothing.

        wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", wrapper_a)

        # A wrapt-decorated wrapper function is a proxy, but still never
        # a chain entry, and funnels into the same error.

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthrough
        def decorated_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", decorated_wrapper)

    def test_terminal_original_as_handle(self):
        # The terminal original object is yielded by the chain and so
        # matches by identity, but not being a wrapper it is not a
        # legitimate handle and is treated as not found.

        original = self.module.function

        wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", original)

        self.assertIsNone(
            wrapt.unwrap_object(self.module, "function", original, missing_ok=True)
        )

    def test_equal_but_distinct_proxy(self):
        # An object which merely compares equal to a chain entry is not
        # matched; the scan is identity only.

        handle = wrapt.wrap_object(self.module, "function", wrapt.ObjectProxy)

        imposter = wrapt.ObjectProxy(
            object.__getattribute__(handle, "__wrapped__")
        )

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", imposter)

        self.assertIs(wrapt.unwrap_object(self.module, "function", handle), handle)

    def test_same_wrapper_function_twice(self):
        # The same wrapper function installed twice produces two
        # distinct handles, each removing exactly its own instance.

        first = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)
        second = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        self.assertIs(wrapt.unwrap_object(self.module, "function", first), first)
        self.assertIs(self.module.function, second)

        self.assertIs(wrapt.unwrap_object(self.module, "function", second), second)
        self.assertEqual(self.module.function(), "original")

    def test_wholesale_replacement(self):
        # After a third party blindly restores the original with
        # setattr(), the handle is no longer present.

        original = self.module.function

        handle = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        self.module.function = original

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(self.module, "function", handle)

        self.assertIsNone(
            wrapt.unwrap_object(self.module, "function", handle, missing_ok=True)
        )

    def test_class_attribute(self):
        class MyClass:
            def method(self):
                return "original"

        original = vars(MyClass)["method"]

        handle = wrapt.wrap_function_wrapper(MyClass, "method", wrapper_a)

        self.assertIs(wrapt.unwrap_object(MyClass, "method", handle), handle)
        self.assertIs(vars(MyClass)["method"], original)
        self.assertEqual(MyClass().method(), "original")

    def test_inherited_owner(self):
        # A wrapper installed on a base class and removed via a subclass
        # is restored at the defining base class, leaving no shadowing
        # copy on the subclass.

        class Base:
            def method(self):
                return "original"

        class Derived(Base):
            pass

        original = vars(Base)["method"]

        handle = wrapt.wrap_function_wrapper(Base, "method", wrapper_a)

        self.assertIs(wrapt.unwrap_object(Derived, "method", handle), handle)
        self.assertIs(vars(Base)["method"], original)
        self.assertNotIn("method", vars(Derived))
        self.assertEqual(Base().method(), "original")

    def test_shadow_removed_without_residue(self):
        # Installing via a subclass shadows the inherited definition on
        # the subclass. Removal deletes the shadowing attribute rather
        # than assigning the original into it, so the original lookup
        # path is reinstated and later patches of the base class are
        # seen through the subclass again.

        class Base:
            def method(self):
                return "original"

        class Derived(Base):
            pass

        handle = wrapt.wrap_function_wrapper(Derived, "method", wrapper_a)

        self.assertIn("method", vars(Derived))

        self.assertIs(wrapt.unwrap_object(Derived, "method", handle), handle)
        self.assertNotIn("method", vars(Derived))

        base_handle = wrapt.wrap_function_wrapper(Base, "method", wrapper_b)

        self.assertEqual(Derived().method(), ("b", "original"))

        wrapt.unwrap_object(Base, "method", base_handle)

    def test_too_deep_not_suppressed(self):
        # A handle buried deeper than the traversal limit raises
        # WrapperChainTooDeepError, not WrapperNotFoundError, and
        # missing_ok does not suppress it: an indeterminate scan is not
        # the same thing as the wrapper being gone.

        handle = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        for _ in range(80):
            wrapt.wrap_function_wrapper(self.module, "function", wrapper_b)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            wrapt.unwrap_object(self.module, "function", handle)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            wrapt.unwrap_object(self.module, "function", handle, missing_ok=True)

    def test_deferred_wrap_and_handle_recovery(self):
        # A deferred wrap of a not-yet-imported module returns None, so
        # no handle exists. Once the module is imported and the patch
        # applied, the installed wrapper can be recovered with a
        # predicate and the recovered entry used as the handle.

        self.assertIsNone(
            wrapt.wrap_function_wrapper(
                "unwrap_object_deferred?", "function", wrapper_a
            )
        )

        module = types.ModuleType("unwrap_object_deferred")
        module.function = lambda: "original"
        original = module.function
        sys.modules["unwrap_object_deferred"] = module

        try:
            wrapt.notify_module_loaded(module)

            current = wrapt.resolve_path(module, "function")[2]

            recovered = wrapt.find_wrapper(
                current,
                predicate=lambda entry: getattr(entry, "_self_wrapper", None)
                is wrapper_a,
            )

            self.assertIsNotNone(recovered)

            self.assertIs(
                wrapt.unwrap_object(module, "function", recovered), recovered
            )
            self.assertIs(module.function, original)
        finally:
            del sys.modules["unwrap_object_deferred"]

    def test_dynamic_attribute_not_found(self):
        # An attribute served dynamically has no owning location. When
        # the wrapper is not present in the served value there is
        # nothing of the caller's statically installed, so this is the
        # not-found case.

        class Meta(type):
            def __getattr__(cls, name):
                if name == "dynamic":
                    return 42
                raise AttributeError(name)

        class MyClass(metaclass=Meta):
            pass

        handle = wrapt.FunctionWrapper(lambda: None, wrapper_a)

        with self.assertRaises(wrapt.WrapperNotFoundError):
            wrapt.unwrap_object(MyClass, "dynamic", handle)

        self.assertIsNone(
            wrapt.unwrap_object(MyClass, "dynamic", handle, missing_ok=True)
        )

    def test_dynamic_attribute_with_wrapper_raises(self):
        # When the wrapper is present in a dynamically served value it
        # cannot be removed, since there is no owning location to
        # restore, and that is not the same as it being gone.

        wrapper = wrapt.FunctionWrapper(lambda: "original", wrapper_a)

        class Meta(type):
            def __getattr__(cls, name):
                if name == "dynamic":
                    return wrapper
                raise AttributeError(name)

        class MyClass(metaclass=Meta):
            pass

        with self.assertRaises(wrapt.WrapperNotOutermostError):
            wrapt.unwrap_object(MyClass, "dynamic", wrapper)

        with self.assertRaises(wrapt.WrapperNotOutermostError):
            wrapt.unwrap_object(MyClass, "dynamic", wrapper, missing_ok=True)

    def test_value_proxy(self):
        # A non-callable attribute wrapped with an object proxy is
        # removed by its handle with the identical original restored.

        class TrackingProxy(wrapt.ObjectProxy):
            pass

        self.module.client = object()
        original = self.module.client

        handle = wrapt.wrap_object(self.module, "client", TrackingProxy)

        self.assertIs(wrapt.unwrap_object(self.module, "client", handle), handle)
        self.assertIs(self.module.client, original)


class TestUnwrapObjectAttribute(unittest.TestCase):

    def setUp(self):
        self.module = types.ModuleType("unwrap_attribute_target")
        sys.modules["unwrap_attribute_target"] = self.module

    def tearDown(self):
        del sys.modules["unwrap_attribute_target"]

    def test_buried_interceptor_spliced(self):
        # A buried AttributeWrapper is spliced out in place, with the
        # remaining layers still composing.

        class SpecialDescriptor:
            def __get__(self, instance, owner=None):
                if instance is None:
                    return self
                return instance.__dict__.get("_special", "their-default")

            def __set__(self, instance, value):
                instance.__dict__["_special"] = value

        class MyClass:
            value = SpecialDescriptor()

        self.module.MyClass = MyClass

        inner = wrapt.wrap_object_attribute(
            self.module, "MyClass.value", lambda value: ("inner", value)
        )
        outer = wrapt.wrap_object_attribute(
            self.module, "MyClass.value", lambda value: ("outer", value)
        )

        instance = MyClass()
        instance.value = 1

        self.assertEqual(instance.value, ("outer", ("inner", 1)))

        self.assertIs(wrapt.unwrap_object(MyClass, "value", inner), inner)

        self.assertIs(vars(MyClass)["value"], outer)
        self.assertEqual(instance.value, ("outer", 1))

    def test_outermost_restores_descriptor(self):
        # Removing the outermost interceptor restores the replaced
        # custom descriptor to the class slot bit-identical.

        class SpecialDescriptor:
            def __get__(self, instance, owner=None):
                if instance is None:
                    return self
                return instance.__dict__.get("_special", "their-default")

            def __set__(self, instance, value):
                instance.__dict__["_special"] = value

        class MyClass:
            value = SpecialDescriptor()

        theirs = vars(MyClass)["value"]

        self.module.MyClass = MyClass

        handle = wrapt.wrap_object_attribute(
            self.module, "MyClass.value", lambda value: ("wrapped", value)
        )

        instance = MyClass()
        instance.value = 1

        self.assertIs(wrapt.unwrap_object(MyClass, "value", handle), handle)
        self.assertIs(vars(MyClass)["value"], theirs)
        self.assertEqual(instance.value, 1)

    def test_missing_terminal_removed(self):
        # An interceptor installed where no prior definition existed is
        # removed with the attribute deleted outright, and instance
        # values are unaffected, since the interceptor stores raw
        # values.

        class MyClass:
            def __init__(self, value):
                self.value = value

        self.module.MyClass = MyClass

        handle = wrapt.wrap_object_attribute(
            self.module, "MyClass.value", lambda value: ("wrapped", value)
        )

        instance = MyClass(5)

        self.assertEqual(instance.value, ("wrapped", 5))

        self.assertIs(wrapt.unwrap_object(MyClass, "value", handle), handle)
        self.assertNotIn("value", vars(MyClass))
        self.assertEqual(instance.value, 5)

    def test_class_default_restored(self):
        class MyClass:
            value = "default"

        self.module.MyClass = MyClass

        handle = wrapt.wrap_object_attribute(
            self.module, "MyClass.value", lambda value: ("wrapped", value)
        )

        self.assertEqual(MyClass().value, ("wrapped", "default"))

        self.assertIs(wrapt.unwrap_object(MyClass, "value", handle), handle)
        self.assertEqual(vars(MyClass)["value"], "default")
        self.assertEqual(MyClass().value, "default")


class TestUnwrapObjectCreatedSlot(unittest.TestCase):

    # The wrap functions record on the wrapper whether applying the
    # patch created the attribute slot, and unwrap_object() consults
    # that record to decide between restoring by assignment and
    # removing the attribute.

    def setUp(self):
        self.module = types.ModuleType("unwrap_created_target")
        sys.modules["unwrap_created_target"] = self.module

    def tearDown(self):
        del sys.modules["unwrap_created_target"]

    def test_instance_target_no_residue(self):
        # A wrapper installed through an instance for a method defined
        # on its class creates a shadowing entry in the instance
        # dictionary. Removal deletes that entry rather than leaving a
        # bound copy of the method behind on the instance.

        class MyClass:
            def method(self):
                return "original"

        instance = MyClass()

        handle = wrapt.wrap_function_wrapper(instance, "method", wrapper_a)

        self.assertIn("method", vars(instance))

        self.assertIs(wrapt.unwrap_object(instance, "method", handle), handle)
        self.assertNotIn("method", vars(instance))
        self.assertEqual(instance.method(), "original")

    def test_dynamic_attribute_no_residue(self):
        # A wrapper installed over a value served by a module level
        # __getattr__ creates a static shadowing attribute on the
        # module. Removal deletes it again, so the dynamic lookup is
        # reinstated rather than a static copy of the original being
        # left behind.

        def module_getattr(name):
            if name == "dynamic":
                return lambda: "original"
            raise AttributeError(name)

        self.module.__getattr__ = module_getattr

        handle = wrapt.wrap_function_wrapper(self.module, "dynamic", wrapper_a)

        self.assertIn("dynamic", vars(self.module))

        self.assertIs(wrapt.unwrap_object(self.module, "dynamic", handle), handle)
        self.assertNotIn("dynamic", vars(self.module))
        self.assertEqual(self.module.dynamic(), "original")

    def test_fallback_without_record(self):
        # A wrapper installed manually with apply_patch() carries no
        # installation record, so removal falls back to the MRO check,
        # which still removes a class level shadow of an inherited
        # definition.

        class Base:
            def method(self):
                return "original"

        class Derived(Base):
            pass

        original = wrapt.resolve_path(Derived, "method")[2]
        handle = wrapt.FunctionWrapper(original, wrapper_a)
        wrapt.apply_patch(Derived, "method", handle)

        self.assertIs(wrapt.unwrap_object(Derived, "method", handle), handle)
        self.assertNotIn("method", vars(Derived))
        self.assertEqual(Derived().method(), "original")

    def test_record_not_read_through_delegation(self):
        # The installation record must be read from the wrapper's own
        # local state only. A handle installed manually over a wrapper
        # which does carry a record must not have the inner wrapper's
        # record answered through attribute delegation, which here
        # would wrongly delete the module attribute.

        self.module.function = lambda: "original"

        inner = wrapt.wrap_function_wrapper(self.module, "function", wrapper_a)

        outer = wrapt.FunctionWrapper(inner, wrapper_b)
        wrapt.apply_patch(self.module, "function", outer)

        self.assertIs(wrapt.unwrap_object(self.module, "function", outer), outer)

        # The attribute must have been restored by assignment to the
        # inner wrapper, not deleted.

        self.assertIn("function", vars(self.module))
        self.assertIs(self.module.function, inner)
