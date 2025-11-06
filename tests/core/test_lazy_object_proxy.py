import sys
import unittest

import wrapt


class TestLazyObjectProxy(unittest.TestCase):

    def test_lazy_object_proxy(self):
        status = {"created": 0}

        def factory():
            status["created"] += 1
            return 42

        proxy = wrapt.LazyObjectProxy(factory)

        self.assertEqual(status["created"], 0)
        self.assertEqual(proxy.__wrapped__, 42)
        self.assertEqual(int(proxy), 42)
        self.assertEqual(status["created"], 1)
        self.assertEqual(int(proxy), 42)
        self.assertEqual(status["created"], 1)

    def test_lazy_import(self):
        if "sched" in sys.modules:
            del sys.modules["sched"]

        sched_mod = wrapt.lazy_import("sched")

        self.assertFalse("sched" in sys.modules)

        self.assertIsNotNone(sched_mod.scheduler)

        self.assertTrue("sched" in sys.modules)

    def test_lazy_import_attribute(self):
        if "sched" in sys.modules:
            del sys.modules["sched"]

        scheduler = wrapt.lazy_import("sched", "scheduler")

        self.assertFalse("sched" in sys.modules)

        import sched

        self.assertIsNotNone(scheduler.__wrapped__)
        self.assertIs(scheduler.__wrapped__, sched.scheduler)

        self.assertTrue("sched" in sys.modules)

    def test_lazy_import_dotted(self):
        if "http.client" in sys.modules:
            del sys.modules["http.client"]

        client_mod = wrapt.lazy_import("http.client")

        self.assertFalse("http.client" in sys.modules)

        self.assertIsNotNone(client_mod.HTTPConnection)

        self.assertTrue("http.client" in sys.modules)

    def test_lazy_import_callable(self):
        dumps = wrapt.lazy_import("json", "dumps")

        self.assertTrue(callable(dumps))

        result = dumps({"key": "value"})

        self.assertEqual(result, '{"key": "value"}')

    def test_lazy_import_iterable(self):
        from collections.abc import Iterable

        if "string" in sys.modules:
            del sys.modules["string"]

        digits0 = wrapt.lazy_import("string", "digits")

        self.assertFalse(hasattr(type(digits0), "__iter__"))

        self.assertTrue(callable(digits0))

        # XXX Iteration does not seem to test for __iter__ being a method
        # on the type, so this test is not sufficient to raise the TypeError.
        # I was at some point seeing expected failures here, but not now and
        # I don't know why.

        # if "string" in sys.modules:
        #     del sys.modules["string"]

        # digits1 = wrapt.lazy_import("string", "digits")

        # with self.assertRaises(TypeError):
        #     for char in digits1:
        #         pass

        if "string" in sys.modules:
            del sys.modules["string"]

        digits2 = wrapt.lazy_import("string", "digits", interface=Iterable)

        self.assertTrue(hasattr(type(digits2), "__iter__"))

        self.assertFalse(callable(digits2))

        for char in digits2:
            self.assertIn(char, "0123456789")

        self.assertEqual("".join(digits2), "0123456789")
