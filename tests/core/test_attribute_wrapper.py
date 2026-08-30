import unittest

import wrapt


class Class:
    def __init__(self, value):
        self.value = value


class ClassWithHandle:
    def __init__(self, value):
        self.value = value


class SpecialDescriptor:
    """Their docstring."""

    marker = "their-marker"

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__.get("_special", "their-default")

    def __set__(self, instance, value):
        instance.__dict__["_special"] = value


class ClassWithDescriptor:
    value = SpecialDescriptor()


class ClassWithStacked:
    def __init__(self, value):
        self.value = value


class ClassWithDefault:
    value = "default"


class ClassWithNothing:
    pass


class ValidatingDescriptor:
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__["_validated"]

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise ValueError("value must be an integer")
        instance.__dict__["_validated"] = value


class ClassWithValidation:
    value = ValidatingDescriptor()


class ClassWithProperty:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @value.deleter
    def value(self):
        del self._value


class ClassWithDelete:
    def __init__(self, value):
        self.value = value


class ClassWithReadOnlyProperty:
    @property
    def value(self):
        return 1


class ClassWithPropertyIntrospection:
    @property
    def value(self):
        """Property docstring."""
        return 1


class TestAttributeProxy(unittest.TestCase):

    def test_wrap_attribute(self):
        wrapt.wrap_object_attribute(__name__, "Class.value", wrapt.ObjectProxy)

        instance = Class(1)

        self.assertEqual(instance.value, 1)
        self.assertTrue(isinstance(instance.value, wrapt.ObjectProxy))

        instance.value = 2

        self.assertEqual(instance.value, 2)
        self.assertTrue(isinstance(instance.value, wrapt.ObjectProxy))

    def test_returns_handle(self):
        handle = wrapt.wrap_object_attribute(
            __name__, "ClassWithHandle.value", wrapt.ObjectProxy
        )

        # The returned handle is the AttributeWrapper descriptor which
        # was installed on the class, with the prior definition, here
        # the MISSING sentinel, held as the wrapped object.

        self.assertTrue(type(handle) is wrapt.AttributeWrapper)
        self.assertIs(vars(ClassWithHandle)["value"], handle)
        self.assertIs(
            object.__getattribute__(handle, "__wrapped__"), wrapt.MISSING
        )

        self.assertEqual(handle._self_attribute, "value")
        self.assertIs(handle._self_factory, wrapt.ObjectProxy)
        self.assertEqual(handle._self_args, ())
        self.assertEqual(handle._self_kwargs, {})

    def test_composes_over_descriptor(self):
        # Interception composes over a prior custom descriptor, whose
        # own logic keeps running beneath it.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithDescriptor.value", lambda value: ("wrapped", value)
        )

        instance = ClassWithDescriptor()

        self.assertEqual(instance.value, ("wrapped", "their-default"))

        # Writes delegate to the descriptor's __set__, so its own
        # storage location is used.

        instance.value = 1

        self.assertEqual(instance.__dict__["_special"], 1)
        self.assertEqual(instance.value, ("wrapped", 1))

    def test_class_access_transparent(self):
        # Class level access returns the descriptor itself, which being
        # a transparent proxy exposes the prior definition for
        # introspection.

        self.assertEqual(ClassWithDescriptor.value.__doc__, "Their docstring.")
        self.assertEqual(ClassWithDescriptor.value.marker, "their-marker")
        self.assertTrue(
            isinstance(vars(ClassWithDescriptor)["value"], SpecialDescriptor)
        )

    def test_stacked_application_composes(self):
        # A second application on the same attribute composes with the
        # first rather than silently replacing it.

        inner = wrapt.wrap_object_attribute(
            __name__, "ClassWithStacked.value", lambda value: ("inner", value)
        )
        outer = wrapt.wrap_object_attribute(
            __name__, "ClassWithStacked.value", lambda value: ("outer", value)
        )

        self.assertIs(vars(ClassWithStacked)["value"], outer)
        self.assertIs(object.__getattribute__(outer, "__wrapped__"), inner)

        instance = ClassWithStacked(1)

        self.assertEqual(instance.value, ("outer", ("inner", 1)))

    def test_class_default_fallback(self):
        # With no instance value, reads fall back to a plain class
        # default rather than raising KeyError.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithDefault.value", lambda value: ("wrapped", value)
        )

        instance = ClassWithDefault()

        self.assertEqual(instance.value, ("wrapped", "default"))

        # An instance value takes precedence over the class default.

        instance.value = 1

        self.assertEqual(instance.value, ("wrapped", 1))

    def test_missing_terminal_raises_attribute_error(self):
        # With no instance value and no prior definition of any sort,
        # reads raise AttributeError, not KeyError.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithNothing.value", lambda value: ("wrapped", value)
        )

        instance = ClassWithNothing()

        with self.assertRaises(AttributeError) as cm:
            instance.value

        self.assertIn("'value'", str(cm.exception))

        # An instance value is served once assigned.

        instance.value = 1

        self.assertEqual(instance.value, ("wrapped", 1))

    def test_prior_descriptor_validation(self):
        # Writes delegate to a prior descriptor's __set__, so its
        # validation is enforced and its storage used, and reads serve
        # the written values back through the interception.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithValidation.value", lambda value: ("wrapped", value)
        )

        instance = ClassWithValidation()

        with self.assertRaises(ValueError):
            instance.value = "not an integer"

        instance.value = 1

        self.assertEqual(instance.__dict__["_validated"], 1)
        self.assertEqual(instance.value, ("wrapped", 1))

    def test_prior_property(self):
        # A property as the prior definition works through the
        # interception, getter, setter and deleter included.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithProperty.value", lambda value: ("wrapped", value)
        )

        instance = ClassWithProperty(1)

        self.assertEqual(instance.value, ("wrapped", 1))

        instance.value = 2

        self.assertEqual(instance._value, 2)
        self.assertEqual(instance.value, ("wrapped", 2))

        del instance.value

        self.assertFalse(hasattr(instance, "_value"))

    def test_delete_instance_value(self):
        wrapt.wrap_object_attribute(
            __name__, "ClassWithDelete.value", lambda value: ("wrapped", value)
        )

        instance = ClassWithDelete(1)

        self.assertEqual(instance.value, ("wrapped", 1))

        del instance.value

        self.assertNotIn("value", instance.__dict__)

        # Deleting again, when no instance value exists, raises the
        # same AttributeError which deleting the attribute would raise
        # if the wrapper had not been applied, not KeyError.

        with self.assertRaises(AttributeError) as cm:
            del instance.value

        self.assertIn("'value'", str(cm.exception))

    def test_prior_read_only_property(self):
        # A read-only property as the prior definition rejects writes
        # and deletes through the interception with the same
        # AttributeError it raises without the wrapper applied.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithReadOnlyProperty.value",
            lambda value: ("wrapped", value)
        )

        instance = ClassWithReadOnlyProperty()

        self.assertEqual(instance.value, ("wrapped", 1))

        with self.assertRaises(AttributeError):
            instance.value = 2

        with self.assertRaises(AttributeError):
            del instance.value

    def test_class_access_through_property(self):
        # Class level access returns the descriptor, which being a
        # transparent proxy exposes the prior property for
        # introspection.

        wrapt.wrap_object_attribute(
            __name__, "ClassWithPropertyIntrospection.value",
            lambda value: ("wrapped", value)
        )

        self.assertEqual(
            ClassWithPropertyIntrospection.value.__doc__, "Property docstring."
        )
        self.assertTrue(
            callable(ClassWithPropertyIntrospection.value.fget)
        )
        self.assertTrue(
            isinstance(vars(ClassWithPropertyIntrospection)["value"], property)
        )
