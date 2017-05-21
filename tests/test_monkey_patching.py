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

class Class_2(object):
    @classmethod
    def method(cls, *args, **kwargs):
        return cls, args, kwargs

class Class_2_1(Class_2):
    pass

class Class_2_2(Class_2_1):
    pass

class Class_3(object):
    @staticmethod
    def method(*args, **kwargs):
        return args, kwargs

class TestMonkeyPatching(unittest.TestCase):

    def test_function_wrapper(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

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

    def test_function_wrapper_instance_method(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        _self = self

        class wrapper(object):
            @wrapt.function_wrapper
            def __call__(self, wrapped, instance, args, kwargs):
                _self.assertEqual(type(self), wrapper)
                called.append((args, kwargs))
                _self.assertEqual(instance, None)
                _self.assertEqual(args, _args)
                _self.assertEqual(kwargs, _kwargs)
                return wrapped(*args, **kwargs)

        @wrapper()
        def function(*args, **kwargs):
            return args, kwargs

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_function_wrapper_class_method(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        class wrapper(object):
            @wrapt.function_wrapper
            @classmethod
            def __call__(cls, wrapped, instance, args, kwargs):
                self.assertEqual(cls, wrapper)
                called.append((args, kwargs))
                self.assertEqual(instance, None)
                self.assertEqual(args, _args)
                self.assertEqual(kwargs, _kwargs)
                return wrapped(*args, **kwargs)

        @wrapper()
        def function(*args, **kwargs):
            return args, kwargs

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_wrap_function_module_name(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

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
        _kwargs = {'one': 1, 'two': 2}

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
        _kwargs = {'one': 1, 'two': 2}

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

    def test_wrap_class_method_module_name(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, Class_2)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(__name__, 'Class_2.method',
                wrapper)

        result = Class_2.method(*_args, **_kwargs)

        self.assertEqual(result, (Class_2, _args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_wrap_class_method_inherited(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(__name__, 'Class_2_1.method',
                wrapper)

        result = Class_2_1.method(*_args, **_kwargs)
        self.assertEqual(result, (Class_2_1, _args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

        called.pop()

        result = Class_2_2.method(*_args, **_kwargs)
        self.assertEqual(result, (Class_2_2, _args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_wrap_static_method_module_name(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, None)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(__name__, 'Class_3.method',
                wrapper)

        result = Class_3.method(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_patch_function_module_name(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

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
        _kwargs = {'one': 1, 'two': 2}

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

    def _test_transient_function_wrapper(self, *args, **kwargs):
        return args, kwargs

    def test_transient_function_wrapper(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        @wrapt.transient_function_wrapper(__name__,
                'TestMonkeyPatching._test_transient_function_wrapper')
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(wrapped, self._test_transient_function_wrapper)
            self.assertEqual(instance, self)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @wrapper
        def function(*args, **kwargs):
            return self._test_transient_function_wrapper(*args, **kwargs)

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_transient_function_wrapper_instance_method(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        _self = self

        class wrapper(object):
            @wrapt.transient_function_wrapper(__name__,
                    'TestMonkeyPatching._test_transient_function_wrapper')
            def __call__(self, wrapped, instance, args, kwargs):
                called.append((args, kwargs))
                _self.assertEqual(wrapped, _self._test_transient_function_wrapper)
                _self.assertEqual(instance, _self)
                _self.assertEqual(args, _args)
                _self.assertEqual(kwargs, _kwargs)
                return wrapped(*args, **kwargs)

        @wrapper()
        def function(*args, **kwargs):
            return self._test_transient_function_wrapper(*args, **kwargs)

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

class TestExplicitMonkeyPatching(unittest.TestCase):

    def test_patch_instance_method_class(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        @wrapt.function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, _instance)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        Class.function = wrapper(Class.function)

        _instance = Class()

        result = _instance.function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_patch_instance_method_dict(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        @wrapt.function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, _instance)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        Class.function = wrapper(vars(Class)['function'])

        _instance = Class()

        result = _instance.function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_patch_instance_method_instance(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        @wrapt.function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, _instance)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        _instance = Class()

        _instance.function = wrapper(_instance.function)

        result = _instance.function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

    def test_patch_instance_method_extracted(self):

        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        called = []

        @wrapt.function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            called.append((args, kwargs))
            self.assertEqual(instance, _instance)
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        _instance = Class()

        function = wrapper(_instance.function)

        result = function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(called[0], (_args, _kwargs))

if __name__ == '__main__':
    unittest.main()
