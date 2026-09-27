"""A derived class of BaseObjectProxy may define __doc__ as a descriptor in
its class body, and that is then used for instances of the class in place of
the default delegation of __doc__ to the wrapped object. This is what the
with_doc decorator relies on. Both the pure Python metaclass and the C
extension attribute hooks have to honour it, and both have to inherit it
into further derived classes."""

import unittest

import wrapt


def _function():
    """Wrapped docstring."""


class ReadOnlyDocProxy(wrapt.BaseObjectProxy):
    @property
    def __doc__(self):
        return "Proxy docstring."


class StoredDocProxy(wrapt.BaseObjectProxy):
    def __init__(self, wrapped, doc):
        super().__init__(wrapped)
        self._self_doc = doc

    @property
    def __doc__(self):
        return self._self_doc

    @__doc__.setter
    def __doc__(self, value):
        self._self_doc = value

    @__doc__.deleter
    def __doc__(self):
        self._self_doc = None


class DerivedWithoutDocstring(ReadOnlyDocProxy):
    pass


class DerivedWithDocstring(ReadOnlyDocProxy):
    """Class docstring."""


class TestDocDescriptor(unittest.TestCase):
    def test_descriptor_used_for_instances(self):
        proxy = ReadOnlyDocProxy(_function)

        self.assertEqual(proxy.__doc__, "Proxy docstring.")
        self.assertEqual(_function.__doc__, "Wrapped docstring.")

    def test_descriptor_found_by_generic_attribute_lookup(self):
        # pydoc reads __doc__ using object.__getattribute__() to avoid
        # inherited docstrings, which bypasses the attribute hooks of the
        # proxy, so the descriptor must be found by generic lookup too.

        proxy = ReadOnlyDocProxy(_function)

        self.assertEqual(object.__getattribute__(proxy, "__doc__"), "Proxy docstring.")

    def test_read_only_descriptor_rejects_assignment(self):
        proxy = ReadOnlyDocProxy(_function)

        with self.assertRaises(AttributeError):
            proxy.__doc__ = "Replaced."

        with self.assertRaises(AttributeError):
            del proxy.__doc__

        self.assertEqual(proxy.__doc__, "Proxy docstring.")
        self.assertEqual(_function.__doc__, "Wrapped docstring.")

    def test_descriptor_setter_and_deleter_used(self):
        def function():
            """Wrapped docstring."""

        proxy = StoredDocProxy(function, "Proxy docstring.")

        self.assertEqual(proxy.__doc__, "Proxy docstring.")

        proxy.__doc__ = "Replaced."

        self.assertEqual(proxy.__doc__, "Replaced.")
        self.assertEqual(function.__doc__, "Wrapped docstring.")

        del proxy.__doc__

        self.assertIsNone(proxy.__doc__)
        self.assertEqual(function.__doc__, "Wrapped docstring.")

    def test_module_still_delegates(self):
        proxy = ReadOnlyDocProxy(_function)

        self.assertEqual(proxy.__module__, _function.__module__)

    def test_class_docstring_not_replaced_by_descriptor(self):
        # A descriptor defined as __doc__ in the class body is not the
        # class docstring, so type level access does not report it as a
        # string, whereas a class which does have a docstring still
        # reports that at type level.

        self.assertNotIsInstance(ReadOnlyDocProxy.__doc__, str)
        self.assertEqual(DerivedWithDocstring.__doc__, "Class docstring.")
        self.assertIsNone(DerivedWithoutDocstring.__doc__)


class TestInheritedDocDescriptor(unittest.TestCase):
    def test_inherited_by_class_without_docstring(self):
        proxy = DerivedWithoutDocstring(_function)

        self.assertEqual(proxy.__doc__, "Proxy docstring.")

    def test_inherited_by_class_with_docstring(self):
        proxy = DerivedWithDocstring(_function)

        self.assertEqual(proxy.__doc__, "Proxy docstring.")

    def test_inherited_descriptor_rejects_assignment(self):
        proxy = DerivedWithoutDocstring(_function)

        with self.assertRaises(AttributeError):
            proxy.__doc__ = "Replaced."

        self.assertEqual(_function.__doc__, "Wrapped docstring.")

    def test_inherited_setter_used(self):
        class Derived(StoredDocProxy):
            """Class docstring."""

        def function():
            """Wrapped docstring."""

        proxy = Derived(function, "Proxy docstring.")

        proxy.__doc__ = "Replaced."

        self.assertEqual(proxy.__doc__, "Replaced.")
        self.assertEqual(function.__doc__, "Wrapped docstring.")
        self.assertEqual(Derived.__doc__, "Class docstring.")


class TestDefaultDelegation(unittest.TestCase):
    def test_plain_proxy_delegates(self):
        def function():
            """Wrapped docstring."""

        proxy = wrapt.BaseObjectProxy(function)

        self.assertEqual(proxy.__doc__, "Wrapped docstring.")

        proxy.__doc__ = "Replaced."

        self.assertEqual(proxy.__doc__, "Replaced.")
        self.assertEqual(function.__doc__, "Replaced.")

        del proxy.__doc__

        self.assertIsNone(proxy.__doc__)
        self.assertIsNone(function.__doc__)

    def test_derived_class_with_docstring_delegates(self):
        class Derived(wrapt.BaseObjectProxy):
            """Class docstring."""

        proxy = Derived(_function)

        self.assertEqual(proxy.__doc__, "Wrapped docstring.")
        self.assertEqual(Derived.__doc__, "Class docstring.")

    def test_derived_class_of_delegating_class_delegates(self):
        # The search for an inherited descriptor stops at the first class
        # which delegates, so a descriptor further up is not picked up
        # through a class which does not use it.

        class Delegating(wrapt.BaseObjectProxy):
            pass

        class Derived(Delegating):
            pass

        self.assertEqual(Derived(_function).__doc__, "Wrapped docstring.")

    def test_function_wrapper_subclass(self):
        class DocFunctionWrapper(wrapt.FunctionWrapper):
            @property
            def __doc__(self):
                return "Wrapper docstring."

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        def function():
            """Wrapped docstring."""
            return 1

        proxy = DocFunctionWrapper(function, wrapper)

        self.assertEqual(proxy.__doc__, "Wrapper docstring.")
        self.assertEqual(function.__doc__, "Wrapped docstring.")
        self.assertEqual(proxy(), 1)


if __name__ == "__main__":
    unittest.main()
