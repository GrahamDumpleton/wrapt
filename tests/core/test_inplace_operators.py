import unittest

import wrapt


class CustomObjectProxy1(wrapt.ObjectProxy):
    pass


class CustomObjectProxy2(wrapt.ObjectProxy):
    @property
    def __object_proxy__(self):
        return CustomObjectProxy2


class CustomObjectProxy3(wrapt.ObjectProxy):
    def __object_proxy__(self, wrapped):
        return CustomObjectProxy3(wrapped)


class InplaceOperatorsTests(unittest.TestCase):

    def test_inplace_add_integer(self):
        p1 = wrapt.ObjectProxy(10)
        p2 = p1

        p1 += 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_add_string(self):
        p1 = wrapt.ObjectProxy("Hello ")
        p2 = p1

        p1 += "World"

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, "Hello World")
        self.assertEqual(p2, "Hello ")

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_add_tuple(self):
        p1 = wrapt.ObjectProxy((1, 2, 3))
        p2 = p1

        p1 += (4, 5, 6)

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, (1, 2, 3, 4, 5, 6))
        self.assertEqual(p2, (1, 2, 3))

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_add_list(self):
        p1 = wrapt.ObjectProxy([1, 2, 3])
        p2 = p1

        p1 += [4, 5, 6]

        self.assertIs(p1, p2)
        self.assertEqual(p1, p2)
        self.assertEqual(p1, [1, 2, 3, 4, 5, 6])
        self.assertEqual(p2, [1, 2, 3, 4, 5, 6])

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_add_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(10)
        p2 = p1

        p1 += 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_add_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(10)
        p2 = p1

        p1 += 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_add_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(10)
        p2 = p1

        p1 += 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_add_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(10)
        p2 = p1

        p1 += 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_subtract_integer(self):
        p1 = wrapt.ObjectProxy(10)
        p2 = p1

        p1 -= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_subtract_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(10)
        p2 = p1

        p1 -= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_subtract_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(10)
        p2 = p1

        p1 -= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_subtract_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(10)
        p2 = p1

        p1 -= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_subtract_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(10)
        p2 = p1

        p1 -= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_multiply_integer(self):
        p1 = wrapt.ObjectProxy(10)
        p2 = p1

        p1 *= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 50)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_multiply_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(10)
        p2 = p1

        p1 *= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 50)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_multiply_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(10)
        p2 = p1

        p1 *= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 50)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_multiply_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(10)
        p2 = p1

        p1 *= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 50)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_multiply_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(10)
        p2 = p1

        p1 *= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 50)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_true_divide_integer(self):
        p1 = wrapt.ObjectProxy(10)
        p2 = p1

        p1 /= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 2.0)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_true_divide_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(10)
        p2 = p1

        p1 /= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 2.0)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_true_divide_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(10)
        p2 = p1

        p1 /= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 2.0)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_true_divide_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(10)
        p2 = p1

        p1 /= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 2.0)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_true_divide_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(10)
        p2 = p1

        p1 /= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 2.0)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_floor_divide_integer(self):
        p1 = wrapt.ObjectProxy(10)
        p2 = p1

        p1 //= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 3)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_floor_divide_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(10)
        p2 = p1

        p1 //= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 3)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_floor_divide_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(10)
        p2 = p1

        p1 //= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 3)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_floor_divide_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(10)
        p2 = p1

        p1 //= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 3)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_floor_divide_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(10)
        p2 = p1

        p1 //= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 3)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_remainder_integer(self):
        p1 = wrapt.ObjectProxy(10)
        p2 = p1

        p1 %= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 1)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_remainder_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(10)
        p2 = p1

        p1 %= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 1)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_remainder_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(10)
        p2 = p1

        p1 %= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 1)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_remainder_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(10)
        p2 = p1

        p1 %= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 1)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_remainder_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(10)
        p2 = p1

        p1 %= 3

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 1)
        self.assertEqual(p2, 10)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_power_integer(self):
        p1 = wrapt.ObjectProxy(2)
        p2 = p1

        p1 **= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 32)
        self.assertEqual(p2, 2)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_power_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(2)
        p2 = p1

        p1 **= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 32)
        self.assertEqual(p2, 2)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_power_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(2)
        p2 = p1

        p1 **= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 32)
        self.assertEqual(p2, 2)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_power_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(2)
        p2 = p1

        p1 **= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 32)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_power_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(2)
        p2 = p1

        p1 **= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 32)
        self.assertEqual(p2, 2)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_lshift_integer(self):
        p1 = wrapt.ObjectProxy(2)
        p2 = p1

        p1 <<= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 64)
        self.assertEqual(p2, 2)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_lshift_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(2)
        p2 = p1

        p1 <<= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 64)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_lshift_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(2)
        p2 = p1

        p1 <<= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 64)
        self.assertEqual(p2, 2)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_lshift_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(2)
        p2 = p1

        p1 <<= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 64)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_lshift_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(2)
        p2 = p1

        p1 <<= 5

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 64)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_rshift_integer(self):
        p1 = wrapt.ObjectProxy(32)
        p2 = p1

        p1 >>= 2

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 8)
        self.assertEqual(p2, 32)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_rshift_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(32)
        p2 = p1

        p1 >>= 2

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 8)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_rshift_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(32)
        p2 = p1

        p1 >>= 2

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 8)
        self.assertEqual(p2, 32)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_rshift_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(32)
        p2 = p1

        p1 >>= 2

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 8)
        self.assertEqual(p2, 32)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_rshift_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(32)
        p2 = p1

        p1 >>= 2

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 8)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_and_integer(self):
        p1 = wrapt.ObjectProxy(13)
        p2 = p1

        p1 &= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_and_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(13)
        p2 = p1

        p1 &= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_and_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(13)
        p2 = p1

        p1 &= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_and_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(13)
        p2 = p1

        p1 &= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_and_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(13)
        p2 = p1

        p1 &= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 5)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_xor_integer(self):
        p1 = wrapt.ObjectProxy(13)
        p2 = p1

        p1 ^= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 10)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_xor_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(13)
        p2 = p1

        p1 ^= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 10)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_xor_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(13)
        p2 = p1

        p1 ^= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 10)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_xor_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(13)
        p2 = p1

        p1 ^= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 10)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_xor_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(13)
        p2 = p1

        p1 ^= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 10)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_or_integer(self):
        p1 = wrapt.ObjectProxy(13)
        p2 = p1

        p1 |= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_or_base_object_proxy(self):
        p1 = wrapt.BaseObjectProxy(13)
        p2 = p1

        p1 |= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.BaseObjectProxy)

    def test_inplace_or_custom_object_proxy1(self):
        p1 = CustomObjectProxy1(13)
        p2 = p1

        p1 |= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), wrapt.ObjectProxy)

    def test_inplace_or_custom_object_proxy2(self):
        p1 = CustomObjectProxy2(13)
        p2 = p1

        p1 |= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), CustomObjectProxy2)

    def test_inplace_or_custom_object_proxy3(self):
        p1 = CustomObjectProxy3(13)
        p2 = p1

        p1 |= 7

        self.assertIsNot(p1, p2)
        self.assertEqual(p1, 15)
        self.assertEqual(p2, 13)

        self.assertEqual(type(p1), CustomObjectProxy3)

    def test_inplace_matmul(self):
        class Matrix:
            def __init__(self, value):
                self.value = value

            def __imatmul__(self, other):
                self.value *= other.value
                return self

            def __repr__(self):
                return f"Matrix({self.value})"

            def __eq__(self, other):
                if isinstance(other, Matrix):
                    return self.value == other.value
                return False

        m1 = Matrix(3)
        m2 = Matrix(4)

        p1 = wrapt.ObjectProxy(m1)
        p2 = p1

        p1 @= m2

        self.assertIs(p1, p2)
        self.assertEqual(p1.value, 12)
        self.assertEqual(p2.value, 12)

        self.assertEqual(type(p1), wrapt.ObjectProxy)
