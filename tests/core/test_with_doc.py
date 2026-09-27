import inspect
import pydoc
import unittest

import wrapt


def _proto(user: str, count: int = 1) -> bool: ...


def _method_proto(self, value: int) -> int: ...


class TestDoc(unittest.TestCase):
    def test_docstring_overridden(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn(*args, **kwargs):
            """Original."""
            return args, kwargs

        self.assertEqual(fn.__doc__, "Overridden.")
        self.assertEqual(inspect.getdoc(fn), "Overridden.")

    def test_original_function_not_mutated(self):
        def target(*args, **kwargs):
            """Original."""
            return args, kwargs

        decorated = wrapt.with_doc(doc="Overridden.")(target)

        self.assertEqual(target.__doc__, "Original.")
        self.assertIs(decorated.__wrapped__, target)
        self.assertEqual(decorated.__wrapped__.__doc__, "Original.")
        self.assertIs(inspect.unwrap(decorated), target)
        self.assertEqual(inspect.unwrap(decorated).__doc__, "Original.")

    def test_call_delegates_to_wrapped(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(fn(1, b=2), ((1,), {"b": 2}))

    def test_pydoc_shows_override(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn(*args, **kwargs):
            """Original."""

        rendered = pydoc.render_doc(fn)

        self.assertIn("Overridden.", rendered)
        self.assertNotIn("Original.", rendered)

    def test_signature_of_wrapped_still_reported(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn(a, b=1):
            """Original."""

        self.assertEqual(str(inspect.signature(fn)), "(a, b=1)")

    def test_none_docstring(self):
        # The docstring may be overridden to None, in which case the
        # wrapped function's docstring is not reported either.

        @wrapt.with_doc(factory=lambda wrapped: None)
        def fn(*args, **kwargs):
            """Original."""

        self.assertIsNone(fn.__doc__)
        self.assertEqual(fn.__wrapped__.__doc__, "Original.")


class TestFactory(unittest.TestCase):
    def test_factory_receives_wrapped(self):
        seen = []

        def factory(wrapped):
            seen.append(wrapped)
            return f"Documentation for {wrapped.__name__}."

        def target():
            """Original."""

        decorated = wrapt.with_doc(factory=factory)(target)

        self.assertEqual(seen, [target])
        self.assertEqual(decorated.__doc__, "Documentation for target.")
        self.assertEqual(target.__doc__, "Original.")

    def test_factory_called_once_at_decoration_time(self):
        calls = []

        def factory(wrapped):
            calls.append(wrapped)
            return "Overridden."

        @wrapt.with_doc(factory=factory)
        def fn():
            pass

        self.assertEqual(len(calls), 1)

        fn.__doc__
        fn.__doc__

        self.assertEqual(len(calls), 1)

    def test_factory_sees_overridden_signature_when_stacked_above(self):
        def factory(wrapped):
            return f"{wrapped.__name__}{inspect.signature(wrapped)}"

        @wrapt.with_doc(factory=factory)
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            """Original."""

        self.assertEqual(fn.__doc__, "fn(user: str, count: int = 1) -> bool")
        self.assertEqual(
            str(inspect.signature(fn)), "(user: str, count: int = 1) -> bool"
        )


class TestAssignment(unittest.TestCase):
    def test_assignment_replaces_override(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn():
            """Original."""

        fn.__doc__ = "Replaced."

        self.assertEqual(fn.__doc__, "Replaced.")
        self.assertEqual(fn.__wrapped__.__doc__, "Original.")

    def test_deletion_restores_delegation(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn():
            """Original."""

        del fn.__doc__

        self.assertEqual(fn.__doc__, "Original.")
        self.assertEqual(fn.__wrapped__.__doc__, "Original.")

    def test_assignment_after_deletion_writes_through(self):
        # Once the override is removed the wrapper behaves as any other
        # wrapt wrapper, with assignment reaching the wrapped function.

        @wrapt.with_doc(doc="Overridden.")
        def fn():
            """Original."""

        del fn.__doc__
        fn.__doc__ = "Replaced."

        self.assertEqual(fn.__doc__, "Replaced.")
        self.assertEqual(fn.__wrapped__.__doc__, "Replaced.")

    def test_assignment_of_none(self):
        @wrapt.with_doc(doc="Overridden.")
        def fn():
            """Original."""

        fn.__doc__ = None

        self.assertIsNone(fn.__doc__)
        self.assertEqual(fn.__wrapped__.__doc__, "Original.")


class TestValidation(unittest.TestCase):
    def test_no_spec_raises(self):
        with self.assertRaises(TypeError):
            wrapt.with_doc()

    def test_multiple_specs_raises(self):
        with self.assertRaises(TypeError):
            wrapt.with_doc(doc="Overridden.", factory=lambda wrapped: "Other.")

    def test_bare_decorator_raises(self):
        # @wrapt.with_doc (no parens, no kwargs) means `wrapped` is the
        # function, no docstring supplied -- must raise TypeError.

        def fn():
            pass

        with self.assertRaises(TypeError):
            wrapt.with_doc(fn)


class TestInstanceMethod(unittest.TestCase):
    def setUp(self):
        class C:
            @wrapt.with_doc(doc="Overridden.")
            def method(self, *args):
                """Original."""
                return args

        self.C = C

    def test_class_view(self):
        self.assertEqual(self.C.method.__doc__, "Overridden.")

    def test_bound_view(self):
        self.assertEqual(self.C().method.__doc__, "Overridden.")

    def test_bound_view_is_read_only(self):
        # The docstring of a bound method cannot be assigned to, and the
        # bound view of the wrapper follows that.

        c = self.C()

        with self.assertRaises(AttributeError):
            c.method.__doc__ = "Replaced."

        self.assertEqual(c.method.__doc__, "Overridden.")
        self.assertEqual(self.C.method.__wrapped__.__doc__, "Original.")

    def test_call_through_binding(self):
        self.assertEqual(self.C().method(1, 2), (1, 2))

    def test_pydoc_on_bound_method(self):
        rendered = pydoc.render_doc(self.C().method)

        self.assertIn("Overridden.", rendered)
        self.assertNotIn("Original.", rendered)

    def test_pydoc_on_class(self):
        rendered = pydoc.render_doc(self.C)

        self.assertIn("Overridden.", rendered)
        self.assertNotIn("Original.", rendered)


class TestClassmethod(unittest.TestCase):
    def test_above_classmethod(self):
        class D:
            @wrapt.with_doc(doc="Overridden.")
            @classmethod
            def build(cls, *args):
                """Original."""
                return cls, args

        self.assertEqual(D.build.__doc__, "Overridden.")
        self.assertEqual(D().build.__doc__, "Overridden.")
        self.assertEqual(D.build(1), (D, (1,)))
        self.assertEqual(D().build(1), (D, (1,)))

    def test_below_classmethod(self):
        class D:
            @classmethod
            @wrapt.with_doc(doc="Overridden.")
            def build(cls, *args):
                """Original."""
                return cls, args

        self.assertEqual(D.build.__doc__, "Overridden.")
        self.assertEqual(D().build.__doc__, "Overridden.")
        self.assertEqual(D.build(1), (D, (1,)))
        self.assertEqual(D().build(1), (D, (1,)))


class TestStaticmethod(unittest.TestCase):
    def test_above_staticmethod(self):
        class E:
            @wrapt.with_doc(doc="Overridden.")
            @staticmethod
            def twice(*args):
                """Original."""
                return args

        self.assertEqual(E.twice.__doc__, "Overridden.")
        self.assertEqual(E().twice.__doc__, "Overridden.")
        self.assertEqual(E.twice(1), (1,))
        self.assertEqual(E().twice(1), (1,))

    def test_below_staticmethod(self):
        class E:
            @staticmethod
            @wrapt.with_doc(doc="Overridden.")
            def twice(*args):
                """Original."""
                return args

        self.assertEqual(E.twice.__doc__, "Overridden.")
        self.assertEqual(E().twice.__doc__, "Overridden.")
        self.assertEqual(E.twice(1), (1,))
        self.assertEqual(E().twice(1), (1,))


class TestStacking(unittest.TestCase):
    @staticmethod
    def _pass_through():
        @wrapt.decorator
        def pass_through(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        return pass_through

    def test_with_doc_above_with_signature(self):
        @wrapt.with_doc(doc="Overridden.")
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            """Original."""

        self.assertEqual(fn.__doc__, "Overridden.")
        self.assertEqual(
            str(inspect.signature(fn)), "(user: str, count: int = 1) -> bool"
        )

        rendered = pydoc.render_doc(fn)

        self.assertIn("Overridden.", rendered)
        self.assertIn("user: str, count: int = 1", rendered)

    def test_with_doc_below_with_signature(self):
        @wrapt.with_signature(prototype=_proto)
        @wrapt.with_doc(doc="Overridden.")
        def fn(*args, **kwargs):
            """Original."""

        self.assertEqual(fn.__doc__, "Overridden.")
        self.assertEqual(
            str(inspect.signature(fn)), "(user: str, count: int = 1) -> bool"
        )

        rendered = pydoc.render_doc(fn)

        self.assertIn("Overridden.", rendered)
        self.assertIn("user: str, count: int = 1", rendered)

    def test_docstring_propagates_through_outer_decorator(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_doc(doc="Overridden.")
        def fn(*args, **kwargs):
            """Original."""
            return args, kwargs

        self.assertEqual(fn.__doc__, "Overridden.")
        self.assertEqual(fn(1), ((1,), {}))

        rendered = pydoc.render_doc(fn)

        self.assertIn("Overridden.", rendered)
        self.assertNotIn("Original.", rendered)

    def test_docstring_propagates_through_outer_decorator_on_method(self):
        pass_through = self._pass_through()

        class C:
            @pass_through
            @wrapt.with_doc(doc="Overridden.")
            def method(self, *args):
                """Original."""
                return args

        self.assertEqual(C.method.__doc__, "Overridden.")
        self.assertEqual(C().method.__doc__, "Overridden.")
        self.assertEqual(C().method(1), (1,))

    def test_with_doc_on_top_of_with_doc(self):
        @wrapt.with_doc(doc="Outer.")
        @wrapt.with_doc(doc="Inner.")
        def fn():
            """Original."""

        self.assertEqual(fn.__doc__, "Outer.")
        self.assertEqual(fn.__wrapped__.__doc__, "Inner.")
        self.assertEqual(fn.__wrapped__.__wrapped__.__doc__, "Original.")


if __name__ == "__main__":
    unittest.main()
