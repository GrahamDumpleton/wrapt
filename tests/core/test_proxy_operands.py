"""Tests for binary operators where both operands are an ObjectProxy.

The pure Python implementation of the binary operator dunder methods only
unwraps ``self`` before delegating to the operator on the wrapped object,
whereas the C extension unwraps both operands. In the common case this
difference is hidden, because the wrapped object's own dunder method
returns ``NotImplemented`` when handed a proxy, and the proxy's reflected
dunder method then gets a turn and unwraps the other side.

The difference becomes visible in two situations, both of which only
arise when the right hand operand is also a proxy:

* The wrapped type raises ``TypeError`` for an operand it does not
  recognise, rather than returning ``NotImplemented``. Python treats a
  raised exception as final and never tries the reflected method, so
  the right hand proxy never gets to unwrap itself.

* The right hand operand's type is a subclass of the left hand operand's
  type and overrides the reflected method. Python gives the reflected
  method priority in that case, but only when it sees the real types.
  The left hand proxy running the operator on the wrapped objects
  restores that priority if it unwraps the right hand side first.

Both cases pass with the C extension and are expected to pass with the
pure Python implementation once it also unwraps a proxy on the right
hand side.
"""

import operator
import unittest

import wrapt

# Names of the binary operators, in the form used for the dunder methods.
# All except divmod also have an in-place form.

BINARY_OPERATORS = [
    ("add", operator.add),
    ("sub", operator.sub),
    ("mul", operator.mul),
    ("truediv", operator.truediv),
    ("floordiv", operator.floordiv),
    ("mod", operator.mod),
    ("divmod", divmod),
    ("pow", operator.pow),
    ("lshift", operator.lshift),
    ("rshift", operator.rshift),
    ("and", operator.and_),
    ("xor", operator.xor),
    ("or", operator.or_),
    ("matmul", operator.matmul),
]

INPLACE_OPERATORS = [
    ("add", operator.iadd),
    ("sub", operator.isub),
    ("mul", operator.imul),
    ("truediv", operator.itruediv),
    ("floordiv", operator.ifloordiv),
    ("mod", operator.imod),
    ("pow", operator.ipow),
    ("lshift", operator.ilshift),
    ("rshift", operator.irshift),
    ("and", operator.iand),
    ("xor", operator.ixor),
    ("or", operator.ior),
    ("matmul", operator.imatmul),
]


class Strict:
    """A type which only combines with other instances of itself.

    Every binary operator raises TypeError when given anything other
    than a Strict instance, instead of returning NotImplemented. The
    result records which operator was applied and to what.
    """

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return type(other) is Strict and other.value == self.value

    __hash__ = None

    def __repr__(self):
        return "Strict(%r)" % (self.value,)


class StrictInplace(Strict):
    """As Strict, but also implements the in-place operators, which
    mutate the instance and return it."""

    def __eq__(self, other):
        return type(other) is StrictInplace and other.value == self.value

    __hash__ = None


def _strict_binary(name):
    def method(self, other):
        if type(other) is not type(self):
            raise TypeError(
                "unsupported operand type for %s: %r" % (name, type(other).__name__)
            )
        return type(self)((name, self.value, other.value))

    method.__name__ = "__%s__" % name
    return method


def _strict_inplace(name):
    def method(self, other):
        if type(other) is not type(self):
            raise TypeError(
                "unsupported operand type for i%s: %r" % (name, type(other).__name__)
            )
        self.value = (name, self.value, other.value)
        return self

    method.__name__ = "__i%s__" % name
    return method


for _name, _ in BINARY_OPERATORS:
    setattr(Strict, "__%s__" % _name, _strict_binary(_name))

for _name, _ in INPLACE_OPERATORS:
    setattr(StrictInplace, "__i%s__" % _name, _strict_inplace(_name))


class Base:
    """Accepts any Base instance in its binary operators and returns
    NotImplemented otherwise. The reflected operators are also defined
    so that a subclass can override them."""

    def __repr__(self):
        return "Base()"


class Sub(Base):
    """Overrides only the reflected operators. Python gives these
    priority over the forward operator of a Base instance on the left
    hand side."""

    def __repr__(self):
        return "Sub()"


def _base_forward(name):
    def method(self, other):
        if isinstance(other, Base):
            return "Base.__%s__" % name
        return NotImplemented

    method.__name__ = "__%s__" % name
    return method


def _reflected(cls, name):
    def method(self, other):
        return "%s.__r%s__" % (cls, name)

    method.__name__ = "__r%s__" % name
    return method


for _name, _ in BINARY_OPERATORS:
    setattr(Base, "__%s__" % _name, _base_forward(_name))
    setattr(Base, "__r%s__" % _name, _reflected("Base", _name))
    setattr(Sub, "__r%s__" % _name, _reflected("Sub", _name))


