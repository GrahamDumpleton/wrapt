import inspect
import unittest

import wrapt


def _proto(a: int, b: str = "x") -> bool: ...


def _method_proto(self, value: int) -> int: ...


def _cm_proto(cls, value: int) -> int: ...


def _sm_proto(value: int) -> int: ...


def _full_proto(
    a: int,
    b: str = "x",
    /,
    c: float = 1.5,
    *args: int,
    d: bool = True,
    e: bytes,
    **kwargs: str,
) -> None: ...


class TestPrototype(unittest.TestCase):
    def test_signature_and_annotations(self):
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )
        self.assertEqual(
            fn.__annotations__, {"a": int, "b": str, "return": bool}
        )

    def test_call_delegates_to_wrapped(self):
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(fn(1, "y"), ((1, "y"), {}))

    def test_original_function_not_mutated(self):
        def target(*args, **kwargs):
            return args, kwargs

        decorated = wrapt.with_signature(prototype=_proto)(target)

        self.assertEqual(str(inspect.signature(target)), "(*args, **kwargs)")
        self.assertEqual(target.__annotations__, {})
        self.assertIs(decorated.__wrapped__, target)

    def test_getfullargspec(self):
        @wrapt.with_signature(prototype=_proto)
        def fn(x, y, z):
            return x, y, z

        spec = inspect.getfullargspec(fn)
        self.assertEqual(spec.args, ["a", "b"])
        self.assertEqual(spec.defaults, ("x",))
        self.assertEqual(
            spec.annotations, {"a": int, "b": str, "return": bool}
        )


class TestSignatureObject(unittest.TestCase):
    def test_signature_used_directly(self):
        sig = inspect.Signature(
            [
                inspect.Parameter(
                    "x",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=int,
                ),
            ],
            return_annotation=str,
        )

        @wrapt.with_signature(signature=sig)
        def fn(*args, **kwargs):
            return "ok"

        self.assertEqual(str(inspect.signature(fn)), "(x: int) -> str")
        self.assertEqual(fn.__annotations__, {"x": int, "return": str})
        self.assertIs(fn.__signature__, sig)


class TestFactory(unittest.TestCase):
    def test_factory_returning_signature(self):
        def factory(wrapped):
            s = inspect.signature(wrapped)
            return s.replace(
                parameters=[
                    inspect.Parameter(
                        "request_id",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    ),
                    *s.parameters.values(),
                ]
            )

        @wrapt.with_signature(factory=factory)
        def fn(a, b):
            return a + b

        self.assertEqual(str(inspect.signature(fn)), "(request_id, a, b)")
        self.assertEqual(fn(1, 2), 3)

    def test_factory_returning_callable_prototype(self):
        def factory(wrapped):
            def prototype(first: int, second: int) -> int: ...
            return prototype

        @wrapt.with_signature(factory=factory)
        def fn(a, b):
            return a + b

        self.assertEqual(
            str(inspect.signature(fn)), "(first: int, second: int) -> int"
        )


class TestValidation(unittest.TestCase):
    def test_no_spec_raises(self):
        with self.assertRaises(TypeError):
            wrapt.with_signature()

    def test_multiple_specs_raises(self):
        sig = inspect.signature(_proto)
        with self.assertRaises(TypeError):
            wrapt.with_signature(prototype=_proto, signature=sig)

    def test_bare_decorator_raises(self):
        # @wrapt.with_signature (no parens, no kwargs) means `wrapped` is
        # the function, no spec supplied -- must raise TypeError.
        def fn():
            pass

        with self.assertRaises(TypeError):
            wrapt.with_signature(fn)


