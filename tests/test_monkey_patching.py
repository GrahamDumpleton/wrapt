from __future__ import print_function

import unittest
import sys

import wrapt

def global_function_1(*args, **kwargs):
    return args, kwargs

def global_function_2(*args, **kwargs):
    return args, kwargs

def global_function_3(*args, **kwargs):
    return args, kwargs

def global_function_4(*args, **kwargs):
    return args, kwargs

class Class_1(object):
    def method(self, *args, **kwargs):
        return args, kwargs

class TestMonkeyPatching(unittest.TestCase):

    def test_function_wrapper(self):

        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        called = []

        @wrapt.function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @wrapper
        def function(*args, **kwargs):
            return args, kwargs

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_wrap_function_module_name(self):

        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(__name__, 'global_function_1', wrapper)

        result = global_function_1(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_wrap_function_module(self):

        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        module = sys.modules[__name__]

        wrapt.wrap_function_wrapper(module, 'global_function_2', wrapper)

        result = global_function_2(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_wrap_instance_method_module_name(self):

        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        called = []

        _instance = Class_1()

        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, _instance)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(__name__, 'Class_1.method',
                wrapper)

        result = _instance.method(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_patch_function_module_name(self):

        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        called = []

        @wrapt.patch_function_wrapper(__name__, 'global_function_3')
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        result = global_function_3(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_patch_function_module(self):

        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        called = []

        module = sys.modules[__name__]

        @wrapt.patch_function_wrapper(module, 'global_function_4')
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        result = global_function_4(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

if __name__ == '__main__':
    unittest.main()
