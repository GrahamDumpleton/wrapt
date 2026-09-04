import unittest

import wrapt


class TestPartialCallableObjectProxy(unittest.TestCase):

    def test_no_arguments(self):
        def func0():
            return ((), {})

        partial0 = wrapt.partial(func0)

        args, kwargs = (), {}

        self.assertEqual(partial0(), (args, kwargs))

    def test_empty_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {}

        partial0 = wrapt.partial(func0, *args, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_1_positional_argument(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (1,), {}

        partial0 = wrapt.partial(func0, *args)

        self.assertEqual(partial0(), (args, kwargs))

    def test_1_keyword_argument(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {"k1": 1}

        partial0 = wrapt.partial(func0, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_multiple_positional_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (1, 2, 3), {}

        partial0 = wrapt.partial(func0, *args)

        self.assertEqual(partial0(), (args, kwargs))

    def test_multiple_keyword_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        args, kwargs = (), {"k1": 1, "k2": 2, "k3": 3}

        partial0 = wrapt.partial(func0, **kwargs)

        self.assertEqual(partial0(), (args, kwargs))

    def test_bound_arguments_no_arguments(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.partial(func0)

        self.assertEqual(partial0._self_args, ())
        self.assertEqual(partial0._self_kwargs, {})

    def test_bound_arguments_positional(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.partial(func0, 1, 2, 3)

        self.assertEqual(partial0._self_args, (1, 2, 3))
        self.assertEqual(partial0._self_kwargs, {})

    def test_bound_arguments_keyword(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.partial(func0, k1=1, k2=2)

        self.assertEqual(partial0._self_args, ())
        self.assertEqual(partial0._self_kwargs, {"k1": 1, "k2": 2})

    def test_bound_arguments_mixed(self):
        def func0(*args, **kwargs):
            return (args, kwargs)

        partial0 = wrapt.PartialCallableObjectProxy(func0, 1, 2, k1=1)

        self.assertEqual(partial0._self_args, (1, 2))
        self.assertEqual(partial0._self_kwargs, {"k1": 1})

    def test_bound_arguments_not_forwarded_to_wrapped(self):
        # The attributes must come from the proxy itself and not be
        # forwarded to a same named attribute on the wrapped callable.

        class Callable:
            _self_args = ("wrapped",)
            _self_kwargs = {"wrapped": True}

            def __call__(self, *args, **kwargs):
                return (args, kwargs)

        partial0 = wrapt.partial(Callable(), 1, k1=1)

        self.assertEqual(partial0._self_args, (1,))
        self.assertEqual(partial0._self_kwargs, {"k1": 1})


if __name__ == "__main__":
    unittest.main()
