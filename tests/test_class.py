from __future__ import print_function

import unittest
import inspect
import imp

import wrapt

from compat import PY2, PY3, exec_

DECORATORS_CODE = """
import wrapt

@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
"""

decorators = imp.new_module('decorators')
exec_(DECORATORS_CODE, decorators.__dict__, decorators.__dict__)

class class1(object):
    pass

class1o = class1

class1d = decorators.passthru_decorator(class1)

class Testintrospection(unittest.TestCase):

    def test_getmembers(self):
        class1o_members = inspect.getmembers(class1o)
        class1d_members = inspect.getmembers(class1d)
