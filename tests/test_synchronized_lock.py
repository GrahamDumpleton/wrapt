from __future__ import print_function

import unittest
import threading

import wrapt

@wrapt.decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        # Wrapped function is a normal function or static method.
        # Synchronisation is against the individual function. We
        # need to traverse __wrapped__ if it exists in case we are
        # dealing with a bound static method.

        context = getattr(wrapped, '__wrapped__', wrapped)
        name = '_synchronized_function_lock'

    elif isinstance(instance, type):
        # Wrapped function is a class method. Synchronisation is
        # against the class type.

        context = instance
        name = '_synchronized_class_lock'

    else:
        # Wrapped function is an instance method. Synchronisation
        # is against the class instance.

        context = instance
        name = '_synchronized_instance_lock'

    try:
        lock = getattr(context, name)

    except AttributeError:
        # There is no existing lock defined for the context we
        # are dealing with so we need to create one. This needs
        # to be done in a way to guarantee there is only one
        # created, even if multiple threads try and create it at
        # the same time. We can't always use the setdefault()
        # method on the __dict__ for the context. This is the
        # case where the context is a class, as __dict__ is
        # actually a dictproxy. What we therefore do is use a
        # meta lock on this wrapper itself, to control the
        # creation and assignment of the lock attribute against
        # the context.

        meta_lock = synchronized.__wrapped__.__dict__.setdefault(
                '_synchronized_meta_lock', threading.RLock())

        with meta_lock:
            lock = threading.Lock()
            setattr(context, name, lock)

    with lock:
        return wrapped(*args, **kwargs)

@synchronized
def function():
    print('function')

class Class(object):

    @synchronized
    def function1(self):
        print('function1')

    @synchronized
    @classmethod
    def function2(cls):
        print('function2')

    @synchronized
    @staticmethod
    def function3():
        print('function3')

class TestAdapterAttributes(unittest.TestCase):

    def test_synchronized_function(self):
        _lock0 = getattr(function, '_synchronized_function_lock', None)
        self.assertEqual(_lock0, None)

        function()

        _lock1 = getattr(function, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock1, None)

        function()

        _lock2 = getattr(function, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        function()

        _lock3 = getattr(function, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_staticmethod(self):
        _lock0 = getattr(Class.function3, '_synchronized_function_lock', None)
        self.assertEqual(_lock0, None)

        Class.function3()

        _lock1 = getattr(Class.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock1, None)

        Class.function3()

        _lock2 = getattr(Class.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        Class.function3()

        _lock3 = getattr(Class.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_classmethod(self):
        _lock0 = getattr(Class, '_synchronized_class_lock', None)
        self.assertEqual(_lock0, None)

        Class.function2()

        _lock1 = getattr(Class, '_synchronized_class_lock', None)
        self.assertNotEqual(_lock1, None)

        Class.function2()

        _lock2 = getattr(Class, '_synchronized_class_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        Class.function2()

        _lock3 = getattr(Class, '_synchronized_class_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_syncrhonized_instancemethod(self):
        c = Class()

        _lock0 = getattr(c, '_synchronized_instance_lock', None)
        self.assertEqual(_lock0, None)

        c.function1()

        _lock1 = getattr(c, '_synchronized_instance_lock', None)
        self.assertNotEqual(_lock1, None)

        c.function1()

        _lock2 = getattr(c, '_synchronized_instance_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c.function1()

        _lock3 = getattr(c, '_synchronized_instance_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

if __name__ == '__main__':
    unittest.main()
