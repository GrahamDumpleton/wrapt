import wrapt  # https://pypi.python.org/pypi/wrapt
import decorator  # https://pypi.python.org/pypi/decorator

def function1():
    pass

def wrapper2(func):
    def _wrapper2(*args, **kwargs):
        return func(*args, **kwargs)
    return _wrapper2

@wrapper2
def function2():
    pass

@wrapt.decorator
def wrapper3(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapper3
def function3():
    pass

@decorator.decorator
def wrapper4(wrapped, *args, **kwargs):
    return wrapped(*args, **kwargs)

@wrapper4
def function4():
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
