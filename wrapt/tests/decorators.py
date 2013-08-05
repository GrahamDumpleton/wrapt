import wrapt

@wrapt.generic_decorator
def passthru_generic_decorator(wrapped, obj, cls, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.function_decorator
def passthru_function_decorator(wrapped, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.instancemethod_decorator
def passthru_instancemethod_decorator(wrapped, obj, cls, args, kwargs):
    return wrapped(*args, **kwargs)
