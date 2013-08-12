from __future__ import print_function

import unittest
import imp

import wrapt

from wrapt import six

OBJECTS_CODE = """
class Target(object):
    "documentation"

def target():
    "documentation"
    pass
"""

objects = imp.new_module('objects')
six.exec_(OBJECTS_CODE, objects.__dict__, objects.__dict__)

class TestNamingObjectProxy(unittest.TestCase):

    def test_class_object_name(self):
        # Test preservation of class __name__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__name__, target.__name__)

    def test_class_object_qualname(self):
        # Test preservation of class __qualname__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        try:
            __qualname__ = target.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(wrapper.__qualname__, __qualname__)

    def test_class_module_name(self):
       # Test preservation of class __module__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__module__, target.__module__)

    def test_class_doc_string(self):
        # Test preservation of class __doc__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_instance_module_name(self):
       # Test preservation of instance __module__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__module__, target.__module__)

    def test_instance_doc_string(self):
        # Test preservation of instance __doc__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_function_object_name(self):
        # Test preservation of function __name__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__name__, target.__name__)

    def test_function_object_qualname(self):
        # Test preservation of function __qualname__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        try:
            __qualname__ = target.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(wrapper.__qualname__, __qualname__)

    def test_function_module_name(self):
       # Test preservation of function __module__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__module__, target.__module__)

    def test_function_doc_string(self):
        # Test preservation of function __doc__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__doc__, target.__doc__)

class TestTypeObjectProxy(unittest.TestCase):

    def test_class_of_class(self):
        # Test preservation of class __class__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__class__, target.__class__)
        self.assertTrue(isinstance(wrapper, type(target)))

    def test_class_of_instance(self):
        # Test preservation of instance __class__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__class__, target.__class__)
        self.assertTrue(isinstance(wrapper, type(target)))

    def test_class_of_function(self):
        # Test preservation of function __class__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__class__, target.__class__)
        self.assertTrue(isinstance(wrapper, type(target)))

if __name__ == '__main__':
    unittest.main()
