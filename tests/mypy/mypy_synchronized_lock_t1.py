"""
This example demonstrates the usage of synchronized locking.
"""

from threading import Lock

from wrapt import synchronized


@synchronized
def synchronized_function() -> None:
    return


synchronized_function()


lock = Lock()


@synchronized
class SynchronizedClass:

    @synchronized
    def method(self) -> None:
        return

    @synchronized
    @classmethod
    def class_method(cls) -> None:
        return

    @synchronized
    @staticmethod
    def static_method() -> None:
        return

    @synchronized(lock)
    def method_with_lock(self) -> None:
        return

    @synchronized(lock)
    @classmethod
    def class_method_with_lock(cls) -> None:
        return

    @synchronized(lock)
    @staticmethod
    def static_method_with_lock() -> None:
        return


class_instance = SynchronizedClass()

class_instance.method()
class_instance.class_method()
class_instance.static_method()

class_instance.method_with_lock()
class_instance.class_method_with_lock()
class_instance.static_method_with_lock()


def synchronized_lock() -> None:
    with synchronized(lock):
        pass


@synchronized(lock)
def synchronized_lock_function() -> None:
    return


class Dummy:
    pass


object_instance = Dummy()


def synchronized_object() -> None:
    with synchronized(object_instance):
        pass


@synchronized(object_instance)
def synchronized_object_function() -> None:
    return


# Wrong number of arguments to synchronized(). (FAIL)
def synchronized_wrong_args() -> None:
    with synchronized():
        pass
    return


# Call synchronized function with wrong arguments. (FAIL)
def function_with_wrong_args() -> None:
    synchronized_function(1, 2, 3)
