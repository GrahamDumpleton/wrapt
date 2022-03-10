import unittest
import sys
from inspect import getfullargspec

from wrapt import formatargspec

class TestFormatargspec35(unittest.TestCase):

    def assertFormatEqual(self, func, ref):
        formatted = formatargspec(*getfullargspec(func))
        self.assertEqual(formatted, ref)

    def test_formatargspec(self):
        def foo1(): pass
        self.assertFormatEqual(foo1, '()')

        def foo2(a, b='c'): pass
        self.assertFormatEqual(foo2, ("(a, b='c')"))

        def foo3(a, b, *args, **kwargs): pass
        self.assertFormatEqual(foo3, '(a, b, *args, **kwargs)')

        def foo4(a: int, b) -> list: pass
        if sys.version_info[:2] < (3, 7):
            formatted4 = '(a:int, b) -> list'
        else:
            formatted4 = '(a: int, b) -> list'
        self.assertFormatEqual(foo4, formatted4)

        # examples from https://www.python.org/dev/peps/pep-3102/
        def sortwords(*wordlist, case_sensitive=False): pass
        self.assertFormatEqual(sortwords, '(*wordlist, case_sensitive=False)')

        def compare(a, b, *, key=None): pass
        self.assertFormatEqual(compare, '(a, b, *, key=None)')
