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

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
            self.assertEqual(p1, 1)
            self.assertEqual(p2, 2)
            return wrapped(*args, **kwargs)

        @_decorator()
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_all(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
            self.assertEqual(p1, 3)
            self.assertEqual(p2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(p1=3, p2=4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_partial(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
            self.assertEqual(p1, 1)
            self.assertEqual(p2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(p2=4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_required_parameter_missing(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator()
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.MissingParameter,
                run, ())

    def test_unexpected_parameters_one(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(p3=3)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

    def test_unexpected_parameters_many(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(p3=3, p4=4)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

    def test_override_parameters_positional_all(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
            self.assertEqual(p1, 3)
            self.assertEqual(p2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(3, 4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_positional_partial(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
            self.assertEqual(p1, 3)
            self.assertEqual(p2, 2)
            return wrapped(*args, **kwargs)

        @_decorator(3)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_positional_plus_keyword(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
            self.assertEqual(p1, 3)
            self.assertEqual(p2, 4)
            return wrapped(*args, **kwargs)

        @_decorator(3, p2=4)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_override_parameters_positional_excess_one(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(3, 4, 5)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

    def test_override_parameters_positional_excess_many(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(3, 4, 5, 6)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(wrapt.exceptions.UnexpectedParameters, run, ())

if __name__ == '__main__':
    unittest.main()
