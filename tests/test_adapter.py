from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from wrapt import six

DECORATORS_CODE = """
import wrapt

def adapter1(func):
    @wrapt.adapter(target=func)
    def _adapter(arg):
        '''adapter documentation'''
        return func(arg, arg)
    return _adapter
"""

decorators = imp.new_module('decorators')
six.exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

def function1(arg1, arg2):
    '''documentation'''
    return arg1, arg2

function1o = function1

@decorators.adapter1
def function1(arg1, arg2):
    '''documentation'''
    return arg1, arg2

function1d = function1

class TestNamingAdapter(unittest.TestCase):

    def test_object_name(self):
        # Test preservation of function __name__ attribute.

        self.assertEqual(function1d.__name__, function1o.__name__)

    def test_object_qualname(self):
        # Test preservation of function __qualname__ attribute.

        try:
            __qualname__ = function1o.__qualname__
        except AttributeError:
            pass
        else:
            self.assertEqual(function1d.__qualname__, __qualname__)

    def test_module_name(self):
       # Test preservation of function __module__ attribute.

        self.assertEqual(function1d.__module__, __name__)

    def test_doc_string(self):
        # Test preservation of function __doc__ attribute from the
        # adapter rather than from the original target wrapped function.

        self.assertEqual(function1d.__doc__, 'adapter documentation')

    def test_argspec(self):
        # Test preservation of function argument specification. It
        # actually needs to match that of the adapter function.

        def _adapter(arg): pass

        function1a_argspec = inspect.getargspec(_adapter)
        function1d_argspec = inspect.getargspec(function1d)
        self.assertEqual(function1a_argspec, function1d_argspec)

    def test_isinstance(self):
        # Test preservation of isinstance() checks.

        self.assertTrue(isinstance(function1d, type(function1o)))

class TestAdapter(unittest.TestCase):

    def test_no_arguments(self):
        events = []

        def _adapter(events):
            def _trace(func):
                @wrapt.adapter(target=func)
                def _wrapper():
                    if events is not None:
                        events.append('in')
                    try:
                        return func()
                    finally:
                        if events is not None:
                            events.append('out')
                return _wrapper
            return _trace

        @_adapter(events=events)
        def _function():
            '''documentation'''
            events.append('call')

        _function()

        self.assertEqual(events, ['in', 'call', 'out'])

    def test_add_argument(self):
        events = []

        def _adapter(events):
            def _trace(func):
                @wrapt.adapter(target=func)
                def _wrapper():
                    if events is not None:
                        events.append('in')
                    try:
                        return func(1)
                    finally:
                        if events is not None:
                            events.append('out')
                return _wrapper
            return _trace

        @_adapter(events=events)
        def _function(*args):
            '''documentation'''
            events.append('call')
            return args

        result = _function()

        self.assertEqual(result, (1,))
        self.assertEqual(events, ['in', 'call', 'out'])

if __name__ == '__main__':
    unittest.main()
