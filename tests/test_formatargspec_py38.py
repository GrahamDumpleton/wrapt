import unittest
import sys
from inspect import getfullargspec

from wrapt import formatargspec

class TestFormatargspec38(unittest.TestCase):

    def assertFormatEqual(self, func, ref):
        formatted = formatargspec(*getfullargspec(func))
        self.assertEqual(formatted, ref)

    def test_formatargspec(self):
        # exemples from https://www.python.org/dev/peps/pep-0570/
        def name1(p1, p2, /, p_or_kw, *, kw): pass
        self.assertFormatEqual(name1, '(p1, p2, p_or_kw, *, kw)')

        def name2(p1, p2=None, /, p_or_kw=None, *, kw): pass
        self.assertFormatEqual(name2, '(p1, p2=None, p_or_kw=None, *, kw)')

        def name3(p1, p2=None, /, *, kw): pass
        self.assertFormatEqual(name3, '(p1, p2=None, *, kw)')

        def name4(p1, p2=None, /): pass
        self.assertFormatEqual(name4, '(p1, p2=None)')

        def name5(p1, p2, /, p_or_kw): pass
        self.assertFormatEqual(name5, '(p1, p2, p_or_kw)')

        def name6(p1, p2, /): pass
        self.assertFormatEqual(name6, '(p1, p2)')

        def name7(p_or_kw, *, kw): pass
        self.assertFormatEqual(name7, '(p_or_kw, *, kw)')

        def name8(*, kw): pass
        self.assertFormatEqual(name8, '(*, kw)')
