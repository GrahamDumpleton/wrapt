from __future__ import print_function

import unittest

import wrapt

class TestDecorator(unittest.TestCase):

    def test_no_parameters(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_method_as_decorator(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Instance(object):
            def __init__(self):
                self.count = 0
            @wrapt.decorator
            def decorator(self, wrapped, instance, args, kwargs):
                self.count += 1
                return wrapped(*args, **kwargs)

        instance = Instance()

        @instance.decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(instance.count, 1)

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(instance.count, 2)

    def test_class_method_as_decorator(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Instance(object):
            count = 0
            @wrapt.decorator
            @classmethod
            def decorator(cls, wrapped, instance, args, kwargs):
                cls.count += 1
                return wrapped(*args, **kwargs)

        @Instance.decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(Instance.count, 1)

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(Instance.count, 2)

    def test_class_type_as_decorator(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        class ClassDecorator(object):
            def __call__(self, wrapped, instance, args, kwargs):
                return wrapped(*args, **kwargs)

        @ClassDecorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_type_as_decorator_args(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        class ClassDecorator(object):
            def __init__(self, arg):
                assert arg == 1
            def __call__(self, wrapped, instance, args, kwargs):
                return wrapped(*args, **kwargs)

        @ClassDecorator(arg=1)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

if __name__ == '__main__':
    unittest.main()
