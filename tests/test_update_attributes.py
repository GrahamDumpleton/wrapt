from __future__ import print_function

import unittest

import wrapt

from compat import PY2, PY3, exec_

@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

class TestUpdateAttributes(unittest.TestCase):

    def test_update_name(self):
        @passthru_decorator
        def function():
            pass

        self.assertEqual(function.__name__, 'function')

        function.__name__ = 'override_name'

        self.assertEqual(function.__name__, 'override_name')

    def test_update_name_modified_on_original(self):
        def function():
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        instance = wrapt.FunctionWrapper(function, wrapper)

        self.assertEqual(instance.__name__, 'function')

        instance.__name__ = 'override_name'

        self.assertEqual(function.__name__, 'override_name')
        self.assertEqual(instance.__name__, 'override_name')

    def test_update_qualname(self):

        @passthru_decorator
        def function():
            pass

        if PY3:
            method = self.test_update_qualname
            self.assertEqual(function.__qualname__,
                    (method.__qualname__ + '.<locals>.function'))

        function.__qualname__ = 'override_qualname'

        self.assertEqual(function.__qualname__, 'override_qualname')

    def test_update_qualname_modified_on_original(self):
        def function():
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        instance = wrapt.FunctionWrapper(function, wrapper)

        if PY3:
            method = self.test_update_qualname_modified_on_original
            self.assertEqual(instance.__qualname__,
                    (method.__qualname__ + '.<locals>.function'))

        instance.__qualname__ = 'override_qualname'

        self.assertEqual(function.__qualname__, 'override_qualname')
        self.assertEqual(instance.__qualname__, 'override_qualname')

    def test_update_module(self):
        @passthru_decorator
        def function():
            pass

        self.assertEqual(function.__module__, __name__)

        function.__module__ = 'override_module'

        self.assertEqual(function.__module__, 'override_module')

    def test_update_module_modified_on_original(self):
        def function():
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        instance = wrapt.FunctionWrapper(function, wrapper)

        self.assertEqual(instance.__module__, __name__)

        instance.__module__ = 'override_module'

        self.assertEqual(function.__module__, 'override_module')
        self.assertEqual(instance.__module__, 'override_module')

    def test_update_doc(self):
        @passthru_decorator
        def function():
            """documentation"""
            pass

        self.assertEqual(function.__doc__, "documentation")

        function.__doc__ = 'override_doc'

        self.assertEqual(function.__doc__, 'override_doc')

    def test_update_doc_modified_on_original(self):
        def function():
            """documentation"""
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        instance = wrapt.FunctionWrapper(function, wrapper)

        self.assertEqual(instance.__doc__, "documentation")

        instance.__doc__ = 'override_doc'

        self.assertEqual(function.__doc__, 'override_doc')
        self.assertEqual(instance.__doc__, 'override_doc')

    def test_update_annotations(self):
        @passthru_decorator
        def function():
            pass

        if PY3:
            self.assertEqual(function.__annotations__, {})

        else:
            def run(*args):
                function.__annotations__

            self.assertRaises(AttributeError, run, ())

        override_annotations = {'override_annotations': ''}
        function.__annotations__ = override_annotations

        self.assertEqual(function.__wrapped__.__annotations__, override_annotations)
        self.assertEqual(function.__annotations__, override_annotations)

    def test_update_annotations_modified_on_original(self):
        def function():
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        instance = wrapt.FunctionWrapper(function, wrapper)

        if PY3:
            self.assertEqual(instance.__annotations__, {})

        else:
            def run(*args):
                instance.__annotations__

            self.assertRaises(AttributeError, run, ())

        override_annotations = {'override_annotations': ''}
        instance.__annotations__ = override_annotations

        self.assertEqual(function.__annotations__, override_annotations)
        self.assertEqual(instance.__annotations__, override_annotations)

if __name__ == '__main__':
    unittest.main()
