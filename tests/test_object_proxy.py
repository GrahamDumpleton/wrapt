from __future__ import print_function

import unittest
import imp
import operator
import sys

is_pypy = '__pypy__' in sys.builtin_module_names

import wrapt

from compat import PY2, PY3, exec_

OBJECTS_CODE = """
class TargetBaseClass(object):
    "documentation"

class Target(TargetBaseClass):
    "documentation"

def target():
    "documentation"
    pass
"""

objects = imp.new_module('objects')
exec_(OBJECTS_CODE, objects.__dict__, objects.__dict__)

class TestAttributeAccess(unittest.TestCase):

    def test_init_not_called(self):
        a = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        b = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            a.__wrapped__
        except ValueError:
            pass

        try:
            a + b
        except ValueError:
            pass

    def test_attributes(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        self.assertEqual(function2.__wrapped__, function1)

    def test_get_wrapped(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        self.assertEqual(function2.__wrapped__, function1)

        function3 = wrapt.ObjectProxy(function2)

        self.assertEqual(function3.__wrapped__, function1)

    def test_set_wrapped(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        self.assertEqual(function2, function1)
        self.assertEqual(function2.__wrapped__, function1)
        self.assertEqual(function2.__name__, function1.__name__)

        if PY3:
            self.assertEqual(function2.__qualname__, function1.__qualname__)

        function2.__wrapped__ = None

        self.assertFalse(hasattr(function1, '__wrapped__'))

        self.assertEqual(function2, None)
        self.assertEqual(function2.__wrapped__, None)
        self.assertFalse(hasattr(function2, '__name__'))

        if PY3:
            self.assertFalse(hasattr(function2, '__qualname__'))

        def function3(*args, **kwargs):
            return args, kwargs

        function2.__wrapped__ = function3

        self.assertEqual(function2, function3)
        self.assertEqual(function2.__wrapped__, function3)
        self.assertEqual(function2.__name__, function3.__name__)

        if PY3:
            self.assertEqual(function2.__qualname__, function3.__qualname__)

    def test_delete_wrapped(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        def run(*args):
            del function2.__wrapped__

        self.assertRaises(TypeError, run, ())

    def test_proxy_attribute(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        function2._self_variable = True

        self.assertFalse(hasattr(function1, '_self_variable'))
        self.assertTrue(hasattr(function2, '_self_variable'))

        self.assertEqual(function2._self_variable, True)

        del function2._self_variable

        self.assertFalse(hasattr(function1, '_self_variable'))
        self.assertFalse(hasattr(function2, '_self_variable'))

        self.assertEqual(getattr(function2, '_self_variable', None), None)

    def test_wrapped_attribute(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        function2.variable = True

        self.assertTrue(hasattr(function1, 'variable'))
        self.assertTrue(hasattr(function2, 'variable'))

        self.assertEqual(function2.variable, True)

        del function2.variable

        self.assertFalse(hasattr(function1, 'variable'))
        self.assertFalse(hasattr(function2, 'variable'))

        self.assertEqual(getattr(function2, 'variable', None), None)

class TestNamingObjectProxy(unittest.TestCase):

    def test_class_object_name(self):
        # Test preservation of class __name__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__name__, target.__name__)

    def test_class_object_qualname(self):
        # Test preservation of class __qualname__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        try:
            __qualname__ = target.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(wrapper.__qualname__, __qualname__)

    def test_class_module_name(self):
        # Test preservation of class __module__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__module__, target.__module__)

    def test_class_doc_string(self):
        # Test preservation of class __doc__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_instance_module_name(self):
        # Test preservation of instance __module__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__module__, target.__module__)

    def test_instance_doc_string(self):
        # Test preservation of instance __doc__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__doc__, target.__doc__)

    def test_function_object_name(self):
        # Test preservation of function __name__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__name__, target.__name__)

    def test_function_object_qualname(self):
        # Test preservation of function __qualname__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        try:
            __qualname__ = target.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(wrapper.__qualname__, __qualname__)

    def test_function_module_name(self):
        # Test preservation of function __module__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__module__, target.__module__)

    def test_function_doc_string(self):
        # Test preservation of function __doc__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__doc__, target.__doc__)

class TestTypeObjectProxy(unittest.TestCase):

    def test_class_of_class(self):
        # Test preservation of class __class__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__class__, target.__class__)

        self.assertTrue(isinstance(wrapper, type(target)))

    def test_class_of_instance(self):
        # Test preservation of instance __class__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__class__, target.__class__)

        self.assertTrue(isinstance(wrapper, objects.Target))
        self.assertTrue(isinstance(wrapper, objects.TargetBaseClass))

    def test_class_of_function(self):
        # Test preservation of function __class__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(wrapper.__class__, target.__class__)

        self.assertTrue(isinstance(wrapper, type(target)))

class TestDirObjectProxy(unittest.TestCase):

    def test_dir_of_class(self):
        # Test preservation of class __dir__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(dir(wrapper), dir(target))

    def test_vars_of_class(self):
        # Test preservation of class __dir__ attribute.

        target = objects.Target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(vars(wrapper), vars(target))

    def test_dir_of_instance(self):
        # Test preservation of instance __dir__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(dir(wrapper), dir(target))

    def test_vars_of_instance(self):
        # Test preservation of instance __dir__ attribute.

        target = objects.Target()
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(vars(wrapper), vars(target))

    def test_dir_of_function(self):
        # Test preservation of function __dir__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(dir(wrapper), dir(target))

    def test_vars_of_function(self):
        # Test preservation of function __dir__ attribute.

        target = objects.target
        wrapper = wrapt.ObjectProxy(target)

        self.assertEqual(vars(wrapper), vars(target))

class TestCallingObject(unittest.TestCase):

    def test_function_no_args(self):
        _args = ()
        _kwargs = {}

        def function(*args, **kwargs):
            return args, kwargs

        wrapper = wrapt.CallableObjectProxy(function)

        result = wrapper()

        self.assertEqual(result, (_args, _kwargs))

    def test_function_args(self):
        _args = (1, 2)
        _kwargs = {}

        def function(*args, **kwargs):
            return args, kwargs

        wrapper = wrapt.CallableObjectProxy(function)

        result = wrapper(*_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_function_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        def function(*args, **kwargs):
            return args, kwargs

        wrapper = wrapt.CallableObjectProxy(function)

        result = wrapper(**_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_function_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        def function(*args, **kwargs):
            return args, kwargs

        wrapper = wrapt.CallableObjectProxy(function)

        result = wrapper(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_no_args(self):
        _args = ()
        _kwargs = {}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper()

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_args(self):
        _args = (1, 2)
        _kwargs = {}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(*_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(**_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_via_class_no_args(self):
        _args = ()
        _kwargs = {}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(Class())

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_via_class_args(self):
        _args = (1, 2)
        _kwargs = {}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(Class(), *_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_via_class_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(Class(), **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instancemethod_via_class_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            def function(self, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(Class(), *_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_no_args(self):
        _args = ()
        _kwargs = {}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper()

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_args(self):
        _args = (1, 2)
        _kwargs = {}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(*_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(**_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_via_class_no_args(self):
        _args = ()
        _kwargs = {}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper()

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_via_class_args(self):
        _args = (1, 2)
        _kwargs = {}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(*_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_via_class_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(**_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_classmethod_via_class_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_no_args(self):
        _args = ()
        _kwargs = {}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper()

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_args(self):
        _args = (1, 2)
        _kwargs = {}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(*_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(**_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class().function)

        result = wrapper(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_via_class_no_args(self):
        _args = ()
        _kwargs = {}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper()

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_via_class_args(self):
        _args = (1, 2)
        _kwargs = {}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(*_args)

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_via_class_kwargs(self):
        _args = ()
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(**_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_staticmethod_via_class_args_plus_kwargs(self):
        _args = (1, 2)
        _kwargs = {"one": 1, "two": 2}

        class Class(object):
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

        wrapper = wrapt.CallableObjectProxy(Class.function)

        result = wrapper(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

class TestIterObjectProxy(unittest.TestCase):

    def test_iteration(self):
        items = [1, 2]

        wrapper = wrapt.ObjectProxy(items)

        result = [x for x in wrapper]

        self.assertEqual(result, items)

class TestContextManagerObjectProxy(unittest.TestCase):

    def test_context_manager(self):
        class Class(object):
            def __enter__(self):
                return self
            def __exit__(*args, **kwargs):
                return

        instance = Class()

        wrapper = wrapt.ObjectProxy(instance)

        with wrapper:
            pass

class TestEqualityObjectProxy(unittest.TestCase):

    def test_object_hash(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        self.assertEqual(hash(function2), hash(function1))

    def test_mapping_key(self):
        def function1(*args, **kwargs):
            return args, kwargs
        function2 = wrapt.ObjectProxy(function1)

        table = dict()
        table[function1] = True

        self.assertTrue(table.get(function2))

        table = dict()
        table[function2] = True

        self.assertTrue(table.get(function1))

    def test_comparison(self):
        one = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertTrue(two > 1)
        self.assertTrue(two >= 1)
        self.assertTrue(two < 3)
        self.assertTrue(two <= 3)
        self.assertTrue(two != 1)
        self.assertTrue(two == 2)
        self.assertTrue(two != 3)

        self.assertTrue(2 > one)
        self.assertTrue(2 >= one)
        self.assertTrue(2 < three)
        self.assertTrue(2 <= three)
        self.assertTrue(2 != one)
        self.assertTrue(2 == two)
        self.assertTrue(2 != three)

        self.assertTrue(two > one)
        self.assertTrue(two >= one)
        self.assertTrue(two < three)
        self.assertTrue(two <= three)
        self.assertTrue(two != one)
        self.assertTrue(two == two)
        self.assertTrue(two != three)

class TestAsNumberObjectProxy(unittest.TestCase):

    def test_nonzero(self):
        true = wrapt.ObjectProxy(True)
        false = wrapt.ObjectProxy(False)

        self.assertTrue(true)
        self.assertFalse(false)

        self.assertTrue(bool(true))
        self.assertFalse(bool(false))

        self.assertTrue(not false)
        self.assertFalse(not true)

    def test_int(self):
        one = wrapt.ObjectProxy(1)

        self.assertEqual(int(one), 1)

        if not PY3:
            self.assertEqual(long(one), 1)

    def test_float(self):
        one = wrapt.ObjectProxy(1)

        self.assertEqual(float(one), 1.0)

    def test_add(self):
        one = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy(2)

        self.assertEqual(one+two, 1+2)
        self.assertEqual(1+two, 1+2)
        self.assertEqual(one+2, 1+2)

    def test_add_uninitialized_args(self):
        result = object()

        one = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        two = wrapt.ObjectProxy(2)

        try:
            assert one + two == result
        except ValueError:
            pass

        one = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert one + two == result
        except ValueError:
            pass

    def test_sub(self):
        one = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy(2)

        self.assertEqual(one-two, 1-2)
        self.assertEqual(1-two, 1-2)
        self.assertEqual(one-2, 1-2)

    def test_sub_uninitialized_args(self):
        result = object()

        one = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        two = wrapt.ObjectProxy(2)

        try:
            assert one - two == result
        except ValueError:
            pass

        one = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert one - two == result
        except ValueError:
            pass

    def test_mul(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(two*three, 2*3)
        self.assertEqual(2*three, 2*3)
        self.assertEqual(two*3, 2*3)

    def test_mul_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert two * three == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert two * three == result
        except ValueError:
            pass

    def test_div(self):
        # On Python 2 this will pick up div and on Python
        # 3 it will pick up truediv.

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(two/three, 2/3)
        self.assertEqual(2/three, 2/3)
        self.assertEqual(two/3, 2/3)

    def test_div_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert two / three == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert two / three == result
        except ValueError:
            pass

    def test_floordiv(self):
        two = wrapt.ObjectProxy(2)
        four = wrapt.ObjectProxy(4)

        self.assertEqual(four//two, 4//2)
        self.assertEqual(4//two, 4//2)
        self.assertEqual(four//2, 4//2)

    def test_floordiv_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        four = wrapt.ObjectProxy(4)

        try:
            assert two // four == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        four = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert two // four == result
        except ValueError:
            pass

    def test_mod(self):
        two = wrapt.ObjectProxy(2)
        four = wrapt.ObjectProxy(4)

        self.assertEqual(four % two, 4 % 2)
        self.assertEqual(4 % two, 4 % 2)
        self.assertEqual(four % 2, 4 % 2)

    def test_mod_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        four = wrapt.ObjectProxy(4)

        try:
            assert two % four == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        four = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert two % four == result
        except ValueError:
            pass

    def test_divmod(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(divmod(three, two), divmod(3, 2))
        self.assertEqual(divmod(3, two), divmod(3, 2))
        self.assertEqual(divmod(three, 2), divmod(3, 2))

    def test_divmod_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert divmod(two, three) == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert divmod(two, three) == result
        except ValueError:
            pass

    def test_pow(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(three**two, pow(3, 2))
        self.assertEqual(3**two, pow(3, 2))
        self.assertEqual(three**2, pow(3, 2))

        self.assertEqual(pow(three, two), pow(3, 2))
        self.assertEqual(pow(3, two), pow(3, 2))
        self.assertEqual(pow(three, 2), pow(3, 2))

        # Only PyPy implements __rpow__ for ternary pow().

        if is_pypy:
            self.assertEqual(pow(three, two, 2), pow(3, 2, 2))
            self.assertEqual(pow(3, two, 2), pow(3, 2, 2))

        self.assertEqual(pow(three, 2, 2), pow(3, 2, 2))

    def test_pow_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert three**two == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert three**two == result
        except ValueError:
            pass

    def test_lshift(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(three << two, 3 << 2)
        self.assertEqual(3 << two, 3 << 2)
        self.assertEqual(three << 2, 3 << 2)

    def test_lshift_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert three << two == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert three << two == result
        except ValueError:
            pass

    def test_rshift(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(three >> two, 3 >> 2)
        self.assertEqual(3 >> two, 3 >> 2)
        self.assertEqual(three >> 2, 3 >> 2)

    def test_rshift_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert three >> two == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert three >> two == result
        except ValueError:
            pass

    def test_and(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(three & two, 3 & 2)
        self.assertEqual(3 & two, 3 & 2)
        self.assertEqual(three & 2, 3 & 2)

    def test_and_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert three & two == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert three & two == result
        except ValueError:
            pass

    def test_xor(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(three ^ two, 3 ^ 2)
        self.assertEqual(3 ^ two, 3 ^ 2)
        self.assertEqual(three ^ 2, 3 ^ 2)

    def test_xor_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert three ^ two == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert three ^ two == result
        except ValueError:
            pass

    def test_or(self):
        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy(3)

        self.assertEqual(three | two, 3 | 2)
        self.assertEqual(3 | two, 3 | 2)
        self.assertEqual(three | 2, 3 | 2)

    def test_or_uninitialized_args(self):
        result = object()

        two = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)
        three = wrapt.ObjectProxy(3)

        try:
            assert three | two == result
        except ValueError:
            pass

        two = wrapt.ObjectProxy(2)
        three = wrapt.ObjectProxy.__new__(wrapt.ObjectProxy)

        try:
            assert three | two == result
        except ValueError:
            pass

    def test_iadd(self):
        value = wrapt.ObjectProxy(1)
        one = wrapt.ObjectProxy(1)

        value += 1
        self.assertEqual(value, 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value += one
        self.assertEqual(value, 3)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_isub(self):
        value = wrapt.ObjectProxy(1)
        one = wrapt.ObjectProxy(1)

        value -= 1
        self.assertEqual(value, 0)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value -= one
        self.assertEqual(value, -1)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_imul(self):
        value = wrapt.ObjectProxy(2)
        two = wrapt.ObjectProxy(2)

        value *= 2
        self.assertEqual(value, 4)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value *= two
        self.assertEqual(value, 8)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_idiv(self):
        # On Python 2 this will pick up div and on Python
        # 3 it will pick up truediv.

        value = wrapt.ObjectProxy(2)
        two = wrapt.ObjectProxy(2)

        value /= 2
        self.assertEqual(value, 2/2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value /= two
        self.assertEqual(value, 2/2/2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_ifloordiv(self):
        value = wrapt.ObjectProxy(2)
        two = wrapt.ObjectProxy(2)

        value //= 2
        self.assertEqual(value, 2//2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value //= two
        self.assertEqual(value, 2//2//2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_imod(self):
        value = wrapt.ObjectProxy(10)
        two = wrapt.ObjectProxy(2)

        value %= 2
        self.assertEqual(value, 10 % 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value %= two
        self.assertEqual(value, 10 % 2 % 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_ipow(self):
        value = wrapt.ObjectProxy(10)
        two = wrapt.ObjectProxy(2)

        value **= 2
        self.assertEqual(value, 10**2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value **= two
        self.assertEqual(value, 10**2**2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_ilshift(self):
        value = wrapt.ObjectProxy(256)
        two = wrapt.ObjectProxy(2)

        value <<= 2
        self.assertEqual(value, 256 << 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value <<= two
        self.assertEqual(value, 256 << 2 << 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_irshift(self):
        value = wrapt.ObjectProxy(2)
        two = wrapt.ObjectProxy(2)

        value >>= 2
        self.assertEqual(value, 2 >> 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value >>= two
        self.assertEqual(value, 2 >> 2 >> 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_iand(self):
        value = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy(2)

        value &= 2
        self.assertEqual(value, 1 & 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value &= two
        self.assertEqual(value, 1 & 2 & 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_ixor(self):
        value = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy(2)

        value ^= 2
        self.assertEqual(value, 1 ^ 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value ^= two
        self.assertEqual(value, 1 ^ 2 ^ 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_ior(self):
        value = wrapt.ObjectProxy(1)
        two = wrapt.ObjectProxy(2)

        value |= 2
        self.assertEqual(value, 1 | 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

        value |= two
        self.assertEqual(value, 1 | 2 | 2)

        self.assertEqual(type(value), wrapt.ObjectProxy)

    def test_ior_list_self(self):
        value = wrapt.ObjectProxy([])

        try:
            value |= value
        except TypeError:
            pass

    def test_neg(self):
        value = wrapt.ObjectProxy(1)

        self.assertEqual(-value, -1)

    def test_pos(self):
        value = wrapt.ObjectProxy(1)

        self.assertEqual(+value, 1)

    def test_abs(self):
        value = wrapt.ObjectProxy(-1)

        self.assertEqual(abs(value), 1)

    def test_invert(self):
        value = wrapt.ObjectProxy(1)

        self.assertEqual(~value, ~1)

    def test_oct(self):
        value = wrapt.ObjectProxy(20)

        self.assertEqual(oct(value), oct(20))

    def test_hex(self):
        value = wrapt.ObjectProxy(20)

        self.assertEqual(hex(value), hex(20))

    def test_index(self):
        class Class(object):
            def __index__(self):
                return 1
        value = wrapt.ObjectProxy(Class())
        items = [0, 1, 2]

        self.assertEqual(items[value], items[1])

class TestAsSequenceObjectProxy(unittest.TestCase):

    def test_length(self):
        value = wrapt.ObjectProxy(list(range(3)))

        self.assertEqual(len(value), 3)

    def test_contains(self):
        value = wrapt.ObjectProxy(list(range(3)))

        self.assertTrue(2 in value)
        self.assertFalse(-2 in value)

    def test_getitem(self):
        value = wrapt.ObjectProxy(list(range(3)))

        self.assertEqual(value[1], 1)

    def test_setitem(self):
        value = wrapt.ObjectProxy(list(range(3)))
        value[1] = -1

        self.assertEqual(value[1], -1)

    def test_delitem(self):
        value = wrapt.ObjectProxy(list(range(3)))

        self.assertEqual(len(value), 3)

        del value[1]

        self.assertEqual(len(value), 2)
        self.assertEqual(value[1], 2)

    def test_getslice(self):
        value = wrapt.ObjectProxy(list(range(5)))

        self.assertEqual(value[1:4], [1, 2, 3])

    def test_setslice(self):
        value = wrapt.ObjectProxy(list(range(5)))

        value[1:4] = reversed(value[1:4])

        self.assertEqual(value[1:4], [3, 2, 1])

    def test_delslice(self):
        value = wrapt.ObjectProxy(list(range(5)))

        del value[1:4]

        self.assertEqual(len(value), 2)
        self.assertEqual(value, [0, 4])

class TestAsMappingObjectProxy(unittest.TestCase):

    def test_length(self):
        value = wrapt.ObjectProxy(dict.fromkeys(range(3), False))

        self.assertEqual(len(value), 3)

    def test_contains(self):
        value = wrapt.ObjectProxy(dict.fromkeys(range(3), False))

        self.assertTrue(2 in value)
        self.assertFalse(-2 in value)

    def test_getitem(self):
        value = wrapt.ObjectProxy(dict.fromkeys(range(3), False))

        self.assertEqual(value[1], False)

    def test_setitem(self):
        value = wrapt.ObjectProxy(dict.fromkeys(range(3), False))
        value[1] = True

        self.assertEqual(value[1], True)

    def test_delitem(self):
        value = wrapt.ObjectProxy(dict.fromkeys(range(3), False))

        self.assertEqual(len(value), 3)

        del value[1]

        self.assertEqual(len(value), 2)

class TestObjectRepresentationObjectProxy(unittest.TestCase):

    def test_str(self):
        value = wrapt.ObjectProxy(10)

        self.assertEqual(str(value), str(10))

        value = wrapt.ObjectProxy((10,))

        self.assertEqual(str(value), str((10,)))

        value = wrapt.ObjectProxy([10])

        self.assertEqual(str(value), str([10]))

        value = wrapt.ObjectProxy({10: 10})

        self.assertEqual(str(value), str({10: 10}))

    def test_repr(self):
        number = 10
        value = wrapt.ObjectProxy(number)

        self.assertNotEqual(repr(value).find('ObjectProxy at'), -1)

class TestDerivedClassCreation(unittest.TestCase):

    def test_derived_new(self):

        class DerivedObjectProxy(wrapt.ObjectProxy):

            def __new__(cls, wrapped):
                instance = super(DerivedObjectProxy, cls).__new__(cls)
                instance.__init__(wrapped)

            def __init__(self, wrapped):
                super(DerivedObjectProxy, self).__init__(wrapped)

        def function():
            pass

        obj = DerivedObjectProxy(function)

    def test_derived_setattr(self):

        class DerivedObjectProxy(wrapt.ObjectProxy):

            def __init__(self, wrapped):
                self._self_attribute = True
                super(DerivedObjectProxy, self).__init__(wrapped)

        def function():
            pass

        obj = DerivedObjectProxy(function)

    def test_derived_missing_init(self):

        class DerivedObjectProxy(wrapt.ObjectProxy):

            def __init__(self, wrapped):
                self.__wrapped__ = wrapped

        def function():
            pass

        obj = DerivedObjectProxy(function)

        self.assertEqual(function, obj)
        self.assertEqual(function, obj.__wrapped__)

class DerivedClassAttributes(unittest.TestCase):

    def test_setup_class_attributes(self):

        def function():
            pass

        class DerivedObjectProxy(wrapt.ObjectProxy):
            pass

        obj = DerivedObjectProxy(function)

        DerivedObjectProxy.ATTRIBUTE = 1

        self.assertEqual(obj.ATTRIBUTE, 1)
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

        del DerivedObjectProxy.ATTRIBUTE

        self.assertFalse(hasattr(DerivedObjectProxy, 'ATTRIBUTE'))
        self.assertFalse(hasattr(obj, 'ATTRIBUTE'))
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

    def test_override_class_attributes(self):

        def function():
            pass

        class DerivedObjectProxy(wrapt.ObjectProxy):
            ATTRIBUTE = 1

        obj = DerivedObjectProxy(function)

        self.assertEqual(DerivedObjectProxy.ATTRIBUTE, 1)
        self.assertEqual(obj.ATTRIBUTE, 1)

        obj.ATTRIBUTE = 2

        self.assertEqual(DerivedObjectProxy.ATTRIBUTE, 1)

        self.assertEqual(obj.ATTRIBUTE, 2)
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

        del DerivedObjectProxy.ATTRIBUTE

        self.assertFalse(hasattr(DerivedObjectProxy, 'ATTRIBUTE'))
        self.assertEqual(obj.ATTRIBUTE, 2)
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

    def test_class_properties(self):

        def function():
            pass

        class DerivedObjectProxy(wrapt.ObjectProxy):
            def __init__(self, wrapped):
                super(DerivedObjectProxy, self).__init__(wrapped)
                self._self_attribute = 1
            @property
            def ATTRIBUTE(self):
                return self._self_attribute
            @ATTRIBUTE.setter
            def ATTRIBUTE(self, value):
                self._self_attribute = value
            @ATTRIBUTE.deleter
            def ATTRIBUTE(self):
                del self._self_attribute

        obj = DerivedObjectProxy(function)

        self.assertEqual(obj.ATTRIBUTE, 1)

        obj.ATTRIBUTE = 2

        self.assertEqual(obj.ATTRIBUTE, 2)
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

        del obj.ATTRIBUTE

        self.assertFalse(hasattr(obj, 'ATTRIBUTE'))
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

        obj.ATTRIBUTE = 1

        self.assertEqual(obj.ATTRIBUTE, 1)

        obj.ATTRIBUTE = 2

        self.assertEqual(obj.ATTRIBUTE, 2)
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

        del obj.ATTRIBUTE

        self.assertFalse(hasattr(obj, 'ATTRIBUTE'))
        self.assertFalse(hasattr(function, 'ATTRIBUTE'))

class OverrideAttributeAccess(unittest.TestCase):

    def test_attr_functions(self):

        def function():
            pass

        proxy = wrapt.ObjectProxy(function)

        self.assertTrue(hasattr(proxy, '__getattr__'))
        self.assertTrue(hasattr(proxy, '__setattr__'))
        self.assertTrue(hasattr(proxy, '__delattr__'))

    def test_override_getattr(self):

        def function():
            pass

        accessed = []

        class DerivedObjectProxy(wrapt.ObjectProxy):
            def __getattr__(self, name):
                accessed.append(name)
                try:
                    __getattr__ = super(DerivedObjectProxy, self).__getattr__
                except AttributeError as e:
                    raise RuntimeError(str(e))
                return __getattr__(name)

        function.attribute = 1

        proxy = DerivedObjectProxy(function)

        self.assertEqual(proxy.attribute, 1)

        self.assertTrue('attribute' in accessed)

class CallableFunction(unittest.TestCase):

    def test_proxy_hasattr_call(self):
        proxy = wrapt.ObjectProxy(None)

        self.assertFalse(hasattr(proxy, '__call__'))

    def test_proxy_getattr_call(self):
        proxy = wrapt.ObjectProxy(None)

        self.assertEqual(getattr(proxy, '__call__', None), None)

    def test_proxy_is_callable(self):
        proxy = wrapt.ObjectProxy(None)

        self.assertFalse(callable(proxy))

    def test_callable_proxy_hasattr_call(self):
        proxy = wrapt.CallableObjectProxy(None)

        self.assertTrue(hasattr(proxy, '__call__'))

    def test_callable_proxy_getattr_call(self):
        proxy = wrapt.CallableObjectProxy(None)

        self.assertTrue(getattr(proxy, '__call__', None), None)

    def test_callable_proxy_is_callable(self):
        proxy = wrapt.CallableObjectProxy(None)

        self.assertTrue(callable(proxy))

class SpecialMethods(unittest.TestCase):

    def test_class_bytes(self):
        if PY3:
            class Class(object):
                def __bytes__(self):
                    return b'BYTES'
            instance = Class()

            proxy = wrapt.ObjectProxy(instance)

            self.assertEqual(bytes(instance), bytes(proxy))

    def test_str_format(self):
        instance = 'abcd'

        proxy = wrapt.ObjectProxy(instance)

        self.assertEqual(format(instance, ''), format(proxy, ''))

    def test_list_reversed(self):
        instance = [1, 2]

        proxy = wrapt.ObjectProxy(instance)

        self.assertEqual(list(reversed(instance)), list(reversed(proxy)))

    def test_complex(self):
        instance = 1.0+2j

        proxy = wrapt.ObjectProxy(instance)

        self.assertEqual(complex(instance), complex(proxy))

    def test_decimal_complex(self):
        import decimal

        instance = decimal.Decimal(123)

        proxy = wrapt.ObjectProxy(instance)

        self.assertEqual(complex(instance), complex(proxy))

    def test_fractions_round(self):
        import fractions

        instance = fractions.Fraction('1/2')

        proxy = wrapt.ObjectProxy(instance)

        self.assertEqual(round(instance), round(proxy))

if __name__ == '__main__':
    unittest.main()
