from __future__ import print_function

import inspect
import unittest
import imp
import collections
from typing import Iterable

import wrapt

class TestDynamicAdapter(unittest.TestCase):

    def test_adapter_factory_with_type_hints(self):
        def argspec_factory(wrapped):
            return inspect.getfullargspec(wrapped)

        def add_option(func):
            """Decorator with custom adapter factory."""
            @wrapt.decorator(adapter=wrapt.adapter_factory(argspec_factory))
            def _add_option(func, instance, args, kwargs):
                return func(*args, **kwargs)

            return _add_option(func)

        @add_option
        def run() -> Iterable:
            """We add the non-default typehint `Iterable`, which reveals the error."""
            return [True]

        # This should run without a NameError being thrown
        self.assertTrue(run())


if __name__ == '__main__':
    unittest.main()
