"""Test that __module__ and __doc__ on proxy types are strings, not descriptors.

Regression test for an issue where accessing __module__ on the proxy type
itself (e.g. BaseObjectProxy.__module__) returns a getset_descriptor or property
object instead of a string. This breaks tools like pylint/astroid that expect
type.__module__ to be a string they can call .split() on.

Also tests that instance-level __module__ and __doc__ correctly proxy to the
wrapped object across the full class hierarchy, including subclasses where
type.__new__ would normally set __module__/__doc__ as strings that could
shadow the proxying descriptors.
"""

import types
import unittest

import wrapt

from wrapt.__wrapt__ import BaseObjectProxy

OBJECTS_CODE = """
class Target:
    "target documentation"

def target():
    "target documentation"
    pass
"""

objects = types.ModuleType("objects")
exec(OBJECTS_CODE, objects.__dict__, objects.__dict__)


# -- Type-level __module__ tests --


class TestBaseTypeModuleAttribute(unittest.TestCase):
    """Test that __module__ is a string when accessed on the base C/Python
    proxy types (from __wrapt__), not the Python subclasses in proxies.py."""

    def test_base_object_proxy_type_module_is_string(self):
        module = BaseObjectProxy.__module__
        self.assertIsInstance(module, str,
            f"BaseObjectProxy.__module__ should be a string, got {type(module)}")
        module.split(".")

    def test_callable_object_proxy_type_module_is_string(self):
        module = wrapt.CallableObjectProxy.__module__
        self.assertIsInstance(module, str,
            f"CallableObjectProxy.__module__ should be a string, got {type(module)}")
        module.split(".")

    def test_function_wrapper_type_module_is_string(self):
        module = wrapt.FunctionWrapper.__module__
        self.assertIsInstance(module, str,
            f"FunctionWrapper.__module__ should be a string, got {type(module)}")
        module.split(".")

    def test_bound_function_wrapper_type_module_is_string(self):
        module = wrapt.BoundFunctionWrapper.__module__
        self.assertIsInstance(module, str,
            f"BoundFunctionWrapper.__module__ should be a string, got {type(module)}")
        module.split(".")

    def test_partial_callable_object_proxy_type_module_is_string(self):
        module = wrapt.PartialCallableObjectProxy.__module__
        self.assertIsInstance(module, str,
            f"PartialCallableObjectProxy.__module__ should be a string, got {type(module)}")
        module.split(".")


class TestBaseTypeDocAttribute(unittest.TestCase):
    """Test that __doc__ is a string or None when accessed on base proxy types."""

    def test_base_object_proxy_type_doc_is_string_or_none(self):
        doc = BaseObjectProxy.__doc__
        self.assertTrue(doc is None or isinstance(doc, str),
            f"BaseObjectProxy.__doc__ should be a string or None, got {type(doc)}")

    def test_callable_object_proxy_type_doc_is_string_or_none(self):
        doc = wrapt.CallableObjectProxy.__doc__
        self.assertTrue(doc is None or isinstance(doc, str),
            f"CallableObjectProxy.__doc__ should be a string or None, got {type(doc)}")

    def test_function_wrapper_type_doc_is_string_or_none(self):
        doc = wrapt.FunctionWrapper.__doc__
        self.assertTrue(doc is None or isinstance(doc, str),
            f"FunctionWrapper.__doc__ should be a string or None, got {type(doc)}")


