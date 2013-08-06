import wrapt

@wrapt.decorator
def passthru_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.function_decorator
def passthru_function_decorator(wrapped, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.method_decorator
def passthru_method_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
