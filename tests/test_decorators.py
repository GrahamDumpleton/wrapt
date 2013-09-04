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

if __name__ == '__main__':
    unittest.main()