class TestStrictOperandBinary(unittest.TestCase):
    """The wrapped type raises TypeError instead of returning
    NotImplemented, so the operator only succeeds if the proxy on the
    right hand side is unwrapped before the wrapped operator runs."""

    def check(self, name, op):
        expected = op(Strict(1), Strict(2))

        self.assertEqual(expected, Strict((name, 1, 2)))

        # A proxy on the left only has always worked.

        self.assertEqual(op(wrapt.ObjectProxy(Strict(1)), Strict(2)), expected)

        # A proxy on both sides requires the left hand proxy to unwrap
        # the right hand one, since Strict never returns NotImplemented
        # and so the right hand proxy's reflected method never runs.

        self.assertEqual(
            op(wrapt.ObjectProxy(Strict(1)), wrapt.ObjectProxy(Strict(2))),
            expected,
        )

    def test_add(self):
        self.check("add", operator.add)

    def test_sub(self):
        self.check("sub", operator.sub)

    def test_mul(self):
        self.check("mul", operator.mul)

    def test_truediv(self):
        self.check("truediv", operator.truediv)

    def test_floordiv(self):
        self.check("floordiv", operator.floordiv)

    def test_mod(self):
        self.check("mod", operator.mod)

    def test_divmod(self):
        self.check("divmod", divmod)

    def test_pow(self):
        self.check("pow", operator.pow)

    def test_lshift(self):
        self.check("lshift", operator.lshift)

    def test_rshift(self):
        self.check("rshift", operator.rshift)

    def test_and(self):
        self.check("and", operator.and_)

    def test_xor(self):
        self.check("xor", operator.xor)

    def test_or(self):
        self.check("or", operator.or_)

    def test_matmul(self):
        self.check("matmul", operator.matmul)


class TestStrictOperandInplace(unittest.TestCase):
    """In-place operators with a proxy on both sides. Covers both the
    case where the wrapped type implements the in-place dunder method
    and the proxy is updated in place, and the case where it does not
    and the proxy falls back to the binary operator and wraps the
    result in a new proxy."""

    def check(self, name, iop):
        # Wrapped type implements the in-place operator. The same proxy
        # is returned and the wrapped object mutated in place.

        expected = StrictInplace(1)
        iop(expected, StrictInplace(2))

        self.assertEqual(expected, StrictInplace((name, 1, 2)))

        value = StrictInplace(1)
        proxy = wrapt.ObjectProxy(value)

        result = iop(proxy, wrapt.ObjectProxy(StrictInplace(2)))

        self.assertIs(result, proxy)
        self.assertIs(result.__wrapped__, value)
        self.assertEqual(value, expected)

        # Wrapped type only implements the binary operator. A new proxy
        # is returned wrapping the result.

        expected = Strict(1)
        expected = iop(expected, Strict(2))

        self.assertEqual(expected, Strict((name, 1, 2)))

        value = Strict(1)
        proxy = wrapt.ObjectProxy(value)

        result = iop(proxy, wrapt.ObjectProxy(Strict(2)))

        self.assertIsNot(result, proxy)
        self.assertIsInstance(result, wrapt.ObjectProxy)
        self.assertEqual(result.__wrapped__, expected)
        self.assertEqual(value, Strict(1))

    def test_iadd(self):
        self.check("add", operator.iadd)

    def test_isub(self):
        self.check("sub", operator.isub)

    def test_imul(self):
        self.check("mul", operator.imul)

    def test_itruediv(self):
        self.check("truediv", operator.itruediv)

    def test_ifloordiv(self):
        self.check("floordiv", operator.ifloordiv)

    def test_imod(self):
        self.check("mod", operator.imod)

    def test_ipow(self):
        self.check("pow", operator.ipow)

    def test_ilshift(self):
        self.check("lshift", operator.ilshift)

    def test_irshift(self):
        self.check("rshift", operator.irshift)

    def test_iand(self):
        self.check("and", operator.iand)

    def test_ixor(self):
        self.check("xor", operator.ixor)

    def test_ior(self):
        self.check("or", operator.ior)

    def test_imatmul(self):
        self.check("matmul", operator.imatmul)


class TestSubclassReflectedPriority(unittest.TestCase):
    """When the right hand operand's type is a subclass of the left hand
    operand's type and overrides the reflected method, Python calls the
    reflected method first. With a proxy on both sides, Python only
    sees the proxy types, so the left hand proxy must unwrap the right
    hand operand for the wrapped objects to be dispatched correctly."""

    def check(self, name, op):
        expected = "Sub.__r%s__" % name

        self.assertEqual(op(Base(), Sub()), expected)

        # A proxy on the left only has always worked, as Python sees
        # Sub on the right and gives its reflected method priority.

        self.assertEqual(op(wrapt.ObjectProxy(Base()), Sub()), expected)

        # A proxy on both sides. Python sees two proxies and calls the
        # left hand proxy's forward method. That must then apply the
        # operator to the two wrapped objects for Python to see that
        # Sub is a subclass of Base and prefer Sub's reflected method.
        # Without unwrapping, Base sees the proxy as a Base instance via
        # isinstance() and handles it itself.

        self.assertEqual(
            op(wrapt.ObjectProxy(Base()), wrapt.ObjectProxy(Sub())),
            expected,
        )

    def test_add(self):
        self.check("add", operator.add)

    def test_sub(self):
        self.check("sub", operator.sub)

    def test_mul(self):
        self.check("mul", operator.mul)

    def test_truediv(self):
        self.check("truediv", operator.truediv)

    def test_floordiv(self):
        self.check("floordiv", operator.floordiv)

    def test_mod(self):
        self.check("mod", operator.mod)

    def test_divmod(self):
        self.check("divmod", divmod)

    def test_pow(self):
        self.check("pow", operator.pow)

    def test_lshift(self):
        self.check("lshift", operator.lshift)

    def test_rshift(self):
        self.check("rshift", operator.rshift)

    def test_and(self):
        self.check("and", operator.and_)

    def test_xor(self):
        self.check("xor", operator.xor)

    def test_or(self):
        self.check("or", operator.or_)

    def test_matmul(self):
        self.check("matmul", operator.matmul)


if __name__ == "__main__":
    unittest.main()
