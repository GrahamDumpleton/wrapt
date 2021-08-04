from __future__ import print_function

import inspect
import unittest
import imp
import collections

from typing import Iterable

import wrapt

from compat import PY2, PY3, exec_

DECORATORS_CODE = """
import wrapt
from typing import Iterable

def prototype1(arg1, arg2, arg3=None, *args, **kwargs) -> Iterable: pass
@wrapt.decorator(adapter=prototype1)
def adapter1(wrapped, instance, args, kwargs):
    '''adapter documentation'''
    return wrapped(*args, **kwargs)

def prototype2(arg1, arg2, arg3=None, *args, **kwargs) -> int: pass
@wrapt.decorator(adapter=prototype2)
def adapter2(wrapped, instance, args, kwargs):
    '''adapter documentation'''
    return wrapped(*args, **kwargs)
"""

decorators = imp.new_module('decorators')
exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

def function1(arg1, arg2) -> Iterable:
    '''documentation'''
    return arg1, arg2

function1o = function1

@decorators.adapter1
def function1(arg1, arg2) -> Iterable:
    '''documentation'''
    return arg1, arg2

function1d = function1

def function2(arg1, arg2) -> Iterable:
    '''documentation'''
    return arg1, arg2

function2o = function2

@decorators.adapter1
def function2(arg1, arg2) -> Iterable:
    '''documentation'''
    return arg1, arg2

function2d = function2

class TestAdapterAttributesWithAnnotations(unittest.TestCase):

    def test_annotations(self):
        # Test preservation of function __annotations__ attribute.

        self.assertEqual(function1d.__annotations__, function1o.__annotations__)

class TestArgumentSpecificationWithAnnotations(unittest.TestCase):

    def test_argspec(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        def _adapter(arg1, arg2, arg3=None, *args, **kwargs) -> Iterable: pass

        function1a_argspec = inspect.getfullargspec(_adapter)
        function1d_argspec = inspect.getfullargspec(function1d)
        self.assertEqual(function1a_argspec, function1d_argspec)

        # Now bind the function to an instance. The argspec should
        # still match.

        bound_function1d = function1d.__get__(object(), object)
        bound_function1d_argspec = inspect.getfullargspec(bound_function1d)
        self.assertEqual(function1a_argspec, bound_function1d_argspec)

    def test_signature(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function the
        # prototype of which was supplied via the dummy function.

        if PY2:
            return

        def _adapter(arg1, arg2, arg3=None, *args, **kwargs) -> Iterable: pass

        function1a_signature = str(inspect.signature(_adapter))
        function1d_signature = str(inspect.signature(function1d))
        self.assertEqual(function1a_signature, function1d_signature)

    def test_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(function1d, type(function1o)))

class TestDynamicAdapterWithAnnotations(unittest.TestCase):

    def test_dynamic_adapter_function(self):
        def _adapter1(arg1, arg2, arg3=None, *args, **kwargs) -> Iterable: pass

        argspec1 = inspect.getfullargspec(_adapter1)

        @wrapt.decorator(adapter=argspec1)
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_wrapper_1
        def _function_1():
            pass

        self.assertEqual(inspect.getfullargspec(_function_1), argspec1)

        # Can't use a function signature with adapter factory which has
        # annotations which reference a non builtin type, so use test
        # function which returns int rather than Iterable.

        def _adapter2(arg1, arg2, arg3=None, *args, **kwargs) -> int: pass

        argspec2 = inspect.getfullargspec(_adapter2)

        args = inspect.formatargspec(*argspec2)

        @wrapt.decorator(adapter=args)
        def _wrapper_2(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_wrapper_2
        def _function_2():
           pass

        self.assertEqual(inspect.getfullargspec(_function_2), argspec2)

    def test_dynamic_adapter_instancemethod(self):
        def _adapter1(self, arg1, arg2, arg3=None, *args, **kwargs) -> Iterable: pass

        argspec1 = inspect.getfullargspec(_adapter1)

        @wrapt.decorator(adapter=argspec1)
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class1(object):
            @_wrapper_1
            def function(self):
                pass

        instance1 = Class1()

        self.assertEqual(inspect.getfullargspec(Class1.function), argspec1)
        self.assertEqual(inspect.getfullargspec(instance1.function), argspec1)

        # Can't use a function signature with adapter factory which has
        # annotations which reference a non builtin type.

        def _adapter2(self, arg1, arg2, arg3=None, *args, **kwargs) -> int: pass

        argspec2 = inspect.getfullargspec(_adapter2)

        args = inspect.formatargspec(*argspec2)

        @wrapt.decorator(adapter=args)
        def _wrapper_2(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class2(object):
            @_wrapper_2
            def function(self):
                pass

        instance2 = Class2()

        self.assertEqual(inspect.getfullargspec(Class2.function), argspec2)
        self.assertEqual(inspect.getfullargspec(instance2.function), argspec2)

    def test_dynamic_adapter_classmethod(self):
        def _adapter1(cls, arg1, arg2, arg3=None, *args, **kwargs) -> Iterable: pass

        argspec1 = inspect.getfullargspec(_adapter1)

        @wrapt.decorator(adapter=argspec1)
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class1(object):
            @_wrapper_1
            @classmethod
            def function(cls):
                pass

        instance1 = Class1()

        self.assertEqual(inspect.getfullargspec(Class1.function), argspec1)
        self.assertEqual(inspect.getfullargspec(instance1.function), argspec1)

        # Can't use a function signature with adapter factory which has
        # annotations which reference a non builtin type.

        def _adapter2(cls, arg1, arg2, arg3=None, *args, **kwargs) -> int: pass

        argspec2 = inspect.getfullargspec(_adapter2)

        args = inspect.formatargspec(*argspec2)

        @wrapt.decorator(adapter=args)
        def _wrapper_2(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        class Class2(object):
            @_wrapper_2
            @classmethod
            def function(self):
                pass

        instance2 = Class2()

        self.assertEqual(inspect.getfullargspec(Class2.function), argspec2)
        self.assertEqual(inspect.getfullargspec(instance2.function), argspec2)

    def test_adapter_factory(self):
        def factory(wrapped):
            argspec = inspect.getfullargspec(wrapped)
            argspec.args.insert(0, 'arg0')
            return argspec

        @wrapt.decorator(adapter=wrapt.adapter_factory(factory))
        def _wrapper_1(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        @_wrapper_1
        def _function_1(arg1, arg2) -> Iterable:
            pass

        argspec = inspect.getfullargspec(_function_1)

        self.assertEqual(argspec.args, ['arg0', 'arg1', 'arg2'])
        self.assertEqual(argspec.annotations, {'return': Iterable})

if __name__ == '__main__':
    unittest.main()
