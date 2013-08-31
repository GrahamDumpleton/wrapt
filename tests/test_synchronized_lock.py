from __future__ import print_function

import unittest
import threading
import inspect

import wrapt

@wrapt.decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        if inspect.isclass(wrapped):
            # Wrapped function is a class and we are creating an
            # instance of the class. Synchronisation is against
            # the type.

            context = wrapped
            name = '_synchronized_type_lock'

        else:
            # Wrapped function is a normal function or static method.
            # Synchronisation is against the individual function. We
            # need to traverse __wrapped__ if it exists in case we are
            # dealing with a bound static method.

            context = getattr(wrapped, '__wrapped__', wrapped)
            name = '_synchronized_function_lock'

    else:
        if inspect.isclass(instance):
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

class C1(object):

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

c1 = C1()

@synchronized
class C2(object):
    pass

@synchronized
class C3:
    pass

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
        _lock0 = getattr(C1.function3, '_synchronized_function_lock', None)
        self.assertEqual(_lock0, None)

        c1.function3()

        _lock1 = getattr(C1.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock1, None)

        C1.function3()

        _lock2 = getattr(C1.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C1.function3()

        _lock3 = getattr(C1.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_classmethod(self):
        _lock0 = getattr(C1, '_synchronized_class_lock', None)
        self.assertEqual(_lock0, None)

        c1.function2()

        _lock1 = getattr(C1, '_synchronized_class_lock', None)
        self.assertNotEqual(_lock1, None)

        C1.function2()

        _lock2 = getattr(C1, '_synchronized_class_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C1.function2()

        _lock3 = getattr(C1, '_synchronized_class_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_syncrhonized_instancemethod(self):
        _lock0 = getattr(c1, '_synchronized_instance_lock', None)
        self.assertEqual(_lock0, None)

        C1.function1(c1)

        _lock1 = getattr(c1, '_synchronized_instance_lock', None)
        self.assertNotEqual(_lock1, None)

        c1.function1()

        _lock2 = getattr(c1, '_synchronized_instance_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c1.function1()

        _lock3 = getattr(c1, '_synchronized_instance_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_syncrhonized_type(self):
        _lock0 = getattr(C2, '_synchronized_type_lock', None)
        self.assertEqual(_lock0, None)

        c2 = C2()

        _lock1 = getattr(C2, '_synchronized_type_lock', None)
        self.assertNotEqual(_lock1, None)

        c2 = C2()

        _lock2 = getattr(C2, '_synchronized_type_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c2 = C2()

        _lock3 = getattr(C2, '_synchronized_type_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_syncrhonized_type_old_style(self):
        _lock0 = getattr(C3, '_synchronized_type_lock', None)
        self.assertEqual(_lock0, None)

        c2 = C3()

        _lock1 = getattr(C3, '_synchronized_type_lock', None)
        self.assertNotEqual(_lock1, None)

        c2 = C3()

        _lock2 = getattr(C3, '_synchronized_type_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        c2 = C3()

        _lock3 = getattr(C3, '_synchronized_type_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

if __name__ == '__main__':
    unittest.main()