class TestInstanceMethod(unittest.TestCase):
    def test_class_view(self):
        class C:
            @wrapt.with_signature(prototype=_method_proto)
            def scale(self, *args, **kwargs):
                return args[0] * 10

        self.assertEqual(
            str(inspect.signature(C.scale)), "(self, value: int) -> int"
        )

    def test_bound_view_strips_self(self):
        class C:
            @wrapt.with_signature(prototype=_method_proto)
            def scale(self, *args, **kwargs):
                return args[0] * 10

        c = C()
        self.assertEqual(
            str(inspect.signature(c.scale)), "(value: int) -> int"
        )

    def test_call_through_binding(self):
        class C:
            @wrapt.with_signature(prototype=_method_proto)
            def scale(self, *args, **kwargs):
                return args[0] * 10

        c = C()
        self.assertEqual(c.scale(3), 30)


class TestClassmethod(unittest.TestCase):
    def test_below_classmethod(self):
        # @classmethod on the outside, @with_signature on the inside.
        class D:
            @classmethod
            @wrapt.with_signature(prototype=_cm_proto)
            def build(cls, *args, **kwargs):
                return args[0] + 1

        self.assertEqual(D.build(5), 6)
        self.assertEqual(D().build(5), 6)
        self.assertEqual(
            str(inspect.signature(D.build)), "(value: int) -> int"
        )

    def test_above_classmethod(self):
        # @with_signature on the outside, @classmethod on the inside.
        # Conventional stacking order for wrapt decorators.
        class D:
            @wrapt.with_signature(prototype=_cm_proto)
            @classmethod
            def build(cls, *args, **kwargs):
                return args[0] + 1

        self.assertEqual(D.build(5), 6)
        self.assertEqual(D().build(5), 6)
        self.assertEqual(
            str(inspect.signature(D.build)), "(value: int) -> int"
        )


class TestStaticmethod(unittest.TestCase):
    def test_below_staticmethod(self):
        class E:
            @staticmethod
            @wrapt.with_signature(prototype=_sm_proto)
            def twice(*args, **kwargs):
                return args[0] * 2

        self.assertEqual(E.twice(4), 8)
        self.assertEqual(E().twice(4), 8)
        self.assertEqual(
            str(inspect.signature(E.twice)), "(value: int) -> int"
        )

    def test_above_staticmethod(self):
        class E:
            @wrapt.with_signature(prototype=_sm_proto)
            @staticmethod
            def twice(*args, **kwargs):
                return args[0] * 2

        self.assertEqual(E.twice(4), 8)
        self.assertEqual(E().twice(4), 8)
        self.assertEqual(
            str(inspect.signature(E.twice)), "(value: int) -> int"
        )


class TestDerivedCodeAttributes(unittest.TestCase):
    def setUp(self):
        @wrapt.with_signature(prototype=_full_proto)
        def fn(*args, **kwargs):
            return None

        self.fn = fn

    def test_co_argcount(self):
        self.assertEqual(self.fn.__code__.co_argcount, 3)  # a, b, c

    def test_co_posonlyargcount(self):
        self.assertEqual(self.fn.__code__.co_posonlyargcount, 2)  # a, b

    def test_co_kwonlyargcount(self):
        self.assertEqual(self.fn.__code__.co_kwonlyargcount, 2)  # d, e

    def test_co_varnames(self):
        self.assertEqual(
            self.fn.__code__.co_varnames,
            ("a", "b", "c", "d", "e", "args", "kwargs"),
        )

    def test_co_flags_varargs(self):
        self.assertTrue(self.fn.__code__.co_flags & inspect.CO_VARARGS)

    def test_co_flags_varkeywords(self):
        self.assertTrue(self.fn.__code__.co_flags & inspect.CO_VARKEYWORDS)

    def test_defaults(self):
        self.assertEqual(self.fn.__defaults__, ("x", 1.5))

    def test_kwdefaults(self):
        self.assertEqual(self.fn.__kwdefaults__, {"d": True})

    def test_no_defaults_returns_none(self):
        def minimal_proto(a, b): ...

        @wrapt.with_signature(prototype=minimal_proto)
        def fn(*args, **kwargs): ...

        self.assertIsNone(fn.__defaults__)
        self.assertIsNone(fn.__kwdefaults__)


