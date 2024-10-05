from __future__ import print_function

import operator
import unittest

import wrapt

class TestDecorator(unittest.TestCase):

    def test_no_parameters(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_instance_method_as_decorator(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Instance(object):
            def __init__(self):
                self.count = 0
            @wrapt.decorator
            def decorator(self, wrapped, instance, args, kwargs):
                self.count += 1
                return wrapped(*args, **kwargs)

        instance = Instance()

        @instance.decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(instance.count, 1)

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(instance.count, 2)

    def test_class_method_as_decorator(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        class Instance(object):
            count = 0
            @wrapt.decorator
            @classmethod
            def decorator(cls, wrapped, instance, args, kwargs):
                cls.count += 1
                return wrapped(*args, **kwargs)

        @Instance.decorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(Instance.count, 1)

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))
        self.assertEqual(Instance.count, 2)

    def test_class_type_as_decorator(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        class ClassDecorator(object):
            def __call__(self, wrapped, instance, args, kwargs):
                return wrapped(*args, **kwargs)

        @ClassDecorator
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_class_type_as_decorator_args(self):
        _args = (1, 2)
        _kwargs = {'one': 1, 'two': 2}

        @wrapt.decorator
        class ClassDecorator(object):
            def __init__(self, arg):
                assert arg == 1
            def __call__(self, wrapped, instance, args, kwargs):
                return wrapped(*args, **kwargs)

        @ClassDecorator(arg=1)
        def _function(*args, **kwargs):
            return args, kwargs

        result = _function(*_args, **_kwargs)

        self.assertEqual(result, (_args, _kwargs))

    def test_decorated_function_as_class_attribute(self):

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)
        
        @passthrough
        def function(self):
            pass

        class A:
            _function = function

        self.assertTrue(A._function._self_parent is function)
        self.assertEqual(A._function._self_binding, "function")
        self.assertEqual(A._function._self_owner, A)

        a = A()

        A._function(a)

        self.assertTrue(a._function._self_parent is function)
        self.assertEqual(a._function._self_binding, "function")
        self.assertEqual(a._function._self_owner, A)

        a._function()

        # Test example without using the decorator to show same outcome.

        def xfunction(self):
            pass

        class B:
            _xfunction = xfunction

        b = B()

        B._xfunction(b)

        b._xfunction()

    def test_decorated_function_as_instance_attribute(self):

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @passthrough
        def function(self):
            pass

        class A:
            def __init__(self):
                self._function = function

        a = A()

        self.assertTrue(a._function._self_parent is None)
        self.assertEqual(a._function._self_binding, "function")
        self.assertTrue(a._function._self_owner is None)

        a._function(a)

        bound_a = a._function.__get__(a, A)
        self.assertTrue(bound_a._self_parent is function)
        self.assertEqual(bound_a._self_binding, "function")
        self.assertTrue(bound_a._self_owner is A)

        bound_a()

        # Test example without using the decorator to show same outcome.

        def xfunction(self):
            pass

        class B:
            def __init__(self):
                self._xfunction = xfunction

        b = B()

        b._xfunction(b) 

    def test_decorated_builtin_as_class_attribute(self):

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        function = passthrough(operator.add)

        class A:
            _function = function

        self.assertTrue(A._function._self_parent is None)
        self.assertEqual(A._function._self_binding, "builtin")
        self.assertTrue(A._function._self_owner is None)

        A._function(1, 2)

        a = A()

        self.assertTrue(a._function._self_parent is None)
        self.assertEqual(a._function._self_binding, "builtin")
        self.assertTrue(a._function._self_owner is None)

        a._function(1, 2)

        # Test example without using the decorator to show same outcome.

        class B:
            _xfunction = operator.add

        B._xfunction(1, 2)

        b = B()

        b._xfunction(1, 2)

    def test_call_semantics_for_assorted_decorator_use_cases(self):
        def g1():
            pass

        def g2(self):
            pass

        class C1:
            def __init__(self):
                self.f3 = g1

            def f1(self):
                print("SELF", self)

            f2 = g2

        c1 = C1()

        c1.f2()
        c1.f3()

        class C2:
            f2 = C1.f1
            f3 = C1.f2

        c2 = C2()

        c2.f2()
        c2.f3()

        class C3:
            f2 = c1.f1

        c3 = C3()

        c3.f2()

        @wrapt.decorator
        def passthrough(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class C11:
            @passthrough
            def f1(self):
                print("SELF", self)

        c11 = C11()

        class C12:
            f2 = C11.f1

        c12 = C12()

        c12.f2()

        class C13:
            f2 = c11.f1

        c13 = C13()

        c13.f2()

        C11.f1(c11)
        C12.f2(c12)

    def test_call_semantics_for_assorted_wrapped_descriptor_use_cases(self):
        class A:
            def __call__(self):
                print("A:__call__")

        a = A()

        class B:
            def __call__(self):
                print("B:__call__")
            def __get__(self, obj, type):
                print("B:__get__")
                return self

        b = B()

        class C:
            f1 = a
            f2 = b

        c = C()

        c.f1()
        c.f2()

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class D:
            f1 = wrapper(a)
            f2 = wrapper(b)

        d = D()

        d.f1()
        d.f2()

if __name__ == '__main__':
    unittest.main()
