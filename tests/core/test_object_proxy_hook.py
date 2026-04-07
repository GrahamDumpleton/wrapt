import unittest

import wrapt


class _Sentinel(Exception):
    pass


class BrokenObjectProxy(wrapt.ObjectProxy):
    @property
    def __object_proxy__(self):
        raise _Sentinel("intentional failure from __object_proxy__")


class ImmutableMatrix:
    """Defines __matmul__ but not __imatmul__, so the proxy must construct
    a new instance via __object_proxy__ on @= ."""

    def __init__(self, value):
        self.value = value

    def __matmul__(self, other):
        return ImmutableMatrix(self.value * other.value)


class ObjectProxyHookTests(unittest.TestCase):
    # Each test wraps an immutable value so the corresponding __iXXX__ slot
    # is absent and the C inplace path falls through to the branch that calls
    # PyObject_GetAttrString(self, "__object_proxy__"). Our property raises,
    # GetAttrString returns NULL, and the buggy code (prior to the fix) did
    # Py_DECREF(NULL) -- guaranteed crash. After the fix, the exception
    # propagates cleanly.

    def test_inplace_add_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(10)
        with self.assertRaises(_Sentinel):
            p += 5

    def test_inplace_subtract_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(10)
        with self.assertRaises(_Sentinel):
            p -= 5

    def test_inplace_multiply_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(10)
        with self.assertRaises(_Sentinel):
            p *= 5

    def test_inplace_remainder_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(10)
        with self.assertRaises(_Sentinel):
            p %= 3

    def test_inplace_power_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(2)
        with self.assertRaises(_Sentinel):
            p **= 5

    def test_inplace_lshift_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(2)
        with self.assertRaises(_Sentinel):
            p <<= 5

    def test_inplace_rshift_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(32)
        with self.assertRaises(_Sentinel):
            p >>= 2

    def test_inplace_and_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(13)
        with self.assertRaises(_Sentinel):
            p &= 7

    def test_inplace_xor_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(13)
        with self.assertRaises(_Sentinel):
            p ^= 7

    def test_inplace_or_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(13)
        with self.assertRaises(_Sentinel):
            p |= 7

    def test_inplace_floor_divide_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(10)
        with self.assertRaises(_Sentinel):
            p //= 3

    def test_inplace_true_divide_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(10)
        with self.assertRaises(_Sentinel):
            p /= 5

    def test_inplace_matrix_multiply_propagates_object_proxy_error(self):
        p = BrokenObjectProxy(ImmutableMatrix(3))
        with self.assertRaises(_Sentinel):
            p @= ImmutableMatrix(4)
