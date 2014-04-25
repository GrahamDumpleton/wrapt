from __future__ import print_function

import unittest

import wrapt

class Class(object):
    def __init__(self, value):
        self.value = value

class TestAttributeProxy(unittest.TestCase):

    def test_wrap_attribute(self):
        wrapt.wrap_object_attribute(__name__, 'Class.value', wrapt.ObjectProxy)

        instance = Class(1)

        self.assertEqual(instance.value, 1)
        self.assertTrue(isinstance(instance.value, wrapt.ObjectProxy))

        instance.value = 2

        self.assertEqual(instance.value, 2)
        self.assertTrue(isinstance(instance.value, wrapt.ObjectProxy))
