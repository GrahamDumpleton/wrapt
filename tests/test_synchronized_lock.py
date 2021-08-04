from __future__ import print_function

import unittest

import wrapt

from compat import PYXY

@wrapt.synchronized
def function():
    print('function')

class C1(object):

    @wrapt.synchronized
    def function1(self):
        print('function1')

    @wrapt.synchronized
    @classmethod
    def function2(cls):
        print('function2')

    @wrapt.synchronized
    @staticmethod
    def function3():
        print('function3')

c1 = C1()

@wrapt.synchronized
class C2(object):
    pass

@wrapt.synchronized
class C3:
    pass

class C4(object):

    # Prior to Python 3.9, this yields undesirable results due to how
    # class method is implemented. The classmethod doesn't bind the
    # method to the class before calling. As a consequence, the
    # decorator wrapper function sees the instance as None with the
    # class being explicitly passed as the first argument. It isn't
    # possible to detect and correct this. For more details see:
    # https://bugs.python.org/issue19072

    @classmethod
    @wrapt.synchronized
    def function2(cls):
        print('function2')

    @staticmethod
    @wrapt.synchronized
    def function3():
        print('function3')

c4 = C4()

class C5(object):

    def __bool__(self):
        return False
    __nonzero__=__bool__

    @wrapt.synchronized
    def function1(self):
        print('function1')

c5 = C5()

class TestSynchronized(unittest.TestCase):

    def test_synchronized_function(self):
        _lock0 = getattr(function, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        function()

        _lock1 = getattr(function, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        function()

        _lock2 = getattr(function, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        function()

        _lock3 = getattr(function, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_inner_staticmethod(self):
        _lock0 = getattr(C1.function3, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        c1.function3()

        _lock1 = getattr(C1.function3, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        C1.function3()

        _lock2 = getattr(C1.function3, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C1.function3()

        _lock3 = getattr(C1.function3, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_outer_staticmethod(self):
        _lock0 = getattr(C4.function3, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        c4.function3()

        _lock1 = getattr(C4.function3, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        C4.function3()

        _lock2 = getattr(C4.function3, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C4.function3()

        _lock3 = getattr(C4.function3, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_inner_classmethod(self):
        if hasattr(C1, '_synchronized_lock'):
            del C1._synchronized_lock

        _lock0 = getattr(C1, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        c1.function2()

        _lock1 = getattr(C1, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        C1.function2()

        _lock2 = getattr(C1, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C1.function2()

        _lock3 = getattr(C1, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_outer_classmethod(self):
        # Prior to Python 3.9 this isn't detected as a class method
        # call, as the classmethod decorator doesn't bind the wrapped
        # function to the class before calling and just calls it direct,
        # explicitly passing the class as first argument. For more
        # details see: https://bugs.python.org/issue19072

        if PYXY < (3, 9):
            _lock0 = getattr(C4.function2, '_synchronized_lock', None)
        else:
            _lock0 = getattr(C4, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        c4.function2()

        if PYXY < (3, 9):
            _lock1 = getattr(C4.function2, '_synchronized_lock', None)
        else:
            _lock1 = getattr(C4, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        C4.function2()

        if PYXY < (3, 9):
            _lock2 = getattr(C4.function2, '_synchronized_lock', None)
        else:
            _lock2 = getattr(C4, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C4.function2()

        if PYXY < (3, 9):
            _lock3 = getattr(C4.function2, '_synchronized_lock', None)
        else:
            _lock3 = getattr(C4, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_instancemethod(self):
        if hasattr(C1, '_synchronized_lock'):
            del C1._synchronized_lock

        _lock0 = getattr(c1, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        C1.function1(c1)

        _lock1 = getattr(c1, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        c1.function1()

        _lock2 = getattr(c1, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c1.function1()

        _lock3 = getattr(c1, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

        del c1._synchronized_lock

        C1.function2()

        _lock4 = getattr(C1, '_synchronized_lock', None)
        self.assertNotEqual(_lock4, None)

        c1.function1()

        _lock5 = getattr(c1, '_synchronized_lock', None)
        self.assertNotEqual(_lock5, None)
        self.assertNotEqual(_lock5, _lock4)

    def test_synchronized_type_new_style(self):
        if hasattr(C2, '_synchronized_lock'):
            del C2._synchronized_lock

        _lock0 = getattr(C2, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        c2 = C2()

        _lock1 = getattr(C2, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        c2 = C2()

        _lock2 = getattr(C2, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c2 = C2()

        _lock3 = getattr(C2, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_type_old_style(self):
        if hasattr(C3, '_synchronized_lock'):
            del C3._synchronized_lock

        _lock0 = getattr(C3, '_synchronized_lock', None)
        self.assertEqual(_lock0, None)

        c2 = C3()

        _lock1 = getattr(C3, '_synchronized_lock', None)
        self.assertNotEqual(_lock1, None)

        c2 = C3()

        _lock2 = getattr(C3, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c2 = C3()

        _lock3 = getattr(C3, '_synchronized_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_false_instance(self):
        c5.function1()

        self.assertEqual(bool(c5), False)

        _lock1 = getattr(C5, '_synchronized_lock', None)
        self.assertEqual(_lock1, None)

        _lock2 = getattr(c5, '_synchronized_lock', None)
        self.assertNotEqual(_lock2, None)

if __name__ == '__main__':
    unittest.main()
