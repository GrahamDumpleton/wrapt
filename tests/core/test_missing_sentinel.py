import copy
import pickle
import unittest

import wrapt


class TestMissingSentinel(unittest.TestCase):

    def test_exported(self):
        self.assertIn("MISSING", wrapt.__all__)

    def test_singleton(self):
        # Constructing the type again returns the same instance, so the
        # sentinel is always identity comparable.

        self.assertIs(type(wrapt.MISSING)(), wrapt.MISSING)

    def test_distinct_from_other_sentinels(self):
        self.assertIsNot(wrapt.MISSING, None)
        self.assertIsNot(wrapt.MISSING, Ellipsis)
        self.assertIsNot(wrapt.MISSING, NotImplemented)

    def test_repr(self):
        self.assertEqual(repr(wrapt.MISSING), "<wrapt.MISSING>")

    def test_pickle_round_trip(self):
        self.assertIs(pickle.loads(pickle.dumps(wrapt.MISSING)), wrapt.MISSING)

    def test_copy(self):
        self.assertIs(copy.copy(wrapt.MISSING), wrapt.MISSING)
        self.assertIs(copy.deepcopy(wrapt.MISSING), wrapt.MISSING)
