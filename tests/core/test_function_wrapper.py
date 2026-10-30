import unittest

import wrapt


class TestClassInheritence(unittest.TestCase):

    def test_function_type_inheritence(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def _function(*args, **kwargs):
            return args, kwargs

        self.assertTrue(isinstance(_function, wrapt.FunctionWrapper))
        # self.assertTrue(isinstance(_function, wrapt.BaseObjectProxy))

    def test_instancemethod_type_inheritence(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            def function(self, args, **kwargs):
                return args, kwargs

            self.assertTrue(isinstance(function, wrapt.FunctionWrapper))
            # self.assertTrue(isinstance(function, wrapt.BaseObjectProxy))

        instance = Class()

        self.assertFalse(isinstance(instance.function, wrapt.FunctionWrapper))
        # self.assertTrue(isinstance(instance.function, wrapt.BaseObjectProxy))

    def test_classmethod_type_inheritence(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            @classmethod
            def function(cls, *args, **kwargs):
                return args, kwargs

            self.assertTrue(isinstance(function, wrapt.FunctionWrapper))
            # self.assertTrue(isinstance(function, wrapt.BaseObjectProxy))

        instance = Class()

        self.assertFalse(isinstance(instance.function, wrapt.FunctionWrapper))
        # self.assertTrue(isinstance(instance.function, wrapt.BaseObjectProxy))

    def test_staticmethod_type_inheritence(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            @staticmethod
            def function(*args, **kwargs):
                return args, kwargs

            self.assertTrue(isinstance(function, wrapt.FunctionWrapper))
            # self.assertTrue(isinstance(function, wrapt.BaseObjectProxy))

        instance = Class()

        self.assertFalse(isinstance(instance.function, wrapt.FunctionWrapper))
        # self.assertTrue(isinstance(instance.function, wrapt.BaseObjectProxy))


class TestAttributeAccess(unittest.TestCase):

    def test_function_attributes(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        def function1(*args, **kwargs):
            return args, kwargs

        function2 = decorator2(function1)

        self.assertEqual(function2.__wrapped__, function1)
        self.assertEqual(function2._self_wrapper, decorator1)
        self.assertEqual(function2._self_binding, "function")

    def test_instancemethod_attributes(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            def function1(self, *args, **kwargs):
                return args, kwargs

            function2 = decorator2(function1)

            self.assertEqual(function2.__wrapped__, function1)
            self.assertEqual(function2._self_wrapper, decorator1)
            self.assertEqual(function2._self_binding, "function")

        instance = Class()

        self.assertEqual(instance.function2.__wrapped__, instance.function1)
        self.assertEqual(instance.function2._self_instance, instance)
        self.assertEqual(instance.function2._self_wrapper, decorator1)

    def test_classmethod_attributes(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            @classmethod
            def function1(cls, *args, **kwargs):
                return args, kwargs

            function2 = decorator2(function1)

            self.assertEqual(function2.__wrapped__, function1)
            self.assertEqual(function2._self_wrapper, decorator1)
            self.assertEqual(function2._self_binding, "classmethod")

        instance = Class()

        self.assertEqual(instance.function2.__wrapped__, instance.function1)
        self.assertEqual(instance.function2._self_instance, instance)
        self.assertEqual(instance.function2._self_wrapper, decorator1)

    def test_staticmethod_attributes(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            @staticmethod
            def function1(*args, **kwargs):
                return args, kwargs

            function2 = decorator2(function1)

            self.assertEqual(function2.__wrapped__, function1)
            self.assertEqual(function2._self_wrapper, decorator1)
            self.assertEqual(function2._self_binding, "staticmethod")

    def test_instancemethod_attributes_external_class(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            def function1(self, *args, **kwargs):
                return args, kwargs

        function2 = decorator2(Class.function1)

        self.assertEqual(function2._self_wrapper, decorator2)

        # We can't identify this as being an instance method in
        # Python 3 because there is no concept of unbound methods.
        # We therefore don't try for Python 2 either.

        self.assertEqual(function2._self_binding, "function")

    def test_classmethod_attributes_external_class(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            @classmethod
            def function1(cls, *args, **kwargs):
                return args, kwargs

        function2 = decorator2(Class.function1)

        self.assertEqual(function2._self_wrapper, decorator2)
        self.assertEqual(function2._self_binding, "classmethod")

    def test_staticmethod_attributes_external_class(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            @staticmethod
            def function1(*args, **kwargs):
                return args, kwargs

        function2 = decorator2(Class.function1)

        self.assertEqual(function2._self_wrapper, decorator2)

        # We can't identify this as being a static method because
        # the binding has resulted in a normal function being returned.

        self.assertEqual(function2._self_binding, "function")

    def test_instancemethod_attributes_external_instance(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            def function1(self, *args, **kwargs):
                return args, kwargs

        function2 = decorator2(Class().function1)

        self.assertEqual(function2._self_wrapper, decorator2)

        self.assertEqual(function2._self_binding, "instancemethod")

    def test_classmethod_attributes_external_instance(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            @classmethod
            def function1(cls, *args, **kwargs):
                return args, kwargs

        function2 = decorator2(Class().function1)

        self.assertEqual(function2._self_wrapper, decorator2)
        self.assertEqual(function2._self_binding, "classmethod")

    def test_staticmethod_attributes_external_instance(self):
        def decorator1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        decorator2 = wrapt.decorator(decorator1)

        class Class:
            @staticmethod
            def function1(*args, **kwargs):
                return args, kwargs

        function2 = decorator2(Class().function1)

        self.assertEqual(function2._self_wrapper, decorator2)

        # We can't identify this as being a static method because
        # the binding has resulted in a normal function being returned.

        self.assertEqual(function2._self_binding, "function")


class TestParentReference(unittest.TestCase):

    def test_function_decorator(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def function():
            pass

        self.assertEqual(function._self_parent, None)

    def test_class_decorator(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        class Class:
            pass

        self.assertEqual(Class._self_parent, None)

    def test_nested_class_decorator(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            class Nested:
                pass

        self.assertEqual(Class.Nested._self_parent, None)

    def test_instancemethod(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            def function_im(self):
                pass

        c = Class()

        self.assertNotEqual(c.function_im._self_parent, None)
        self.assertNotEqual(Class.function_im._self_parent, None)

    def test_classmethod(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            @classmethod
            def function_cm(cls):
                pass

        self.assertNotEqual(Class.function_cm._self_parent, None)

    def test_staticmethod_inner(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            @staticmethod
            def function_sm_inner():
                pass

        self.assertNotEqual(Class.function_sm_inner._self_parent, None)


class TestGuardArgument(unittest.TestCase):

    def test_boolean_false_guard_on_decorator(self):
        @wrapt.decorator(enabled=False)
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def function():
            pass

        self.assertFalse(isinstance(function, wrapt.FunctionWrapper))

    def test_boolean_true_guard_on_decorator(self):
        @wrapt.decorator(enabled=True)
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_decorator
        def function():
            pass

        self.assertTrue(isinstance(function, wrapt.FunctionWrapper))

    def test_boolean_dynamic_guard_on_decorator(self):
        class Guard:
            value = True

            def __nonzero__(self):
                return self.value

            __bool__ = __nonzero__

        guard = Guard()

        result = []

        @wrapt.decorator(enabled=guard)
        def _decorator(wrapped, instance, args, kwargs):
            result.append(1)
            return wrapped(*args, **kwargs)

        @_decorator
        def function():
            pass

        self.assertTrue(isinstance(function, wrapt.FunctionWrapper))

        function()

        self.assertNotEqual(len(result), 0)

        result = []
        guard.value = False

        function()

        self.assertEqual(len(result), 0)

    def test_function_guard_on_decorator(self):
        value = True

        def guard():
            return value

        result = []

        @wrapt.decorator(enabled=guard)
        def _decorator(wrapped, instance, args, kwargs):
            result.append(1)
            return wrapped(*args, **kwargs)

        @_decorator
        def function():
            pass

        self.assertTrue(isinstance(function, wrapt.FunctionWrapper))

        function()

        self.assertNotEqual(len(result), 0)

        result = []
        value = False

        function()

        self.assertEqual(len(result), 0)

    def test_guard_on_instancemethod(self):
        value = True

        def guard():
            return value

        result = []

        @wrapt.decorator(enabled=guard)
        def _decorator(wrapped, instance, args, kwargs):
            result.append(1)
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            def function(self):
                pass

        c = Class()

        self.assertTrue(isinstance(c.function, wrapt.BoundFunctionWrapper))

        c.function()

        self.assertNotEqual(len(result), 0)

        result = []
        value = False

        self.assertTrue(isinstance(c.function, wrapt.BoundFunctionWrapper))

        c.function()

        self.assertEqual(len(result), 0)


class TestDerivedFunctionWrapper(unittest.TestCase):

    def test_override_bound_type(self):

        class _BoundFunctionWrapper(wrapt.BoundFunctionWrapper):
            ATTRIBUTE = 1

        class _FunctionWrapper(wrapt.FunctionWrapper):
            __bound_function_wrapper__ = _BoundFunctionWrapper

        def function():
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        _wrapper = _FunctionWrapper(function, wrapper)

        self.assertTrue(isinstance(_wrapper, _FunctionWrapper))

        instance = object()

        _bound_wrapper = _wrapper.__get__(instance, type(instance))

        self.assertTrue(isinstance(_bound_wrapper, _BoundFunctionWrapper))
        self.assertEqual(_bound_wrapper.ATTRIBUTE, 1)


class TestFunctionBinding(unittest.TestCase):

    def test_double_binding(self):

        def function():
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        _wrapper = wrapt.FunctionWrapper(function, wrapper)

        self.assertTrue(isinstance(_wrapper, wrapt.FunctionWrapper))

        instance = object()

        _bound_wrapper_1 = _wrapper.__get__(instance, type(instance))

        self.assertTrue(_bound_wrapper_1._self_parent is _wrapper)

        self.assertTrue(isinstance(_bound_wrapper_1, wrapt.BoundFunctionWrapper))
        self.assertEqual(_bound_wrapper_1._self_instance, instance)

        _bound_wrapper_2 = _bound_wrapper_1.__get__(instance, type(instance))

        self.assertTrue(_bound_wrapper_2._self_parent is _wrapper)

        self.assertTrue(isinstance(_bound_wrapper_2, wrapt.BoundFunctionWrapper))
        self.assertEqual(
            _bound_wrapper_2._self_instance, _bound_wrapper_1._self_instance
        )

        self.assertTrue(_bound_wrapper_1 is _bound_wrapper_2)

    def test_re_bind_after_none(self):

        def function(self):
            pass

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        _wrapper = wrapt.FunctionWrapper(function, wrapper)

        self.assertTrue(isinstance(_wrapper, wrapt.FunctionWrapper))

        instance = object()

        _bound_wrapper_1 = _wrapper.__get__(None, type(instance))

        _bound_wrapper_1(instance)

        self.assertTrue(_bound_wrapper_1._self_parent is _wrapper)

        self.assertTrue(isinstance(_bound_wrapper_1, wrapt.BoundFunctionWrapper))
        self.assertEqual(_bound_wrapper_1._self_instance, None)

        _bound_wrapper_2 = _bound_wrapper_1.__get__(instance, type(instance))

        self.assertTrue(_bound_wrapper_2._self_parent is _wrapper)

        self.assertTrue(isinstance(_bound_wrapper_2, wrapt.BoundFunctionWrapper))
        self.assertEqual(_bound_wrapper_2._self_instance, instance)

        _bound_wrapper_2()

        self.assertTrue(_bound_wrapper_1 is not _bound_wrapper_2)


class TestBindingValues(unittest.TestCase):

    def check_fallback_binding(self, wrapped, expected_instance, binding):
        calls = []

        def wrapper(wrapped, instance, args, kwargs):
            calls.append((wrapped, instance, args, kwargs))
            return "ok"

        bound = wrapt.BoundFunctionWrapper(
            wrapped, object(), wrapper, None, binding
        )

        self.assertEqual(bound("value", flag=True), "ok")
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], wrapped)
        self.assertIs(calls[0][1], expected_instance)
        self.assertEqual(calls[0][2], ("value",))
        self.assertEqual(calls[0][3], {"flag": True})

    def test_non_string_binding_free_function(self):
        def function():
            pass

        for binding in (object(), None, 0, False, b"function", [], {}):
            with self.subTest(binding_type=type(binding).__name__):
                self.check_fallback_binding(function, None, binding)

    def test_non_string_binding_class_method(self):
        class Target:
            @classmethod
            def method(cls):
                pass

        for binding in (object(), None, 0, False, b"function", [], {}):
            with self.subTest(binding_type=type(binding).__name__):
                self.check_fallback_binding(Target.method, Target, binding)

    def test_unknown_string_binding_keeps_fallback(self):
        def function():
            pass

        self.check_fallback_binding(function, None, "custom")

    def test_disabled_non_string_binding_calls_wrapped(self):
        def function(value):
            return value

        def wrapper(wrapped, instance, args, kwargs):
            self.fail("Disabled wrapper must not be called")

        for enabled in (False, lambda: False):
            with self.subTest(enabled=enabled):
                bound = wrapt.BoundFunctionWrapper(
                    function, None, wrapper, enabled, object()
                )
                self.assertEqual(bound("value"), "value")


class TestInvalidWrapper(unittest.TestCase):

    def test_none_for_wrapped(self):

        def run(*args):
            def _wrapper(wrapped, instance, args, kwargs):
                return wrapped(*args, **kwargs)

            wrapper = wrapt.FunctionWrapper(None, _wrapper)
            wrapper.__get__(list(), list)()

        self.assertRaises(TypeError, run, ())


class TestInvalidCalling(unittest.TestCase):

    def test_missing_self_via_class(self):
        @wrapt.decorator
        def _decorator(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class:
            @_decorator
            def method(self):
                pass

        def run(*args):
            Class.method()

        self.assertRaises(TypeError, run, ())


if __name__ == "__main__":
    unittest.main()
