from __future__ import print_function

import unittest

import wrapt

class TestArguments(unittest.TestCase):

    def test_getcallargs(self):
        def function(a, b=2, c=3, d=4, e=5, *args, **kwargs):
            pass

        expected = {'a': 10, 'c': 3, 'b': 20, 'e': 5, 'd': 40,
                'args': (), 'kwargs': {'f': 50}}
        calculated = wrapt.getcallargs(function, 10, 20, d=40, f=50)

        self.assertEqual(expected, calculated)

        expected = {'a': 10, 'c': 30, 'b': 20, 'e': 50, 'd': 40,
                'args': (60,), 'kwargs': {}}
        calculated = wrapt.getcallargs(function, 10, 20, 30, 40, 50, 60)

        self.assertEqual(expected, calculated)

    def test_unexpected_unicode_keyword(self):
        def function(a=2):
            pass

        kwargs = { u'b': 40 }
        self.assertRaises(TypeError, wrapt.getcallargs, function, **kwargs)
