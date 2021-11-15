from __future__ import print_function

import unittest

import wrapt

class TestObjectDescriptors(unittest.TestCase):

    def test_set_name(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        attribute_name = []

        class _descriptor_wrapper:
            def __init__(self, descriptor):
                self.__wrapped__ = descriptor

            def __set_name__(self, owner, name):
                attribute_name.append(name)

            def __get__(self, instance, owner=None):
                return self.__wrapped__.__get__(instance, owner)

        class Instance(object):
            @_decorator
            @_descriptor_wrapper
            def method(self):
                return True

        instance = Instance()

        self.assertEqual(attribute_name, ["method"])
        self.assertEqual(instance.method(), True)

if __name__ == '__main__':
    unittest.main()
