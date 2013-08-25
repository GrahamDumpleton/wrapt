from __future__ import print_function

import unittest

import wrapt

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

        self.assertRaises(TypeError, run, ())

    def test_unexpected_parameters_one(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(p3=3)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(TypeError, run, ())

    def test_unexpected_parameters_many(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(p3=3, p4=4)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(TypeError, run, ())

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

        self.assertRaises(TypeError, run, ())

    def test_override_parameters_positional_excess_many(self):
        def run(*args):
            @wrapt.decorator
            def _decorator(wrapped, instance, args, kwargs, p1=1, p2=2):
                return wrapped(*args, **kwargs)

            @_decorator(3, 4, 5, 6)
            def _function(*args, **kwargs):
                return args, kwargs

        self.assertRaises(TypeError, run, ())

    def test_varargs_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, *wrapper_args):
            self.assertEqual(wrapper_args, tuple(reversed(_args)))
            return wrapped(*args, **kwargs)

        @_decorator(*reversed(_args))
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_args_plus_varargs_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, p1, *wrapper_args):
            self.assertEqual(p1, 2)
            self.assertEqual(wrapper_args, tuple(reversed(_args))[1:])
            return wrapped(*args, **kwargs)

        @_decorator(*reversed(_args))
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_keyword_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, **wrapper_kwargs):
            self.assertEqual(wrapper_kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator(**_kwargs)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_args_plus_keyword_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs, one, **wrapper_kwargs):
            self.assertEqual(one, 1)
            self.assertEqual(wrapper_kwargs, {'two': 2})
            return wrapped(*args, **kwargs)

        @_decorator(**_kwargs)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_varargs_plus_keyword_parameters(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs,
                *wrapper_args, **wrapper_kwargs):
            self.assertEqual(wrapper_args, tuple(reversed(_args)))
            self.assertEqual(wrapper_kwargs, _kwargs)
            return wrapped(*args, **kwargs)

        @_decorator(*reversed(_args), **_kwargs)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_parameter_missing_no_validation(self):
        _args = (1, 2)
        _kwargs = { 'one': 1, 'two': 2 }

        @wrapt.decorator(validate=False)
        def _decorator(wrapped, instance, args, kwargs, p1, p2=2):
            return wrapped(*args, **kwargs)

        @_decorator()
        def _function(*args, **kwargs):
            return args, kwargs

        def run():
            result = _function(*_args, **_kwargs)

        self.assertRaises(TypeError, run, ())

if __name__ == '__main__':
    unittest.main()
