from __future__ import print_function

import unittest

import wrapt
import wrapt.exceptions

class TestDecorator(unittest.TestCase):

    def test_no_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_default_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(param1=1, param2=2)
        def _decorator(wrapped, instance, args, kwargs, param1, param2):
            self.assertEqual(param1, 1)
            self.assertEqual(param2, 2)
            return wrapped(*args, **kwargs)

        @_decorator()
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_all(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(param1=1, param2=2)
        def _decorator(wrapped, instance, args, kwargs, param1, param2):
            self.assertEqual(param1, 3)
            self.assertEqual(param2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(param1=3, param2=4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_partial(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(param1=1, param2=2)
        def _decorator(wrapped, instance, args, kwargs, param1, param2):
            self.assertEqual(param1, 1)
            self.assertEqual(param2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(param2=4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_missing_default_parameter(self):
        def run(*args):
            @wrapt.decorator(param1=1)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

        self.assertRaises(wrapt.exceptions.MissingDefaultParameter,
                run, ())

    def test_unexpected_default_parameters_one(self):
        def run(*args):
            @wrapt.decorator(param1=1, param2=2, param3=4)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

        self.assertRaises(wrapt.exceptions.UnexpectedDefaultParameters,
                run, ())

    def test_unexpected_default_parameters_many(self):
        def run(*args):
            @wrapt.decorator(param1=1, param2=2, param3=4, param4=4)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

        self.assertRaises(wrapt.exceptions.UnexpectedDefaultParameters,
                run, ())

    def test_unexpected_override_parameters_one(self):
        def run(*args):
            @wrapt.decorator(param1=1, param2=2)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

            @_decorator(param3=3)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

    def test_unexpected_override_parameters_many(self):
        def run(*args):
            @wrapt.decorator(param1=1, param2=2)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

            @_decorator(param3=3, param4=4)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

    def test_override_parameters_positional_all(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(param1=1, param2=2)
        def _decorator(wrapped, instance, args, kwargs, param1, param2):
            self.assertEqual(param1, 3)
            self.assertEqual(param2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(3, 4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_positional_partial(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(param1=1, param2=2)
        def _decorator(wrapped, instance, args, kwargs, param1, param2):
            self.assertEqual(param1, 3)
            self.assertEqual(param2, 2)
            return wrapped(*args, **kwargs)

        @_decorator(3)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_positional_plus_keyword(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(param1=1, param2=2)
        def _decorator(wrapped, instance, args, kwargs, param1, param2):
            self.assertEqual(param1, 3)
            self.assertEqual(param2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(3, param2=4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_positional_excess_one(self):
        def run(*args):
            @wrapt.decorator(param1=1, param2=2)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

            @_decorator(3, 4, 5)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

    def test_override_parameters_positional_excess_many(self):
        def run(*args):
            @wrapt.decorator(param1=1, param2=2)
            def _decorator(wrapped, instance, args, kwargs, param1, param2):
                return wrapped(*args, **kwargs)

            @_decorator(3, 4, 5, 6)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())
