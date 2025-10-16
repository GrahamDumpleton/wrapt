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
