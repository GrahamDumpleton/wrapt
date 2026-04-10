"""Test that __module__ and __doc__ on proxy types are strings, not descriptors.

Regression test for an issue where accessing __module__ on the proxy type
itself (e.g. ObjectProxy.__module__) returns a getset_descriptor or property
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
        class MyProxy(wrapt.ObjectProxy):
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
        class MyProxy(wrapt.ObjectProxy):
            """My custom proxy."""
            pass
        doc = MyProxy.__doc__
        self.assertEqual(doc, "My custom proxy.")

    def test_user_subclass_no_doc_is_none(self):
        class MyProxy(wrapt.ObjectProxy):
            pass
        doc = MyProxy.__doc__
        self.assertTrue(doc is None or isinstance(doc, str))


# -- Instance-level __module__ proxying tests --


class TestInstanceModuleProxying(unittest.TestCase):
    """Verify instance-level __module__ proxies to wrapped across all types."""

    def test_object_proxy_class_target(self):
        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_object_proxy_instance_target(self):
        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)
        self.assertEqual(wrapper.__module__, target.__module__)

    def test_object_proxy_function_target(self):
        target = objects.target
        wrapper = wrapt.ObjectProxy(target)
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
        class MyProxy(wrapt.ObjectProxy):
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
        wrapper = wrapt.ObjectProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_object_proxy_instance_target(self):
        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)
        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_object_proxy_function_target(self):
        target = objects.target
        wrapper = wrapt.ObjectProxy(target)
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
        class MyProxy(wrapt.ObjectProxy):
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
        wrapper = wrapt.ObjectProxy(target)
        wrapper.__module__ = "override_module"
        self.assertEqual(target.__module__, "override_module")

    def test_set_doc_on_object_proxy(self):
        target = objects.target
        wrapper = wrapt.ObjectProxy(target)
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
        class MyProxy(wrapt.ObjectProxy):
            pass
        target = objects.target
        wrapper = MyProxy(target)
        wrapper.__module__ = "override_module"
        self.assertEqual(target.__module__, "override_module")


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

        wrapper = wrapt.ObjectProxy(func1)
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

        wrapper = wrapt.ObjectProxy(func1)
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


if __name__ == "__main__":
    unittest.main()