class TestBoundMethodSurrogate(unittest.TestCase):
    def test_bound_surrogate_exposes_derived_attrs(self):
        class C:
            @wrapt.with_signature(prototype=_method_proto)
            def scale(self, *args, **kwargs):
                return args[0]

        c = C()
        self.assertEqual(c.scale.__func__.__code__.co_argcount, 2)
        self.assertEqual(
            c.scale.__func__.__code__.co_varnames, ("self", "value")
        )
        self.assertEqual(
            c.scale.__func__.__annotations__, {"value": int, "return": int}
        )


class TestCaching(unittest.TestCase):
    def test_code_object_cached(self):
        @wrapt.with_signature(prototype=_full_proto)
        def fn(*args, **kwargs): ...

        first = fn.__code__
        self.assertIs(fn.__code__, first)

    def test_annotations_cached(self):
        @wrapt.with_signature(prototype=_full_proto)
        def fn(*args, **kwargs): ...

        first = fn.__annotations__
        self.assertIs(fn.__annotations__, first)

    def test_derived_co_attr_cached(self):
        @wrapt.with_signature(prototype=_full_proto)
        def fn(*args, **kwargs): ...

        first = fn.__code__.co_varnames
        self.assertIs(fn.__code__.co_varnames, first)


class TestPassThroughStacking(unittest.TestCase):
    """Verify that placing another wrapt decorator OVER @with_signature
    still surfaces the override via introspection on the outer wrapper.

    These are the critical integration tests: the outer FunctionWrapper
    must propagate __signature__, __annotations__, __defaults__,
    __kwdefaults__, and __code__ attributes from the inner
    _SignatureFunctionWrapper without mutation or loss.
    """

    @staticmethod
    def _pass_through():
        @wrapt.decorator
        def pass_through(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        return pass_through

    def test_signature_propagates_up(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )

    def test_annotations_propagate_up(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(
            fn.__annotations__, {"a": int, "b": str, "return": bool}
        )

    def test_defaults_propagate_up(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_signature(prototype=_full_proto)
        def fn(*args, **kwargs): ...

        self.assertEqual(fn.__defaults__, ("x", 1.5))
        self.assertEqual(fn.__kwdefaults__, {"d": True})

    def test_code_co_attrs_propagate_up(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_signature(prototype=_full_proto)
        def fn(*args, **kwargs): ...

        self.assertEqual(fn.__code__.co_argcount, 3)
        self.assertEqual(fn.__code__.co_posonlyargcount, 2)
        self.assertEqual(fn.__code__.co_kwonlyargcount, 2)
        self.assertEqual(
            fn.__code__.co_varnames,
            ("a", "b", "c", "d", "e", "args", "kwargs"),
        )

    def test_call_still_works(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(fn(1, "y"), ((1, "y"), {}))

    def test_getfullargspec_propagates_up(self):
        pass_through = self._pass_through()

        @pass_through
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs): ...

        spec = inspect.getfullargspec(fn)
        self.assertEqual(spec.args, ["a", "b"])
        self.assertEqual(spec.defaults, ("x",))

    def test_instance_method_unbound_view(self):
        pass_through = self._pass_through()

        class C:
            @pass_through
            @wrapt.with_signature(prototype=_method_proto)
            def scale(self, *args, **kwargs):
                return args[0] * 10

        self.assertEqual(
            str(inspect.signature(C.scale)), "(self, value: int) -> int"
        )

    def test_instance_method_bound_view(self):
        pass_through = self._pass_through()

        class C:
            @pass_through
            @wrapt.with_signature(prototype=_method_proto)
            def scale(self, *args, **kwargs):
                return args[0] * 10

        c = C()
        self.assertEqual(c.scale(3), 30)
        # With an outer wrapt decorator the bound view still reports the
        # stripped signature via __signature__ propagation.
        self.assertEqual(
            str(inspect.signature(c.scale)), "(value: int) -> int"
        )

    def test_nested_pass_through_layers(self):
        # Multiple pass-through layers on top of @with_signature must all
        # propagate the override.
        p1 = self._pass_through()
        p2 = self._pass_through()

        @p1
        @p2
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args, kwargs

        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )
        self.assertEqual(
            fn.__annotations__, {"a": int, "b": str, "return": bool}
        )
        self.assertEqual(fn(1, "y"), ((1, "y"), {}))


class TestMarkerStacking(unittest.TestCase):
    """Verify ``with_signature`` composes cleanly with the calling-convention
    markers ``mark_as_sync`` and ``mark_as_async``.

    These decorators touch disjoint bits of ``co_flags`` --
    ``with_signature`` owns ``CO_VARARGS`` / ``CO_VARKEYWORDS`` (derived
    from the signature), while the markers own the convention bits
    (``CO_COROUTINE``, ``CO_ASYNC_GENERATOR``, ``CO_GENERATOR``,
    ``CO_ITERABLE_COROUTINE``). Stacking one over the other should
    preserve each layer's contribution.
    """

    def test_mark_as_sync_over_with_signature(self):
        @wrapt.mark_as_sync
        @wrapt.with_signature(prototype=_proto)
        async def fn(*args, **kwargs):
            return args[0]

        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )
        self.assertEqual(
            fn.__annotations__, {"a": int, "b": str, "return": bool}
        )
        self.assertFalse(inspect.iscoroutinefunction(fn))

    def test_mark_as_async_over_with_signature(self):
        @wrapt.mark_as_async
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            return args[0]

        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )
        self.assertTrue(inspect.iscoroutinefunction(fn))

    def test_with_signature_over_mark_as_sync(self):
        # Reverse order also works; signature and convention still compose.
        @wrapt.with_signature(prototype=_proto)
        @wrapt.mark_as_sync
        async def fn(*args, **kwargs):
            return args[0]

        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )
        self.assertEqual(
            fn.__annotations__, {"a": int, "b": str, "return": bool}
        )
        self.assertFalse(inspect.iscoroutinefunction(fn))

    def test_mark_as_async_generator_over_with_signature(self):
        # mark_as_async(generator=True) yields async-generator convention
        # while with_signature provides the signature.
        @wrapt.mark_as_async(generator=True)
        @wrapt.with_signature(prototype=_proto)
        def fn(*args, **kwargs):
            yield args[0]

        self.assertTrue(inspect.isasyncgenfunction(fn))
        self.assertFalse(inspect.iscoroutinefunction(fn))
        self.assertEqual(
            str(inspect.signature(fn)), "(a: int, b: str = 'x') -> bool"
        )

    def test_stacking_on_instance_method(self):
        # Convention marker + signature override on a method. The bound
        # view should still have self stripped.
        class C:
            @wrapt.mark_as_sync
            @wrapt.with_signature(prototype=_method_proto)
            async def scale(self, *args, **kwargs):
                return args[0] * 10

        c = C()
        self.assertEqual(
            str(inspect.signature(C.scale)), "(self, value: int) -> int"
        )
        self.assertEqual(
            str(inspect.signature(c.scale)), "(value: int) -> int"
        )
        self.assertFalse(inspect.iscoroutinefunction(C.scale))
        self.assertFalse(inspect.iscoroutinefunction(c.scale))

    def test_varargs_flag_preserved_through_marker(self):
        # Prototype with *args / **kwargs must preserve CO_VARARGS and
        # CO_VARKEYWORDS (owned by with_signature) even after mark_as_sync
        # strips the convention bits on top.
        def proto_with_varargs(*args: int, **kwargs: str) -> None: ...

        @wrapt.mark_as_sync
        @wrapt.with_signature(prototype=proto_with_varargs)
        async def fn(*args, **kwargs): ...

        self.assertTrue(fn.__code__.co_flags & inspect.CO_VARARGS)
        self.assertTrue(fn.__code__.co_flags & inspect.CO_VARKEYWORDS)
        self.assertFalse(inspect.iscoroutinefunction(fn))


if __name__ == "__main__":
    unittest.main()
