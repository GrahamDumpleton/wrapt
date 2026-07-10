import unittest
from inspect import getfullargspec

from wrapt.arguments import formatargspec


class TestFormatargspec(unittest.TestCase):

    def assertFormatEqual(self, func, ref):
        formatted = formatargspec(*getfullargspec(func))
        self.assertEqual(formatted, ref)

    def test_formatargspec(self):
        def foo1():
            pass

        self.assertFormatEqual(foo1, "()")

        def foo2(a, b="c"):
            pass

        self.assertFormatEqual(foo2, ("(a, b='c')"))

        def foo3(a, b, *args, **kwargs):
            pass

        self.assertFormatEqual(foo3, "(a, b, *args, **kwargs)")

        def foo4(a: int, b) -> list:
            return []

        formatted4 = "(a: int, b) -> list"
        self.assertFormatEqual(foo4, formatted4)

        # examples from https://www.python.org/dev/peps/pep-3102/
        def sortwords(*wordlist, case_sensitive=False):
            pass

        self.assertFormatEqual(sortwords, "(*wordlist, case_sensitive=False)")

        def compare(a, b, *, key=None):
            pass

        self.assertFormatEqual(compare, "(a, b, *, key=None)")


class TestFormatargspecPositionalOnly(unittest.TestCase):

    def assertFormatEqual(self, func, ref):
        formatted = formatargspec(*getfullargspec(func))
        self.assertEqual(formatted, ref)

    def test_formatargspec(self):
        # examples from https://www.python.org/dev/peps/pep-0570/
        def name1(p1, p2, /, p_or_kw, *, kw):
            pass

        self.assertFormatEqual(name1, "(p1, p2, p_or_kw, *, kw)")

        def name2(p1, p2=None, /, p_or_kw=None, *, kw):
            pass

        self.assertFormatEqual(name2, "(p1, p2=None, p_or_kw=None, *, kw)")

        def name3(p1, p2=None, /, *, kw):
            pass

        self.assertFormatEqual(name3, "(p1, p2=None, *, kw)")

        def name4(p1, p2=None, /):
            pass

        self.assertFormatEqual(name4, "(p1, p2=None)")

        def name5(p1, p2, /, p_or_kw):
            pass

        self.assertFormatEqual(name5, "(p1, p2, p_or_kw)")

        def name6(p1, p2, /):
            pass

        self.assertFormatEqual(name6, "(p1, p2)")

        def name7(p_or_kw, *, kw):
            pass

        self.assertFormatEqual(name7, "(p_or_kw, *, kw)")

        def name8(*, kw):
            pass

        self.assertFormatEqual(name8, "(*, kw)")
