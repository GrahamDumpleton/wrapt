import unittest

import pickle

import wrapt


class UnwrappingProxy(wrapt.ObjectProxy):
    # `__reduce__` that returns a reconstructor other than the proxy
    # class itself. On unpickling the proxy is dropped and only the
    # wrapped value is restored.

    def __reduce__(self):
        return (list, (self.__wrapped__,))


class RestoringProxy(wrapt.ObjectProxy):
    # `__reduce__` that returns the proxy class itself as the
    # reconstructor. On unpickling an instance of the same proxy class
    # is restored around the wrapped value.

    def __reduce__(self):
        return (type(self), (self.__wrapped__,))


class TestObjectPickle(unittest.TestCase):

    def test_pickle(self):
        proxy = wrapt.ObjectProxy([1])

        with self.assertRaises(NotImplementedError) as context:
            data = pickle.dumps(proxy)

        self.assertTrue(
            str(context.exception) == "object proxy must define __reduce__()"
        )

    def test_pickle_unwrapping_proxy(self):
        proxy1 = UnwrappingProxy([1])
        pickled = pickle.dumps(proxy1)
        restored = pickle.loads(pickled)

        self.assertEqual(proxy1.__wrapped__, restored)
        self.assertNotIsInstance(restored, UnwrappingProxy)

    def test_pickle_restoring_proxy(self):
        proxy1 = RestoringProxy([1])
        pickled = pickle.dumps(proxy1)
        restored = pickle.loads(pickled)

        self.assertIsInstance(restored, RestoringProxy)
        self.assertEqual(list(restored), [1])
        self.assertEqual(restored.__wrapped__, [1])


class LabelledProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped, label):
        super().__init__(wrapped)
        self._self_label = label

    def __reduce__(self):
        return (type(self), (self.__wrapped__, self._self_label))


class TestProxyRoundTrip(unittest.TestCase):

    def test_roundtrip_preserves_wrapped_object(self):
        original = LabelledProxy({"count": 3, "sum": 6}, label="demo")

        restored = pickle.loads(pickle.dumps(original))

        self.assertEqual(dict(restored), {"count": 3, "sum": 6})

    def test_roundtrip_preserves_proxy_state(self):
        original = LabelledProxy({"count": 3, "sum": 6}, label="demo")

        restored = pickle.loads(pickle.dumps(original))

        self.assertEqual(restored._self_label, "demo")

    def test_roundtrip_preserves_proxy_type(self):
        original = LabelledProxy({"a": 1}, label="demo")

        restored = pickle.loads(pickle.dumps(original))

        self.assertIsInstance(restored, LabelledProxy)

    def test_roundtrip_across_pickle_protocols(self):
        original = LabelledProxy([1, 2, 3], label="list")

        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            restored = pickle.loads(pickle.dumps(original, protocol))

            self.assertEqual(list(restored), [1, 2, 3])
            self.assertEqual(restored._self_label, "list")

    def test_unpickleable_wrapped_object_raises(self):
        # The wrapped object must itself be pickleable, since pickle
        # recursively pickles the arguments returned from __reduce__.
        original = LabelledProxy(lambda x: x, label="lambda")

        with self.assertRaises((pickle.PicklingError, AttributeError)):
            pickle.dumps(original)


if __name__ == "__main__":
    unittest.main()
