import functools
import unittest

import wrapt


def function(*args, **kwargs):
    return args, kwargs


def wrapper(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


class ClassWithAttribute:
    def __init__(self, value):
        self.value = value


def build_chain(depth):
    result = function
    for _ in range(depth):
        result = wrapt.ObjectProxy(result)
    return result


class TestWrapperChain(unittest.TestCase):

    def test_unwrapped_object(self):
        # An object which is not wrapped yields just itself.

        self.assertEqual(list(wrapt.wrapper_chain(function)), [function])

    def test_function_wrapper_stack(self):
        inner = wrapt.FunctionWrapper(function, wrapper)
        outer = wrapt.FunctionWrapper(inner, wrapper)

        chain = list(wrapt.wrapper_chain(outer))

        # Outermost wrapper first, and the final item is the innermost
        # object, which is not itself a wrapper.

        self.assertEqual(len(chain), 3)
        self.assertIs(chain[0], outer)
        self.assertIs(chain[1], inner)
        self.assertIs(chain[2], function)

        # Traversal does not disturb the wrappers; calling still works.

        self.assertEqual(outer(1, one=1), ((1,), {"one": 1}))

    def test_functools_wraps_interop(self):
        # The chain protocol is shared with anything honouring the
        # __wrapped__ convention, such as functools.wraps.

        @functools.wraps(function)
        def decorated(*args, **kwargs):
            return function(*args, **kwargs)

        chain = list(wrapt.wrapper_chain(decorated))

        self.assertEqual(len(chain), 2)
        self.assertIs(chain[0], decorated)
        self.assertIs(chain[1], function)

    def test_attribute_wrapper_missing_terminal(self):
        # An AttributeWrapper installed where no prior definition
        # existed yields the MISSING sentinel as the chain terminal.

        handle = wrapt.wrap_object_attribute(
            __name__, "ClassWithAttribute.value", wrapt.ObjectProxy
        )

        chain = list(wrapt.wrapper_chain(handle))

        self.assertEqual(len(chain), 2)
        self.assertIs(chain[0], handle)
        self.assertIs(chain[1], wrapt.MISSING)

    def test_cycle_terminates(self):
        # A cyclic chain built from plain functions terminates cleanly
        # once an object already seen comes around again.

        def function1():
            pass

        def function2():
            pass

        function1.__wrapped__ = function2
        function2.__wrapped__ = function1

        chain = list(wrapt.wrapper_chain(function1))

        self.assertEqual(len(chain), 2)
        self.assertIs(chain[0], function1)
        self.assertIs(chain[1], function2)

    def test_deep_chain_raises(self):
        # A chain deeper than the limit raises rather than silently
        # truncating, since a truncated scan would be indistinguishable
        # from a complete one.

        deep = build_chain(200)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            list(wrapt.wrapper_chain(deep))

        with self.assertRaises(RuntimeError):
            list(wrapt.wrapper_chain(deep))

    def test_chain_of_exactly_limit(self):
        # A chain of exactly the limit in length which ends naturally
        # is a complete scan, not an error.

        exact = build_chain(63)

        chain = list(wrapt.wrapper_chain(exact))

        self.assertEqual(len(chain), 64)
        self.assertIs(chain[-1], function)

        over = build_chain(64)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            list(wrapt.wrapper_chain(over))

    def test_custom_limit(self):
        exact = build_chain(2)

        self.assertEqual(len(list(wrapt.wrapper_chain(exact, limit=3))), 3)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            list(wrapt.wrapper_chain(exact, limit=2))

    def test_generative_chain_raises(self):
        # A __wrapped__ implemented as a property manufacturing a fresh
        # object on every read defeats identity based cycle detection,
        # so the limit is what terminates the scan, loudly.

        class Generative:
            @property
            def __wrapped__(self):
                return Generative()

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            list(wrapt.wrapper_chain(Generative()))

    def test_lazy_proxy_materializes(self):
        # Reading __wrapped__ from a lazy object proxy materializes it,
        # with the factory fired only once, and the chain continues into
        # the materialized object.

        called = []

        def factory():
            called.append(True)
            return function

        proxy = wrapt.LazyObjectProxy(factory)

        chain = list(wrapt.wrapper_chain(proxy))

        self.assertEqual(len(chain), 2)
        self.assertIs(chain[0], proxy)
        self.assertIs(chain[1], function)
        self.assertEqual(len(called), 1)

        list(wrapt.wrapper_chain(proxy))

        self.assertEqual(len(called), 1)

    def test_broken_proxy_error_propagates(self):
        # A proxy in an inconsistent state, where __init__ was called
        # but __wrapped__ was never set, raises
        # WrapperNotInitializedError which must propagate rather than
        # being swallowed as the natural end of the chain. The state is
        # reached by removing the lazy factory before __wrapped__ is
        # accessed, restoring the class attribute afterwards for the
        # benefit of later tests.

        proxy = wrapt.LazyObjectProxy(lambda: 42)

        del proxy.__wrapped_factory__

        restore = []
        for cls in type(proxy).__mro__:
            if "__wrapped_factory__" in cls.__dict__:
                restore.append((cls, cls.__dict__["__wrapped_factory__"]))
                delattr(cls, "__wrapped_factory__")
                break

        try:
            with self.assertRaises(wrapt.WrapperNotInitializedError):
                list(wrapt.wrapper_chain(proxy))
        finally:
            for cls, attr in restore:
                setattr(cls, "__wrapped_factory__", attr)

    def test_lazy_factory_error_propagates(self):
        def factory():
            raise ZeroDivisionError("broken factory")

        proxy = wrapt.LazyObjectProxy(factory)

        with self.assertRaises(ZeroDivisionError):
            list(wrapt.wrapper_chain(proxy))


class TestUnwrapped(unittest.TestCase):

    def test_unwrapped_object(self):
        self.assertIs(wrapt.unwrapped(function), function)

    def test_wrapper_stack(self):
        inner = wrapt.FunctionWrapper(function, wrapper)
        outer = wrapt.FunctionWrapper(inner, wrapper)

        self.assertIs(wrapt.unwrapped(outer), function)

    def test_lazy_proxy(self):
        proxy = wrapt.LazyObjectProxy(lambda: function)

        self.assertIs(wrapt.unwrapped(proxy), function)

    def test_deep_chain_raises(self):
        # An indeterminate scan raises rather than returning a mid
        # chain wrapper as if it were the innermost object.

        deep = build_chain(200)

        with self.assertRaises(wrapt.WrapperChainTooDeepError):
            wrapt.unwrapped(deep)

    def test_custom_limit(self):
        deep = build_chain(200)

        self.assertIs(wrapt.unwrapped(deep, limit=201), function)
