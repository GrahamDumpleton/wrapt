from __future__ import print_function

import unittest
import threading
import inspect

import wrapt

@wrapt.decorator
def memoize(wrapped, instance, args, kwargs):
    if instance is None and inspect.isclass(wrapped):
        # Wrapped function is a class and we are creating an
        # instance of the class. Don't support this case, just
        # return straight away.

        return wrapped(*args, **kwargs)

    # Retrieve the cache, attaching an empty one if none exists.

    cache = wrapped.__dict__.setdefault('_memoize_cache', {})

    # Now see if entry is in the cache and if it isn't then call
    # the wrapped function to generate it.

    try:
        key = (args, frozenset(kwargs.items()))
        return cache[key]

    except KeyError:
        result = cache[key] = wrapped(*args, **kwargs)
        return result

@memoize
def function1(count, text):
    return count * text

class C1(object):

    @memoize
    def function1(self, count, text):
        return count * text

    @memoize
    @classmethod
    def function2(cls, count, text):
        return count * text

    @memoize
    @staticmethod
    def function3(count, text):
        return count * text

c1 = C1()

class TestSynchronized(unittest.TestCase):

    def test_function(self):
        value1 = function1(10, '0123456789')
        value2 = function1(10, '0123456789')

        self.assertEqual(value1, value2)
        self.assertEqual(id(value1), id(value2))

        self.assertTrue(hasattr(function1, '_memoize_cache'))

    def test_instancemethod(self):
        value1 = c1.function1(10, '0123456789')
        value2 = c1.function1(10, '0123456789')

        self.assertEqual(value1, value2)
        self.assertEqual(id(value1), id(value2))

        self.assertTrue(hasattr(C1.function1, '_memoize_cache'))

    def test_classmethod(self):
        value1 = C1.function2(10, '0123456789')
        value2 = C1.function2(10, '0123456789')

        self.assertEqual(value1, value2)
        self.assertEqual(id(value1), id(value2))

        self.assertTrue(hasattr(C1.function2, '_memoize_cache'))

    def test_staticmethod(self):
        value1 = C1.function3(10, '0123456789')
        value2 = C1.function3(10, '0123456789')

        self.assertEqual(value1, value2)
        self.assertEqual(id(value1), id(value2))

        self.assertTrue(hasattr(C1.function3, '_memoize_cache'))

if __name__ == '__main__':
    unittest.main()