class TestPythonSubclassTypeModuleAttribute(unittest.TestCase):
    """Test that Python subclasses also have correct type-level __module__.
    This verifies that the string type.__new__ sets in the subclass dict
    is not shadowed by the proxying descriptors."""

    def test_object_proxy_type_module_is_string(self):
        module = wrapt.ObjectProxy.__module__
        self.assertIsInstance(module, str)
        self.assertEqual(module, "wrapt.proxies")

    def test_user_subclass_type_module_is_string(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        module = MyProxy.__module__
        self.assertIsInstance(module, str)

    def test_user_subclass_of_callable_proxy_type_module_is_string(self):
        class MyCallable(wrapt.CallableObjectProxy):
            pass
        module = MyCallable.__module__
        self.assertIsInstance(module, str)

    def test_user_subclass_of_function_wrapper_type_module_is_string(self):
        class MyWrapper(wrapt.FunctionWrapper):
            pass
        module = MyWrapper.__module__
        self.assertIsInstance(module, str)

    def test_user_subclass_type_doc_is_string_or_none(self):
        class MyProxy(wrapt.BaseObjectProxy):
            """My custom proxy."""
            pass
        doc = MyProxy.__doc__
        self.assertEqual(doc, "My custom proxy.")

    def test_user_subclass_no_doc_is_none(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        doc = MyProxy.__doc__
        self.assertTrue(doc is None or isinstance(doc, str))


# -- Instance-level __module__ proxying tests --


class TestInstanceModuleProxying(unittest.TestCase):
    """Verify instance-level __module__ proxies to wrapped across all types."""

    def test_object_proxy_class_target(self):
        target = objects.Target
        wrapper = wrapt.BaseObjectProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_object_proxy_instance_target(self):
        target = objects.Target()
        wrapper = wrapt.BaseObjectProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_object_proxy_function_target(self):
        target = objects.target
        wrapper = wrapt.BaseObjectProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_callable_object_proxy(self):
        target = objects.target
        wrapper = wrapt.CallableObjectProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_function_wrapper(self):
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = objects.target
        wrapper = wrapt.FunctionWrapper(target, my_wrapper)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_user_subclass_of_object_proxy(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        target = objects.target
        wrapper = MyProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_user_subclass_of_callable_proxy(self):
        class MyCallable(wrapt.CallableObjectProxy):
            pass
        target = objects.target
        wrapper = MyCallable(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_user_subclass_of_function_wrapper(self):
        class MyWrapper(wrapt.FunctionWrapper):
            pass
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = objects.target
        wrapper = MyWrapper(target, my_wrapper)
        self.assertEqual(wrapper.__module__, target.__module__)


# -- Instance-level __doc__ proxying tests --


class TestInstanceDocProxying(unittest.TestCase):
    """Verify instance-level __doc__ proxies to wrapped across all types."""

    def test_object_proxy_class_target(self):
        target = objects.Target
        wrapper = wrapt.BaseObjectProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_object_proxy_instance_target(self):
        target = objects.Target()
        wrapper = wrapt.BaseObjectProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_object_proxy_function_target(self):
        target = objects.target
        wrapper = wrapt.BaseObjectProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_callable_object_proxy(self):
        target = objects.target
        wrapper = wrapt.CallableObjectProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_function_wrapper(self):
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = objects.target
        wrapper = wrapt.FunctionWrapper(target, my_wrapper)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_user_subclass_of_object_proxy(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        target = objects.target
        wrapper = MyProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_user_subclass_of_function_wrapper(self):
        class MyWrapper(wrapt.FunctionWrapper):
            pass
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = objects.target
        wrapper = MyWrapper(target, my_wrapper)
        self.assertEqual(wrapper.__doc__, target.__doc__)


# -- Setting __module__ and __doc__ tests --


class TestSetModuleAndDoc(unittest.TestCase):
    """Verify setting __module__ and __doc__ on instances."""

    def test_set_module_on_object_proxy(self):
        target = objects.target
        wrapper = wrapt.BaseObjectProxy(target)
        wrapper.__module__ = "override_module"
        self.assertEqual(target.__module__, "override_module")

    def test_set_doc_on_object_proxy(self):
        target = objects.target
        wrapper = wrapt.BaseObjectProxy(target)
        wrapper.__doc__ = "override doc"
        self.assertEqual(target.__doc__, "override doc")

    def test_set_module_on_function_wrapper(self):
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = objects.target
        wrapper = wrapt.FunctionWrapper(target, my_wrapper)
        wrapper.__module__ = "override_module"
        self.assertEqual(target.__module__, "override_module")

    def test_set_module_on_user_subclass(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        target = objects.target
        wrapper = MyProxy(target)
        wrapper.__module__ = "override_module"
        self.assertEqual(target.__module__, "override_module")


# -- Deleting __module__ and __doc__ tests --


class TestDeleteModuleAndDoc(unittest.TestCase):
    """Verify deleting __module__ and __doc__ on instances is forwarded to
    the wrapped object, in the same way as setting them. Targets are
    created per test rather than shared, as deletion changes them."""

    @staticmethod
    def make_function():
        def target():
            "target documentation"
            pass
        return target

    @staticmethod
    def make_class():
        class Target:
            "target documentation"
        return Target

    @staticmethod
    def delete_outcome(obj, name):
        # Return None if deletion succeeds, else the exception type and
        # message, so the outcome via a proxy can be compared with the
        # outcome of the same deletion made directly on the target.
        try:
            delattr(obj, name)
        except Exception as e:
            return (type(e), str(e))
        return None

    def test_delete_module_on_object_proxy(self):
        target = self.make_function()
        wrapper = wrapt.BaseObjectProxy(target)
        del wrapper.__module__
        self.assertIsNone(target.__module__)
        self.assertIsNone(wrapper.__module__)

    def test_delete_doc_on_object_proxy(self):
        target = self.make_function()
        wrapper = wrapt.BaseObjectProxy(target)
        del wrapper.__doc__
        self.assertIsNone(target.__doc__)
        self.assertIsNone(wrapper.__doc__)

    def test_delete_module_after_set(self):
        target = self.make_function()
        wrapper = wrapt.BaseObjectProxy(target)
        wrapper.__module__ = "override_module"
        del wrapper.__module__
        self.assertIsNone(target.__module__)
        self.assertIsNone(wrapper.__module__)

    def test_delete_doc_after_set(self):
        target = self.make_function()
        wrapper = wrapt.BaseObjectProxy(target)
        wrapper.__doc__ = "override doc"
        del wrapper.__doc__
        self.assertIsNone(target.__doc__)
        self.assertIsNone(wrapper.__doc__)

    def test_delete_module_on_function_wrapper(self):
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = self.make_function()
        wrapper = wrapt.FunctionWrapper(target, my_wrapper)
        del wrapper.__module__
        self.assertIsNone(target.__module__)
        self.assertIsNone(wrapper.__module__)

    def test_delete_doc_on_function_wrapper(self):
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        target = self.make_function()
        wrapper = wrapt.FunctionWrapper(target, my_wrapper)
        del wrapper.__doc__
        self.assertIsNone(target.__doc__)
        self.assertIsNone(wrapper.__doc__)

    def test_delete_module_on_user_subclass(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        target = self.make_function()
        wrapper = MyProxy(target)
        del wrapper.__module__
        self.assertIsNone(target.__module__)
        self.assertIsNone(wrapper.__module__)

    def test_delete_doc_on_user_subclass(self):
        class MyProxy(wrapt.BaseObjectProxy):
            pass
        target = self.make_function()
        wrapper = MyProxy(target)
        del wrapper.__doc__
        self.assertIsNone(target.__doc__)
        self.assertIsNone(wrapper.__doc__)

    def test_delete_module_on_class_target(self):
        # A class does not permit deletion of __module__. The outcome via
        # the proxy must match a direct deletion on an equivalent class.
        expected = self.delete_outcome(self.make_class(), "__module__")
        wrapper = wrapt.BaseObjectProxy(self.make_class())
        self.assertEqual(self.delete_outcome(wrapper, "__module__"), expected)

    def test_delete_doc_on_class_target(self):
        expected = self.delete_outcome(self.make_class(), "__doc__")
        wrapper = wrapt.BaseObjectProxy(self.make_class())
        self.assertEqual(self.delete_outcome(wrapper, "__doc__"), expected)

    def test_proxy_state_matches_fresh_proxy_after_delete(self):
        # After deletion the proxy's own instance dictionary must be the
        # same as for a proxy newly created over the wrapped object in
        # its current state, so the C extension's cached copies of the
        # attributes do not go stale or linger.
        target = self.make_function()
        wrapper = wrapt.BaseObjectProxy(target)
        del wrapper.__module__
        del wrapper.__doc__
        fresh = wrapt.BaseObjectProxy(target)
        self.assertEqual(dict(wrapper.__self_dict__), dict(fresh.__self_dict__))


# -- Wrapped replacement tests --


class TestWrappedReplacement(unittest.TestCase):
    """Verify __module__ and __doc__ reflect the new wrapped object after
    __wrapped__ is replaced."""

    def test_module_after_wrapped_replacement(self):
        def func1():
            pass
        func1.__module__ = "module1"

        def func2():
            pass
        func2.__module__ = "module2"

        wrapper = wrapt.BaseObjectProxy(func1)
        self.assertEqual(wrapper.__module__, "module1")
        wrapper.__wrapped__ = func2
        self.assertEqual(wrapper.__module__, "module2")

    def test_doc_after_wrapped_replacement(self):
        def func1():
            "doc1"
            pass

        def func2():
            "doc2"
            pass

        wrapper = wrapt.BaseObjectProxy(func1)
        self.assertEqual(wrapper.__doc__, "doc1")
        wrapper.__wrapped__ = func2
        self.assertEqual(wrapper.__doc__, "doc2")

    def test_module_after_wrapped_replacement_on_function_wrapper(self):
        def my_wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        def func1():
            pass
        func1.__module__ = "module1"

        def func2():
            pass
        func2.__module__ = "module2"

        wrapper = wrapt.FunctionWrapper(func1, my_wrapper)
        self.assertEqual(wrapper.__module__, "module1")
        wrapper.__wrapped__ = func2
        self.assertEqual(wrapper.__module__, "module2")


class TestNonInternedAttributeNames(unittest.TestCase):
    """The C extension intercepts __module__ and __doc__ by name in the
    attribute get and set slots. Names arriving from Python code are
    interned, but names constructed at runtime are not, and the interception
    must work for those too rather than falling through to a stale copy.
    """

    @staticmethod
    def dynamic(name):
        # Build an equal but distinct, non interned string object.
        result = "".join(list(name))
        assert result == name and result is not name
        return result

    def test_get_module_and_doc_via_non_interned_name(self):
        def function():
            """original doc"""

        proxy = BaseObjectProxy(function)

        function.__module__ = "changed.module"
        function.__doc__ = "changed doc"

        self.assertEqual(getattr(proxy, self.dynamic("__module__")), "changed.module")
        self.assertEqual(getattr(proxy, self.dynamic("__doc__")), "changed doc")

    def test_set_module_and_doc_via_non_interned_name(self):
        def function():
            """original doc"""

        proxy = BaseObjectProxy(function)

        setattr(proxy, self.dynamic("__module__"), "set.module")
        setattr(proxy, self.dynamic("__doc__"), "set doc")

        self.assertEqual(function.__module__, "set.module")
        self.assertEqual(function.__doc__, "set doc")
        self.assertEqual(proxy.__module__, "set.module")
        self.assertEqual(proxy.__doc__, "set doc")

    def test_delete_module_and_doc_via_non_interned_name(self):
        def function():
            """original doc"""

        proxy = BaseObjectProxy(function)

        delattr(proxy, self.dynamic("__module__"))
        delattr(proxy, self.dynamic("__doc__"))

        self.assertIsNone(function.__module__)
        self.assertIsNone(function.__doc__)
        self.assertIsNone(proxy.__module__)
        self.assertIsNone(proxy.__doc__)


if __name__ == "__main__":
    unittest.main()
