Benchmarks
==========

The **wrapt** module ensures that your decorators will work in all
situations. The implementation therefore does not take the shortcuts that
people usually take with decorators of using function closures. Instead it
implements the wrappers as a class, which also acts as a descriptor.
Ensuring correctness though does come at an additional cost in runtime
overhead. The following attempts to quantify what that overhead is and
compare it to other solutions typically used.

Results were collected under MacOS X Mountain Lion on a 2012 model MacBook
Pro, running with Python 2.7.

Undecorated Calls
-----------------

These tests provide a baseline for comparing decorated functions against a
normal undecorated function call.

**Test Code**::

    def function1():
        pass

    class Class(object):

        def function1(self):
            pass

        @classmethod
        def function1cm(cls):
            pass

        @staticmethod
        def function1sm():
            pass

**Test Results**::

    $ python -m timeit -s 'import benchmarks' 'benchmarks.function1()'
    10000000 loops, best of 3: 0.132 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function1()'
    10000000 loops, best of 3: 0.143 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function1cm()'
    1000000 loops, best of 3: 0.217 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function1cm()'
    10000000 loops, best of 3: 0.159 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function1sm()'
    1000000 loops, best of 3: 0.199 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function1sm()'
    10000000 loops, best of 3: 0.13 usec per loop

Note that differences between calling the class and static methods via the
class vs the instance are possibly more to do with needing to traverse
the dotted path.

Function Closures
-----------------

These tests provide results for decorated functions where the decorators are
implemented using function closures.

**Test Code**::

    def wrapper2(func):
        def _wrapper2(*args, **kwargs):
            return func(*args, **kwargs)
        return _wrapper2

    @wrapper2
    def function2():
        pass

    class Class(object):

        @wrapper2
        def function2(self):
            pass

        @classmethod
        @wrapper2
        def function2cmi(cls):
            pass

        @staticmethod
        @wrapper2
        def function2smi():
            pass

**Test Results**::

    $ python -m timeit -s 'import benchmarks' 'benchmarks.function2()'
    1000000 loops, best of 3: 0.326 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function2()'
    1000000 loops, best of 3: 0.382 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function2cmi()'
    1000000 loops, best of 3: 0.46 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function2cmi()'
    1000000 loops, best of 3: 0.384 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function2smi()'
    1000000 loops, best of 3: 0.389 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function2smi()'
    1000000 loops, best of 3: 0.319 usec per loop

Note that decorators implemented as function closures cannot be added around
staticmethod and classmethod decorators and must be added inside of those
decorators.

wrapt.decorator
---------------

These tests provides results for decorated functions where the decorators
are implemented using the **wrapt** module. Separate results are provided
for when using the C extension and when using the pure Python
implementation.

**Test Code**::

    @wrapt.decorator
    def wrapper3(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    @wrapper3
    def function3():
        pass

    class Class(object):

        @wrapper3
        def function3(self):
            pass

        @wrapper3
        @classmethod
        def function3cmo(cls):
            pass

        @classmethod
        @wrapper3
        def function3cmi(cls):
            pass

        @wrapper3
        @staticmethod
        def function3smo():
            pass

        @staticmethod
        @wrapper3
        def function3smi():
            pass

**Test Results (C Extension)**::

    $ python -m timeit -s 'import benchmarks' 'benchmarks.function3()'
    1000000 loops, best of 3: 0.384 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3()'
    1000000 loops, best of 3: 0.699 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmo()'
    1000000 loops, best of 3: 0.901 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmo()'
    1000000 loops, best of 3: 0.84 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmi()'
    1000000 loops, best of 3: 0.531 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmi()'
    1000000 loops, best of 3: 0.455 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smo()'
    1000000 loops, best of 3: 1.22 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smo()'
    1000000 loops, best of 3: 1.21 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smi()'
    1000000 loops, best of 3: 0.454 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smi()'
    1000000 loops, best of 3: 0.379 usec per loop

Note that results for where the decorator is inside that of the classmethod
decorator is quite a bit less than that where it is outside. This due to a
potential bug in Python whereby it doesn't apply the descriptor protocol to
what the classmethod decorator wraps. Instead it is executing a straight
function call, which has less overhead.

**Test Results (Pure Python)**::

    $ python -m timeit -s 'import benchmarks' 'benchmarks.function3()'
    1000000 loops, best of 3: 0.727 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3()'
    100000 loops, best of 3: 6.36 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmo()'
    100000 loops, best of 3: 6.42 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmo()'
    100000 loops, best of 3: 6.36 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3cmi()'
    1000000 loops, best of 3: 0.853 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3cmi()'
    1000000 loops, best of 3: 0.803 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smo()'
    100000 loops, best of 3: 6.93 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smo()'
    100000 loops, best of 3: 6.97 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function3smi()'
    1000000 loops, best of 3: 0.77 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function3smi()'
    1000000 loops, best of 3: 0.727 usec per loop

Note that results for where the decorator is inside that of the classmethod
decorator is quite a bit less than that where it is outside. This due to a
potential bug in Python whereby it doesn't apply the descriptor protocol to
what the classmethod decorator wraps. Instead it is executing a straight
function call, which has less overhead.

decorator.decorator
-------------------

These tests provides results for decorated functions where the decorators
are implemented using the **decorator** module available from PyPi.

**Test Code**::

    @decorator.decorator
    def wrapper4(wrapped, *args, **kwargs):
        return wrapped(*args, **kwargs)

    @wrapper4
    def function4():
        pass

    class Class(object):

        @wrapper4
        def function4(self):
            pass

        @classmethod
        @wrapper4
        def function4cmi(cls):
            pass

        @staticmethod
        @wrapper4
        def function4smi():
            pass

**Test Results**::

    $ python -m timeit -s 'import benchmarks' 'benchmarks.function4()'
    1000000 loops, best of 3: 0.465 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function4()'
    1000000 loops, best of 3: 0.537 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function4cmi()'
    1000000 loops, best of 3: 0.606 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function4cmi()'
    1000000 loops, best of 3: 0.533 usec per loop

    $ python -m timeit -s 'import benchmarks' 'benchmarks.Class.function4smi()'
    1000000 loops, best of 3: 0.532 usec per loop

    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.function4smi()'
    1000000 loops, best of 3: 0.456 usec per loop

Note that decorators implemented using the decorator module cannot be added
around staticmethod and classmethod decorators and must be added inside of
those decorators.
