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

    lock = getattr(context, name, None)

    if lock is None:
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
            # We need to check again for whether the lock we want
            # exists in case two threads were trying to create it
            # at the same time and were competing to create the
            # meta lock.

            lock = getattr(context, name, None)

            if lock is None:
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

class C4(object):

    # XXX This yields undesirable results due to how class method is
    # implemented. The classmethod doesn't bind the method to the class
    # before calling. As a consequence, the decorator wrapper function
    # sees the instance as None with the class being explicitly passed
    # as the first argument. It isn't possible to detect and correct
    # this.

    @classmethod
    @synchronized
    def function2(cls):
        print('function2')

    @staticmethod
    @synchronized
    def function3():
        print('function3')

c4 = C4()

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

    def test_synchronized_inner_staticmethod(self):
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

    def test_synchronized_outer_staticmethod(self):
        _lock0 = getattr(C4.function3, '_synchronized_function_lock', None)
        self.assertEqual(_lock0, None)

        c4.function3()

        _lock1 = getattr(C4.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock1, None)

        C4.function3()

        _lock2 = getattr(C4.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C4.function3()

        _lock3 = getattr(C4.function3, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock3, None)
        self.assertEqual(_lock3, _lock2)

    def test_synchronized_inner_classmethod(self):
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

    def test_synchronized_outer_classmethod(self):
        # XXX If all was good, this would be detected as a class
        # method call, but the classmethod decorator doesn't bind
        # the wrapped function to the class before calling and
        # just calls it direct, explicitly passing the class as
        # first argument. This screws things up. Would be nice if
        # Python were fixed, but that isn't likely to happen.

        #_lock0 = getattr(C4, '_synchronized_class_lock', None)
        _lock0 = getattr(C4.function2, '_synchronized_function_lock', None)
        self.assertEqual(_lock0, None)

        c4.function2()

        #_lock1 = getattr(C4, '_synchronized_class_lock', None)
        _lock1 = getattr(C4.function2, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock1, None)

        C4.function2()

        #_lock2 = getattr(C4, '_synchronized_class_lock', None)
        _lock2 = getattr(C4.function2, '_synchronized_function_lock', None)
        self.assertNotEqual(_lock2, None)
        self.assertEqual(_lock2, _lock1)

        C4.function2()

        #_lock3 = getattr(C4, '_synchronized_class_lock', None)
        _lock3 = getattr(C4.function2, '_synchronized_function_lock', None)
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
